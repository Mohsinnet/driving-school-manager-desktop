import io

p = r"E:\موقعي\app exe\app.py"
s = io.open(p, encoding="utf-8").read()

old = '        # Context menu\n        self._build_context_menu()\n'
new = (
    "        # Context menu\n"
    "        self.ctx = tk.Menu(self, tearoff=0, font=F_BODY)\n"
    "        self.ctx.add_command(label=\"تعديل  (Enter)\", command=self.on_edit)\n"
    "        self.ctx.add_command(label=\"تسجيل دفعة\", command=self.on_pay)\n"
    "        self.ctx.add_command(label=\"كشف حساب\", command=self.on_receipt)\n"
    "        self.ctx.add_separator()\n"
    "        self.ctx.add_command(label=\"حذف  (Delete)\", command=self.on_delete)\n"
)

if old in s:
    s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8").write(s)
    print("CONTEXT MENU FIXED")
else:
    print("OLD BLOCK NOT FOUND")
