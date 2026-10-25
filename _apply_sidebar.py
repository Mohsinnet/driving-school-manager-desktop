# -*- coding: utf-8 -*-
path = "app.py"
start_marker = "    # ---------- القائمة المنسدلة ----------"
end_marker = "    # ---------- بطاقة ----------"

with open(path, "r", encoding="utf-8", newline="") as f:
    data = f.read()

assert data.count(start_marker) == 1, data.count(start_marker)
assert data.count(end_marker) == 1, data.count(end_marker)

start = data.index(start_marker)
end = data.index(end_marker, start)
with open("_sidebar_block.txt", "r", encoding="utf-8", newline="") as f:
    block = f.read().replace("\r\n", "\n").replace("\r", "\n")
if not block.endswith("\n"):
    block += "\n"

new_data = data[:start] + block + data[end:]
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(new_data)

print("old chars:", end - start, "new chars:", len(block),
      "removed:", end - start - len(block))
