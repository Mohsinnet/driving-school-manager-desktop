# -*- coding: utf-8 -*-
"""لقطة للقائمة الجانبية المصمّمة من جديد (نافذة طويلة لعرض كل الأقسام)."""
import os
import sys
import tempfile
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import app

tmp = tempfile.mkdtemp(prefix="dsm_shot3_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

w = app.App(role="admin", key=None, auth=app.Auth(), username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1280x1000+30+30")
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

w._show_sidebar()
w.attributes("-topmost", True)
time.sleep(0.5)
w.update()

from PIL import ImageGrab
x = w.winfo_rootx()
y = w.winfo_rooty()
img = ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()))
img.save("_sidebar_preview_new.png")
print("saved", img.size)
print("x+w:", w._sidebar.winfo_x() + w._sidebar.winfo_width(),
      "parent:", w._sb_parent.winfo_width())

w.attributes("-topmost", False)
w._hide_sidebar()
w.db.close()
w.destroy()
