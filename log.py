"""Warning collection: each distinct message is reported once, at the end,
prefixed with the slide it concerns (set by document.read_body)."""

warnings = []
where = ""          # e.g. 'slide 5 "Results"'; empty outside frames


def warn(msg):
    msg = "%s: %s" % (where, msg) if where else msg
    if msg not in warnings:
        warnings.append(msg)
