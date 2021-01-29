"""ASCII art rendering script"""
import obs
import obs.props as OP

import requests
from time import sleep

VALUES = {}

PROPERTIES = [
    OP.Checkbox("on", "Enabled", default=False),
    OP.Group("group1", "Frame Grab", elements=[
        OP.Number("interval", "Time (s)", 0.1, 5, 0.1, default=1.0),
        OP.TextSources("out", "Text Output"),
        OP.SourceList("framesource", "Source"),
        OP.Text("key", "Key", default=" .-ox+OXG&"),
    ]),
]

def do_switching():
    while True:
        if not VALUES["on"] or not VALUES["key"] or not VALUES["framesource"] or not VALUES["out"]:
            return
        if VALUES["framesource"].name == VALUES["out"].name:
            return
        key = VALUES["key"]
        sleep(max(VALUES["interval"], 1))
        data = VALUES["framesource"].get_frame()
        text = '\n'.join(''.join(key[int(i / 256.0 * len(key))] for i in d) for d in data)
        VALUES["out"]["text"] = text


def on_update():
    if VALUES["on"]:
        obs.run(do_switching)


obs.ready(globals())
