"""My testing script"""
import obs
import obs.props as OP

import requests
from time import sleep

PROPERTIES = [
    OP.Text("url", "URL"),
    OP.Number("interval", "Time (s)", 1, 30, 0.5),
    OP.TextSources("source", "Source"),
]

VALUES = {}

def do_switching():
    while True:
        r = requests.get(VALUES["url"])
        r.raise_for_status()
        VALUES["source"]["text"] = r.text
        sleep(max(VALUES["interval"], 1))


def on_update():
    if VALUES["url"] and VALUES["interval"] and VALUES["source"]:
        obs.run(do_switching)


obs.ready(globals())
