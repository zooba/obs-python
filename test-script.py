"""My testing script"""
import obs
import obs.props as OP

PROPERTIES = [
    OP.Text("text1", "My Text Box"),
    OP.SourceList("source", "Source", "text*", editable=True),
    OP.SourceList("source2", "Source2", "*source"),
    OP.Text("text2", "Password", password=True),
    OP.Text("text3", "Lines", multiline=True),
    OP.Path("path1", "File", open_file=True, filter="*.txt"),
    OP.Path("path2", "Directory", open_directory=True),
    OP.DropDown("items1", "Items 1", editable=True, items=["A", "B", ("C", "c")]),
    OP.DropDown("items2", "Items 2", editable=True, type=int, items=[1, 2, 3]),
    OP.DropDown("items3", "Items 3", type=float, items=[("One", 1.0), ("Two", 2), 3.0]),
]

VALUES = {}

def on_update():
    print(VALUES)


obs.ready(globals())
