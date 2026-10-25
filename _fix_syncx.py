import io

p = r"E:\موقعي\app exe\app.py"
s = io.open(p, encoding="utf-8").read()

# Find the _sync_x function definition and its body
start = s.find("        def _sync_x(*args):")
if start == -1:
    print("ERROR: Could not find _sync_x definition")
    exit(1)
# Find the end of the function (next line that is not indented as part of the function)
# Look for the line after the function body that starts with 8 spaces (same indent as def)
# Actually the function body is indented by 8 spaces (two tabs? 8 spaces). 
# The line after the function body is `sx = ttk.Scrollbar(container, orient="horizontal",`
# which starts with 8 spaces? Let's check: the line after function body is at same indent as the def? 
# The def line has 8 spaces, the body has 12 spaces? Let's see from the file:
# Line 2261:         def _sync_x(*args):   -> 8 spaces? Actually looking at original file:
# In the file, the indentation level for code inside _build_table is 8 spaces (two tabs?).
# The def _sync_x line starts with 8 spaces, then the function body lines start with 12 spaces (8+4).
# The line after the function body (sx = ...) starts with 8 spaces again.
# So we can find the line after the function body by looking for the first line after start that has indent <= 8 spaces.
# But easier: we know the function body is exactly 4 lines (from line 2261 to 2264 inclusive).
# Let's just replace those 4 lines.

# Compute end of the 4-line block: start + length of "        def _sync_x(*args):\n" + 3 more lines.
# Let's just find the line after the fourth line.
lines = s.splitlines(keepends=True)
# Find line index of start
start_line_idx = None
for i, line in enumerate(lines):
    if line.startswith("        def _sync_x(*args):"):
        start_line_idx = i
        break
if start_line_idx is None:
    print("ERROR: Could not find _sync_x line")
    exit(1)
# Replace lines[start_line_idx : start_line_idx+4] with new block
new_sync_x_lines = [
    "        def _sync_x(*args):\n",
    "            # Sync horizontal scroll between header canvas and treeview\n",
    "            # args can be like ('moveto', fraction) or ('scroll', number, 'units'/'pages')\n",
    "            # or sometimes just a fraction? we'll handle both.\n",
    "            if not args:\n",
    "                return\n",
    "            # Some Tk versions may pass just a float for moveto? \n",
    "            # But typically args is tuple like ('moveto', 0.5) or ('scroll', 1, 'units')\n",
    "            # If first arg is a string, we assume it's a proper tuple\n",
    "            if isinstance(args[0], str):\n",
    "                # normal case: ('moveto', f) or ('scroll', n, 'units')\n",
    "                self._head_canvas.xview(*args)\n",
    "                self.tree.xview(*args)\n",
    "            else:\n",
    "                # Assume it's a single float for moveto\n",
    "                fraction = args[0]\n",
    "                self._head_canvas.xview('moveto', fraction)\n",
    "                self.tree.xview('moveto', fraction)\n"
]
# Replace the 4 lines with new_sync_x_lines
lines[start_line_idx:start_line_idx+4] = new_sync_x_lines
s = ''.join(lines)
io.open(p, "w", encoding="utf-8").write(s)
print("_sync_x function updated to handle scroll arguments correctly.")
