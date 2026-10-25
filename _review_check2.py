# -*- coding: utf-8 -*-
import os, sqlite3, sys, tempfile
from cryptography.fernet import Fernet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

tmp = tempfile.mkdtemp(prefix="dsm_review_")
app.data_dir = lambda: tmp
key = Fernet.generate_key()
enc = os.path.join(tmp, "driving_school.db.enc")
plain = os.path.join(tmp, "driving_school.db")


def make_db(path, name):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS candidates("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT)")
    con.execute("INSERT INTO candidates(full_name) VALUES(?)", (name,))
    con.commit()
    con.close()


def names(path):
    con = sqlite3.connect(path)
    out = [r[0] for r in con.execute("SELECT full_name FROM candidates")]
    con.close()
    return out


# 1) enc قديم + plain أحدث (وضعية انهيار البرنامج قبل التشفير عند الإغلاق)
make_db(plain, "جديد-بعد-الانهيار")
app.db_encrypt_to_disk(plain, enc, key)
make_db(plain, "أحدث-من-النسخة-المشفرة")
p = app.ensure_plain_db(key)
print("1) بعد ensure_plain_db:", names(plain))

# 2) فشل فك التشفير ثم الإغلاق: هل يطمس الملف المشفر؟
with open(enc, "wb") as f:
    f.write(b"corrupted")
os.remove(plain)
p = app.ensure_plain_db(key)
print("2) نتيجة فك التشفير التالف:", p)
db = app.DB(plain)
db.close()
app.seal_db_after_close(key)
back = Fernet(key).decrypt(open(enc, "rb").read())
print("2) enc بعد الإغلاق يحتوي قاعدة جديدة فارغة:",
      b"CREATE TABLE candidates" in back)

# 3) fmt_money مع قيم غير منتهية
for v in ("nan", "inf", "1e309"):
    try:
        print("3) fmt_money(parse_num(%r)) =" % v,
              app.fmt_money(app.parse_num(v)))
    except Exception as e:
        print("3) fmt_money(parse_num(%r)) -> استثناء: %s: %s"
              % (v, type(e).__name__, e))

print("tmp =", tmp)
