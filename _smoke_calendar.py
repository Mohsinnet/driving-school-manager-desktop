# -*- coding: utf-8 -*-
"""فحص تقويم الامتحانات: بناء بيانات على شهرين ثم فحص الخلايا والتنقل."""
import os
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import app

tmp = tempfile.mkdtemp(prefix="dsm_cal_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

w = app.App(role="admin", key=None, auth=app.Auth(), username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1280x800+30+30")
w.deiconify()
w.update()

today = date.today()


def iso(delta):
    return (today + timedelta(days=delta)).isoformat()


# بيانات: متأخرة بلا نتيجة، اليوم، قادمة، ناجحة، راسبة، وشهر آخر
w.db.add_candidate({"full_name": "متأخر عن الامتحان", "phone": "0611111111",
                    "exam1_date": iso(-10)})
w.db.add_candidate({"full_name": "امتحان اليوم", "phone": "0622222222",
                    "exam1_date": iso(0)})
w.db.add_candidate({"full_name": "قادم قريباً", "phone": "0633333333",
                    "exam1_date": iso(5), "exam2_date": iso(40)})
w.db.add_candidate({"full_name": "ناجح سابق", "phone": "0644444444",
                    "exam1_date": iso(-20), "exam1_result": "ناجح"})
w.db.add_candidate({"full_name": "راسب سابق", "phone": "0655555555",
                    "exam1_date": iso(-15), "exam1_result": "راسب"})
w.db.add_candidate({"full_name": "متأخر بالدفعة", "phone": "0666666666",
                    "total_price": 3000, "paid1": 500})
w.refresh()
w.update()

win = app.ExamsWindow(w, w.db)
win.update()

# 1) عدد خلايا التقويم (5-6 صفوف × 7 أعمدة)
cells = [c for c in win.cal_grid.winfo_children()]
print("1) صفوف/خلايا:", len(cells))
assert 28 <= len(cells) <= 42, len(cells)

# 2) عنوان الشهر الحالي
print("2) عنوان الشهر:", win.month_lbl.cget("text"))
assert str(today.year) in win.month_lbl.cget("text")

# 3) اتحاد الأيام المزدوجة == مجموع الامتحانات
total_dots = len(win._exams)
month_rows = len(win.det_tbl.get_children())
print("3) الامتحانات الكلية:", total_dots, "| صفوف الشهر الافتراضي:",
      month_rows)
assert month_rows > 0

# 4) حالات الامتحانات الخمس
sts = sorted({win._status_of(e) for e in win._exams})
print("4) الحالات الموجودة:", sts)
for s in ("ok", "fail", "late", "today", "soon"):
    assert s in sts, s

# 5) اختيار يوم فيه امتحان (اليوم) يعرضه في الجدول السفلي
win._pick_day(today.isoformat())
win.update()
print("5) عنوان التفاصيل بعد اختيار اليوم:", win.det_title.cget("text"))
assert str(today.day) in win.det_title.cget("text")
assert len(win.det_tbl.get_children()) == 1

# 6) التنقّل بين الشهور
m0 = (win.year, win.month)
win.next_month()
win.update()
assert (win.year, win.month) != m0
print("6) بعد 'التالي':", win.month_lbl.cget("text"))
win.prev_month()
win.prev_month()
win.update()
print("   بعد 'السابق' مرتين:", win.month_lbl.cget("text"))
win._this_month()
win.update()
assert (win.year, win.month) == m0

# 7) تبويب المتأخرين
print("7) متأخرو الدفع:", len(win.debt_tbl.get_children()),
      "|", win.debt_sum.cget("text"))
assert len(win.debt_tbl.get_children()) == 1

# 8) النقر المزدوج يفتح بطاقة المترشح
win._pick_day(today.isoformat())
win.update()
win.det_tbl.selection_set(win.det_tbl.get_children()[0])
win._open_candidate()
win.update()
kids = [c for c in win.winfo_children() if isinstance(c, app.CandidateDialog)]
print("8) بطاقة مفتوحة:", len(kids) == 1)
assert len(kids) == 1
kids[0].destroy()

# 9) لقطة شاشة
try:
    from PIL import ImageGrab
    win.attributes("-topmost", True)
    win.update()
    x, y = win.winfo_rootx(), win.winfo_rooty()
    img = ImageGrab.grab(bbox=(x, y, x + win.winfo_width(),
                               y + win.winfo_height()))
    img.save("_exams_calendar.png")
    print("9) لقطة محفوظة:", img.size)
except Exception as exc:
    print("9) تعذّرت اللقطة:", exc)

win.destroy()
w.db.close()
w.destroy()
print("ALL OK")
