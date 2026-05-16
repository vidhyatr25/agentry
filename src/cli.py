import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

from .core.config import build_settings, load_json, validate_workflow
from .core.loader import load_plugins
from .core.registry import registry
from .core.secrets import SecretResolver
from .core.telemetry import Telemetry
from .core.workflow import WorkflowRunner

ROOT = Path(__file__).resolve().parent.parent


def _logger():
    logger = logging.getLogger("workflow-studio")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def _sync_site(state_dir, site_data):
    site_data.mkdir(parents=True, exist_ok=True)
    for name in ("stats.json", "published.json", "usage.json", "runs.json"):
        src = state_dir / name
        if src.exists():
            shutil.copy2(src, site_data / name)
    wf_out = site_data / "workflows"
    wf_out.mkdir(parents=True, exist_ok=True)
    index = []
    for path in sorted((ROOT / "workflows").glob("*.json")):
        shutil.copy2(path, wf_out / path.name)
        try:
            data = json.loads(path.read_text())
            index.append({"file": path.name, "name": data.get("name"),
                          "description": data.get("description", ""),
                          "schedule": data.get("schedule")})
        except json.JSONDecodeError:
            continue
    (wf_out / "index.json").write_text(json.dumps(index, indent=2))
    (site_data / "providers.json").write_text(json.dumps(registry.snapshot(), indent=2))
    for cfg in ("schedules.yaml", "settings.yaml"):
        src = ROOT / "config" / cfg
        if src.exists():
            shutil.copy2(src, site_data / cfg)


def _execute_workflow(workflow_path, dry_run, settings_path, workdir_root, state_dir, logger):
    load_plugins()
    workflow = validate_workflow(load_json(workflow_path))
    settings = build_settings(settings_path, workflow)
    run_id = f"{workflow['name']}-{int(time.time())}"
    secrets = SecretResolver(lenient=dry_run)
    telemetry = Telemetry(
        pricing=settings.get("telemetry", {}).get("pricing", {}), run_id=run_id
    )
    workdir = Path(workdir_root) / run_id
    runner = WorkflowRunner(workflow, settings, secrets, telemetry, workdir, dry_run, logger)
    state_dir = Path(state_dir)
    status = "ok"
    try:
        result = runner.run()
    except Exception as exc:
        status = "error"
        result = {"workflow": workflow["name"], "status": "error", "error": secrets.mask(str(exc))}
        logger.error(secrets.mask(str(exc)))
    finally:
        telemetry.persist(state_dir / "usage.json")
        runs_file = state_dir / "runs.json"
        runs = []
        if runs_file.exists():
            try:
                runs = json.loads(runs_file.read_text())
            except json.JSONDecodeError:
                runs = []
        runs.append(
            {
                "run_id": run_id,
                "workflow": workflow["name"],
                "status": result.get("status", status),
                "dry_run": dry_run,
                "at": time.time(),
                "totals": telemetry.totals(),
            }
        )
        runs_file.parent.mkdir(parents=True, exist_ok=True)
        runs_file.write_text(json.dumps(runs[-500:], indent=2))
        _sync_site(state_dir, ROOT / "site" / "data")
    logger.info(f"run finished: {workflow['name']} -> {result.get('status', status)}")
    return result


def cmd_run(args):
    logger = _logger()
    result = _execute_workflow(
        args.workflow, args.dry_run, args.settings, args.workdir, args.state_dir, logger
    )
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "ok" else 1


def cmd_scheduler(args):
    import yaml

    from .core.scheduler import due_in_window, utcnow

    logger = _logger()
    sched_path = Path(args.schedules)
    if not sched_path.exists():
        logger.error(f"no schedule file at {sched_path}")
        return 1
    config = yaml.safe_load(sched_path.read_text()) or {}
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    sched_state_file = state_dir / "schedule_state.json"
    sched_state = {}
    if sched_state_file.exists():
        try:
            sched_state = json.loads(sched_state_file.read_text())
        except json.JSONDecodeError:
            sched_state = {}
    now = utcnow()
    summary = []
    ran = 0
    for entry in config.get("workflows", []):
        wf = entry.get("file")
        enabled = entry.get("enabled", False)
        cron = entry.get("cron", "")
        last_run = sched_state.get(wf)
        record = {"file": wf, "enabled": enabled, "cron": cron,
                  "last_run": last_run, "due": False, "ran": False}
        if enabled and cron and Path(ROOT / wf).exists():
            is_due, hit = due_in_window(cron, now, args.window, last_run)
            record["due"] = is_due
            if is_due and not args.dry_check:
                logger.info(f"scheduler: running due workflow {wf}")
                result = _execute_workflow(
                    str(ROOT / wf), bool(entry.get("dry_run", False)),
                    args.settings, args.workdir, args.state_dir, logger
                )
                sched_state[wf] = hit or now.replace(tzinfo=__import__("datetime").timezone.utc).timestamp()
                record["ran"] = True
                record["status"] = result.get("status")
                ran += 1
        summary.append(record)
    sched_state_file.write_text(json.dumps(sched_state, indent=2))
    site_data = ROOT / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)
    (state_dir / "schedule.json").write_text(
        json.dumps({"checked_at": time.time(), "workflows": summary}, indent=2)
    )
    shutil.copy2(state_dir / "schedule.json", site_data / "schedule.json")
    _sync_site(state_dir, site_data)
    logger.info(f"scheduler: {ran} workflow(s) ran, {len(summary)} registered")
    print(json.dumps(summary, indent=2, default=str))
    return 0


