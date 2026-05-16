import json
import time
from pathlib import Path


class Telemetry:
    def __init__(self, pricing=None, run_id=None):
        self.pricing = pricing or {}
        self.run_id = run_id or str(int(time.time()))
        self.events = []
        self.started_at = time.time()

    def _price(self, provider, model):
        table = self.pricing.get(provider, {})
        return table.get(model) or table.get("default") or {"in": 0.0, "out": 0.0}

    def record_llm(self, provider, model, prompt_tokens, completion_tokens, step=None):
        rate = self._price(provider, model)
        cost = (prompt_tokens / 1000.0) * rate.get("in", 0.0) + (
            completion_tokens / 1000.0
        ) * rate.get("out", 0.0)
        self.events.append(
            {
                "kind": "llm",
                "provider": provider,
                "model": model,
                "step": step,
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens),
                "cost_usd": round(cost, 6),
                "ts": time.time(),
            }
        )
        return cost

    def record_usage(self, kind, provider, units=1, cost_usd=0.0, step=None, meta=None):
        self.events.append(
            {
                "kind": kind,
                "provider": provider,
                "step": step,
                "units": units,
                "cost_usd": round(float(cost_usd), 6),
                "meta": meta or {},
                "ts": time.time(),
            }
        )

    def totals(self):
        prompt = sum(e.get("prompt_tokens", 0) for e in self.events)
        completion = sum(e.get("completion_tokens", 0) for e in self.events)
        cost = sum(e.get("cost_usd", 0.0) for e in self.events)
        by_provider = {}
        for e in self.events:
            p = e.get("provider", "unknown")
            agg = by_provider.setdefault(
                p, {"total_tokens": 0, "cost_usd": 0.0, "calls": 0}
            )
            agg["total_tokens"] += e.get("total_tokens", 0)
            agg["cost_usd"] = round(agg["cost_usd"] + e.get("cost_usd", 0.0), 6)
            agg["calls"] += 1
        return {
            "run_id": self.run_id,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
            "cost_usd": round(cost, 6),
            "duration_sec": round(time.time() - self.started_at, 2),
            "by_provider": by_provider,
            "calls": len(self.events),
        }

    def over_budget(self, max_cost_usd=0.0, max_tokens=0):
        totals = self.totals()
        if max_cost_usd and totals["cost_usd"] > max_cost_usd:
            return f"cost ${totals['cost_usd']:.4f} exceeded cap ${max_cost_usd}"
        if max_tokens and totals["total_tokens"] > max_tokens:
            return f"tokens {totals['total_tokens']} exceeded cap {max_tokens}"
        return None

    def persist(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if path.exists():
            try:
                history = json.loads(path.read_text())
            except json.JSONDecodeError:
                history = []
        history.append({"totals": self.totals(), "events": self.events})
        history = history[-500:]
        path.write_text(json.dumps(history, indent=2))
