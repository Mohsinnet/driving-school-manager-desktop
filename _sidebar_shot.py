# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

tmp = tempfile.mkdtemp(prefix="dsm_shot_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

w = app.App(role="admin", key=None, auth=app.Auth(), username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1200x800+40+40")
w.deiconify()
w.update()
w.focus_force()
w.update()

c1 = w.db.add_candidate({
    "full_name": "محمد أمين", "phone": "0612345678",
    "category": "B", "total_price": 3500, "paid1": 1500,
    "exam1_date": (date.today() + timedelta(days=3)).isoformat(),
})
c2 = w.db.add_candidate({"full_name": "سعاد بنعلي", "phone": "0622222222"})
w.db.soft_delete_candidate(c2)
w.refresh()
w.update()
w.tree.selection_set(str(c1))
w.update()

print("before show:", w._sb_open)
w._show_sidebar()
print("after show:", w._sb_open, w._sidebar.place_info(),
      w._sidebar.winfo_ismapped())
w.attributes("-topmost", True)
w.update()
print("after update:", w._sb_open, w._sidebar.place_info(),
      w._sidebar.winfo_ismapped())
time.sleep(0.6)
w.update()
print("after sleep:", w._sb_open, w._sidebar.place_info(),
      w._sidebar.winfo_ismapped())

from PIL import ImageGrab
x = w.winfo_rootx()
y = w.winfo_rooty()
img = ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()))
img.save("_sidebar_preview2.png")
print("saved", img.size)
print("edit enabled:", w._nav_items["edit"]["enabled"],
      "trash badge:", w._nav_items["trash"]["badge"].cget("text"),
      "exam badge:", w._nav_items["exams"]["badge"].cget("text"))

w.attributes("-topmost", False)
w._hide_sidebar()
w.db.close()
w.destroy()
shutil.rmtree(tmp, ignore_errors=True)
