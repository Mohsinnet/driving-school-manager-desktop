# -*- coding: utf-8 -*-
"""فحص إضافي للقائمة الجانبية بعد إعادة التصميم: دور الموظف، التنقل
بلوحة المفاتيح، الحركة، النقر الخارجي، وشارة الامتحانات."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import app

tmp = tempfile.mkdtemp(prefix="dsm_sb2_")
app.data_dir = lambda: tmp
app.LOG.disabled = True

# ---------- 1) دور الموظف: الأقسام تُرشّح حسب الصلاحيات ----------
# صلاحيات الموظف: add/edit/pay/receipt/search/reports/exams/export فقط
w = app.App(role="employee", key=None, auth=app.Auth(), username="employe")
w.withdraw()
w.state("normal")
w.geometry("1200x800+40+40")
w.deiconify()
w.update()

emp_keys = sorted(w._nav_items.keys())
print("1) keys(employee):", emp_keys)
assert "users" not in emp_keys and "settings" not in emp_keys, emp_keys
assert "trash" not in emp_keys and "delete" not in emp_keys, emp_keys
assert "export" in emp_keys and "reports" in emp_keys
assert w._cta_row is not None, "زر الإضافة مفقود لدور الموظف"
print("1) OK: ترشيح الأقسام حسب صلاحيات الموظف")

# ---------- 2) التنقل بلوحة المفاتيح ----------
w._show_sidebar()
w.update()
w._sidebar.focus_set()
w.update()
first = w.focus_get()
w._nav_move(1)
w.update()
second = w.focus_get()
assert first is not second, "التنقل للأسفل لم يغيّر التركيز"
print("2) OK: التنقل بلوحة المفاتيح", first.winfo_class(),
      "->", second.winfo_class())

# ---------- 3) النقر الخارجي يغلق الدرج ----------
w._arm_outside()
w._on_global_click(type("E", (), {"x_root": 5, "y_root": 400})())
w.update()
assert not w._sb_open and not w._sidebar.winfo_ismapped()
print("3) OK: النقر خارج الدرج أغلقه")

# ---------- 4) زر التبديل في الترويسة ----------
w.hamburger.invoke()
w.update()
assert w._sb_open and w._sidebar.winfo_ismapped()
print("4) OK: زر القائمة يفتح الدرج، العرض:",
      w._sidebar.winfo_width(), "الارتفاع:", w._sidebar.winfo_height())

# ---------- 5) تعطيل الإجراءات عند إلغاء تحديد الصف ----------
w.tree.selection_remove(w.tree.selection())
w.update()
assert not w._nav_items["edit"]["enabled"]
print("5) OK: تعطيل 'تعديل البيانات' عند عدم تحديد صف")

# ---------- 6) Escape يغلق الدرج ----------
w._show_sidebar()
w.update()
w.event_generate("<Escape>")
w.update()
assert not w._sb_open
print("6) OK: Escape يغلق الدرج")
w.db.close()
w.destroy()

# ---------- 7) دور المدير: الشارات + كل الأقسام ----------
w = app.App(role="admin", key=None, auth=app.Auth(), username="koutoubia")
w.withdraw()
w.state("normal")
w.geometry("1200x800+40+40")
w.deiconify()
w.update()
adm_keys = sorted(w._nav_items.keys())
print("7) keys(admin):", adm_keys)
for k in ("trash", "users", "settings", "import", "delete"):
    assert k in adm_keys, k
cid = w.db.add_candidate({"full_name": "اختبار الشارة"})
w.db.soft_delete_candidate(cid)
w.refresh()
w.update()
badge = w._nav_items["trash"]["badge"]
print("7) شارة السلة:", badge.cget("text"), "mapped:", badge.winfo_ismapped())
assert badge.cget("text") == "1"
w._show_sidebar()
w.update()
assert w._sidebar.winfo_x() + w._sidebar.winfo_width() == \
    w._sb_parent.winfo_width(), "الدرج لا يلامس الحافة اليمنى"
print("7) OK: الدرج ملاصق للحافة اليمنى x=%s w=%s parent=%s"
      % (w._sidebar.winfo_x(), w._sidebar.winfo_width(),
         w._sb_parent.winfo_width()))
w.db.close()
w.destroy()
print("ALL OK")

