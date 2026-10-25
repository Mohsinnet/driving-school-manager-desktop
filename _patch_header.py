import io

p = r"E:\موقعي\app exe\app.py"
s = io.open(p, encoding="utf-8").read()

old_start = s.find("    # ---------- الترويسة ----------\n    def _build_header(self):")
old_end = s.find("\n    # ---------- القائمة المنسدلة ----------", old_start)

print("start:", old_start, "end:", old_end)

if old_start >= 0 and old_end > old_start:
    new_block = (
        "    # ---------- شريط التنقل العلوي (Navbar) ----------\n"
        "    def _build_header(self):\n"
        "        \"\"\"شريط علوي ثابت مع شعار، اسم المؤسسة، زر القائمة، ومؤشر المستخدم.\"\"\"\n"
        "        header = tk.Frame(self, bg=NAVY, height=64)\n"
        "        header.pack(fill=\"x\")\n"
        "        header.pack_propagate(False)\n"
        "        inner = tk.Frame(header, bg=NAVY)\n"
        "        inner.pack(fill=\"both\", expand=True, padx=16, pady=6)\n"
        "\n"
        "        # زر القائمة (يسار الواجهة في RTL)\n"
        "        self.hamburger = tk.Button(\n"
        "            inner, text=icon_text(\"menu\"), command=self._toggle_sidebar,\n"
        "            bg=NAVY, fg=\"white\", activebackground=NAVY_HOVER,\n"
        "            activeforeground=GOLD, relief=\"flat\", bd=0,\n"
        "            highlightthickness=0, font=icon_font(20), cursor=\"hand2\",\n"
        "            padx=8, pady=0, takefocus=True)\n"
        "        self.hamburger.pack(side=\"left\")\n"
        "\n"
        "        # منطقة الوسط: شعار + اسم التطبيق\n"
        "        center = tk.Frame(inner, bg=NAVY)\n"
        "        center.pack(side=\"right\")\n"
        "        seal = tk.Canvas(center, width=34, height=34, bg=NAVY,\n"
        "                         highlightthickness=0, bd=0)\n"
        "        seal.pack(side=\"right\", padx=(0, 8))\n"
        "        seal.create_oval(2, 2, 32, 32, fill=NAV_CHIP, outline=GOLD, width=1)\n"
        "        seal.create_text(17, 17, text=icon_text(\"education\"), fill=GOLD,\n"
        "                         font=icon_font(15))\n"
        "\n"
        "        app_info = tk.Frame(center, bg=NAVY)\n"
        "        app_info.pack(side=\"right\")\n"
        "        tk.Label(app_info, text=APP_TITLE, bg=NAVY, fg=\"white\",\n"
        "                 font=F_TITLE, anchor=\"e\").pack(anchor=\"e\")\n"
        "        tk.Label(app_info, text=school(), bg=NAVY, fg=GOLD,\n"
        "                 font=(FONT, 9), anchor=\"e\").pack(anchor=\"e\")\n"
        "\n"
        "        # المستخدم الحالي وصلاحيته (يسار وسط)\n"
        "        who = \"%s  \\u2022  %s\" % (self.username or \"\\u2014\",\n"
        "                             ROLE_LABELS.get(self.role, self.role))\n"
        "        user_pill = tk.Frame(inner, bg=\"#123F63\")\n"
        "        user_pill.pack(side=\"left\", padx=(12, 0), pady=2)\n"
        "        tk.Label(user_pill, text=\" %s \" % who, bg=\"#123F63\", fg=\"#B8C7D9\",\n"
        "                 font=(FONT, 9)).pack(side=\"left\")\n"
        "\n"
        "        tk.Frame(self, bg=GOLD, height=3).pack(fill=\"x\")\n"
    )

    s = s[:old_start] + new_block + s[old_end:]
    io.open(p, "w", encoding="utf-8").write(s)
    print("HEADER REPLACED OK")
else:
    print("MARKERS NOT FOUND")
