"""Pattern tracking script"""
import math
import obs
import obs.props as OP

import requests
from time import sleep, perf_counter

VALUES = {
    "_state": None,
    "_stop": True,
}

def on_start():
    print("starting")
    if VALUES["_stop"]:
        obs.run(do_tracking)
    VALUES["_state"] = None
    VALUES["_stop"] = False
    for p in PROPERTIES:
        print(p.name)
        if p.name == "stop":
            p.enable()
            break
    return True

def on_stop():
    print("stopping")
    VALUES["_stop"] = True
    for p in PROPERTIES:
        print(p.name)
        if p.name == "stop":
            p.disable()
            break
    return True

def on_framesource_changed(v):
    VALUES["_state"] = None

def on_search_changed(v):
    VALUES["_state"] = None


PROPERTIES = [
    OP.Button("start", "Start", on_start),
    OP.Button("stop", "Stop", on_stop, enabled=False),
    OP.Group("trackinggroup", "Tracking", elements=[
        OP.VideoSources("framesource", "Source"),
        OP.Number("interval", "Time (s)", 0.01, 5, 0.01, default=1.0),
        OP.Number("pointX", "Point X", 0, 1.0, 0.01, default=0.5),
        OP.Number("pointY", "Point Y", 0, 1.0, 0.01, default=0.5),
        OP.Number("search", "Search radius", 0.01, 1.0, 0.01, default=0.1),
    ]),
    OP.Group("reactiongroup", "Reaction", elements=[
        OP.SourceList("movesource", "Move"),
        OP.Number("movescale", "Scale", 0.5, 100.0, 0.5, default=1.0),
    ]),
    OP.Group("debug", "Debugging", checkable=True, default=False, elements=[
        OP.TextSources("debugcoords", "Show Offset"),
        OP.TextSources("debugtime", "Show Time"),
    ]),
]


class TrackState:
    def __init__(self):
        self.pattern = None
        self.x = self.y = 0
        self.last_dx = self.last_dy = 0
        self.radius = 0
        self._points = {}

    def _generate_points(self, radius, dx, dy):
        try:
            return self._points[radius, dx, dy]
        except KeyError:
            pass
        self._points[radius, dx, dy] = pts = []
        r2 = radius * radius
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= r2:
                    pts.append((x + dx, y + dy))
                elif x > 0:
                    break
        return pts

    def get_pixels(self, frame, dx=0, dy=0):
        pts = self._generate_points(
            self.radius,
            int(dx + self.x),
            int(dy + self.y),
        )
        return frame[pts]


def distance(x, y):
    return sum(abs(i2 - i1) for i1, i2 in zip(x, y))


def do_tracking():
    while not VALUES["_stop"]:
        fs = VALUES.get("framesource")
        if not fs:
            sleep(0.5)
            continue

        sleep(max(VALUES["interval"], 0.01))
        start = perf_counter()
        with fs.get_frame() as f:
            state = VALUES.get("_state")
            if not state:
                VALUES["_state"] = state = TrackState()
                state.x = f.width * VALUES["pointX"]
                state.y = f.height * VALUES["pointY"]
                state.radius = int(math.ceil(VALUES["search"] * max(f.width, f.height)))
                state.pattern = state.get_pixels(f)
                continue

            off = best = 0, 0
            best_p = state.get_pixels(f)
            best_v = distance(state.pattern, best_p)

            def check(dx, dy):
                nonlocal best, best_p, best_v
                p = state.get_pixels(f, off[0] + dx, off[1] + dy)
                v = distance(state.pattern, p)
                if v < best_v:
                    best = off[0] + dx, off[1] + dy
                    best_p = p
                    best_v = v

            if state.last_dx or state.last_dy:
                check(state.last_dx, state.last_dy)
                off = best

            ry = range(1, state.radius + 1, 4)
            rx = range(2, state.radius + 1, 4)
            for dy_a in ry:
                for dy in [-dy_a, dy_a]:
                    for dx_a in rx:
                        for dx in [-dx_a, dx_a]:
                            check(dx, dy)
            off = best
            for dy in [-1, 1]:
                for dx in [-1, 1]:
                    check(dx, dy)

            state.last_dx, state.last_dy = best
            state.x += best[0]
            state.y += best[1]

        if VALUES["debug"] and VALUES["debugcoords"]:
            VALUES["debugcoords"]["text"] = "({}, {})".format(state.x, state.y)
        if VALUES["debug"] and VALUES["debugtime"]:
            VALUES["debugtime"]["text"] = "{:.3f}s".format(perf_counter() - start)

        s = VALUES["movescale"]
        p = VALUES["movesource"].get_pos()
        VALUES["movesource"].set_pos(p[0] + best[0] * s, p[1] + best[1] * s)


def on_update():
    pass


obs.ready(globals())
