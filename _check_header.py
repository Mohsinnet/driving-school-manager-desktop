import io

p = r"E:\موقعي\app exe\app.py"
s = io.open(p, encoding="utf-8").read()

old_start = s.find("    # ---------- الترويسة ----------\n    def _build_header(self):")
old_end = s.find("\n    # ---------- القائمة المنسدلة ----------", old_start)
print("start:", old_start, "end:", old_end)

if old_start >= 0 and old_end > old_start:
    old_block = s[old_start:old_end]
    print("OLD BLOCK LENGTH:", len(old_block))
    print(repr(old_block[:200]))
else:
    print("MARKERS NOT FOUND")
