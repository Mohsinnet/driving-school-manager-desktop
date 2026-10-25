# -*- coding: utf-8 -*-
import sys
import tkinter as tk
from tkinter import font as tkfont

r = tk.Tk()
r.withdraw()
fams = sorted(tkfont.families())
for want in ("Segoe Fluent Icons", "Segoe MDL2 Assets", "Segoe UI Symbol"):
    print(want, "->", want in fams)

try:
    from fontTools.ttLib import TTFont
    print("fontTools: yes")
    path = r""
    import os
    for f in ("segmdl2.ttf", "SegoeIcons.ttf"):
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
        if os.path.exists(p):
            path = p
            break
    print("font file:", path)
    if path:
        font = TTFont(path)
        cmap = font.getBestCmap()
        for cp in (0xE710, 0xE70F, 0xE749, 0xE8C7, 0xE74D, 0xE738,
                   0xE9D2, 0xE787, 0xE896, 0xE898, 0xE713, 0xE716,
                   0xE946, 0xE7E8, 0xE711, 0xE700, 0xE7BE):
            print(hex(cp), cmap.get(cp))
        font.close()
except Exception as e:
    print("fontTools: no ->", e)
r.destroy()
