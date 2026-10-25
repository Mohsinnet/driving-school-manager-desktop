data = open("app.py", "rb").read()
print("CRLF", data.count(b"\r\n"), "LF", data.count(b"\n"), "BOM", data[:3])
print("size", len(data))
