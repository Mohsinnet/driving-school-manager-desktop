# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

tmp = tempfile.mkdtemp(prefix="dsm_ui_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

auth = app.Auth()
w = app.App(role="admin", key=None, auth=auth, username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1200x800+40+40")
w.deiconify()
w.update()
w.focus_force()
w.update()

print("icon family:", app.icon_family())
print("nav keys:", sorted(w._nav_items.keys()))
print("cta:", w._cta_row is not None, "order:", len(w._nav_order))
print("edit disabled initially:", not w._nav_items["edit"]["enabled"])

cid = w.db.add_candidate({"full_name": "مترشح اختبار"})
w.refresh()
w.update()
first = w.tree.get_children()[0]
w.tree.selection_set(first)
w.update()
print("edit enabled after select:", w._nav_items["edit"]["enabled"])

w._show_sidebar()
w.update()
print("sidebar open:", w._sb_open,
      "mapped:", w._sidebar.winfo_ismapped(),
      "w/h:", w._sidebar.winfo_width(), w._sidebar.winfo_height())
print("edit mapped:", w._nav_items["edit"]["row"].winfo_ismapped())
print("logout mapped:", w._nav_items["logout"]["row"].winfo_ismapped())
print("canvas:", w._sb_canvas.winfo_ismapped(),
      w._sb_canvas.winfo_width(), w._sb_canvas.winfo_height(),
      "yview:", w._sb_canvas.yview())
print("content:", w._sb_content.winfo_ismapped(),
      w._sb_content.winfo_width(), w._sb_content.winfo_height(),
      "y:", w._sb_content.winfo_y())
print("edit manager/y/req:",
      w._nav_items["edit"]["row"].winfo_manager(),
      w._nav_items["edit"]["row"].winfo_y(),
      w._nav_items["edit"]["row"].winfo_reqheight())
print("vsb:", w._sb_vsb.winfo_manager(),
      w._sb_vsb.winfo_ismapped(), w._sb_vsb.winfo_width(),
      "canvas width:", w._sb_canvas.winfo_width())

w.db.soft_delete_candidate(cid)
w.refresh()
w.update()
print("trash badge text:", w._nav_items["trash"]["badge"].cget("text"))
print("trash badge mapped:",
      w._nav_items["trash"]["badge"].winfo_ismapped())

w._hide_sidebar(True)
w.update()
print("sidebar closed:", not w._sb_open,
      "hamburger focus:", w.focus_get() is w.hamburger)

w.db.close()
w.destroy()
shutil.rmtree(tmp, ignore_errors=True)
print("OK")
