"""Synchronise multiple sources"""

import obs
import obs.props as OP

SOURCE_IDS = range(1, 11)

VALUES = {}


def _generate_properties(ids):
    for i in ids:
        yield OP.SourceList(f"source{i}", f"Source {i}")
        yield OP.Number(f"delay{i}", "Sync", -5000, 5000, 50, slider=True, default=0)


PROPERTIES = [
    *_generate_properties(SOURCE_IDS)
]


def set_sync_delay(source, delay):
    if not (-10000 < delay < 10000):
        #print("Invalid delay:", delay)
        return
    for f in source.get_filters():
        if f.get_type() in {"async_delay_filter", "gpu_delay"}:
            #print(source.name, f["delay_ms",].get("delay_ms", 0), "to", delay, "(video)")
            f["delay_ms"] = delay
            source.set_sync_offset(0)
            break
    else:
        #print(source.name, source.get_sync_offset() / 1000000, "to", delay, "(audio)")
        source.set_sync_offset(delay * 1000000)


def do_update():
    min_delay = None
    offsets = []
    for i in SOURCE_IDS:
        s = VALUES.get(f"source{i}")
        if s:
            d = VALUES.get(f"delay{i}", 0)
            if min_delay is None or d < min_delay:
                min_delay = d
            offsets.append((s, d))
    if min_delay is not None:
        for s, d in offsets:
            set_sync_delay(s, d - min_delay)


def on_update():
    obs.run(do_update)


obs.ready(globals())