def cmd_validate(args):
    load_plugins()
    workflow = validate_workflow(load_json(args.workflow))
    print(f"valid workflow: {workflow['name']} ({len(workflow['steps'])} steps)")
    return 0


def cmd_providers(_args):
    load_plugins()
    print(json.dumps(registry.snapshot(), indent=2))
    return 0


def cmd_list(args):
    wf_dir = Path(args.dir)
    for path in sorted(wf_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            print(f"{path.name}: {data.get('name')} - {data.get('description', '')}")
        except json.JSONDecodeError:
            print(f"{path.name}: INVALID JSON")
    return 0


def cmd_doctor(args):
    import shutil as _sh

    load_plugins()
    ok = True

    def check(label, passed, detail=""):
        nonlocal ok
        mark = "OK " if passed else "FAIL"
        if not passed:
            ok = False
        print(f"[{mark}] {label}{(' - ' + detail) if detail else ''}")

    check("ffmpeg on PATH", bool(_sh.which("ffmpeg")), "CI installs it; needed locally for real runs")
    check("ffprobe on PATH", bool(_sh.which("ffprobe")))
    for mod in ("requests", "yaml", "PIL", "edge_tts", "gtts"):
        try:
            __import__(mod)
            check(f"python dep: {mod}", True)
        except ImportError:
            check(f"python dep: {mod}", False, "pip install -r requirements.txt")

    workflow = validate_workflow(load_json(args.workflow))
    check(f"workflow valid: {workflow['name']}", True, f"{len(workflow['steps'])} steps")

    secrets = SecretResolver(lenient=True)
    needed = set()
    secrets.referenced_names(workflow.get("providers", {}), needed)
    secrets.referenced_names(workflow.get("steps", []), needed)
    for name in sorted(needed):
        present = bool(secrets.get(name, required=False))
        check(f"secret available: {name}", present, "" if present else "set as GitHub Secret before live run")

    print("\n" + ("READY for deployment." if ok else
                   "Issues above. Secrets can be missing locally (set them in GitHub); "
                   "ffmpeg is provided by the Action runner."))
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="workflow-studio")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("workflow")
    run.add_argument("--settings", default=str(ROOT / "config" / "settings.yaml"))
    run.add_argument("--workdir", default=str(ROOT / "runs"))
    run.add_argument("--state-dir", default=str(ROOT / "state"))
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(func=cmd_run)

    validate = sub.add_parser("validate")
    validate.add_argument("workflow")
    validate.set_defaults(func=cmd_validate)

    providers = sub.add_parser("providers")
    providers.set_defaults(func=cmd_providers)

    listing = sub.add_parser("list")
    listing.add_argument("--dir", default=str(ROOT / "workflows"))
    listing.set_defaults(func=cmd_list)

    doctor = sub.add_parser("doctor")
    doctor.add_argument("workflow", nargs="?", default=str(ROOT / "workflows" / "kids_video_youtube.json"))
    doctor.set_defaults(func=cmd_doctor)

    scheduler = sub.add_parser("scheduler")
    scheduler.add_argument("--schedules", default=str(ROOT / "config" / "schedules.yaml"))
    scheduler.add_argument("--settings", default=str(ROOT / "config" / "settings.yaml"))
    scheduler.add_argument("--workdir", default=str(ROOT / "runs"))
    scheduler.add_argument("--state-dir", default=str(ROOT / "state"))
    scheduler.add_argument("--window", type=int, default=35)
    scheduler.add_argument("--dry-check", action="store_true")
    scheduler.set_defaults(func=cmd_scheduler)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
