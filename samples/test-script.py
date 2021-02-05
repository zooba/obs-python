"""My testing script"""
import obs
import obs.props as OP

import requests
from time import sleep

PROPERTIES = [
    OP.Button("button", "Button Text", print, doc="Clicking this button will do something"),
    OP.Button("disbutton", "Dis Button", print, enabled=False, doc="'Dis' means 'Disabled' :3"),
    OP.List("font", "Font", files=True),
    OP.Group("urltext", "Text from URL", checkable=True, default=False, elements=[
        OP.Text("url", "URL", default="https://example.com/"),
        OP.Number("interval", "Time", 1, 30, 0.5, suffix=" s"),
        OP.TextSources("source", "Source"),
    ]),
]

VALUES = {}

def do_switching():
    while True:
        if not VALUES["urltext"]:
            return
        sleep(max(VALUES["interval"], 1))
        #r = requests.get(VALUES["url"])
        #r.raise_for_status()
        #VALUES["source"]["text"] = r.text


def on_update():
    print(VALUES)
    if VALUES["urltext"] and VALUES["url"] and VALUES["interval"] and VALUES["source"]:
        obs.run(do_switching)


obs.ready(globals())
