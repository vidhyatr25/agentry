import time
import traceback

from .context import Context
from .errors import BudgetError, StepError, WorkflowError
from .factory import build_step


class WorkflowRunner:
    def __init__(self, workflow, settings, secrets, telemetry, workdir, dry_run, logger):
        self.workflow = workflow
        self.ctx = Context(
            workflow=workflow,
            settings=settings,
            secrets=secrets,
            telemetry=telemetry,
            workdir=workdir,
            dry_run=dry_run,
            logger=logger,
        )

    def _required_secret_names(self):
        names = set()
        self.ctx.secrets.referenced_names(self.workflow.get("providers", {}), names)
        self.ctx.secrets.referenced_names(
            self.workflow.get("nodes") or self.workflow.get("steps", []), names
        )
        return names

    def preflight(self):
        if self.ctx.dry_run:
            return
        required = self._required_secret_names()
        if required:
            self.ctx.secrets.require(required)

    def _topo_order(self, nodes):
        by_id = {}
        for i, n in enumerate(nodes):
            nid = n.get("id") or n.get("type") or f"node{i}"
            n["id"] = nid
            if nid in by_id:
                raise WorkflowError(f"duplicate node id: {nid}")
            by_id[nid] = n
        order, temp, done = [], set(), set()

        def visit(nid, stack):
            if nid in done:
                return
            if nid in stack:
                raise WorkflowError(f"cycle detected at node '{nid}'")
            stack.add(nid)
            for dep in by_id[nid].get("needs", []) or []:
                if dep not in by_id:
                    raise WorkflowError(f"node '{nid}' needs unknown node '{dep}'")
                visit(dep, stack)
            stack.discard(nid)
            done.add(nid)
            order.append(by_id[nid])

        for n in nodes:
            visit(n["id"], set())
        return order

    def _truthy(self, value):
        return str(value).strip().lower() not in ("", "false", "0", "none", "no")

    def run(self):
        self.preflight()
        runtime = self.ctx.settings.get("runtime", {})
        retries = int(runtime.get("retries", 1))
        backoff = int(runtime.get("retry_backoff_sec", 5))
        budget = self.ctx.settings.get("budget", {})
        max_cost = float(budget.get("max_cost_usd", 0) or 0)
        max_tokens = int(budget.get("max_tokens", 0) or 0)
        result = {
            "workflow": self.workflow.get("name"),
            "started_at": time.time(),
            "dry_run": self.ctx.dry_run,
            "mode": "graph" if self.workflow.get("nodes") else "pipeline",
            "steps": [],
            "status": "running",
        }
        if self.workflow.get("nodes"):
            specs = self._topo_order([dict(n) for n in self.workflow["nodes"]])
        else:
            specs = self.workflow["steps"]

        for index, spec in enumerate(specs):
            label = spec.get("id") or spec.get("type")
            when = spec.get("when")
            if when is not None and not self._truthy(self.ctx.render(when)):
                self.ctx.logger.info(f"node[{index}] {label} skipped (when falsy)")
                result["steps"].append({"type": spec.get("type"), "id": label,
                                        "status": "skipped"})
                continue
            self._run_step(spec, index, label, result, retries, backoff)
            breach = self.ctx.telemetry.over_budget(max_cost, max_tokens)
            if breach:
                result["status"] = "aborted_budget"
                result["ended_at"] = time.time()
                result["totals"] = self.ctx.telemetry.totals()
                self.ctx.logger.error(f"budget breached after '{label}': {breach}")
                raise BudgetError(breach)

        result["status"] = "ok"
        result["ended_at"] = time.time()
        result["totals"] = self.ctx.telemetry.totals()
        result["published"] = self.ctx.get("published")
        return result

    def _run_step(self, spec, index, label, result, retries, backoff):
        step = build_step(spec)
        attempt = 0
        while True:
            attempt += 1
            started = time.time()
            try:
                self.ctx.logger.info(f"node[{index}] {label} (attempt {attempt})")
                step.run(self.ctx)
                result["steps"].append({
                    "type": spec.get("type"), "id": label, "status": "ok",
                    "attempts": attempt,
                    "duration_sec": round(time.time() - started, 2),
                })
                return
            except Exception as exc:
                msg = self.ctx.secrets.mask(str(exc))
                self.ctx.logger.error(
                    f"node[{index}] {label} failed: {msg}\n"
                    + self.ctx.secrets.mask(traceback.format_exc())
                )
                if attempt <= retries:
                    time.sleep(backoff)
                    continue
                result["steps"].append({
                    "type": spec.get("type"), "id": label, "status": "error",
                    "attempts": attempt, "error": msg,
                })
                result["status"] = "error"
                result["ended_at"] = time.time()
                result["totals"] = self.ctx.telemetry.totals()
                raise StepError(f"step '{label}' failed: {msg}") from exc
