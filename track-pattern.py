"""Pattern tracking script"""
import math
import obs
import obs.props as OP

import requests
from time import sleep

VALUES = {
    "_state": None,
}

def reset_data():
    VALUES["_state"] = None


PROPERTIES = [
    OP.Checkbox("on", "Enabled", default=False),
    OP.Group("trackinggroup", "Tracking", elements=[
        OP.VideoSources("framesource", "Source"),
        OP.Number("interval", "Time (s)", 0.01, 5, 0.01, default=1.0),
        OP.Number("pointX", "Point X", 0, 1.0, 0.01, default=0.5),
        OP.Number("pointY", "Point Y", 0, 1.0, 0.01, default=0.5),
        OP.Number("search", "Search radius", 0.01, 1.0, 0.01, default=0.1),
        OP.Button("resetView", "Reset", reset_data),
    ]),
    OP.Group("reactiongroup", "Reaction", elements=[
        OP.SourceList("movesource", "Move"),
        OP.Number("movescale", "Scale", 0.5, 100.0, 0.5, default=1.0),
    ]),
    OP.Group("debug", "Debugging", checkable=True, default=False, elements=[
        OP.TextSources("debugcoords", "Show Offset"),
    ]),
]


class TrackState:
    def __init__(self):
        self.pattern = None
        self.x = self.y = 0
        self.radius = 0
        self._points = None
        self._points_radius = None

    def _generate_points(self, radius):
        if self._points and self._points_radius == radius:
            return self._points
        self._points = pts = []
        self._points_radius = radius
        r2 = radius * radius
        for y in range(-radius, radius + 1):
            pts.append((y, []))
            for x in range(-radius, radius + 1):
                if x * x + y * y <= r2:
                    pts[-1][1].append(x)
                elif x > 0:
                    break
        return pts

    def get_pixels(self, frame, dx=0, dy=0):
        ba = bytearray()
        cy = len(frame)
        cx = len(frame[0])
        for y, xs in self._generate_points(self.radius):
            py = self.y + y + dy
            if 0 <= py < cy:
                row = frame[py]
                for x in xs:
                    px = self.x + x + dx
                    if 0 <= px < cx:
                        ba.append(row[px])
                    else:
                        ba.append(128)
            else:
                for _ in xs:
                    ba.append(128)
        return ba


def distance(x, y):
    return sum(abs(i2 - i1) for i1, i2 in zip(x, y))


def do_tracking():
    while True:
        if not (VALUES["on"] and VALUES["framesource"]):
            return
        sleep(max(VALUES["interval"], 0.05))
        with VALUES["framesource"].get_frame() as frame:
            f = list(frame)

        state = VALUES.get("_state")
        if not state:
            VALUES["_state"] = state = TrackState()
            state.x = int(len(f[0]) * VALUES["pointX"])
            state.y = int(len(f) * VALUES["pointY"])
            state.radius = int(math.ceil(VALUES["search"] * max(len(f), len(f[0]))))
            state.pattern = state.get_pixels(f)
            continue

        best = 0, 0
        best_p = state.get_pixels(f)
        best_v = distance(state.pattern, best_p)
        ry = range(0, state.radius + 1, 2)
        rx = range(1, state.radius + 1, 2)
        for dy_a in ry:
            for dy in [-dy_a, dy_a]:
                for dx_a in rx:
                    for dx in [-dx_a, dx_a]:
                        p = state.get_pixels(f, dx, dy)
                        v = distance(state.pattern, p)
                        if v < best_v:
                            best = dx, dy
                            best_p = p
                            best_v = v
        state.x += best[0]
        state.y += best[1]

        if VALUES["debug"] and VALUES["debugcoords"]:
            VALUES["debugcoords"]["text"] = "({}, {})".format(state.x, state.y)

        s = VALUES["movescale"]
        p = VALUES["movesource"].get_pos()
        VALUES["movesource"].set_pos(p[0] + best[0] * s, p[1] + best[1] * s)


def on_update():
    if VALUES["on"]:
        obs.run(do_tracking)


obs.ready(globals())
