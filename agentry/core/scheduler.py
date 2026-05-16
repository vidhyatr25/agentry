import datetime as _dt


def _field_match(expr, value, lo, hi):
    for part in str(expr).split(","):
        part = part.strip()
        if part in ("*", "?"):
            return True
        step = 1
        base = part
        if "/" in part:
            base, step_s = part.split("/")
            step = int(step_s)
            if base in ("*", ""):
                base = f"{lo}-{hi}"
        if "-" in base:
            a, b = base.split("-")
            start, end = int(a), int(b)
        else:
            if step == 1:
                if int(base) == value:
                    return True
                continue
            start, end = int(base), hi
        if start <= value <= end and (value - start) % step == 0:
            return True
    return False


def cron_match(expr, when):
    fields = expr.split()
    if len(fields) != 5:
        return False
    minute, hour, dom, month, dow = fields
    cron_dow = (when.weekday() + 1) % 7
    return (
        _field_match(minute, when.minute, 0, 59)
        and _field_match(hour, when.hour, 0, 23)
        and _field_match(dom, when.day, 1, 31)
        and _field_match(month, when.month, 1, 12)
        and (_field_match(dow, cron_dow, 0, 6) or _field_match(dow, 7 if cron_dow == 0 else cron_dow, 0, 7))
    )


def due_in_window(expr, now, window_minutes, last_run_epoch):
    start = now - _dt.timedelta(minutes=window_minutes)
    cursor = start.replace(second=0, microsecond=0)
    last_hit = None
    while cursor <= now:
        if cron_match(expr, cursor):
            last_hit = cursor
        cursor += _dt.timedelta(minutes=1)
    if last_hit is None:
        return False, None
    hit_epoch = last_hit.replace(tzinfo=_dt.timezone.utc).timestamp()
    if last_run_epoch is not None and last_run_epoch >= hit_epoch:
        return False, None
    return True, hit_epoch


def utcnow():
    return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
