# -*- coding: utf-8 -*-
"""فحص تنسيق جدول البيانات الجديد: خلفيات ناجح/راسب، شارات الحالة
والباقي، التحويم، والرسالة الفارغة."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import app

tmp = tempfile.mkdtemp(prefix="dsm_table_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

w = app.App(role="admin", key=None, auth=app.Auth(), username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1400x800+20+20")
w.deiconify()
w.update()

w.db.add_candidate({"full_name": "ناجح كامل الدفع", "phone": "0611111111",
                    "exam1_date": "2026-09-01", "exam1_result": "ناجح",
                    "total_price": 3000, "paid1": 3000})
w.db.add_candidate({"full_name": "راسب مدين", "phone": "0622222222",
                    "exam1_date": "2026-08-01", "exam1_result": "راسب",
                    "total_price": 3000, "paid1": 700})
w.db.add_candidate({"full_name": "قيد الدراسة مدين", "phone": "0633333333",
                    "total_price": 3200, "paid1": 1000})
w.db.add_candidate({"full_name": "قيد الدراسة مسدّد", "phone": "0644444444",
                    "total_price": 3000, "paid1": 3000})
w.refresh()
w.update()

cols = list(w.tree["columns"])
print("1) الأعمدة:", len(cols), "| الحالة موجودة:",
      "exam_results" in cols)
assert "exam_results" in cols
heads = {w.tree.heading(c)["text"] for c in cols}
print("2) عنوان الباقي:", [h for h in heads if "الباقي" in h])
assert any("الباقي ●" in h for h in heads)

rows = w.tree.get_children()
print("3) الصفوف:", len(rows))
assert len(rows) == 4
i_name = cols.index("full_name")
i_state = cols.index("exam_results")
i_rem = cols.index("remaining")
by_name = {w.tree.item(r, "values")[i_name]: (r, w.tree.item(r, "tags"),
           w.tree.item(r, "values")) for r in rows}

r, tags, vals = by_name["ناجح كامل الدفع"]
print("4) الناجح:", vals[i_state], "|", vals[i_rem], "|", tags)
assert "✓ ناجح" in vals[i_state] and "سُدّد" in vals[i_rem]
assert any(t in ("pass", "pass_alt") for t in tags)

r, tags, vals = by_name["راسب مدين"]
print("5) الراسب:", vals[i_state], "|", vals[i_rem], "|", tags)
assert "✗ راسب" in vals[i_state] and "مدين" in vals[i_rem]
assert any(t in ("fail", "fail_alt") for t in tags)

r, tags, vals = by_name["قيد الدراسة مدين"]
print("6) المدين:", vals[i_state], "|", vals[i_rem], "|", tags)
assert "قيد الدراسة" in vals[i_state] and "مدين" in vals[i_rem]
assert "debt" in tags

r, tags, vals = by_name["قيد الدراسة مسدّد"]
print("7) المسدّد:", vals[i_state], "|", vals[i_rem], "|", tags)
assert "سُدّد" in vals[i_rem]
assert not any(t in ("pass", "pass_alt", "fail", "fail_alt", "debt")
               for t in tags)

# 8) محاكاة التحويم على أول صف
first = rows[0]
x0, y0 = w.tree.bbox(first, column="#1")[:2]
w.tree.event_generate("<Motion>", x=x0 + 4, y=y0 + 4)
w.update()
tags = w.tree.item(first, "tags")
print("8) وسوم أول صف بعد التحويم:", tags)
assert any(t.startswith("hover") for t in tags), tags

# 9) الرسالة الفارغة عند بحث لا يطابق شيئاً
w.search_var.set("zzzلا_يوجدzzz")
w.refresh()
w.update()
vis = bool(w._empty_hint.winfo_ismapped())
print("9) الرسالة الفارغة ظاهرة:", vis)
assert vis
print("   الرسالة:", w._empty_hint.cget("text")[:40])
w.search_var.set("")
w.refresh()
w.update()
assert not w._empty_hint.winfo_ismapped()
print("   الرسالة مخفية بعد إرجاع البحث")

# 10) لقطة شاشة
try:
    from PIL import ImageGrab
    w.attributes("-topmost", True)
    w.tree.selection_set(rows[1])
    w.tree.see(rows[1])
    w.tree.event_generate("<Motion>", x=x0 + 4, y=y0 + 4)
    w.update()
    x = w.winfo_rootx()
    y = w.winfo_rooty()
    img = ImageGrab.grab(bbox=(x, y, x + w.winfo_width(),
                               y + w.winfo_height()))
    img.save("_table_new.png")
    print("10) لقطة محفوظة:", img.size)
except Exception as exc:
    print("10) تعذّرت اللقطة:", exc)

# 11) الفرز ما زال يعمل مع العمود الجديد
w._sort_by("exam_results")
w.update()
w._sort_by("remaining")
w.update()
print("11) الفرز يعمل، عدد الصفوف:", len(w.tree.get_children()))

w.db.close()
w.destroy()
print("ALL OK")
