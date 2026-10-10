"""Assemble the self-contained interactive page.

Usage: python -I src/build_page.py  ->  output/page/kimchi_premium.html
The chart kit (src/page/chartkit.js.html) is shared with the Strategy 1 page, Crowded Carry.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page")
tpl = open(os.path.join(here, "template.html"), encoding="utf-8").read()
kit = open(os.path.join(here, "chartkit.js.html"), encoding="utf-8").read()
kit = kit.replace("/* Crowded Carry: small dependency-free SVG/canvas chart kit.", "/* Chart kit shared with the Crowded Carry page: small dependency-free SVG/canvas charts.")
js = open(os.path.join(here, "page.js"), encoding="utf-8").read()
data = json.load(open(os.path.join(C.PAGE, "page_data.json"), encoding="utf-8"))
blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
html = tpl + "\n<script>const DATA = " + blob + ";</script>\n" + kit + "\n<script>" + js + "</script>\n"
out = os.path.join(C.PAGE, "kimchi_premium.html")
open(out, "w", encoding="utf-8").write(html)
print(out, len(html) // 1024, "KB")
