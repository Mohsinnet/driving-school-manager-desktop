import io

p = r"E:\موقعي\app exe\app.py"
s = io.open(p, encoding="utf-8").read()

start = s.find("    def _build_table(self, parent):")
end = s.find("\n    def _sort_by(self, col):", start)

print("Table block start:", start, "end:", end)

if start == -1 or end == -1:
    print("ERROR: Could not locate _build_table boundaries")
    exit(1)

new_block = """    # ---------- الجدول (من اليمين إلى اليسار بكل الحقول) ----------
    def _build_table(self, parent):
        mid = ttk.Frame(parent, padding=(16, 10, 16, 10))
        mid.pack(fill="both", expand=True)

        # عرض الجدول من اليمين إلى اليسار: عكس ترتيب الأعمدة
        self._disp_fields = list(reversed(TABLE_FIELDS))
        cols = tuple(f[0] for f in self._disp_fields)
        heads = {f[0]: f[1] for f in TABLE_FIELDS}
        widths = {f[0]: f[2] for f in TABLE_FIELDS}
        stretch = {f[0]: f[3] for f in TABLE_FIELDS}

        self.tree = ttk.Treeview(mid, columns=cols, show="headings",
                                 selectmode="browse")
        self._head_texts = heads
        for c in cols:
            self.tree.heading(c, text=heads[c], anchor="e",
                              command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=widths[c], anchor="e",
                             stretch=stretch[c])
        self.tree.tag_configure("odd", background=ROW_ALT)
        self.tree.tag_configure("even", background=CARD)
        self.tree.tag_configure("debt", foreground=DANGER,
                                font=(FONT, 10, "bold"))
        self.tree.tag_configure("pass", background=PASS_BG)
        self.tree.tag_configure("pass_alt", background="#D8EADD")
        self.tree.tag_configure("fail", background=FAIL_BG)
        self.tree.tag_configure("fail_alt", background="#F2DADA")
        self.tree.tag_configure("hover", background=ROW_HOVER)
        self.tree.tag_configure("hover_pass", background="#D3E6D8")
        self.tree.tag_configure("hover_fail", background="#F0D6D6")
        self._row_bg_tag = {}
        self._hover_row = None

        # رسالة فارغة تُعرض عند خلو الجدول من الصفوف
        self._empty_hint = tk.Label(
            mid, text="لا يوجد مترشحون مطابقون — جرّب تغيير البحث أو الفلتر",
            bg=CARD, fg=MUTED, font=F_BODY_B)
        self._empty_hint.place(relx=0.5, rely=0.45, anchor="center")
        self._empty_hint.place_forget()

        sy = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", lambda e: self.on_edit())
        self.tree.bind("<Button-3>", self._show_context)
        self.tree.bind("<<TreeviewSelect>>",
                       lambda e: self._update_nav_state(), add="+")
        self.tree.bind("<Motion>", self._on_tree_hover, add="+")
        self.tree.bind("<Leave>", self._on_tree_leave, add="+")

        # قائمة السياق
        self.ctx = tk.Menu(self, tearoff=0, font=F_BODY)
        self.ctx.add_command(label="تعديل  (Enter)", command=self.on_edit)
        self.ctx.add_command(label="تسجيل دفعة", command=self.on_pay)
        self.ctx.add_command(label="كشف حساب", command=self.on_receipt)
        self.ctx.add_separator()
        self.ctx.add_command(label="حذف  (Delete)", command=self.on_delete)

        self._sort_col = None
        self._sort_desc = False
"""

s = s[:start] + new_block + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("OLD TABLE RESTORED")
