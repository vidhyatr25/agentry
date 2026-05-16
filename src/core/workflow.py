import time
import traceback

from .context import Context
from .errors import StepError, WorkflowError
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
        self.ctx.secrets.referenced_names(self.workflow.get("steps", []), names)
        return names

    def preflight(self):
        if self.ctx.dry_run:
            return
        required = self._required_secret_names()
        if required:
            self.ctx.secrets.require(required)

    def run(self):
        self.preflight()
        runtime = self.ctx.settings.get("runtime", {})
        retries = int(runtime.get("retries", 1))
        backoff = int(runtime.get("retry_backoff_sec", 5))
        result = {
            "workflow": self.workflow.get("name"),
            "started_at": time.time(),
            "dry_run": self.ctx.dry_run,
            "steps": [],
            "status": "running",
        }
        for index, spec in enumerate(self.workflow["steps"]):
            step = build_step(spec)
            label = spec.get("type")
            attempt = 0
            while True:
                attempt += 1
                started = time.time()
                try:
                    self.ctx.logger.info(f"step[{index}] {label} (attempt {attempt})")
                    step.run(self.ctx)
                    result["steps"].append(
                        {
                            "type": label,
                            "status": "ok",
                            "attempts": attempt,
                            "duration_sec": round(time.time() - started, 2),
                        }
                    )
                    break
                except Exception as exc:
                    msg = self.ctx.secrets.mask(str(exc))
                    self.ctx.logger.error(
                        f"step[{index}] {label} failed: {msg}\n"
                        + self.ctx.secrets.mask(traceback.format_exc())
                    )
                    if attempt <= retries:
                        time.sleep(backoff)
                        continue
                    result["steps"].append(
                        {
                            "type": label,
                            "status": "error",
                            "attempts": attempt,
                            "error": msg,
                        }
                    )
                    result["status"] = "error"
                    result["ended_at"] = time.time()
                    result["totals"] = self.ctx.telemetry.totals()
                    raise StepError(f"step '{label}' failed: {msg}") from exc
        result["status"] = "ok"
        result["ended_at"] = time.time()
        result["totals"] = self.ctx.telemetry.totals()
        result["published"] = self.ctx.get("published")
        return result
