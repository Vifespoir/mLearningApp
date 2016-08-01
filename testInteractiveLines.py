""" Example demonstrating turning lines on and off - with JS only
"""

import numpy as np

from bokeh.io import output_file, show
from bokeh.layouts import row
from bokeh.palettes import Viridis3
from bokeh.plotting import figure
from bokeh.models import CheckboxGroup, CustomJS, ColumnDataSource

output_file("line_on_off.html", title="line_on_off.py example")

def lineCode(line):
    return """
        if ({1} in checkbox.active) {{
            {0}.visible = true
        }} else {{
            {0}.visible = false
        }}
    """.format(line, int(line[1:]))

p = figure()
props = dict(line_width=4, line_alpha=0.7)
x = np.linspace(0, 4 * np.pi, 100)
lines = {}
lines['l0'] = p.line(x, np.sin(x), color=Viridis3[0], legend="Line 0", **props)
lines['l1'] = p.line(x, 4 * np.cos(x), color=Viridis3[1], legend="Line 1", **props)
lines['l2'] = p.line(x, np.tan(x), color=Viridis3[2], legend="Line 2", **props)

code = [lineCode(k) for k in lines.keys()]
code = '\n'.join(code)
print(code)

callback = CustomJS(code=code, args={})
checkbox = CheckboxGroup(labels=["Line 0", "Line 1", "Line 2"], active=[0, 1, 2], callback=callback, width=100)
lines['checkbox'] = checkbox
callback.args = lines
print(callback.args)
layout = row(checkbox, p)
show(layout)
