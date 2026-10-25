# -*- coding: utf-8 -*-
"""ادارة مدرسة تعليم السياقة - نسخة ويندوز (Tkinter + SQLite).

الاساسيات: سجل المترشحين + بحث + مدفوعات، مع استيراد بيانات تطبيق الاندرويد
(نسخة JSON الاحتياطية / CSV / Excel) وتصدير بنفس الصيغ.
"""
import base64 as _b64
import calendar as _calendar
import csv
import hashlib as _hashlib
import json
import logging
import os
import secrets as _secrets
import shutil
import sqlite3
import sys
import tkinter as tk
try:
    import ttkbootstrap as ttk
    TTKBOOTSTRAP_OK = True
except Exception:
    from tkinter import ttk
    TTKBOOTSTRAP_OK = False
import tkinter.ttk as _stdttk
from tkinter import messagebox, filedialog, font as tkfont
from datetime import date, datetime, timedelta

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes as _hashes
    CRYPTO_OK = True
except Exception:
    CRYPTO_OK = False

APP_TITLE = "إدارة مدرسة تعليم السياقة"
APP_VERSION = "3.0"
SCHOOL_NAME = "مؤسسة الكتبية لتعليم السياقة"

RESULTS = ["", "ناجح", "راسب"]
CATEGORIES = ["B", "A", "C", "D", "EB", "EC"]

# نفس عناوين CSV/Excel في تطبيق الاندرويد (لتوافق الاستيراد والتصدير)
CSV_HEADERS = [
    "الاسم الكامل", "الهاتف", "رقم البطاقة الوطنية", "رقم التسجيل",
    "تاريخ التسجيل", "فئة العربة", "رقم العربة", "تاريخ الازدياد",
    "تاريخ الامتحان الأول", "نتيجة الامتحان الأول",
    "تاريخ الامتحان الثاني", "نتيجة الامتحان الثاني",
    "الثمن الإجمالي", "الدفعة الأولى", "الدفعة الثانية", "الدفعة الثالثة",
    "مجموع المدفوع", "الباقي", "ملاحظات",
]

JSON_KEYS = [
    "fullName", "birthDate", "phone", "cin", "regNumber", "regDate",
    "category", "vehicleNumber", "exam1Date", "exam1Result", "exam2Date",
    "exam2Result", "totalPrice", "paid1", "paid2", "paid3", "paidExtra",
    "notes", "photoPath",
]

DB_COLS = [
    "id", "full_name", "birth_date", "phone", "cin", "reg_number",
    "reg_date", "category", "vehicle_number", "exam1_date", "exam1_result",
    "exam2_date", "exam2_result", "total_price", "paid1", "paid2",
    "paid3", "paid_extra", "notes", "photo_path",
]

# ---------------- الهوية البصرية (Apple-inspired) ----------------
# خط: Segoe UI (Windows) قريب من SF؛ للعربية Tajawal/IBM Plex Sans Arabic إن توفر
FONT = "Segoe UI"
FONT_AR = "Segoe UI"   # fallback؛ يمكن تغييره إلى "Tajawal" إن ثُبّت
# ألوان Apple (Light)
NAVY = "#007AFF"          # أزرق Apple أساسي
NAVY_DARK = "#0051D5"
NAVY_HOVER = "#0066E0"
GOLD = "#FF9500"          # برتقالي Apple (تنبيه/تمييز)
GOLD_DARK = "#E08600"
BG = "#F5F5F7"            # خلفية Apple رمادية ناعمة
CARD = "#FFFFFF"
BORDER = "#D2D2D7"
ROW_ALT = "#F5F5F7"
ROW_HOVER = "#E8E8ED"
PASS_BG = "#E3F5E8"
FAIL_BG = "#FDECEA"
TEXT = "#1D1D1F"
MUTED = "#86868B"
OK = "#34C759"
DANGER = "#FF3B30"
WARN = "#FF9500"
STATUS_BG = "#E8E8ED"
STATUS_FG = "#1D1D1F"

# ألوان Apple (Dark)
DARK_BG = "#1C1C1E"
DARK_CARD = "#2C2C2E"
DARK_BORDER = "#3A3A3C"
DARK_TEXT = "#F5F5F7"
DARK_MUTED = "#98989D"
DARK_NAVY = "#0A84FF"
DARK_GOLD = "#FF9F0A"

def apply_theme_constants(mode):
    """إعادة تعيين ثوابت الألوان حسب الوضع (فاتح/داكن)."""
    global THEME_MODE, NAVY, NAVY_DARK, NAVY_HOVER, GOLD, GOLD_DARK
    global BG, CARD, BORDER, ROW_ALT, ROW_HOVER, TEXT, MUTED
    global OK, DANGER, WARN, STATUS_BG, STATUS_FG
    THEME_MODE = mode
    if mode == "dark":
        NAVY = DARK_NAVY
        NAVY_DARK = "#0040A0"
        NAVY_HOVER = "#0A7AE0"
        GOLD = DARK_GOLD
        GOLD_DARK = "#E08600"
        BG = DARK_BG
        CARD = DARK_CARD
        BORDER = DARK_BORDER
        ROW_ALT = "#2C2C2E"
        ROW_HOVER = "#3A3A3C"
        TEXT = DARK_TEXT
        MUTED = DARK_MUTED
        OK = "#30D158"
        DANGER = "#FF453A"
        WARN = DARK_GOLD
        STATUS_BG = "#2C2C2E"
        STATUS_FG = DARK_TEXT
    else:
        NAVY = "#007AFF"
        NAVY_DARK = "#0051D5"
        NAVY_HOVER = "#0066E0"
        GOLD = "#FF9500"
        GOLD_DARK = "#E08600"
        BG = "#F5F5F7"
        CARD = "#FFFFFF"
        BORDER = "#D2D2D7"
        ROW_ALT = "#F5F5F7"
        ROW_HOVER = "#E8E8ED"
        TEXT = "#1D1D1F"
        MUTED = "#86868B"
        OK = "#34C759"
        DANGER = "#FF3B30"
        WARN = "#FF9500"
        STATUS_BG = "#E8E8ED"
        STATUS_FG = "#1D1D1F"

def is_dark():
    return THEME_MODE == "dark"

def C(key):
    """إرجاع لون حسب الثيم الحالي."""
    dark = {
        "bg": DARK_BG, "card": DARK_CARD, "border": DARK_BORDER,
        "text": DARK_TEXT, "muted": DARK_MUTED, "primary": DARK_NAVY,
        "accent": DARK_GOLD, "ok": OK, "danger": DANGER, "warn": DARK_GOLD,
        "status_bg": "#2C2C2E", "status_fg": DARK_TEXT,
        "row_alt": "#2C2C2E", "row_hover": "#3A3A3C",
    }
    light = {
        "bg": BG, "card": CARD, "border": BORDER,
        "text": TEXT, "muted": MUTED, "primary": NAVY,
        "accent": GOLD, "ok": OK, "danger": DANGER, "warn": WARN,
        "status_bg": STATUS_BG, "status_fg": STATUS_FG,
        "row_alt": ROW_ALT, "row_hover": ROW_HOVER,
    }
    return (dark if is_dark() else light).get(key, BG)

F_BODY = (FONT, 11)
F_SMALL = (FONT, 9)
F_BODY_B = (FONT, 11, "bold")
F_HEAD = (FONT, 12, "bold")
F_TITLE = (FONT, 22, "bold")
F_SUB = (FONT, 11)
F_CARD_NUM = (FONT, 28, "bold")
F_CARD_T = (FONT, 10)
F_TH = (FONT, 11, "bold")
F_MONO = ("Consolas", 10)
F_LARGE_TITLE = (FONT, 28, "bold")

# ---------------- القائمة الجانبية (macOS style) ----------------
NAV_SECTION = "#B8C7D9"
NAV_TEXT = "#FFFFFF"
NAV_ICON = "#DDE6F0"
NAV_DISABLED = "#8E9AAF"
NAV_LINE = "#3A6FA0"
NAV_BADGE = "#FF9500"
NAV_CHIP = "#1A5FA0"
NAV_CHIP_HOVER = "#2A70B0"
NAV_SHADOW = "#0051D5"
CARD_BORDER = "#D2D2D7"
CARD_HOVER_BG = "#F2F2F7"
CARD_HOVER_BORDER = "#007AFF"
SIDEBAR_BG = "#007AFF"
SIDEBAR_W = 276

_ICON_FAMILY = None
_ICON_GLYPHS = {
    "add": "\uE710", "edit": "\uE70F", "receipt": "\uE749",
    "pay": "\uE8C7", "remove": "\uE738", "trash": "\uE74D",
    "reports": "\uE9D2", "exams": "\uE787", "import": "\uE896",
    "export": "\uE898", "settings": "\uE713", "users": "\uE716",
    "about": "\uE946", "logout": "\uE7E8", "close": "\uE711",
    "menu": "\uE700", "education": "\uE7BE",
}
_ICON_FALLBACK = {
    "add": "+", "edit": "\u270E", "receipt": "\u25A4", "pay": "\u00A4",
    "remove": "\u2715", "trash": "\u267B", "reports": "\u25A5",
    "exams": "\u25A6", "import": "\u2913", "export": "\u2912",
    "settings": "\u2699", "users": "\u263A", "about": "\u24D8",
    "logout": "\u23FB", "close": "\u2715", "menu": "\u2630",
    "education": "\u25C6",
}


def icon_family():
    """أفضل خط أيقونات خطّي متاح على ويندوز 10/11."""
    global _ICON_FAMILY
    if _ICON_FAMILY is None:
        try:
            fams = set(tkfont.families())
        except Exception:
            fams = set()
        if "Segoe Fluent Icons" in fams:
            _ICON_FAMILY = "Segoe Fluent Icons"
        elif "Segoe MDL2 Assets" in fams:
            _ICON_FAMILY = "Segoe MDL2 Assets"
        else:
            _ICON_FAMILY = ""
    return _ICON_FAMILY


def icon_text(key):
    if icon_family():
        return _ICON_GLYPHS.get(key, "\u2022")
    return _ICON_FALLBACK.get(key, "\u2022")


def icon_font(size=14):
    return ((icon_family() or FONT), size)


# ---------------- تعريف أعمدة الجدول --------------------------------
# المجموعات: كل مجموعة تُعرض بشكل منفصل لتقليل التمرير الأفقي.
# الترتيب الداخلي هو ترتيب الأعمدة المنطقي (من اليمين إلى اليسار في RTL).
TABLE_FIELD_GROUPS = {
    "basic": [
        ("full_name",      "الاسم الكامل",   230, True),
        ("phone",          "الهاتف",           120, False),
        ("cin",            "رقم البطاقة",      140, False),
        ("reg_number",     "رقم التسجيل",      120, False),
        ("category",       "صنف الرخصة",       90,  False),
    ],
    "financial": [
        ("full_name",      "الاسم الكامل",   200, True),
        ("total_price",    "الثمن الإجمالي",   120, False),
        ("paid1",          "الدفعة 1",          90,  False),
        ("paid2",          "الدفعة 2",          90,  False),
        ("paid3",          "الدفعة 3",          90,  False),
        ("paid_extra",     "إضافية",            90,  False),
        ("total_paid",     "مجموع المدفوع",    110, False),
        ("remaining",      "الباقي ●",         130, False),
    ],
    "exams": [
        ("full_name",      "الاسم الكامل",   220, True),
        ("exam1_date",     "تاريخ الامتحان 1", 110, False),
        ("exam1_result",   "نتيجة 1",            80, False),
        ("exam2_date",     "تاريخ الامتحان 2", 110, False),
        ("exam2_result",   "نتيجة 2",            80, False),
        ("category",       "الصنف",             80, False),
    ],
    "full": [
        ("full_name",      "الاسم الكامل",   200, True),
        ("birth_date",     "تاريخ الازدياد",   110, False),
        ("cin",            "رقم البطاقة",      140, False),
        ("phone",          "الهاتف",           120, False),
        ("reg_number",     "رقم التسجيل",      115, False),
        ("reg_date",       "تاريخ التسجيل",    110, False),
        ("category",       "صنف الرخصة",       90,  False),
        ("vehicle_number", "رقم العربة",        100, False),
        ("exam1_date",     "تاريخ الامتحان 1", 100, False),
        ("exam1_result",   "نتيجة 1",             70, False),
        ("exam2_date",     "تاريخ الامتحان 2", 100, False),
        ("exam2_result",   "نتيجة 2",             70, False),
        ("total_price",    "الإجمالي",          110, False),
        ("paid1",          "الدفعة 1",            80, False),
        ("paid2",          "الدفعة 2",            80, False),
        ("paid3",          "الدفعة 3",            80, False),
        ("paid_extra",     "إضافية",              80, False),
        ("remaining",      "الباقي ●",          120, False),
        ("notes",          "ملاحظات",           260, True),
    ],
}

# ترتيب عرض المجموعات في شريط التبديل (المفتاح، التسمية العربية)
TABLE_GROUP_ORDER = [
    ("basic",    "أساسية"),
    ("financial", "مالية"),
    ("exams",    "امتحانات"),
    ("full",     "كاملة"),
]

# أعمدة مالية تُفرز رقمياً (تشمل جميعها عبر المجموعات)
MONEY_FIELDS = {"total_price", "paid1", "paid2", "paid3",
                "paid_extra", "total_paid", "remaining"}


# ---------------- مسارات ----------------
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def writable(p):
    try:
        t = os.path.join(p, ".writetest")
        with open(t, "w") as f:
            f.write("x")
        os.remove(t)
        return True
    except Exception:
        return False


def data_dir():
    d = app_dir()
    if writable(d):
        return d
    d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                     "DrivingSchoolManager")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------- أدوات ----------------
def fmt_money(d):
    try:
        d = float(d or 0)
    except Exception:
        d = 0
    if d == int(d):
        return "{:,.0f}".format(d)
    return "{:,.2f}".format(d)


def parse_num(s):
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip().replace(",", "").replace(" ", "").replace("درهم", "")
    if not t:
        return 0.0
    try:
        return float(t)
    except Exception:
        return 0.0


def norm(s):
    if s is None:
        return ""
    import re as _re
    return _re.sub(r"\s+", " ", str(s).replace("\u00a0", " ")).strip()


def phone_key(phone):
    p = "".join(ch for ch in norm(phone) if ch.isdigit())
    if len(p) > 9:
        p = p[-9:]
    return p


def name_phone_key(name, phone):
    return norm(name).lower() + "|" + phone_key(phone)


def to_ymd(v):
    """تحويل قيمة خلية Excel الى نص yyyy-MM-dd."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, (int, float)) and 20000 < v < 80000:
        try:
            base = datetime(1899, 12, 30)
            from datetime import timedelta
            return (base + timedelta(days=float(v))).strftime("%Y-%m-%d")
        except Exception:
            return ""
    return norm(v)


def today_str():
    return date.today().strftime("%Y-%m-%d")


# ---------------- الإعدادات ----------------
SETTINGS_DEFAULTS = {
    "school_name": SCHOOL_NAME,
    "currency": "درهم",
    "backup_on_start": True,
    "backup_on_exit": True,
    "backup_keep": 30,
    "exam_alert_days": 7,
    "sidebar_open": False,
    "theme": "light",
}


def settings_path():
    return os.path.join(data_dir(), "settings.json")


def load_settings():
    s = dict(SETTINGS_DEFAULTS)
    try:
        with open(settings_path(), "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


SETTINGS = load_settings()

# تطبيق الثيم المحفوظ
THEME_MODE = SETTINGS.get("theme", "light")


def school():
    return SETTINGS.get("school_name") or SCHOOL_NAME


def currency():
    return SETTINGS.get("currency") or "درهم"


# ---------------- التشفير وتسجيل الدخول ----------------
ROLES = ("admin", "employee")
ROLE_LABELS = {"admin": "مدير", "employee": "موظف"}
# صلاحيات كل دور
PERMS = {
    "add": ("admin", "employee"), "edit": ("admin", "employee"),
    "pay": ("admin", "employee"), "receipt": ("admin", "employee"),
    "search": ("admin", "employee"), "reports": ("admin", "employee"),
    "exams": ("admin", "employee"), "export": ("admin", "employee"),
    "delete": ("admin",), "import": ("admin",), "settings": ("admin",),
    "users": ("admin",), "trash": ("admin",), "purge": ("admin",),
}


def _auth_path():
    return os.path.join(data_dir(), "auth.json")


def db_plain_path():
    return os.path.join(data_dir(), "driving_school.db")


def db_enc_path():
    return os.path.join(data_dir(), "driving_school.db.enc")


def _kek(password, salt):
    kdf = PBKDF2HMAC(algorithm=_hashes.SHA256(), length=32,
                      salt=salt, iterations=200000)
    return _b64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _pw_hash(password, salt):
    dk = _hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                              salt, 200000)
    return _b64.urlsafe_b64encode(dk).decode("ascii")


class Auth:
    """إدارة المستخدمين والمفتاح المشفّر (تُحفظ في auth.json)."""

    def __init__(self):
        self.data = {"users": {}}
        self._load()

    def _load(self):
        try:
            with open(_auth_path(), "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {"users": {}}

    def _save(self):
        try:
            with open(_auth_path(), "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def has_users(self):
        return bool(self.data.get("users"))

    def create_user(self, username, password, role, key=None):
        username = norm(username)
        if not username or not password:
            return False, "اسم المستخدم وكلمة المرور مطلوبان."
        if username in self.data["users"]:
            return False, "اسم المستخدم موجود مسبقاً."
        if role not in ROLES:
            role = "employee"
        psalt = _secrets.token_bytes(16)
        u = {"role": role,
             "pw_salt": _b64.urlsafe_b64encode(psalt).decode("ascii"),
             "pw_hash": _pw_hash(password, psalt)}
        if CRYPTO_OK and key is not None:
            ksalt = _secrets.token_bytes(16)
            u["kdf_salt"] = _b64.urlsafe_b64encode(ksalt).decode("ascii")
            u["wrapped_key"] = Fernet(_kek(password, ksalt)).encrypt(
                key).decode("ascii")
        self.data["users"][username] = u
        self._save()
        return True, "تم إنشاء المستخدم."

    def delete_user(self, username):
        if username in self.data["users"]:
            del self.data["users"][username]
            self._save()
            return True
        return False

    def list_users(self):
        return [(name, u.get("role", "employee"))
                for name, u in self.data.get("users", {}).items()]

    def verify(self, username, password):
        """يتحقق من كلمة المرور ويعيد (صحيح, الدور, المفتاح)."""
        username = norm(username)
        u = self.data.get("users", {}).get(username)
        if not u:
            return False, None, None
        psalt = _b64.urlsafe_b64decode(u["pw_salt"].encode("ascii"))
        if _pw_hash(password, psalt) != u["pw_hash"]:
            return False, None, None
        key = None
        if CRYPTO_OK and u.get("wrapped_key"):
            try:
                ksalt = _b64.urlsafe_b64decode(
                    u["kdf_salt"].encode("ascii"))
                key = Fernet(_kek(password, ksalt)).decrypt(
                    u["wrapped_key"].encode("ascii"))
            except Exception:
                return False, None, None
        return True, u.get("role", "employee"), key

    def change_password(self, username, old_pw, new_pw, key=None):
        ok, role, _k = self.verify(username, old_pw)
        if not ok:
            return False, "كلمة المرور الحالية غير صحيحة."
        u = self.data["users"][username]
        psalt = _secrets.token_bytes(16)
        u["pw_salt"] = _b64.urlsafe_b64encode(psalt).decode("ascii")
        u["pw_hash"] = _pw_hash(new_pw, psalt)
        if CRYPTO_OK and key is not None:
            ksalt = _secrets.token_bytes(16)
            u["kdf_salt"] = _b64.urlsafe_b64encode(ksalt).decode("ascii")
            u["wrapped_key"] = Fernet(_kek(new_pw, ksalt)).encrypt(
                key).decode("ascii")
        self._save()
        return True, "تم تغيير كلمة المرور."


def db_encrypt_to_disk(plain_path, enc_path, key):
    with open(plain_path, "rb") as fh:
        data = fh.read()
    with open(enc_path, "wb") as fh:
        fh.write(Fernet(key).encrypt(data))


def db_decrypt_to_plain(enc_path, plain_path, key):
    with open(enc_path, "rb") as fh:
        data = Fernet(key).decrypt(fh.read())
    with open(plain_path, "wb") as fh:
        fh.write(data)


def ensure_plain_db(key):
    """يضمن وجود ملف قاعدة بيانات نصي جاهز للاستخدام (يفكّ التشفير عند الحاجة)."""
    plain, enc = db_plain_path(), db_enc_path()
    if CRYPTO_OK and key is not None and os.path.exists(enc):
        try:
            db_decrypt_to_plain(enc, plain, key)
        except Exception as e:
            LOG.exception("فشل فك تشفير القاعدة: %r", e)
            return None
    return plain if os.path.exists(plain) else None


def seal_db_after_close(key):
    """يشفّر القاعدة بعد الإغلاق ويحذف النسخة النصية (تبقى مشفرة على القرص)."""
    if not (CRYPTO_OK and key is not None):
        return
    plain, enc = db_plain_path(), db_enc_path()
    if not os.path.exists(plain):
        return
    import gc, time
    gc.collect()
    try:
        db_encrypt_to_disk(plain, enc, key)
    except Exception as e:
        LOG.exception("فشل تشفير القاعدة عند الإغلاق: %r", e)
        return
    for attempt in range(5):
        try:
            os.remove(plain)
            return
        except OSError as e:
            LOG.warning("تعذر حذف القاعدة النصية (محاولة %d): %s", attempt + 1, e)
            time.sleep(0.3)
            gc.collect()
    LOG.error("فشل حذف القاعدة النصية بعد 5 محاولات: %s", plain)


# ---------------- السجل (logging + تدقيق) ----------------
def _setup_logging():
    lg = logging.getLogger("app")
    if lg.handlers:
        return lg
    lg.setLevel(logging.INFO)
    try:
        h = logging.FileHandler(os.path.join(data_dir(), "app.log"),
                                encoding="utf-8")
        h.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"))
        lg.addHandler(h)
    except Exception:
        pass
    return lg


LOG = _setup_logging()


def audit(action, details=""):
    """تسجيل عملية تدقيق في جدول audit_log وفي app.log."""
    LOG.info("%s | %s", action, details)
    try:
        if "AUDIT_DB" in globals() and AUDIT_DB is not None:
            AUDIT_DB.con.execute(
                "INSERT INTO audit_log(action,details,ts) VALUES(?,?,?)",
                (action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            AUDIT_DB.con.commit()
    except Exception:
        pass


# ---------------- النسخ الاحتياطي التلقائي ----------------
def backup_dir():
    d = os.path.join(data_dir(), "backups")
    os.makedirs(d, exist_ok=True)
    return d


def auto_backup(db, when="start"):
    """حفظ نسخة مؤرّخة من قاعدة البيانات ثم أرشفة القديم."""
    try:
        if not SETTINGS.get("backup_on_%s" % when, True):
            return None
        src = db.path
        if not os.path.exists(src):
            return None
        db.con.commit()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(backup_dir(),
                           "driving_school_%s_%s.db" % (when, stamp))
        shutil.copy2(src, dst)
        _prune_backups()
        LOG.info("نسخة احتياطية (%s): %s", when, dst)
        return dst
    except Exception as e:
        LOG.exception("فشل فك تشفير القاعدة: %r", e)
        return None


def _prune_backups():
    try:
        keep = int(SETTINGS.get("backup_keep", 30) or 30)
        files = sorted(
            (f for f in os.listdir(backup_dir()) if f.endswith(".db")),
            key=lambda f: os.path.getmtime(os.path.join(backup_dir(), f)))
        while len(files) > keep:
            os.remove(os.path.join(backup_dir(), files.pop(0)))
    except Exception:
        pass


# ---------------- قاعدة البيانات ----------------
class DB:
    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        c = self.con.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS candidates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT DEFAULT '', birth_date TEXT DEFAULT '',
            phone TEXT DEFAULT '', cin TEXT DEFAULT '',
            reg_number TEXT DEFAULT '', reg_date TEXT DEFAULT '',
            category TEXT DEFAULT 'B', vehicle_number TEXT DEFAULT '',
            exam1_date TEXT DEFAULT '', exam1_result TEXT DEFAULT '',
            exam2_date TEXT DEFAULT '', exam2_result TEXT DEFAULT '',
            total_price REAL DEFAULT 0, paid1 REAL DEFAULT 0,
            paid2 REAL DEFAULT 0, paid3 REAL DEFAULT 0,
            paid_extra REAL DEFAULT 0, notes TEXT DEFAULT '',
            photo_path TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER, amount REAL DEFAULT 0,
            date TEXT DEFAULT '', note TEXT DEFAULT '',
            slot TEXT DEFAULT '')""")
        cols = [r[1] for r in c.execute("PRAGMA table_info(candidates)")]
        for col, typ in (("paid_extra", "REAL DEFAULT 0"),
                         ("photo_path", "TEXT DEFAULT ''")):
            if col not in cols:
                c.execute("ALTER TABLE candidates ADD COLUMN %s %s" % (col, typ))
        # سجل التدقيق + سلة المهملات
        c.execute("""CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT DEFAULT '', details TEXT DEFAULT '',
            ts TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS trash(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT DEFAULT '', deleted_at TEXT DEFAULT '')""")
        self.con.commit()

    @staticmethod
    def row_to_dict(r):
        d = dict(r)
        for k in ("total_price", "paid1", "paid2", "paid3", "paid_extra"):
            try:
                d[k] = float(d.get(k) or 0)
            except Exception:
                d[k] = 0.0
        return d

    @staticmethod
    def total_paid(d):
        return (d.get("paid1", 0) + d.get("paid2", 0)
                + d.get("paid3", 0) + d.get("paid_extra", 0))

    @staticmethod
    def remaining(d):
        return (d.get("total_price", 0) or 0) - DB.total_paid(d)

    def add_candidate(self, d):
        c = self.con.cursor()
        c.execute("""INSERT INTO candidates(full_name,birth_date,phone,cin,
            reg_number,reg_date,category,vehicle_number,exam1_date,exam1_result,
            exam2_date,exam2_result,total_price,paid1,paid2,paid3,paid_extra,
            notes,photo_path) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d.get("full_name", ""), d.get("birth_date", ""),
             d.get("phone", ""), d.get("cin", ""),
             d.get("reg_number", ""), d.get("reg_date", ""),
             d.get("category", "B") or "B", d.get("vehicle_number", ""),
             d.get("exam1_date", ""), d.get("exam1_result", ""),
             d.get("exam2_date", ""), d.get("exam2_result", ""),
             d.get("total_price", 0), d.get("paid1", 0),
             d.get("paid2", 0), d.get("paid3", 0),
             d.get("paid_extra", 0), d.get("notes", ""),
             d.get("photo_path", "")))
        self.con.commit()
        return c.lastrowid

    def update_candidate(self, cid, d):
        self.con.execute("""UPDATE candidates SET full_name=?,birth_date=?,
            phone=?,cin=?,reg_number=?,reg_date=?,category=?,vehicle_number=?,
            exam1_date=?,exam1_result=?,exam2_date=?,exam2_result=?,
            total_price=?,paid1=?,paid2=?,paid3=?,paid_extra=?,notes=?,
            photo_path=? WHERE id=?""",
            (d.get("full_name", ""), d.get("birth_date", ""),
             d.get("phone", ""), d.get("cin", ""),
             d.get("reg_number", ""), d.get("reg_date", ""),
             d.get("category", "B") or "B", d.get("vehicle_number", ""),
             d.get("exam1_date", ""), d.get("exam1_result", ""),
             d.get("exam2_date", ""), d.get("exam2_result", ""),
             d.get("total_price", 0), d.get("paid1", 0),
             d.get("paid2", 0), d.get("paid3", 0),
             d.get("paid_extra", 0), d.get("notes", ""),
             d.get("photo_path", ""), cid))
        self.con.commit()

    def delete_candidate(self, cid):
        self.con.execute("DELETE FROM payments WHERE candidate_id=?", (cid,))
        self.con.execute("DELETE FROM candidates WHERE id=?", (cid,))
        self.con.commit()

    # ---- سلة المهملات (حذف مؤجّل) ----
    def soft_delete_candidate(self, cid):
        """نقل المرشح ودفعاته إلى السلة بدل حذفها نهائياً."""
        d = self.get(cid)
        if d is None:
            return False
        pays = self.payments_for(cid)
        payload = json.dumps({"cand": d, "pays": pays}, ensure_ascii=False)
        self.con.execute(
            "INSERT INTO trash(payload,deleted_at) VALUES(?,?)",
            (payload, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.con.execute("DELETE FROM payments WHERE candidate_id=?", (cid,))
        self.con.execute("DELETE FROM candidates WHERE id=?", (cid,))
        self.con.commit()
        audit("حذف (سلة)", d.get("full_name", ""))
        return True

    def list_trash(self):
        out = []
        rows = self.con.execute(
            "SELECT * FROM trash ORDER BY id DESC").fetchall()
        for r in rows:
            try:
                p = json.loads(r["payload"])
                name = p.get("cand", {}).get("full_name", "")
            except Exception:
                name = ""
            out.append({"id": r["id"], "name": name,
                        "deleted_at": r["deleted_at"]})
        return out

    def trash_count(self):
        """عدد العناصر في سلة المهملات (بدون تحميل المحتوى)."""
        try:
            return self.con.execute(
                "SELECT COUNT(*) FROM trash").fetchone()[0]
        except Exception:
            return 0

    def restore_trash(self, tid):
        r = self.con.execute("SELECT * FROM trash WHERE id=?", (tid,)).fetchone()
        if not r:
            return False
        p = json.loads(r["payload"])
        cand = p.get("cand", {})
        new_id = self.add_candidate(cand)
        for pay in p.get("pays", []):
            self.con.execute(
                "INSERT INTO payments(candidate_id,amount,date,note,slot)"
                " VALUES(?,?,?,?,?)",
                (new_id, pay.get("amount", 0), pay.get("date", ""),
                 pay.get("note", ""), pay.get("slot", "")))
        self.con.execute("DELETE FROM trash WHERE id=?", (tid,))
        self.con.commit()
        audit("استرجاع من السلة", cand.get("full_name", ""))
        return True

    def purge_trash(self, tid=None):
        if tid is None:
            self.con.execute("DELETE FROM trash")
        else:
            self.con.execute("DELETE FROM trash WHERE id=?", (tid,))
        self.con.commit()

    # ---- التقارير والإحصائيات ----
    def monthly_income(self, months=12):
        """دخل كل شهر من جدول payments."""
        rows = self.con.execute(
            "SELECT substr(date,1,7) AS ym, SUM(amount) AS total"
            " FROM payments WHERE date!='' GROUP BY ym ORDER BY ym DESC"
            " LIMIT ?", (months,)).fetchall()
        return [(r["ym"], r["total"] or 0) for r in rows]

    def category_counts(self):
        rows = self.con.execute(
            "SELECT category, COUNT(*) AS n FROM candidates"
            " GROUP BY category ORDER BY n DESC").fetchall()
        return [(r["category"] or "-", r["n"]) for r in rows]

    def results_distribution(self):
        passed = self.con.execute(
            "SELECT COUNT(*) AS n FROM candidates WHERE exam1_result='ناجح'"
            " OR exam2_result='ناجح'").fetchone()["n"]
        failed = self.con.execute(
            "SELECT COUNT(*) AS n FROM candidates WHERE"
            " (exam1_result='راسب' OR exam2_result='راسب')"
            " AND exam1_result!='ناجح' AND exam2_result!='ناجح'"
            ).fetchone()["n"]
        total = self.con.execute(
            "SELECT COUNT(*) AS n FROM candidates").fetchone()["n"]
        pending = max(total - passed - failed, 0)
        return [("ناجح", passed), ("راسب", failed), ("قيد الدراسة", pending)]

    def debtors(self):
        rows = self.all()
        return [d for d in rows if self.remaining(d) > 0.01]

    def upcoming_exams(self, days=7, rows=None):
        """الامتحانات خلال عدد الأيام القادمة (أو المتأخرة)."""
        today = date.today()
        horizon = today + timedelta(days=int(days))
        out = []
        for d in (rows if rows is not None else self.all()):
            for label, field, res in (("الامتحان 1", "exam1_date",
                                       "exam1_result"),
                                      ("الامتحان 2", "exam2_date",
                                       "exam2_result")):
                ds = norm(d.get(field))
                if not ds:
                    continue
                try:
                    dt = datetime.strptime(ds, "%Y-%m-%d").date()
                except Exception:
                    continue
                if d.get(res):  # سُجّلت النتيجة بالفعل
                    continue
                if today <= dt <= horizon:
                    out.append({"cand": d, "label": label, "date": ds,
                                "days": (dt - today).days})
        out.sort(key=lambda x: x["date"])
        return out

    def all_exams(self, rows=None):
        """كل الامتحانات المسجّلة (مع نتائجها) لعرضها في تقويم شهري."""
        out = []
        for d in (rows if rows is not None else self.all()):
            for label, field, res in (("الامتحان 1", "exam1_date",
                                       "exam1_result"),
                                      ("الامتحان 2", "exam2_date",
                                       "exam2_result")):
                ds = norm(d.get(field))
                if not ds:
                    continue
                try:
                    dt = datetime.strptime(ds, "%Y-%m-%d").date()
                except Exception:
                    continue
                out.append({"cand": d, "label": label, "date": ds, "dt": dt,
                            "result": norm(d.get(res))})
        out.sort(key=lambda x: x["date"])
        return out

    def get_audit(self, limit=200):
        rows = self.con.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get(self, cid):
        r = self.con.execute("SELECT * FROM candidates WHERE id=?",
                             (cid,)).fetchone()
        return self.row_to_dict(r) if r else None

    def all(self):
        return [self.row_to_dict(r) for r in
                self.con.execute("SELECT * FROM candidates ORDER BY id DESC")]

    def search(self, query, filt="all"):
        q = norm(query)
        rows = self.all()
        if q:
            ql = q.lower()
            rows = [d for d in rows if
                    ql in norm(d.get("full_name")).lower()
                    or ql in norm(d.get("phone")).lower()
                    or ql in norm(d.get("reg_number")).lower()
                    or ql in norm(d.get("cin")).lower()]
        if filt == "debt":
            rows = [d for d in rows if self.remaining(d) > 0.01]
        elif filt == "paid":
            rows = [d for d in rows if self.remaining(d) <= 0.01]
        elif filt == "passed":
            rows = [d for d in rows if "ناجح" in (d.get("exam1_result", ""),
                                                  d.get("exam2_result", ""))]
        elif filt == "failed":
            rows = [d for d in rows if
                    ("راسب" in (d.get("exam1_result", ""),
                                d.get("exam2_result", "")))
                    and "ناجح" not in (d.get("exam1_result", ""),
                                       d.get("exam2_result", ""))]
        return rows

    def find_duplicate(self, reg_number, full_name, phone, index=None):
        if index is None:
            index = self._index()
        rn = norm(reg_number).lower()
        if rn:
            hit = index[0].get(rn)
            if hit:
                return hit
        return index[1].get(name_phone_key(full_name, phone))

    def _index(self):
        by_reg, by_np = {}, {}
        for d in self.all():
            rn = norm(d.get("reg_number")).lower()
            if rn and rn not in by_reg:
                by_reg[rn] = d
            k = name_phone_key(d.get("full_name"), d.get("phone"))
            if k not in by_np:
                by_np[k] = d
        return by_reg, by_np

    def add_payment(self, cid, amount, d, note):
        c = self.get(cid)
        if c is None or amount <= 0:
            return None
        slot = "paid_extra"
        for s in ("paid1", "paid2", "paid3"):
            if (c.get(s) or 0) <= 0:
                slot = s
                break
        c[slot] = (c.get(slot) or 0) + amount
        self.update_candidate(cid, c)
        self.con.execute("""INSERT INTO payments(candidate_id,amount,date,note,
            slot) VALUES(?,?,?,?,?)""", (cid, amount, d, note, slot))
        self.con.commit()
        return slot

    def payments_for(self, cid):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM payments WHERE candidate_id=? ORDER BY id DESC",
            (cid,))]

    def close(self):
        try:
            self.con.close()
        except Exception:
            pass


# ---------------- الاستيراد ----------------
def dict_from_json_obj(o):
    return {
        "full_name": norm(o.get("fullName", "")),
        "birth_date": norm(o.get("birthDate", "")),
        "phone": norm(o.get("phone", "")),
        "cin": norm(o.get("cin", "")),
        "reg_number": norm(o.get("regNumber", "")),
        "reg_date": norm(o.get("regDate", "")),
        "category": norm(o.get("category", "")) or "B",
        "vehicle_number": norm(o.get("vehicleNumber", "")),
        "exam1_date": norm(o.get("exam1Date", "")),
        "exam1_result": norm(o.get("exam1Result", "")),
        "exam2_date": norm(o.get("exam2Date", "")),
        "exam2_result": norm(o.get("exam2Result", "")),
        "total_price": parse_num(o.get("totalPrice", 0)),
        "paid1": parse_num(o.get("paid1", 0)),
        "paid2": parse_num(o.get("paid2", 0)),
        "paid3": parse_num(o.get("paid3", 0)),
        "paid_extra": parse_num(o.get("paidExtra", 0)),
        "notes": norm(o.get("notes", "")),
        "photo_path": norm(o.get("photoPath", "")),
    }


def import_backup_json(db, path):
    with open(path, "r", encoding="utf-8-sig") as f:
        arr = json.load(f)
    if isinstance(arr, dict):
        arr = arr.get("candidates", arr.get("data", []))
    added = updated = 0
    index = db._index()
    for o in arr:
        if not isinstance(o, dict):
            continue
        d = dict_from_json_obj(o)
        if not d["full_name"]:
            continue
        ex = db.find_duplicate(d["reg_number"], d["full_name"],
                               d["phone"], index)
        if ex:
            if not d["photo_path"]:
                d["photo_path"] = ex.get("photo_path", "")
            db.update_candidate(ex["id"], d)
            updated += 1
        else:
            nid = db.add_candidate(d)
            d["id"] = nid
            rn = norm(d["reg_number"]).lower()
            if rn:
                index[0].setdefault(rn, d)
            index[1].setdefault(
                name_phone_key(d["full_name"], d["phone"]), d)
            added += 1
    return added, updated


def row_list_to_dict(vals):
    g = lambda i: norm(vals[i]) if i < len(vals) and vals[i] is not None else ""
    n = lambda i: parse_num(vals[i]) if i < len(vals) else 0.0
    return {
        "full_name": g(0), "phone": g(1), "cin": g(2), "reg_number": g(3),
        "reg_date": g(4), "category": g(5) or "B", "vehicle_number": g(6),
        "birth_date": g(7), "exam1_date": g(8), "exam1_result": g(9),
        "exam2_date": g(10), "exam2_result": g(11), "total_price": n(12),
        "paid1": n(13), "paid2": n(14), "paid3": n(15),
        "paid_extra": 0.0, "notes": g(18), "photo_path": "",
    }


def import_csv(db, path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise Exception("الملف فارغ.")
    start = 0
    if rows[0] and "الاسم الكامل" in norm(rows[0][0]):
        start = 1
    added = updated = 0
    index = db._index()
    for r in rows[start:]:
        if not r or not norm(r[0]):
            continue
        vals = list(r)
        for i in (4, 7, 8, 10):
            if i < len(vals):
                vals[i] = to_ymd(vals[i]) if isinstance(vals[i],
                                                       (int, float)) else vals[i]
        d = row_list_to_dict(vals)
        ex = db.find_duplicate(d["reg_number"], d["full_name"],
                               d["phone"], index)
        if ex:
            d["paid_extra"] = ex.get("paid_extra", 0)
            d["photo_path"] = ex.get("photo_path", "")
            db.update_candidate(ex["id"], d)
            updated += 1
        else:
            nid = db.add_candidate(d)
            d["id"] = nid
            rn = norm(d["reg_number"]).lower()
            if rn:
                index[0].setdefault(rn, d)
            index[1].setdefault(
                name_phone_key(d["full_name"], d["phone"]), d)
            added += 1
    return added, updated


def import_xlsx(db, path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows or len(rows) < 2:
        raise Exception("لا توجد صفوف بيانات في الملف.")
    header = [norm(v) for v in rows[0]]
    if "الاسم الكامل" not in header:
        raise Exception("الصف الأول يجب أن يحتوي عناوين الأعمدة.")
    col = {h: i for i, h in enumerate(header)}
    ci = lambda h: col.get(h, -1)
    gv = lambda r, h: r[ci(h)] if ci(h) >= 0 and ci(h) < len(r) else ""
    added = updated = 0
    index = db._index()
    for r in rows[1:]:
        if r is None or not norm(gv(r, "الاسم الكامل")):
            continue
        d = {
            "full_name": norm(gv(r, "الاسم الكامل")),
            "phone": norm(gv(r, "الهاتف")),
            "cin": norm(gv(r, "رقم البطاقة الوطنية")),
            "reg_number": norm(gv(r, "رقم التسجيل")),
            "reg_date": to_ymd(gv(r, "تاريخ التسجيل")),
            "category": norm(gv(r, "فئة العربة")) or "B",
            "vehicle_number": norm(gv(r, "رقم العربة")),
            "birth_date": to_ymd(gv(r, "تاريخ الازدياد")),
            "exam1_date": to_ymd(gv(r, "تاريخ الامتحان الأول")),
            "exam1_result": norm(gv(r, "نتيجة الامتحان الأول")),
            "exam2_date": to_ymd(gv(r, "تاريخ الامتحان الثاني")),
            "exam2_result": norm(gv(r, "نتيجة الامتحان الثاني")),
            "total_price": parse_num(gv(r, "الثمن الإجمالي")),
            "paid1": parse_num(gv(r, "الدفعة الأولى")),
            "paid2": parse_num(gv(r, "الدفعة الثانية")),
            "paid3": parse_num(gv(r, "الدفعة الثالثة")),
            "paid_extra": 0.0,
            "notes": norm(gv(r, "ملاحظات")),
            "photo_path": "",
        }
        ex = db.find_duplicate(d["reg_number"], d["full_name"],
                               d["phone"], index)
        if ex:
            d["paid_extra"] = ex.get("paid_extra", 0)
            d["photo_path"] = ex.get("photo_path", "")
            db.update_candidate(ex["id"], d)
            updated += 1
        else:
            nid = db.add_candidate(d)
            d["id"] = nid
            rn = norm(d["reg_number"]).lower()
            if rn:
                index[0].setdefault(rn, d)
            index[1].setdefault(
                name_phone_key(d["full_name"], d["phone"]), d)
            added += 1
    return added, updated


def import_file(db, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        return import_backup_json(db, path)
    if ext == ".csv":
        return import_csv(db, path)
    if ext in (".xlsx", ".xlsm"):
        return import_xlsx(db, path)
    raise Exception("صيغة غير مدعومة (JSON / CSV / XLSX فقط).")


# ---------------- التصدير ----------------
def export_csv(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADERS)
        for d in rows:
            tp = DB.total_paid(d)
            w.writerow([d.get("full_name", ""), d.get("phone", ""),
                        d.get("cin", ""), d.get("reg_number", ""),
                        d.get("reg_date", ""), d.get("category", ""),
                        d.get("vehicle_number", ""),
                        d.get("birth_date", ""),
                        d.get("exam1_date", ""), d.get("exam1_result", ""),
                        d.get("exam2_date", ""), d.get("exam2_result", ""),
                        d.get("total_price", 0), d.get("paid1", 0),
                        d.get("paid2", 0), d.get("paid3", 0), tp,
                        DB.remaining(d), d.get("notes", "")])


def export_xlsx(rows, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "المترشحون"
    try:
        ws.sheet_view.rightToLeft = True
    except Exception:
        pass
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="0B2E4A")
    thin = Side(style="thin", color="D8E0E8")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for j, h in enumerate(CSV_HEADERS, start=1):
        cell = ws.cell(row=1, column=j, value=h)
        cell.font = head_font
        cell.fill = head_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    for i, d in enumerate(rows, start=2):
        tp = DB.total_paid(d)
        vals = [d.get("full_name", ""), d.get("phone", ""),
                d.get("cin", ""), d.get("reg_number", ""),
                d.get("reg_date", ""), d.get("category", ""),
                d.get("vehicle_number", ""), d.get("birth_date", ""),
                d.get("exam1_date", ""), d.get("exam1_result", ""),
                d.get("exam2_date", ""), d.get("exam2_result", ""),
                d.get("total_price", 0), d.get("paid1", 0),
                d.get("paid2", 0), d.get("paid3", 0), tp,
                DB.remaining(d), d.get("notes", "")]
        if i % 2 == 0:
            fill = PatternFill("solid", fgColor="F5F8FB")
        else:
            fill = None
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=j, value=v)
            cell.border = border
            if fill:
                cell.fill = fill
    widths = [28, 15, 15, 15, 14, 10, 12, 14, 14, 12, 14, 12,
              12, 12, 12, 12, 12, 12, 30]
    for j, wd in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = wd
    ws.freeze_panes = "A2"
    wb.save(path)


def export_json(rows, path):
    arr = []
    for d in rows:
        arr.append({
            "fullName": d.get("full_name", ""),
            "birthDate": d.get("birth_date", ""),
            "phone": d.get("phone", ""),
            "cin": d.get("cin", ""),
            "regNumber": d.get("reg_number", ""),
            "regDate": d.get("reg_date", ""),
            "category": d.get("category", ""),
            "vehicleNumber": d.get("vehicle_number", ""),
            "exam1Date": d.get("exam1_date", ""),
            "exam1Result": d.get("exam1_result", ""),
            "exam2Date": d.get("exam2_date", ""),
            "exam2Result": d.get("exam2_result", ""),
            "totalPrice": d.get("total_price", 0),
            "paid1": d.get("paid1", 0),
            "paid2": d.get("paid2", 0),
            "paid3": d.get("paid3", 0),
            "paidExtra": d.get("paid_extra", 0),
            "notes": d.get("notes", ""),
            "photoPath": d.get("photo_path", ""),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)


# ---------------- كشف الحساب ----------------
def receipt_text(d, pays):
    L = []
    L.append("*%s*" % school())
    L.append("كشف حساب المترشح")
    L.append("────────────────")
    L.append("*المترشح:* " + d.get("full_name", ""))
    if d.get("cin"):
        L.append("*ب.ت.و:* " + d["cin"])
    if d.get("phone"):
        L.append("*الهاتف:* " + d["phone"])
    if d.get("reg_number"):
        L.append("*رقم التسجيل:* " + d["reg_number"])
    if d.get("category"):
        L.append("*فئة الرخصة:* " + d["category"])
    if d.get("reg_date"):
        L.append("*تاريخ التسجيل:* " + d["reg_date"])
    L.append("────────────────")
    L.append("*الوضعية المالية*")
    L.append("• الثمن الإجمالي: %s درهم" % fmt_money(d.get("total_price", 0)))
    if (d.get("paid1") or 0) > 0:
        L.append("• الدفعة الأولى: %s درهم" % fmt_money(d["paid1"]))
    if (d.get("paid2") or 0) > 0:
        L.append("• الدفعة الثانية: %s درهم" % fmt_money(d["paid2"]))
    if (d.get("paid3") or 0) > 0:
        L.append("• الدفعة الثالثة: %s درهم" % fmt_money(d["paid3"]))
    if (d.get("paid_extra") or 0) > 0:
        L.append("• دفعات إضافية: %s درهم" % fmt_money(d["paid_extra"]))
    L.append("• مجموع المؤدى: %s درهم" % fmt_money(DB.total_paid(d)))
    rem = DB.remaining(d)
    if rem > 0:
        L.append("• *المتبقي:* %s درهم" % fmt_money(rem))
    else:
        L.append("• الحالة: تم سداد كامل المبلغ")
    if pays:
        L.append("────────────────")
        L.append("*سجل الدفعات*")
        for p in pays:
            L.append("• %s درهم بتاريخ %s%s" % (
                fmt_money(p.get("amount", 0)), p.get("date", ""),
                (" (%s)" % p["note"]) if p.get("note") else ""))
    L.append("────────────────")
    if d.get("exam1_date") or d.get("exam2_date"):
        L.append("*الامتحانات*")
        if d.get("exam1_date"):
            s = "• الامتحان 1: " + d["exam1_date"]
            if d.get("exam1_result"):
                s += " (%s)" % d["exam1_result"]
            L.append(s)
        if d.get("exam2_date"):
            s = "• الامتحان 2: " + d["exam2_date"]
            if d.get("exam2_result"):
                s += " (%s)" % d["exam2_result"]
            L.append(s)
        L.append("━━━━━━━━━━━━━━━━━━━━")
    L.append("مع تحيات إدارة " + school())
    return "\n".join(L)


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def print_receipt_html(d, pays):
    """توليد ملف HTML جاهز للطباعة (يدعم العربية) وفتحه في المتصفح."""
    rows = []
    for p in pays:
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            _esc(p.get("date", "")), fmt_money(p.get("amount", 0)),
            _esc(p.get("note", ""))))
    pays_html = "".join(rows)
    rem = DB.remaining(d)
    rem_color = "#2E7D5B" if rem <= 0.01 else "#B23A3A"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = """<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8">
<title>كشف حساب - %(name)s</title>
<style>
body{font-family:'Segoe UI',Tahoma,Arial;direction:rtl;margin:0;padding:24px;color:#1F2933;background:#fff}
.hd{background:#0B2E4A;color:#fff;padding:16px 20px;border-radius:6px}
.hd h1{margin:0;font-size:20px}.hd .sub{color:#C4A35A;font-size:13px;margin-top:4px}
.gold{height:3px;background:#C4A35A;margin:0 0 18px}
table{width:100%%;border-collapse:collapse;margin-top:12px}
th,td{border:1px solid #D8E0E8;padding:8px 10px;text-align:right}
th{background:#0B2E4A;color:#fff}
.info{margin:10px 0}.info span{display:inline-block;min-width:150px;color:#64748B}
.big{font-size:16px;font-weight:bold}
.foot{margin-top:24px;color:#64748B;font-size:12px;text-align:center}
@media print{.noprint{display:none}}
</style></head><body>
<div class="hd"><h1>%(school)s</h1><div class="sub">كشف حساب المترشح</div></div>
<div class="gold"></div>
<div class="info"><span>المترشح:</span> <b>%(name)s</b></div>
%(extra)s
<hr>
<h3>الوضعية المالية</h3>
<div class="info"><span>الثمن الإجمالي:</span> <b>%(tp)s %(cur)s</b></div>
<div class="info"><span>مجموع المؤدى:</span> <b>%(paid)s %(cur)s</b></div>
<div class="info big" style="color:%(rem_color)s"><span>المتبقي:</span> %(rem)s %(cur)s</div>
%(pays_block)s
<div class="foot">طُبع بتاريخ %(stamp)s &mdash; إدارة %(school)s</div>
<div class="noprint" style="text-align:center;margin-top:20px">
<button onclick="window.print()" style="padding:10px 24px;background:#0B2E4A;color:#fff;border:0;border-radius:5px;font-size:15px;cursor:pointer">🖨️ طباعة / حفظ PDF</button>
</div>
</body></html>""" % {
        "school": _esc(school()), "name": _esc(d.get("full_name", "")),
        "extra": "".join(
            "<div class='info'><span>%s:</span> <b>%s</b></div>" % (k, _esc(d.get(kk, "")))
            for k, kk in (("ب.ت.و", "cin"), ("الهاتف", "phone"),
                          ("رقم التسجيل", "reg_number"),
                          ("فئة الرخصة", "category"),
                          ("تاريخ التسجيل", "reg_date")) if d.get(kk)),
        "tp": fmt_money(d.get("total_price", 0)),
        "paid": fmt_money(DB.total_paid(d)),
        "rem": fmt_money(rem), "rem_color": rem_color, "cur": currency(),
        "pays_block": ("<h3>سجل الدفعات</h3><table><tr><th>التاريخ</th>"
                       "<th>المبلغ</th><th>ملاحظة</th></tr>%s</table>" % pays_html)
        if pays_html else "", "stamp": stamp,
    }
    path = os.path.join(data_dir(), "receipt_print.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        os.startfile(path)
    except Exception:
        webbrowser_open(path)
    audit("طباعة كشف", d.get("full_name", ""))
    return path


def webbrowser_open(path):
    try:
        import webbrowser
        webbrowser.open(path)
    except Exception:
        pass


# ================= الواجهة =================
FILTERS = [("الكل", "all"), ("عليه دين", "debt"), ("مسدد بالكامل", "paid"),
           ("ناجح", "passed"), ("راسب", "failed")]


def setup_style(root):
    """تهيئة النمط العام (ttk) بهوية موحدة."""
    # ttkbootstrap's Style signature is Style(theme=...) (not master), so
    # passing `root` as the first positional breaks under ttkbootstrap.
    if TTKBOOTSTRAP_OK:
        try:
            style = ttk.Style("flatly")
        except Exception:
            style = ttk.Style()
    else:
        style = ttk.Style(root)
    try:
        if TTKBOOTSTRAP_OK:
            style.theme_use("flatly")
        else:
            style.theme_use("clam")
    except Exception:
        try:
            style.theme_use("clam")
        except Exception:
            pass

    style.configure(".", font=F_BODY, background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("TEntry", fieldbackground=CARD, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    insertcolor=NAVY, padding=6, relief="flat")
    style.map("TEntry", bordercolor=[("focus", BORDER)],
              lightcolor=[("focus", BORDER)], darkcolor=[("focus", BORDER)])
    style.configure("TCombobox", padding=5, fieldbackground=CARD,
                    bordercolor=BORDER, arrowcolor=NAVY)
    style.map("TCombobox", fieldbackground=[("readonly", CARD)])

    style.configure("TLabelframe", background=BG, bordercolor=BORDER,
                    relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=BG, foreground=NAVY,
                    font=F_HEAD)

    # أزرار
    style.configure("Tool.TButton", background=CARD, foreground=NAVY,
                    bordercolor=BORDER, focuscolor=CARD, padding=(14, 8),
                    font=F_BODY, relief="flat", borderwidth=1)
    style.map("Tool.TButton",
              background=[("active", "#E3EBF3"), ("pressed", "#D5E0EA")],
              bordercolor=[("active", NAVY)])

    style.configure("Primary.TButton", background=NAVY, foreground="white",
                    bordercolor=NAVY, focuscolor=NAVY, padding=(14, 8),
                    font=F_BODY_B, relief="flat", borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", NAVY_HOVER), ("pressed", NAVY_DARK)])

    style.configure("Accent.TButton", background=GOLD, foreground="#3A2E12",
                    bordercolor=GOLD, focuscolor=GOLD, padding=(14, 8),
                    font=F_BODY_B, relief="flat", borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", GOLD_DARK), ("pressed", GOLD_DARK)])

    style.configure("Danger.TButton", background=CARD, foreground=DANGER,
                    bordercolor=BORDER, focuscolor=CARD, padding=(14, 8),
                    font=F_BODY, relief="flat", borderwidth=1)
    style.map("Danger.TButton",
              background=[("active", "#F7E4E4"), ("pressed", "#F0D5D5")],
              bordercolor=[("active", DANGER)])

    # الجدول
    style.configure("Treeview", background=CARD, fieldbackground=CARD,
                    foreground=TEXT, rowheight=38, borderwidth=0,
                    font=F_BODY)
    style.map("Treeview", background=[("selected", NAVY)],
              foreground=[("selected", "white")])
    style.configure("Treeview.Heading", background=NAVY, foreground="white",
                    font=F_TH, relief="flat", padding=(10, 9))
    style.map("Treeview.Heading", background=[("active", NAVY_HOVER),
                                              ("pressed", NAVY_DARK)])
    # إصلاح تقني معروف: تَخطيط clam الافتراضي يغلّف منطقة الصفوف
    # بعنصري field/padding اللذين يرسمان خلفية الحقل فوق خلفية
    # الصف الناتجة عن الوسوم — إزالتهما تُظهر ألوان الصفوف (ناجح/راسب).
    try:
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    except Exception:
        pass

    style.configure("Vertical.TScrollbar", background="#CBD5E1",
                    troughcolor=BG, bordercolor=BG, arrowcolor=NAVY)
    style.configure("Horizontal.TScrollbar", background="#CBD5E1",
                    troughcolor=BG, bordercolor=BG, arrowcolor=NAVY)
    return style


def hover_bind(widget, on, off):
    widget.bind("<Enter>", lambda e: widget.config(bg=on), add="+")
    widget.bind("<Leave>", lambda e: widget.config(bg=off), add="+")


class App(tk.Tk):
    def __init__(self, role="admin", key=None, auth=None, username=""):
        super().__init__()
        self.role = role if role in ROLES else "admin"
        self.db_key = key
        self.auth = auth or Auth()
        self.username = username
        self.title(APP_TITLE + "  |  " + school())
        self.configure(bg=BG)
        setup_style(self)
        try:
            self.state("zoomed")
        except Exception:
            self.geometry("1180x720")
        self.minsize(980, 560)

        # فك تشفير القاعدة (إن وُجدت مشفّرة) ثم فتح ملف نصي مؤقّت
        plain = ensure_plain_db(self.db_key) or db_plain_path()
        self.db = DB(plain)
        global AUDIT_DB
        AUDIT_DB = self.db
        self.exp_dir = os.path.join(data_dir(), "exports")
        os.makedirs(self.exp_dir, exist_ok=True)

        # نسخة احتياطية عند الإقلاع
        auto_backup(self.db, "start")

        self.card_vars = {k: tk.StringVar(value="0")
                          for k in ("c_total", "c_paid", "c_rem", "c_pass")}
        self._current_rows = []
        self.current_group = "basic"
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.logout_requested = False
        self._build()
        self.refresh()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        audit("تسجيل دخول", "%s (%s)" % (username, ROLE_LABELS.get(role, role)))

    def toggle_theme(self):
        """تبديل الوضع (فاتح/داكن) وإعادة بناء الواجهة."""
        global THEME_MODE
        new_mode = "dark" if THEME_MODE == "light" else "light"
        apply_theme_constants(new_mode)
        try:
            SETTINGS["theme"] = THEME_MODE
            save_settings(SETTINGS)
        except Exception:
            pass
        # إعادة بناء الواجهة
        try:
            for w in self.winfo_children():
                w.destroy()
        except Exception:
            pass
        self.configure(bg=C("bg"))
        setup_style(self)
        self._build()
        self.refresh()
        self._bind_keys()

    def on_logout(self):
        """تسجيل الخروج ثم العودة إلى شاشة الدخول."""
        self.logout_requested = True
        self._on_close()

    def can(self, action):
        """هل يملك المستخدم الحالي صلاحية تنفيذ عملية؟"""
        return self.role in PERMS.get(action, ())

    def _on_close(self):
        """نسخة احتياطية عند الإغلاق ثم إغلاق آمن + تشفير القاعدة."""
        try:
            auto_backup(self.db, "exit")
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass
        # تشفير القاعدة على القرص بعد الإغلاق
        seal_db_after_close(self.db_key)
        self.destroy()

    # ---------- شريط التنقل العلوي (Navbar) ----------
    def _build_header(self):
        """شريط علوي ثابت مع شعار، اسم المؤسسة، زر القائمة، ومؤشر المستخدم."""
        header = tk.Frame(self, bg=NAVY, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        inner = tk.Frame(header, bg=NAVY)
        inner.pack(fill="both", expand=True, padx=16, pady=6)

        # زر القائمة (يمين الواجهة في RTL)
        self.hamburger = tk.Button(
            inner, text=icon_text("menu"), command=self._toggle_sidebar,
            bg=NAVY, fg="white", activebackground=NAVY_HOVER,
            activeforeground=GOLD, relief="flat", bd=0,
            highlightthickness=0, font=icon_font(20), cursor="hand2",
            padx=8, pady=0, takefocus=True)
        self.hamburger.pack(side="right")

        # منطقة الوسط: شعار + اسم التطبيق
        center = tk.Frame(inner, bg=NAVY)
        center.pack(side="right")
        seal = tk.Canvas(center, width=34, height=34, bg=NAVY,
                         highlightthickness=0, bd=0)
        seal.pack(side="right", padx=(0, 8))
        seal.create_oval(2, 2, 32, 32, fill=NAV_CHIP, outline=GOLD, width=1)
        seal.create_text(17, 17, text=icon_text("education"), fill=GOLD,
                         font=icon_font(15))

        app_info = tk.Frame(center, bg=NAVY)
        app_info.pack(side="right")
        tk.Label(app_info, text=APP_TITLE, bg=NAVY, fg="white",
                 font=F_TITLE, anchor="e").pack(anchor="e")
        tk.Label(app_info, text=school(), bg=NAVY, fg="white",
                 font=(FONT, 9), anchor="e").pack(anchor="e")

        # المستخدم الحالي وصلاحيته (يسار وسط)
        who = "%s  \u2022  %s" % (self.username or "\u2014",
                             ROLE_LABELS.get(self.role, self.role))
        tk.Label(inner, text=who, bg=NAVY, fg="white",
                 font=(FONT, 10)).pack(side="left", padx=(12, 0))

        # زر تبديل الوضع (فاتح/داكن) - Apple style
        self.theme_btn = tk.Button(
            inner, text=("🌙" if not is_dark() else "☀️"),
            command=self.toggle_theme,
            bg=NAVY, fg="white", activebackground=NAVY_HOVER,
            relief="flat", bd=0, highlightthickness=0,
            font=(FONT, 14), cursor="hand2", padx=6, pady=0)
        self.theme_btn.pack(side="left", padx=(6, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # ---------- القائمة المنسدلة ----------
    def _build_sidebar(self, parent):
        """درج تنقّل جانبي يفتح من يمين الشاشة (RTL) بتنسيق احترافي:
        ترويسة بشعار ودور المستخدم، زر إضافة ذهبي، أقسام بفواصل شعرية،
        أيقونات داخل شرائح، شارة أرقام، وشريط سفلي بالمستخدم والخروج."""
        self._nav_items = {}
        self._nav_order = []
        self._cta_row = None
        self._badge_labels = {}
        self._sb_anim_id = None

        sb = tk.Frame(parent, bg=NAVY, width=SIDEBAR_W, takefocus=1)
        # ظل رفيع على الحافة اليسرى (المحاذية للمحتوى) لفصل الدرج بصرياً
        shadow = tk.Frame(sb, bg=NAV_SHADOW, width=2)
        shadow.pack(side="left", fill="y")
        inner = tk.Frame(sb, bg=NAVY)
        inner.pack(side="left", fill="both", expand=True)
        sb.bind("<FocusIn>", lambda e: shadow.configure(bg=GOLD))
        sb.bind("<FocusOut>", lambda e: shadow.configure(bg=NAV_SHADOW))
        sb.bind("<Up>", lambda e: self._nav_move(-1))
        sb.bind("<Down>", lambda e: self._nav_move(1))
        self._sidebar = sb

        # ترويسة الدرج: شعار + اسم المؤسسة + دور المستخدم + زر الإغلاق
        brand = tk.Frame(inner, bg=NAVY_DARK)
        brand.pack(fill="x")
        tk.Frame(brand, bg=GOLD, height=3).pack(fill="x")
        top = tk.Frame(brand, bg=NAVY_DARK)
        top.pack(fill="x", padx=12, pady=(12, 10))
        close = tk.Button(
            top, text=icon_text("close"),
            command=lambda: self._hide_sidebar(True),
            bg=NAVY_DARK, fg=NAV_ICON, activebackground=NAVY_HOVER,
            activeforeground=GOLD, relief="flat", bd=0,
            highlightthickness=0, font=icon_font(12), cursor="hand2",
            padx=6, pady=2, takefocus=True)
        close.pack(side="left")
        close.bind("<Down>", lambda e: self._nav_move(1))
        close.bind("<Up>", lambda e: self._nav_move(-1))

        seal = tk.Canvas(top, width=40, height=40, bg=NAVY_DARK,
                         highlightthickness=0, bd=0)
        seal.pack(side="right")
        seal.create_oval(2, 2, 38, 38, fill=NAV_CHIP, outline=GOLD, width=1)
        seal.create_text(20, 21, text=icon_text("education"), fill=GOLD,
                         font=icon_font(17))

        meta = tk.Frame(top, bg=NAVY_DARK)
        meta.pack(side="right", fill="both", expand=True, padx=(10, 0))
        tk.Label(meta, text=school(), bg=NAVY_DARK, fg="white",
                 font=(FONT, 10, "bold"), anchor="e", wraplength=160,
                 justify="right").pack(fill="x")
        pill = tk.Frame(meta, bg=NAV_CHIP)
        pill.pack(fill="x", anchor="e", pady=(4, 0))
        tk.Label(pill,
                 text=" %s  •  %s " % ("لوحة التحكم",
                                       ROLE_LABELS.get(self.role, self.role)),
                 bg=NAV_CHIP, fg=GOLD, font=(FONT, 8)).pack(side="right")
        tk.Frame(brand, bg=NAV_LINE, height=1).pack(fill="x", padx=14)

        # الإجراء الأساسي
        if self.can("add"):
            self._build_sidebar_cta(inner)

        # منطقة التمرير
        wrap = tk.Frame(inner, bg=NAVY)
        wrap.pack(fill="both", expand=True)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=1)
        canvas = tk.Canvas(wrap, bg=NAVY, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=canvas.yview,
                           width=10, bg="#2A4A66", troughcolor=NAVY,
                           activebackground=GOLD, relief="flat", bd=0,
                           highlightthickness=0)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=1, sticky="nsew")
        self._sb_vsb = vsb
        content = tk.Frame(canvas, bg=NAVY)
        win = canvas.create_window((0, 0), window=content, anchor="nw")
        self._sb_canvas = canvas
        self._sb_content = content

        def _sync_scroll():
            try:
                bbox = canvas.bbox("all")
                need = bool(bbox and
                            (bbox[3] - bbox[1]) > canvas.winfo_height() + 2)
                managed = vsb.winfo_manager() == "grid"
                if need and not managed:
                    vsb.grid(row=0, column=0, sticky="ns")
                elif not need and managed:
                    vsb.grid_remove()
            except Exception:
                pass

        content.bind(
            "<Configure>",
            lambda e: (canvas.configure(scrollregion=canvas.bbox("all")),
                       self.after_idle(_sync_scroll)))
        canvas.bind(
            "<Configure>",
            lambda e: (canvas.itemconfigure(win, width=e.width),
                       self.after_idle(_sync_scroll)))
        sections = [
            ("المترشحون", [
                ("edit", "edit", "تعديل البيانات", self.on_edit,
                 "item", "edit"),
                ("receipt", "receipt", "كشف حساب", self.on_receipt,
                 "item", "receipt"),
                ("pay", "pay", "تسجيل دفعة", self.on_pay,
                 "item", "pay"),
                ("delete", "remove", "نقل إلى سلة المهملات",
                 self.on_delete, "danger", "delete"),
            ]),
            ("السجلات", [
                ("reports", "reports", "التقارير", self.on_reports,
                 "item", "reports"),
                ("exams", "exams", "الامتحانات", self.on_exams,
                 "item", "exams"),
                ("trash", "trash", "سلة المهملات", self.on_trash,
                 "item", "trash"),
            ]),
            ("البيانات", [
                ("import", "import", "استيراد", self.on_import,
                 "item", "import"),
                ("export", "export", "تصدير", self.on_export,
                 "item", "export"),
            ]),
            ("النظام", [
                ("settings", "settings", "الإعدادات", self.on_settings,
                 "item", "settings"),
                ("users", "users", "المستخدمون", self.on_users,
                 "item", "users"),
                ("about", "about", "حول البرنامج", self.on_about,
                 "item", None),
            ]),
        ]
        for title_text, items in sections:
            visible = [it for it in items
                       if it[5] is None or self.can(it[5])]
            if not visible:
                continue
            # عنوان القسم يميناً + خط شعري يمتد إلى يساره
            hdr = tk.Frame(content, bg=NAVY)
            hdr.pack(fill="x", padx=14, pady=(10, 3))
            tk.Label(hdr, text=title_text, bg=NAVY, fg=NAV_SECTION,
                     font=(FONT, 8, "bold"), anchor="e").pack(side="right")
            tk.Frame(hdr, bg=NAV_LINE, height=1).pack(
                side="right", fill="x", expand=True, padx=(8, 0),
                pady=(5, 0))
            for key, icon, label, cmd, kind, perm in visible:
                self._sb_item(content, key, icon, label, cmd, kind, perm)
            tk.Frame(content, bg=NAVY, height=2).pack(fill="x")

        # التذييل: المستخدم + الخروج
        self._build_sidebar_footer(inner)

        def _wheel(e):
            step = int(e.delta / 120) if e.delta else 0
            if step:
                canvas.yview_scroll(-step, "units")
        bind_mousewheel(canvas, _wheel)
        bind_mousewheel(content, _wheel)

        self.update_idletasks()
        self.after_idle(_sync_scroll)
        self._update_nav_state()
        self._rebuild_nav_order()

        # إعادة فتح الدرج إذا تركه المستخدم مفتوحاً
        if SETTINGS.get("sidebar_open"):
            self.after(250, self._show_sidebar)

    def _build_sidebar_cta(self, parent):
        """زر الإضافة الرئيسي أعلى القائمة (ذهبي + شارة الاختصار)."""
        row = tk.Frame(parent, bg=GOLD, cursor="hand2", takefocus=1,
                       highlightthickness=1, highlightbackground=GOLD)
        row.pack(fill="x", padx=12, pady=(4, 8))
        chip = tk.Frame(row, bg="#B08F48", width=30, height=28)
        chip.pack(side="right", padx=(10, 2), pady=5)
        chip.pack_propagate(False)
        icon = tk.Label(chip, text=icon_text("add"), bg="#B08F48",
                        fg="#2E2409", font=icon_font(14))
        icon.place(relx=0.5, rely=0.5, anchor="center")
        text = tk.Label(row, text="إضافة مترشح", bg=GOLD, fg="#2E2409",
                        font=F_BODY_B, anchor="e")
        text.pack(side="right", fill="x", expand=True, pady=6)
        hint = tk.Label(row, text="Ctrl+N", bg=GOLD, fg="#6B5518",
                        font=(FONT, 8), padx=2)
        hint.pack(side="left", padx=(2, 8))
        state = {"hover": False, "pressed": False, "focus": False}

        def paint():
            bg = GOLD_DARK if state["pressed"] else (
                "#D6B76A" if state["hover"] else GOLD)
            cbg = "#8E7233" if state["pressed"] else (
                GOLD_DARK if state["hover"] else "#B08F48")
            row.configure(bg=bg,
                          highlightbackground=NAVY if state["focus"] else GOLD)
            chip.configure(bg=cbg)
            icon.configure(bg=cbg)
            text.configure(bg=bg)
            hint.configure(bg=bg)

        def enter(e):
            state["hover"] = True
            paint()

        def leave(e):
            state["hover"] = False
            state["pressed"] = False
            paint()

        def press(e):
            state["pressed"] = True
            paint()
            row.focus_set()

        def release(e):
            state["pressed"] = False
            paint()
            if self._inside(row, e):
                self._hide_sidebar()
                self.on_add()

        def activate(e=None):
            self._hide_sidebar()
            self.on_add()
            return "break"

        for w in (row, icon, text, hint):
            w.configure(cursor="hand2")
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", press)
            w.bind("<ButtonRelease-1>", release)
        row.bind("<FocusIn>",
                 lambda e: (state.__setitem__("focus", True), paint()))
        row.bind("<FocusOut>",
                 lambda e: (state.__setitem__("focus", False), paint()))
        row.bind("<Return>", activate)
        row.bind("<space>", activate)
        row.bind("<Up>", lambda e: self._nav_move(-1))
        row.bind("<Down>", lambda e: self._nav_move(1))
        self._cta_row = row
        self._rebuild_nav_order()
    def _build_sidebar_footer(self, parent):
        foot = tk.Frame(parent, bg=NAVY_DARK)
        foot.pack(side="bottom", fill="x")
        tk.Frame(foot, bg=NAV_LINE, height=1).pack(fill="x")
        user = tk.Frame(foot, bg=NAVY_DARK)
        user.pack(fill="x", padx=14, pady=(10, 2))
        av = tk.Canvas(user, width=36, height=36, bg=NAVY_DARK,
                       highlightthickness=0, bd=0)
        av.pack(side="right")
        av.create_oval(2, 2, 34, 34, fill=GOLD, outline="")
        av.create_text(18, 18, text=self._initials(), fill=NAVY,
                       font=(FONT, 11, "bold"))
        info = tk.Frame(user, bg=NAVY_DARK)
        info.pack(side="right", fill="x", expand=True, padx=(10, 0))
        tk.Label(info, text=self.username or "—", bg=NAVY_DARK,
                 fg="white", font=(FONT, 10, "bold"),
                 anchor="e").pack(fill="x")
        tk.Label(info, text=ROLE_LABELS.get(self.role, self.role),
                 bg=NAVY_DARK, fg=NAV_ICON, font=(FONT, 8),
                 anchor="e").pack(fill="x")
        self._sb_item(foot, "logout", "logout", "تسجيل الخروج",
                      self.on_logout, "item", None, base_bg=NAVY_DARK)
        tk.Label(foot, text="الإصدار %s" % APP_VERSION, bg=NAVY_DARK,
                 fg=NAV_DISABLED, font=(FONT, 7), anchor="center").pack(
            fill="x", pady=(0, 8))

    def _initials(self):
        name = (self.username or "?").strip()
        return name[0].upper() if name else "?"

    def _sb_item(self, parent, key, icon, label, cmd, kind, perm,
                 base_bg=NAVY):
        """بند تنقّل: أيقونة داخل شريحة + نص + شارة اختيارية + مؤشر ذهبي."""
        palettes = {
            "item": {"fg": NAV_TEXT, "icon": NAV_ICON,
                     "hover": NAVY_HOVER, "chip": NAV_CHIP,
                     "chip_hot": NAV_CHIP_HOVER, "chip_off": "#0E2A40"},
            "danger": {"fg": "#F1B4B4", "icon": "#E08080",
                       "hover": "#5A2020", "chip": "#3A1D1D",
                       "chip_hot": "#7A2E2E", "chip_off": "#241416"},
        }
        pal = palettes.get(kind, palettes["item"])
        # لون أيقونة أساسي لكل قسم (يبقى ثابتاً ما لم يكن البند نشطاً/ممروراً)
        ICON_COLOR = {
            "edit": NAVY, "receipt": NAVY, "pay": GOLD, "delete": DANGER,
            "reports": NAVY, "exams": GOLD, "trash": DANGER,
            "import": NAVY, "export": NAVY, "settings": NAVY,
            "users": NAVY, "about": NAVY, "logout": NAV_TEXT,
        }
        base_icon = ICON_COLOR.get(key, pal["icon"])
        row = tk.Frame(parent, bg=base_bg, cursor="hand2", takefocus=1,
                       highlightthickness=0, bd=0)
        row.pack(fill="x", padx=10, pady=1)
        # المؤشر الذهب على حافة البداية (اليمين في RTL)
        accent = tk.Frame(row, bg=base_bg, width=3)
        accent.pack(side="right", fill="y")
        chip = tk.Frame(row, bg=pal["chip"], width=30, height=28)
        chip.pack(side="right", padx=(8, 6), pady=5)
        chip.pack_propagate(False)
        icon_lbl = tk.Label(chip, text=icon_text(icon), bg=pal["chip"],
                            fg=pal["icon"], font=icon_font(13))
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")
        text_lbl = tk.Label(row, text=label, bg=base_bg, fg=pal["fg"],
                            font=F_BODY, anchor="e")
        text_lbl.pack(side="right", fill="x", expand=True, pady=7)
        badge = None
        if key in ("exams", "trash"):
            badge = tk.Label(row, text="", bg=NAV_BADGE, fg=NAVY,
                             font=(FONT, 8, "bold"), padx=6, pady=0)
            self._badge_labels[key] = badge
        item = {"row": row, "icon": icon_lbl, "text": text_lbl,
                "accent": accent, "badge": badge, "cmd": cmd,
                "enabled": True, "hover": False, "pressed": False,
                "focus": False, "base": base_bg, "pal": pal, "chip": chip,
                "base_icon": base_icon}
        self._nav_items[key] = item

        def paint():
            if not item["enabled"]:
                bg, fg, ic, cbg = (base_bg, NAV_DISABLED, NAV_DISABLED,
                                   pal["chip_off"])
            else:
                active = (item["hover"] or item["focus"]
                          or item["pressed"])
                bg = (NAVY_DARK if item["pressed"] else
                      (pal["hover"] if item["hover"] else base_bg))
                fg = "white" if active else pal["fg"]
                ic = GOLD if active else item["base_icon"]
                cbg = (pal["chip_hot"] if item["hover"] or item["pressed"]
                       else pal["chip"])
            row.configure(bg=bg)
            chip.configure(bg=cbg)
            icon_lbl.configure(bg=cbg, fg=ic)
            text_lbl.configure(bg=bg, fg=fg)
            accent.configure(
                bg=GOLD if item["enabled"] and
                (item["focus"] or item["pressed"]) else bg)
            if badge is not None:
                badge.configure(
                    bg=NAV_BADGE if item["enabled"] else "#4A5A6A",
                    fg=NAVY if item["enabled"] else NAV_DISABLED)
        item["paint"] = paint

        def enter(e):
            if not item["enabled"]:
                return
            item["hover"] = True
            paint()

        def leave(e):
            item["hover"] = False
            item["pressed"] = False
            paint()

        def press(e):
            if not item["enabled"]:
                return
            item["pressed"] = True
            paint()
            row.focus_set()

        def release(e):
            was = item["pressed"]
            item["pressed"] = False
            paint()
            if was and item["enabled"] and self._inside(row, e):
                self._hide_sidebar()
                cmd()

        def focus_in(e):
            item["focus"] = True
            paint()

        def focus_out(e):
            item["focus"] = False
            paint()

        def activate(e=None):
            if item["enabled"]:
                self._hide_sidebar()
                cmd()
            return "break"

        for w in (row, icon_lbl, text_lbl, accent, chip):
            w.configure(cursor="hand2")
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", press)
            w.bind("<ButtonRelease-1>", release)
        if badge is not None:
            badge.configure(cursor="hand2")
            badge.bind("<Enter>", enter)
            badge.bind("<Leave>", leave)
            badge.bind("<Button-1>", press)
            badge.bind("<ButtonRelease-1>", release)
        row.bind("<FocusIn>", focus_in)
        row.bind("<FocusOut>", focus_out)
        row.bind("<Return>", activate)
        row.bind("<space>", activate)
        row.bind("<Up>", lambda e: self._nav_move(-1))
        row.bind("<Down>", lambda e: self._nav_move(1))
        paint()
        return item

    def _set_item_enabled(self, item, enabled):
        enabled = bool(enabled)
        if item["enabled"] == enabled:
            return
        item["enabled"] = enabled
        if not enabled:
            item["hover"] = False
            item["pressed"] = False
        item["row"].configure(
            takefocus=1 if enabled else 0,
            cursor="hand2" if enabled else "arrow")
        targets = [item["icon"], item["text"], item["accent"],
                   item.get("chip")]
        if item.get("badge") is not None:
            targets.append(item["badge"])
        for w in targets:
            if w is not None:
                w.configure(cursor="hand2" if enabled else "arrow")
        item["paint"]()

    def _update_nav_state(self):
        """تعطيل إجراءات المترشح عند عدم تحديد صف."""
        try:
            has_sel = bool(self.tree.selection())
        except Exception:
            has_sel = False
        selection_actions = {"edit", "pay", "receipt", "delete"}
        for key, item in getattr(self, "_nav_items", {}).items():
            enabled = has_sel if key in selection_actions else True
            self._set_item_enabled(item, enabled)
            if not enabled and self.focus_get() is item["row"]:
                self._sidebar.focus_set()
        state = "normal" if has_sel else "disabled"
        try:
            for idx in (0, 1, 2, 4):
                self.ctx.entryconfig(idx, state=state)
        except Exception:
            pass
        self._rebuild_nav_order()

    def _rebuild_nav_order(self):
        order = []
        if getattr(self, "_cta_row", None) is not None:
            order.append(self._cta_row)
        order.extend(it["row"] for it in self._nav_items.values()
                     if it["enabled"])
        self._nav_order = order

    def _nav_move(self, direction):
        order = getattr(self, "_nav_order", [])
        if not order:
            return "break"
        cur = self.focus_get()
        if cur in order:
            i = (order.index(cur) + direction) % len(order)
        else:
            i = 0 if direction > 0 else len(order) - 1
        order[i].focus_set()
        return "break"

    def _set_badge(self, key, count):
        item = (self._nav_items.get(key)
                if hasattr(self, "_nav_items") else None)
        if not item or item.get("badge") is None:
            return
        try:
            count = int(count)
        except Exception:
            count = 0
        badge = item["badge"]
        if count > 0:
            badge.configure(text=str(count) if count < 100 else "99+")
            if not badge.winfo_ismapped():
                badge.pack(side="left", padx=(4, 8))
        else:
            if badge.winfo_ismapped():
                badge.pack_forget()
        item["paint"]()

    @staticmethod
    def _inside(widget, event):
        try:
            x, y = event.x_root, event.y_root
            wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
            return (wx <= x <= wx + widget.winfo_width()
                    and wy <= y <= wy + widget.winfo_height())
        except Exception:
            return False

    def _toggle_sidebar(self):
        if self._sb_open:
            self._hide_sidebar()
        else:
            self._show_sidebar()

    def _show_sidebar(self):
        if self._sb_open:
            return
        self._sb_open = True
        self.update_idletasks()
        self._sidebar.lift()
        self._sidebar.focus_set()
        self._outside_armed = False
        if self._arm_id:
            try:
                self.after_cancel(self._arm_id)
            except Exception:
                pass
        self._arm_id = self.after(160, self._arm_outside)
        self._animate_sidebar_in()
        self._remember_sidebar_state()

    def _animate_sidebar_in(self):
        """حركة انزلاق سريعة للدرج من حافة اليمين (~60 م.ث)."""
        if self._sb_anim_id:
            try:
                self.after_cancel(self._sb_anim_id)
            except Exception:
                pass
            self._sb_anim_id = None
        steps = 5

        def tick(i):
            self._sb_anim_id = None
            if not self._sb_open:
                return
            if i >= steps:
                self._place_sidebar()
                return
            self._place_sidebar(offset=SIDEBAR_W * (steps - i) // steps)
            self._sb_anim_id = self.after(12, tick, i + 1)
        tick(0)

    def _hide_sidebar(self, focus_back=False):
        if not self._sb_open:
            return
        self._sb_open = False
        self._outside_armed = False
        if self._arm_id:
            try:
                self.after_cancel(self._arm_id)
            except Exception:
                pass
            self._arm_id = None
        if self._sb_anim_id:
            try:
                self.after_cancel(self._sb_anim_id)
            except Exception:
                pass
            self._sb_anim_id = None
        self._sidebar.place_forget()
        if focus_back:
            try:
                self.hamburger.focus_set()
            except Exception:
                pass
        self._remember_sidebar_state()

    def _place_sidebar(self, offset=0):
        parent = self._sb_parent
        try:
            w = max(parent.winfo_width(), 1)
            h = max(parent.winfo_height(), 1)
        except Exception:
            w, h = SIDEBAR_W, 400
        sw = min(SIDEBAR_W, max(w - 24, 200))
        x = max(w - sw, 0) + max(int(offset), 0)
        self._sidebar.place(x=x, y=0, width=sw, height=h)

    def _on_resize(self, e=None):
        if self._sb_open and not self._sb_anim_id:
            self._place_sidebar()

    def _arm_outside(self):
        self._outside_armed = True

    def _remember_sidebar_state(self):
        if SETTINGS.get("sidebar_open") == self._sb_open:
            return
        SETTINGS["sidebar_open"] = self._sb_open
        save_settings(SETTINGS)

    def _on_global_click(self, e):
        if not self._sb_open or not self._outside_armed:
            return
        x, y = e.x_root, e.y_root
        try:
            wx, wy = (self._sidebar.winfo_rootx(),
                      self._sidebar.winfo_rooty())
            ww, wh = (self._sidebar.winfo_width(),
                      self._sidebar.winfo_height())
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                return
            hx, hy = (self.hamburger.winfo_rootx(),
                      self.hamburger.winfo_rooty())
            hw, hh = (self.hamburger.winfo_width(),
                      self.hamburger.winfo_height())
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                return
        except Exception:
            pass
        self._hide_sidebar()




    # ---------- بطاقة ----------
    def _card(self, parent, title, var, accent=GOLD):
        card = tk.Frame(parent, bg=CARD, highlightbackground=CARD_BORDER,
                        highlightthickness=1, bd=0, cursor="hand2")
        tk.Frame(card, bg=accent, width=5).pack(side="right", fill="y")
        body = tk.Frame(card, bg=CARD)
        body.pack(side="right", fill="both", expand=True, padx=14, pady=12)
        tk.Label(body, text=title, bg=CARD, fg=MUTED, font=F_CARD_T,
                 anchor="e").pack(anchor="e")
        val_lbl = tk.Label(body, textvariable=var, bg=CARD, fg=NAVY,
                           font=F_CARD_NUM, anchor="e")
        val_lbl.pack(anchor="e")

        def enter(e):
            card.configure(bg=CARD_HOVER_BG,
                           highlightbackground=CARD_HOVER_BORDER)
            body.configure(bg=CARD_HOVER_BG)
            for w in body.winfo_children():
                w.configure(bg=CARD_HOVER_BG)
            card.configure(cursor="hand2")

        def leave(e):
            card.configure(bg=CARD, highlightbackground=CARD_BORDER)
            body.configure(bg=CARD)
            for w in body.winfo_children():
                w.configure(bg=CARD)
            card.configure(cursor="hand2")

        card.bind("<Enter>", enter)
        card.bind("<Leave>", leave)
        body.bind("<Enter>", enter)
        body.bind("<Leave>", leave)
        val_lbl.bind("<Enter>", enter)
        val_lbl.bind("<Leave>", leave)
        return card

    # ---------- بطاقات الملخص ----------
    def _build_cards(self, parent):
        wrap = ttk.Frame(parent, padding=(16, 10, 16, 8))
        wrap.pack(fill="x")
        specs = [("المترشحون", "c_total", GOLD),
                 ("المُحصَّل (درهم)", "c_paid", NAVY),
                 ("الباقي (درهم)", "c_rem", DANGER),
                 ("الناجحون", "c_pass", OK)]
        for i, (title, key, accent) in enumerate(specs):
            self._card(wrap, title, self.card_vars[key], accent).grid(
                row=0, column=i, sticky="nsew", padx=10)
            wrap.grid_columnconfigure(i, weight=1, minsize=220)

    # ---------- البحث والفلتر ----------
    def _build_search(self, parent):
        bar = ttk.Frame(parent, padding=(16, 10, 16, 8))
        bar.pack(fill="x")

        self.filter_var = tk.StringVar(value=FILTERS[0][0])
        fbox = ttk.Combobox(bar, textvariable=self.filter_var,
                            values=[f[0] for f in FILTERS],
                            state="readonly", width=16, justify="right")
        fbox.pack(side="left", padx=(6, 0))
        fbox.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Label(bar, text="الفلتر:").pack(side="left", padx=(0, 2))

        self.search_var = tk.StringVar()
        sent = ttk.Entry(bar, textvariable=self.search_var,
                         justify="right", width=34)
        sent.pack(side="right", padx=(6, 0))
        ttk.Label(bar, text="بحث:").pack(side="right")
        sent.bind("<KeyRelease>", lambda e: self.refresh())

        # زر إضافة مترشح بجانب البحث (من الجهة اليسرى)
        if self.can("add"):
            ttk.Button(bar, text="➕ إضافة مترشح",
                       style="Accent.TButton", command=self.on_add).pack(
                side="right", padx=(6, 0))

    # ---------- شريط تبديل مجموعات الأعمدة ----------
    def _build_group_bar(self, parent):
        """أزرار switching بين مجموعات الأعمدة (أساسية / مالية / امتحانات / كاملة)."""
        bar = ttk.Frame(parent, padding=(16, 4, 16, 4))
        bar.pack(fill="x")

        ttk.Label(bar, text="عرض الأعمدة:").pack(side="right", padx=(0, 6))

        self.group_var = tk.StringVar(value=self.current_group)
        for key, label in TABLE_GROUP_ORDER:
            btn = ttk.Radiobutton(bar, text=label, value=key,
                                  variable=self.group_var,
                                  command=self._on_group_change)
            btn.pack(side="right", padx=4)

    def _on_group_change(self):
        self.current_group = self.group_var.get()
        self.current_page = 1
        self._rebuild_columns()
        self.refresh()

    def _rebuild_columns(self):
        """تحديث أعمدة الجدول حسب المجموعة المختارة."""
        self.tree.delete(*self.tree.get_children())
        fields = TABLE_FIELD_GROUPS.get(self.current_group,
                                        TABLE_FIELD_GROUPS["basic"])
        self._disp_fields = list(reversed(fields))
        cols = tuple(f[0] for f in self._disp_fields)
        heads = {f[0]: f[1] for f in fields}
        widths = {f[0]: f[2] for f in fields}
        stretch = {f[0]: f[3] for f in fields}

        self.tree.config(columns=cols)
        self._head_texts = heads
        for c in cols:
            self.tree.heading(c, text=heads[c], anchor="e",
                              command=lambda col=c: self._sort_by(col))
            # minwidth verhindert dass die Spalte komplett kollabiert;
            # der Name bekommt ein größeres Minimum, damit er immer sichtbar bleibt.
            self.tree.column(c, width=widths[c], anchor="e",
                             stretch=stretch[c],
                             minwidth=150 if c == "full_name" else 80)
        self._sort_col = None
        self._sort_desc = False


    # ---------- الجدول (من اليمين إلى اليسار بكل الحقول) ----------
    # ---------- الجدول (من اليمين إلى اليسار بكل الحقول) ----------
    def _build_table(self, parent):
        mid = ttk.Frame(parent, padding=(16, 10, 16, 10))
        mid.pack(fill="both", expand=True)

        # عرض الجدول من اليمين إلى اليسار: عكس ترتيب الأعمدة للمجموعة المختارة
        fields = TABLE_FIELD_GROUPS.get(self.current_group, TABLE_FIELD_GROUPS["basic"])
        self._disp_fields = list(reversed(fields))
        cols = tuple(f[0] for f in self._disp_fields)
        heads = {f[0]: f[1] for f in fields}
        widths = {f[0]: f[2] for f in fields}
        stretch = {f[0]: f[3] for f in fields}

        self.tree = ttk.Treeview(mid, columns=cols, show="headings",
                                 selectmode="browse")
        self._head_texts = heads
        for c in cols:
            self.tree.heading(c, text=heads[c], anchor="e",
                              command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=widths[c], anchor="e",
                             stretch=stretch[c],
                             minwidth=150 if c == "full_name" else 80)
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

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        # إعادة تعيين نصوص الرؤوس
        for c in self.tree["columns"]:
            arrow = ""
            if c == self._sort_col:
                arrow = "  ▼" if self._sort_desc else "  ▲"
            self.tree.heading(c, text=self._head_texts[c] + arrow)
        self._apply_sort()

    def _sort_rows(self, rows):
        col = self._sort_col
        if not col:
            return rows
        if col in MONEY_FIELDS:
            def key(d):
                if col == "total_paid":
                    return DB.total_paid(d)
                if col == "remaining":
                    return DB.remaining(d)
                return d.get(col) or 0
        else:
            def key(d):
                return (d.get(col) or "").lower()
        return sorted(rows, key=key, reverse=self._sort_desc)

    def _apply_sort(self):
        self._current_rows = self._sort_rows(self._current_rows)
        self.current_page = 1
        self._render_paginated()

    _HOVER_BG = {"even": "hover", "odd": "hover",
                 "pass": "hover_pass", "pass_alt": "hover_pass",
                 "fail": "hover_fail", "fail_alt": "hover_fail"}

    def _on_tree_hover(self, e=None):
        """تحويم موثوق: استبدال وسم الخلفية بنسخته ثم إعادته."""
        try:
            row = self.tree.identify_row(e.y) if e is not None else None
        except Exception:
            row = None
        if row == getattr(self, "_hover_row", None):
            return
        try:
            prev = getattr(self, "_hover_row", None)
            if prev:
                self._restore_hover_tags(prev)
            self._hover_row = row
            if not row or row == self.tree.focus():
                return
            cur = list(self.tree.item(row, "tags") or ())
            if any(t.startswith("hover") for t in cur):
                return
            base = self._row_bg_tag.get(row, cur[0] if cur else "even")
            keep = [t for t in cur if t != base]
            self.tree.item(row, tags=tuple(
                keep + [self._HOVER_BG.get(base, "hover")]))
        except Exception:
            pass

    def _restore_hover_tags(self, row):
        try:
            base = self._row_bg_tag.get(row)
            tags = [t for t in self.tree.item(row, "tags")
                    if not t.startswith("hover")]
            if base and base not in tags:
                tags.insert(0, base)
            self.tree.item(row, tags=tuple(tags))
        except Exception:
            pass

    def _on_tree_leave(self, e=None):
        self._on_tree_hover_clear()

    def _on_tree_hover_clear(self):
        try:
            if getattr(self, "_hover_row", None):
                self._restore_hover_tags(self._hover_row)
        except Exception:
            pass
        self._hover_row = None

    def _show_context(self, e):
        row = self.tree.identify_row(e.y)
        if row:
            self.tree.selection_set(row)
            self.ctx.tk_popup(e.x_root, e.y_root)

    def _bind_keys(self):
        self.bind("<F5>", lambda e: self.refresh())
        self.bind("<Delete>", lambda e: self.on_delete())
        self.bind("<Return>", lambda e: self.on_edit())
        self.bind("<Control-n>", lambda e: self.on_add())

    # ---------- شريط التصنيف الصفحي ----------
    def _build_pagination_bar(self, parent):
        """أزرار التنقل بين الصفحات + مؤشر رقم الصفحة."""
        bar = ttk.Frame(parent, padding=(16, 6, 16, 6))
        bar.pack(fill="x")

        self.pg_first = ttk.Button(bar, text="<< الأول",
                                   command=self._pg_first, width=10)
        self.pg_first.pack(side="right", padx=3)
        self.pg_prev = ttk.Button(bar, text="‹ السابق",
                                  command=self._pg_prev, width=10)
        self.pg_prev.pack(side="right", padx=3)

        self.pg_label = tk.Label(bar, text="صفحة 1 من 1", bg=BG, fg=MUTED,
                                 font=F_BODY_B)
        self.pg_label.pack(side="right", padx=10)

        self.pg_next = ttk.Button(bar, text="التالي ›",
                                  command=self._pg_next, width=10)
        self.pg_next.pack(side="right", padx=3)
        self.pg_last = ttk.Button(bar, text="الأخير >>",
                                  command=self._pg_last, width=10)
        self.pg_last.pack(side="right", padx=3)

        ttk.Label(bar, text="سجلات في الصفحة:").pack(side="right", padx=(14, 4))
        self.pg_size_var = tk.StringVar(value=str(self.page_size))
        self.pg_size = ttk.Combobox(bar, textvariable=self.pg_size_var,
                                    values=["25", "50", "100", "200"],
                                    width=6, state="readonly")
        self.pg_size.pack(side="right", padx=2)
        self.pg_size.bind("<<ComboboxSelected>>", self._on_page_size_change)

    def _pg_first(self):
        self.current_page = 1
        self._render_paginated()

    def _pg_prev(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_paginated()

    def _pg_next(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_paginated()

    def _pg_last(self):
        self.current_page = self.total_pages
        self._render_paginated()

    def _on_page_size_change(self, e=None):
        try:
            self.page_size = int(self.pg_size_var.get())
        except Exception:
            self.page_size = 50
        self.current_page = 1
        self.refresh()

    def _render_paginated(self):
        """عرض الصفحة الحالية من self._current_rows."""
        total = len(self._current_rows)
        if total == 0:
            self.total_pages = 1
            self.current_page = 1
        else:
            self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_rows = self._current_rows[start:end]

        self._render_rows(page_rows)
        self.pg_label.config(
            text="صفحة %d من %d   (إجمالي %d سجل)"
            % (self.current_page, self.total_pages, total))
        # تحديث حالة أزرار التنقل
        state_first_prev = "normal" if self.current_page > 1 else "disabled"
        state_next_last = "normal" if self.current_page < self.total_pages else "disabled"
        try:
            self.pg_first.config(state=state_first_prev)
            self.pg_prev.config(state=state_first_prev)
            self.pg_next.config(state=state_next_last)
            self.pg_last.config(state=state_next_last)
        except Exception:
            pass

    # ---------- شريط الحالة ----------
    def _build_status(self):
        bar = tk.Frame(self, bg=STATUS_BG)
        bar.pack(fill="x", side="bottom")
        tk.Frame(bar, bg=GOLD, width=5).pack(side="right", fill="y")

        # اليسار: الوقت + التاريخ + عدد السجلات
        info = tk.Frame(bar, bg=STATUS_BG)
        info.pack(side="left", fill="x", padx=12)
        self.status_clock = tk.Label(info, bg=STATUS_BG, fg=STATUS_FG,
                                     font=F_SMALL, anchor="w")
        self.status_clock.pack(side="left")
        self.status_records = tk.Label(info, bg=STATUS_BG, fg=MUTED,
                                       font=F_SMALL, anchor="w")
        self.status_records.pack(side="left", padx=(10, 0))

        # اليمين: الرسالة الرئيسية
        self.status = tk.StringVar()
        tk.Label(bar, textvariable=self.status, bg=STATUS_BG, fg=STATUS_FG,
                 font=F_BODY, anchor="e", padx=12, pady=6).pack(
            side="right", fill="x", expand=True)

        self._tick_status()

    def _tick_status(self):
        """تحديث الوقت والتاريخ وعدد السجلات في شريط الحالة كل ثانية."""
        try:
            from datetime import datetime
            now = datetime.now()
            self.status_clock.config(
                text=now.strftime("%Y-%m-%d  %I:%M:%S %p"))
            try:
                total = len(self.db.all())
            except Exception:
                total = 0
            self.status_records.config(text="السجلات: %d" % total)
        except Exception:
            pass
        self.after(1000, self._tick_status)

    def _show_loading(self, msg="جاري المعالجة..."):
        """عرض غطاء معالجة شفاف فوق النافذة."""
        if getattr(self, "_loading_overlay", None) is not None:
            return
        ov = tk.Frame(self, bg=BG)
        ov.place(relx=0, rely=0, relwidth=1, relheight=1)
        ov.lift()
        center = tk.Frame(ov, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self._loading_spin = ["|", "/", "-", "\\"]
        self._loading_idx = 0
        spin_lbl = tk.Label(center, text=self._loading_spin[0], bg=BG,
                            fg=GOLD, font=(FONT, 14, "bold"))
        spin_lbl.pack(side="right", padx=(8, 0))
        msg_lbl = tk.Label(center, text=msg, bg=BG, fg=NAVY,
                           font=F_BODY_B)
        msg_lbl.pack(side="right")
        self._loading_overlay = ov
        self._loading_spin_lbl = spin_lbl
        self._spin_tick()

    def _spin_tick(self):
        ov = getattr(self, "_loading_overlay", None)
        if ov is None:
            return
        self._loading_idx = (self._loading_idx + 1) % 4
        try:
            self._loading_spin_lbl.config(text=self._loading_spin[self._loading_idx])
        except Exception:
            pass
        self._loading_job = self.after(90, self._spin_tick)

    def _hide_loading(self):
        """إزالة غطاء المعالجة."""
        try:
            if getattr(self, "_loading_job", None):
                self.after_cancel(self._loading_job)
                self._loading_job = None
        except Exception:
            pass
        ov = getattr(self, "_loading_overlay", None)
        if ov is not None:
            ov.place_forget()
            ov.destroy()
            self._loading_overlay = None


    def _build(self):
        self._build_status()
        self._build_header()
        # حاوية: محتوى رئيسي + قائمة منسدلة تتراكب فوقه
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self._sb_parent = container
        main = ttk.Frame(container)
        main.pack(fill="both", expand=True)
        self._build_cards(main)
        self._build_search(main)
        self._build_group_bar(main)
        self._build_table(main)
        self._build_pagination_bar(main)
        self._sb_open = False
        self._outside_armed = False
        self._arm_id = None
        self._build_sidebar(container)
        container.bind("<Configure>", self._on_resize, add="+")
        self.bind("<Button-1>", self._on_global_click, add="+")
        self.bind("<Escape>", lambda e: self._hide_sidebar(True))

    def cur_filter(self):
        for label, key in FILTERS:
            if label == self.filter_var.get():
                return key
        return "all"

    def _row_values(self, d):
        """قيم الصف بنفس ترتيب الأعمدة المعروضة (من اليمين إلى اليسار).

        شارات ملونة للنتيجة والباقي: أخضر للناجح، أحمر للراسب والمدين."""
        tp = DB.total_paid(d)
        rem = DB.remaining(d)
        r1, r2 = norm(d.get("exam1_result")), norm(d.get("exam2_result"))
        if "ناجح" in (r1, r2):
            results = "✓ ناجح"
        elif "راسب" in (r1, r2):
            results = "✗ راسب"
        else:
            results = "… قيد الدراسة"
        rem_txt = "سُدّد ✓" if rem <= 0.01 else "● %s مدين" % fmt_money(rem)
        m = {
            "full_name": d.get("full_name", ""),
            "phone": d.get("phone", ""),
            "cin": d.get("cin", ""),
            "reg_number": d.get("reg_number", ""),
            "reg_date": d.get("reg_date", ""),
            "category": d.get("category", ""),
            "vehicle_number": d.get("vehicle_number", ""),
            "birth_date": d.get("birth_date", ""),
            "exam1_date": d.get("exam1_date", ""),
            "exam1_result": d.get("exam1_result", ""),
            "exam2_date": d.get("exam2_date", ""),
            "exam2_result": d.get("exam2_result", ""),
            "total_price": fmt_money(d.get("total_price", 0)),
            "paid1": fmt_money(d.get("paid1", 0)),
            "paid2": fmt_money(d.get("paid2", 0)),
            "paid3": fmt_money(d.get("paid3", 0)),
            "paid_extra": fmt_money(d.get("paid_extra", 0)),
            "total_paid": fmt_money(tp),
            "remaining": rem_txt,
            "exam_results": results,
            "notes": d.get("notes", ""),
        }
        return tuple(m[f[0]] for f in self._disp_fields)

    def _render_rows(self, rows):
        self._on_tree_hover_clear()
        self._row_bg_tag = {}
        self.tree.delete(*self.tree.get_children())
        for i, d in enumerate(rows):
            rem = DB.remaining(d)
            r1, r2 = norm(d.get("exam1_result")), norm(d.get("exam2_result"))
            # وسم خلفية واحد فقط لكل صف (تكديس خلفيتين يجعل الأقدم يفوز)
            if "ناجح" in (r1, r2):
                bg = "pass_alt" if i % 2 else "pass"
            elif "راسب" in (r1, r2):
                bg = "fail_alt" if i % 2 else "fail"
            else:
                bg = "even" if i % 2 == 0 else "odd"
            tags = [bg]
            if rem > 0.01:
                tags.append("debt")  # خط ونص فقط — لا يتعارض مع الخلفية
            values = self._row_values(d)
            self.tree.insert("", "end", iid=str(d["id"]),
                             tags=tuple(tags),
                             values=values)
            self._row_bg_tag[str(d["id"])] = tags[0]
        try:
            if rows:
                self._empty_hint.place_forget()
            else:
                self._empty_hint.place(relx=0.5, rely=0.45, anchor="center")
                self._empty_hint.lift(self.tree)
        except Exception:
            pass

    def refresh(self):
        all_rows = self.db.all()
        paid = sum(DB.total_paid(d) for d in all_rows)
        rem_total = sum(max(DB.remaining(d), 0) for d in all_rows)
        passed = sum(1 for d in all_rows
                     if "ناجح" in (d.get("exam1_result", ""),
                                   d.get("exam2_result", "")))
        self.card_vars["c_total"].set(str(len(all_rows)))
        self.card_vars["c_paid"].set(fmt_money(paid))
        self.card_vars["c_rem"].set(fmt_money(rem_total))
        self.card_vars["c_pass"].set(str(passed))

        rows = self.db.search(self.search_var.get(), self.cur_filter())
        rows = self._sort_rows(rows)
        self._current_rows = rows
        self._render_paginated()
        self.status.set("المعروض: %d   |   الإجمالي: %d   |   "
                        "مجموع الباقي: %s درهم"
                        % (len(rows), len(all_rows), fmt_money(rem_total)))
        self._update_nav_state()
        try:
            self._set_badge("trash", self.db.trash_count())
        except Exception:
            pass
        try:
            days = int(SETTINGS.get("exam_alert_days", 7))
            self._set_badge("exams",
                            len(self.db.upcoming_exams(days, all_rows)))
        except Exception:
            pass

    def selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "اختر مترشحاً من القائمة أولاً.")
            return None
        return int(sel[0])

    def on_add(self):
        CandidateDialog(self, self.db, None, self.refresh)

    def on_edit(self):
        cid = self.selected_id()
        if cid is None:
            return
        CandidateDialog(self, self.db, cid, self.refresh)

    def on_delete(self):
        if not self.can("delete"):
            messagebox.showwarning(APP_TITLE, "لا تملك صلاحية الحذف.")
            return
        cid = self.selected_id()
        if cid is None:
            return
        d = self.db.get(cid)
        if messagebox.askyesno("تأكيد الحذف",
                               "نقل المترشح «%s» إلى سلة المهملات؟\n"
                               "(يمكن استرجاعه لاحقاً من سلة المهملات)"
                               % d.get("full_name", "")):
            self.db.soft_delete_candidate(cid)
            self.refresh()

    def on_pay(self):
        cid = self.selected_id()
        if cid is None:
            return
        PayDialog(self, self.db, cid, self.refresh)

    def on_receipt(self):
        cid = self.selected_id()
        if cid is None:
            return
        d = self.db.get(cid)
        pays = self.db.payments_for(cid)
        ReceiptWindow(self, d, pays)

    def on_import(self):
        if not self.can("import"):
            messagebox.showwarning(APP_TITLE, "لا تملك صلاحية الاستيراد.")
            return
        p = filedialog.askopenfilename(
            title="استيراد بيانات (نسخة الأندرويد)",
            filetypes=[("كل المدعوم", "*.json *.csv *.xlsx"),
                       ("نسخة JSON", "*.json"), ("CSV", "*.csv"),
                       ("Excel", "*.xlsx *.xlsm")])
        if not p:
            return
        try:
            added, updated = import_file(self.db, p)
        except Exception as e:
            messagebox.showerror("استيراد", "فشل الاستيراد:\n%s" % e)
            return
        self.refresh()
        messagebox.showinfo("استيراد",
                            "تم بنجاح:\n• مضاف: %d\n• محدّث: %d"
                            % (added, updated))

    def on_export(self):
        rows = self.db.search(self.search_var.get(), self.cur_filter())
        if not rows:
            messagebox.showinfo(APP_TITLE, "لا توجد بيانات للتصدير.")
            return
        self._show_loading("جاري تصدير الملف...")
        ExportDialog(self, rows, self.exp_dir)
        self._hide_loading()

    # ---- الأزرار الجديدة ----
    def on_reports(self):
        ReportsWindow(self, self.db)

    def on_exams(self):
        ExamsWindow(self, self.db)

    def on_trash(self):
        if not self.can("trash"):
            messagebox.showwarning(APP_TITLE, "لا تملك صلاحية سلة المهملات.")
            return
        TrashWindow(self, self.db, self.refresh)

    def on_settings(self):
        if not self.can("settings"):
            messagebox.showwarning(APP_TITLE, "لا تملك صلاحية الإعدادات.")
            return
        SettingsWindow(self, self.refresh, self)

    def on_users(self):
        if not self.can("users"):
            messagebox.showwarning(APP_TITLE, "لا تملك صلاحية إدارة المستخدمين.")
            return
        UsersWindow(self, self)

    def on_about(self):
        AboutWindow(self)


# ---------------- عناصر النماذج ----------------
class FieldRow:
    def __init__(self, parent, label):
        self.frame = ttk.Frame(parent)
        f = self.frame
        f.pack(fill="x", pady=3)
        ttk.Label(f, text=label, width=17, anchor="e").pack(side="right")
        self.entry = ttk.Entry(f, justify="right")
        self.entry.pack(side="right", fill="x", expand=True, padx=6)

    def get(self):
        return norm(self.entry.get())

    def set(self, v):
        self.entry.delete(0, "end")
        if v not in (None, ""):
            self.entry.insert(0, str(v))

    def focus(self):
        self.entry.focus_set()


class ComboRow:
    def __init__(self, parent, label, values):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=3)
        ttk.Label(f, text=label, width=17, anchor="e").pack(side="right")
        self.var = tk.StringVar()
        self.box = ttk.Combobox(f, textvariable=self.var, values=values,
                                justify="right")
        self.box.pack(side="right", fill="x", expand=True, padx=6)

    def get(self):
        return norm(self.var.get())

    def set(self, v):
        self.var.set(v if v else "")


class CalendarPicker(tk.Toplevel):
    """تقويم بسيط لاختيار التاريخ بالضغط على اليوم."""

    AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "ماي", "يونيو",
                 "يوليوز", "غشت", "شتنبر", "أكتوبر", "نونبر", "دجنبر"]
    AR_DAYS = ["أحد", "إثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت"]

    def __init__(self, parent, entry):
        super().__init__(parent)
        self.entry = entry
        self.title("اختيار التاريخ")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        cur = norm(entry.get())
        try:
            y, m, _d = [int(x) for x in cur.split("-")]
            self.year, self.month = y, m
        except Exception:
            t = date.today()
            self.year, self.month = t.year, t.month

        self._build()
        self._render()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry("+%d+%d" % (max(0, x), max(0, y)))
        except Exception:
            pass

    def _build(self):
        head = tk.Frame(self, bg=NAVY)
        head.pack(fill="x")
        tk.Button(head, text="‹", width=3, command=self._prev_month,
                  bg=NAVY, fg="white", relief="flat", font=(FONT, 13, "bold"),
                  activebackground=GOLD, activeforeground=NAVY,
                  cursor="hand2").pack(side="right", padx=2, pady=4)
        tk.Button(head, text="›", width=3, command=self._next_month,
                  bg=NAVY, fg="white", relief="flat", font=(FONT, 13, "bold"),
                  activebackground=GOLD, activeforeground=NAVY,
                  cursor="hand2").pack(side="right", padx=2, pady=4)
        tk.Button(head, text="»", width=2, command=self._next_year,
                  bg=NAVY, fg=GOLD, relief="flat", font=(FONT, 11, "bold"),
                  activebackground=GOLD, activeforeground=NAVY,
                  cursor="hand2").pack(side="left", padx=(6, 2), pady=4)
        tk.Button(head, text="«", width=2, command=self._prev_year,
                  bg=NAVY, fg=GOLD, relief="flat", font=(FONT, 11, "bold"),
                  activebackground=GOLD, activeforeground=NAVY,
                  cursor="hand2").pack(side="left", pady=4)
        self.lbl_ym = tk.Label(head, text="", bg=NAVY, fg="white",
                               font=(FONT, 12, "bold"))
        self.lbl_ym.pack(side="left", expand=True)

        days = tk.Frame(self, bg=BG)
        days.pack(fill="x", padx=8, pady=(8, 0))
        for name in self.AR_DAYS:
            tk.Label(days, text=name, bg=BG, fg=MUTED, width=5,
                     font=(FONT, 9, "bold")).pack(side="left", expand=True,
                                                  fill="x")

        self.grid_frame = tk.Frame(self, bg=BG)
        self.grid_frame.pack(fill="both", expand=True, padx=8, pady=8)

        foot = tk.Frame(self, bg=BG)
        foot.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(foot, text="اليوم", style="Tool.TButton",
                   command=self._pick_today).pack(side="right")

    def _render(self):
        self.lbl_ym.config(text="%s %d" % (self.AR_MONTHS[self.month - 1],
                                           self.year))
        for w in self.grid_frame.winfo_children():
            w.destroy()
        weeks = _calendar.monthcalendar(self.year, self.month)
        for week in weeks:
            row = tk.Frame(self.grid_frame, bg=BG)
            row.pack(fill="x", pady=1)
            for day in week:
                cell = tk.Frame(row, bg=BG)
                cell.pack(side="left", expand=True, fill="both")
                if day == 0:
                    continue
                b = tk.Button(cell, text=str(day), width=4, relief="flat",
                              bg=CARD, fg=TEXT, font=(FONT, 10),
                              activebackground=GOLD, activeforeground=NAVY,
                              cursor="hand2",
                              command=lambda d=day: self._pick(d))
                b.pack(fill="both", expand=True, padx=1, pady=1)

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month, self.year = 12, self.year - 1
        self._render()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month, self.year = 1, self.year + 1
        self._render()

    def _prev_year(self):
        self.year -= 1
        self._render()

    def _next_year(self):
        self.year += 1
        self._render()

    def _pick(self, day):
        self.entry.delete(0, "end")
        self.entry.insert(0, "%04d-%02d-%02d" % (self.year, self.month, day))
        self.destroy()

    def _pick_today(self):
        t = date.today()
        self.year, self.month = t.year, t.month
        self._pick(t.day)


class DateField(FieldRow):
    """حقل تاريخ يفتح تقويماً عند الضغط على الخانة أو زر التقويم."""

    def __init__(self, parent, label):
        super().__init__(parent, label)
        btn = ttk.Button(self.frame, text="📅", width=3, command=self.pick)
        btn.pack(side="left", padx=(4, 0))
        self.entry.bind("<Button-1>", lambda e: self.after(1, self.pick),
                        add="+")

    def pick(self):
        CalendarPicker(self.frame.winfo_toplevel(), self.entry)


def section(parent, title):
    lf = ttk.Labelframe(parent, text="  " + title + "  ", padding=10)
    lf.pack(fill="x", pady=(0, 8))
    return lf


def dialog_header(win, title, subtitle=None):
    head = tk.Frame(win, bg=NAVY)
    head.pack(fill="x")
    inner = tk.Frame(head, bg=NAVY)
    inner.pack(fill="x", padx=16, pady=10)
    tk.Label(inner, text=title, bg=NAVY, fg="white",
             font=(FONT, 13, "bold")).pack(side="right")
    if subtitle:
        tk.Label(inner, text=subtitle, bg=NAVY, fg=GOLD,
                 font=F_SUB).pack(side="left")
    tk.Frame(win, bg=GOLD, height=3).pack(fill="x")


def dialog_buttons(win, ok_text, ok_cmd):
    btns = tk.Frame(win, bg=BG)
    btns.pack(fill="x", padx=16, pady=12, side="bottom")
    ttk.Button(btns, text=ok_text, style="Primary.TButton",
               command=ok_cmd).pack(side="right")
    ttk.Button(btns, text="إلغاء", style="Tool.TButton",
               command=win.destroy).pack(side="right", padx=(0, 8))


def bind_mousewheel(widget, handler):
    """يربط عجلة الفأرة بالwidget وأبناءه (لنوافذ التمرير)."""
    try:
        widget.bind("<MouseWheel>", handler, add="+")
    except Exception:
        pass
    for child in widget.winfo_children():
        bind_mousewheel(child, handler)


class ScrollFrame(ttk.Frame):
    """إطار قابل للتمرير عمودياً حتى لا يُقصّ أي جزء من المحتوى."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="left", fill="y")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self._win = self.canvas.create_window((0, 0), window=self.body,
                                              anchor="nw")
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(
                           scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(
                             self._win, width=e.width))

    def on_wheel(self, e):
        step = e.delta // 120 if e.delta else 0
        if step:
            self.canvas.yview_scroll(-step, "units")


class CandidateDialog(tk.Toplevel):
    def __init__(self, parent, db, cid, on_save):
        super().__init__(parent)
        self.db = db
        self.cid = cid
        self.on_save = on_save
        self.configure(bg=BG)
        self.title("تعديل مترشح" if cid else "إضافة مترشح جديد")
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            w = min(780, int(sw * 0.85))
            h = min(800, int(sh * 0.88))
            self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2,
                                           (sh - h) // 2))
        except Exception:
            self.geometry("760x780")
        self.minsize(620, 460)
        dialog_header(self, "بطاقة المترشح",
                      "تعديل البيانات" if cid else "مترشح جديد")

        self.sf = ScrollFrame(self)
        self.sf.pack(fill="both", expand=True)
        bind_mousewheel(self.sf.canvas, self.sf.on_wheel)
        body = ttk.Frame(self.sf.body, padding=(16, 12))
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1, uniform="col")
        body.grid_columnconfigure(1, weight=1, uniform="col")

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="new", padx=(0, 8))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="new", padx=(8, 0))

        s1 = section(left, "البيانات الشخصية")
        self.f_name = FieldRow(s1, "الاسم الكامل *")
        self.f_birth = DateField(s1, "تاريخ الازدياد")
        self.f_phone = FieldRow(s1, "الهاتف")
        self.f_cin = FieldRow(s1, "رقم البطاقة الوطنية")

        # صورة المترشح
        self.photo_path = tk.StringVar(value="")
        pf = ttk.Frame(s1)
        pf.pack(fill="x", pady=(6, 0))
        self.photo_lbl = tk.Label(pf, text="لا توجد صورة", width=14, height=6,
                                  bg=CARD, fg=MUTED, relief="solid",
                                  bd=1, compound="center")
        self.photo_lbl.pack(side="right", padx=(0, 8))
        pbtns = tk.Frame(pf)
        pbtns.pack(side="right", fill="both", expand=True)
        ttk.Button(pbtns, text="رفع صورة", style="Tool.TButton",
                   command=self.pick_photo).pack(anchor="e", pady=2)
        ttk.Button(pbtns, text="حذف الصورة", style="Tool.TButton",
                   command=self.clear_photo).pack(anchor="e", pady=2)
        self._photo_img = None

        s2 = section(left, "التسجيل والرخصة")
        self.f_reg = FieldRow(s2, "رقم التسجيل")
        self.f_regdate = DateField(s2, "تاريخ التسجيل")
        self.f_cat = ComboRow(s2, "صنف الرخصة", CATEGORIES)
        self.f_cat.set("B")
        self.f_veh = FieldRow(s2, "رقم العربة")

        s3 = section(right, "الامتحانات")
        self.f_ex1d = DateField(s3, "تاريخ الامتحان 1")
        self.f_ex1r = ComboRow(s3, "نتيجة الامتحان 1", RESULTS)
        self.f_ex2d = DateField(s3, "تاريخ الامتحان 2")
        self.f_ex2r = ComboRow(s3, "نتيجة الامتحان 2", RESULTS)

        s4 = section(right, "الوضعية المالية")
        self.f_price = FieldRow(s4, "الثمن الإجمالي")
        self.f_p1 = FieldRow(s4, "الدفعة الأولى")
        self.f_p2 = FieldRow(s4, "الدفعة الثانية")
        self.f_p3 = FieldRow(s4, "الدفعة الثالثة")
        self.f_px = FieldRow(s4, "دفعات إضافية")

        # حساب تلقائي للمجموع المؤدى والباقي أثناء الكتابة
        calc = tk.Frame(s4, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        calc.pack(fill="x", pady=(8, 2))
        tk.Frame(calc, bg=NAVY, width=5).pack(side="right", fill="y")
        cb = tk.Frame(calc, bg=CARD)
        cb.pack(side="right", fill="both", expand=True, padx=10, pady=7)

        r1 = tk.Frame(cb, bg=CARD)
        r1.pack(fill="x")
        tk.Label(r1, text="المجموع المؤدى:", bg=CARD, fg=MUTED,
                 font=F_CARD_T, anchor="e").pack(side="right")
        self.l_paid = tk.Label(r1, text="0", bg=CARD, fg=NAVY,
                               font=F_BODY_B, anchor="e")
        self.l_paid.pack(side="right", fill="x", expand=True, padx=(8, 0))

        r2 = tk.Frame(cb, bg=CARD)
        r2.pack(fill="x", pady=(3, 0))
        tk.Label(r2, text="الباقي:", bg=CARD, fg=MUTED,
                 font=F_CARD_T, anchor="e").pack(side="right")
        self.l_rem = tk.Label(r2, text="0", bg=CARD, fg=DANGER,
                              font=F_BODY_B, anchor="e")
        self.l_rem.pack(side="right", fill="x", expand=True, padx=(8, 0))

        for fr in (self.f_price, self.f_p1, self.f_p2, self.f_p3,
                   self.f_px):
            fr.entry.bind("<KeyRelease>",
                          lambda e: self.update_fin(), add="+")
            fr.entry.bind("<<Paste>>",
                          lambda e: self.after(1, self.update_fin),
                          add="+")

        s5 = section(right, "ملاحظات")
        self.f_notes = FieldRow(s5, "ملاحظات")

        if cid:
            d = db.get(cid)
            if d:
                self.f_name.set(d.get("full_name"))
                self.f_phone.set(d.get("phone"))
                self.f_cin.set(d.get("cin"))
                self.f_reg.set(d.get("reg_number"))
                self.f_regdate.set(d.get("reg_date"))
                self.f_cat.set(d.get("category") or "B")
                self.f_veh.set(d.get("vehicle_number"))
                self.f_birth.set(d.get("birth_date"))
                self.f_ex1d.set(d.get("exam1_date"))
                self.f_ex1r.set(d.get("exam1_result"))
                self.f_ex2d.set(d.get("exam2_date"))
                self.f_ex2r.set(d.get("exam2_result"))
                self.f_price.set(d.get("total_price") or "")
                self.f_p1.set(d.get("paid1") or "")
                self.f_p2.set(d.get("paid2") or "")
                self.f_p3.set(d.get("paid3") or "")
                self.f_px.set(d.get("paid_extra") or "")
                self.f_notes.set(d.get("notes"))
                self.photo_path.set(d.get("photo_path") or "")
                self._show_photo()
        else:
            self.f_regdate.set(today_str())

        dialog_buttons(self, "حفظ", self.save)
        self.grab_set()
        self.transient(parent)
        self.f_name.focus()
        self.update_fin()

    def update_fin(self):
        tp = parse_num(self.f_price.get())
        p1 = parse_num(self.f_p1.get())
        p2 = parse_num(self.f_p2.get())
        p3 = parse_num(self.f_p3.get())
        px = parse_num(self.f_px.get())
        paid = p1 + p2 + p3 + px
        rem = tp - paid
        self.l_paid.configure(text=fmt_money(paid))
        self.l_rem.configure(text=fmt_money(rem),
                             fg=OK if rem <= 0.01 else DANGER)

    # ---- صورة المترشح ----
    def pick_photo(self):
        p = filedialog.askopenfilename(
            title="اختر صورة المترشح",
            filetypes=[("صور", "*.png *.jpg *.jpeg *.bmp *.gif"),
                       ("الكل", "*.*")])
        if not p:
            return
        self.photo_path.set(p)
        self._show_photo()

    def clear_photo(self):
        self.photo_path.set("")
        self._show_photo()

    def _show_photo(self):
        from PIL import Image, ImageTk
        p = self.photo_path.get()
        if p and os.path.exists(p):
            try:
                img = Image.open(p)
                img.thumbnail((110, 130))
                self._photo_img = ImageTk.PhotoImage(img)
                self.photo_lbl.configure(image=self._photo_img, text="",
                                         width=110, height=130)
                return
            except Exception:
                pass
        self.photo_lbl.configure(image="", text="لا توجد صورة",
                                 width=14, height=6)

    def save(self):
        name = self.f_name.get()
        if not name:
            messagebox.showwarning("تنبيه", "الاسم الكامل مطلوب.")
            self.f_name.focus()
            return
        d = {
            "full_name": name, "phone": self.f_phone.get(),
            "cin": self.f_cin.get(), "reg_number": self.f_reg.get(),
            "reg_date": self.f_regdate.get(),
            "category": self.f_cat.get() or "B",
            "vehicle_number": self.f_veh.get(),
            "birth_date": self.f_birth.get(),
            "exam1_date": self.f_ex1d.get(),
            "exam1_result": self.f_ex1r.get(),
            "exam2_date": self.f_ex2d.get(),
            "exam2_result": self.f_ex2r.get(),
            "total_price": parse_num(self.f_price.get()),
            "paid1": parse_num(self.f_p1.get()),
            "paid2": parse_num(self.f_p2.get()),
            "paid3": parse_num(self.f_p3.get()),
            "paid_extra": parse_num(self.f_px.get()),
            "notes": self.f_notes.get(),
            "photo_path": self.photo_path.get(),
        }
        if self.cid:
            old = self.db.get(self.cid)
            if old and not d["photo_path"]:
                d["photo_path"] = old.get("photo_path", "")
            self.db.update_candidate(self.cid, d)
            audit("تعديل مترشح", name)
        else:
            nid = self.db.add_candidate(d)
            audit("إضافة مترشح", "%s (id=%s)" % (name, nid))
        self.on_save()
        self.destroy()


class PayDialog(tk.Toplevel):
    def __init__(self, parent, db, cid, on_save):
        super().__init__(parent)
        self.db = db
        self.cid = cid
        self.on_save = on_save
        d = db.get(cid)
        self.configure(bg=BG)
        self.title("تسجيل دفعة")
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            w = min(480, int(sw * 0.5))
            h = min(640, int(sh * 0.85))
            self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2,
                                           (sh - h) // 2))
        except Exception:
            self.geometry("480x640")
        self.minsize(420, 460)
        dialog_header(self, "تسجيل دفعة", d.get("full_name", ""))

        self.sf = ScrollFrame(self)
        self.sf.pack(fill="both", expand=True)
        bind_mousewheel(self.sf.canvas, self.sf.on_wheel)
        body = ttk.Frame(self.sf.body, padding=(16, 12))
        body.pack(fill="both", expand=True)

        info = tk.Frame(body, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        info.pack(fill="x", pady=(0, 10))
        tk.Frame(info, bg=GOLD, width=5).pack(side="right", fill="y")
        ib = tk.Frame(info, bg=CARD)
        ib.pack(side="right", fill="both", expand=True, padx=12, pady=10)
        tk.Label(ib, text="الحالة المالية", bg=CARD, fg=MUTED,
                 font=F_CARD_T, anchor="e").pack(anchor="e")
        tk.Label(ib, text="المدفوع: %s درهم    |    الباقي: %s درهم"
                 % (fmt_money(DB.total_paid(d)), fmt_money(DB.remaining(d))),
                 bg=CARD, fg=NAVY, font=F_BODY_B,
                 anchor="e").pack(anchor="e")

        self.f_amt = FieldRow(body, "المبلغ *")
        self.f_date = DateField(body, "التاريخ")
        self.f_date.set(today_str())
        self.f_note = FieldRow(body, "ملاحظة")

        # حساب تلقائي: الباقي بعد هذه الدفعة
        calc = tk.Frame(body, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        calc.pack(fill="x", pady=(10, 0))
        tk.Frame(calc, bg=NAVY, width=5).pack(side="right", fill="y")
        cb = tk.Frame(calc, bg=CARD)
        cb.pack(side="right", fill="both", expand=True, padx=12, pady=8)
        tk.Label(cb, text="بعد هذه الدفعة، سيكون الباقي:",
                 bg=CARD, fg=MUTED, font=F_CARD_T, anchor="e").pack(anchor="e")
        self.l_after = tk.Label(cb, text="0", bg=CARD, fg=NAVY,
                                font=(FONT, 13, "bold"), anchor="e")
        self.l_after.pack(anchor="e")

        self.f_amt.entry.bind("<KeyRelease>",
                              lambda e: self.update_after(), add="+")
        self.f_amt.entry.bind("<<Paste>>",
                              lambda e: self.after(1, self.update_after),
                              add="+")

        # سجل الدفعات السابقة
        hist_frame = ttk.LabelFrame(body, text="  الدفعات السابقة  ",
                                    padding=8)
        hist_frame.pack(fill="x", pady=(12, 0))
        cols = ("date", "amount", "slot")
        self.hist = ttk.Treeview(hist_frame, columns=cols, show="headings",
                                 height=4)
        self.hist.heading("date", text="التاريخ")
        self.hist.heading("amount", text="المبلغ")
        self.hist.heading("slot", text="الخانة")
        self.hist.column("date", width=110, anchor="center")
        self.hist.column("amount", width=90, anchor="center")
        self.hist.column("slot", width=90, anchor="center")
        hsb = ttk.Scrollbar(hist_frame, orient="vertical",
                            command=self.hist.yview)
        self.hist.configure(yscrollcommand=hsb.set)
        self.hist.pack(side="left", fill="both", expand=True)
        hsb.pack(side="right", fill="y")
        self.load_history()

        dialog_buttons(self, "حفظ الدفعة", self.save)
        self.grab_set()
        self.transient(parent)
        self.f_amt.focus()
        self.update_after()

    SLOT_LABELS = {"paid1": "الدفعة 1", "paid2": "الدفعة 2",
                   "paid3": "الدفعة 3", "paid_extra": "إضافية"}

    def load_history(self):
        for i in self.hist.get_children():
            self.hist.delete(i)
        pays = self.db.payments_for(self.cid)
        for p in pays:
            self.hist.insert("", "end", values=(
                p.get("date", ""),
                fmt_money(p.get("amount") or 0),
                self.SLOT_LABELS.get(p.get("slot"), p.get("slot", ""))))

    def update_after(self):
        amt = parse_num(self.f_amt.get())
        rem_now = DB.remaining(self.db.get(self.cid))
        rem_after = rem_now - amt
        self.l_after.configure(text="%s درهم" % fmt_money(rem_after),
                               fg=OK if rem_after <= 0.01 else DANGER)

    def save(self):
        amt = parse_num(self.f_amt.get())
        if amt <= 0:
            messagebox.showwarning("تنبيه", "أدخل مبلغاً صحيحاً.")
            self.f_amt.focus()
            return
        slot = self.db.add_payment(self.cid, amt, self.f_date.get() or
                                   today_str(), self.f_note.get())
        audit("تسجيل دفعة",
              "%s: %s %s في %s" % (self.db.get(self.cid).get("full_name", ""),
                                   fmt_money(amt), currency(),
                                   self.SLOT_LABELS.get(slot, slot or "")))
        self.on_save()
        messagebox.showinfo(
            "تم الحفظ",
            "تم تسجيل دفعة بمبلغ %s درهم بنجاح في %s."
            % (fmt_money(amt), self.SLOT_LABELS.get(slot, slot or "")))
        self.destroy()


class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, d, pays):
        super().__init__(parent)
        self.configure(bg=BG)
        self.title("كشف حساب")
        self.geometry("560x640")
        dialog_header(self, "كشف حساب", d.get("full_name", ""))

        wrap = tk.Frame(self, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=16, pady=12)
        txt = tk.Text(wrap, wrap="word", font=(FONT, 11), bg=CARD, fg=TEXT,
                      relief="flat", padx=12, pady=12, spacing1=2,
                      spacing3=2)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", receipt_text(d, pays))
        txt.configure(state="disabled")

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(btns, text="🖨️ طباعة / PDF", style="Accent.TButton",
                   command=lambda: print_receipt_html(d, pays)).pack(
            side="right")
        ttk.Button(btns, text="نسخ", style="Primary.TButton",
                   command=lambda: self.copy(txt)).pack(side="right",
                                                        padx=(0, 8))
        ttk.Button(btns, text="حفظ في ملف", style="Tool.TButton",
                   command=lambda: self.savefile(txt)).pack(side="right",
                                                           padx=(0, 8))

    def copy(self, txt):
        self.clipboard_clear()
        self.clipboard_append(txt.get("1.0", "end-1c"))
        messagebox.showinfo(APP_TITLE, "تم نسخ الكشف.")

    def savefile(self, txt):
        p = filedialog.asksaveasfilename(
            title="حفظ الكشف", defaultextension=".txt",
            filetypes=[("نص", "*.txt")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt.get("1.0", "end-1c"))
            messagebox.showinfo(APP_TITLE, "تم الحفظ.")


class ExportDialog(tk.Toplevel):
    def __init__(self, parent, rows, exp_dir):
        super().__init__(parent)
        self.rows = rows
        self.exp_dir = exp_dir
        self.configure(bg=BG)
        self.title("تصدير")
        self.geometry("400x330")
        self.resizable(False, False)
        dialog_header(self, "تصدير البيانات", "%d مترشح" % len(rows))
        body = ttk.Frame(self, padding=(16, 14))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="اختر صيغة الملف:",
                  anchor="e").pack(fill="x", pady=(0, 8))
        ttk.Button(body, text="ملف Excel  (.xlsx)",
                   style="Accent.TButton",
                   command=lambda: self.do("xlsx")).pack(fill="x", pady=4)
        ttk.Button(body, text="ملف CSV  (يُفتح في Excel)",
                   style="Tool.TButton",
                   command=lambda: self.do("csv")).pack(fill="x", pady=4)
        ttk.Button(body, text="نسخة احتياطية  (.json)",
                   style="Tool.TButton",
                   command=lambda: self.do("json")).pack(fill="x", pady=4)

    def do(self, kind):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            if kind == "csv":
                p = os.path.join(self.exp_dir,
                                 "candidates_%s.csv" % stamp)
                export_csv(self.rows, p)
            elif kind == "xlsx":
                p = os.path.join(self.exp_dir,
                                 "candidates_%s.xlsx" % stamp)
                export_xlsx(self.rows, p)
            else:
                p = os.path.join(self.exp_dir,
                                 "backup_driving_school_%s.json" % stamp)
                export_json(self.rows, p)
        except Exception as e:
            messagebox.showerror("تصدير", "فشل التصدير:\n%s" % e)
            return
        try:
            if messagebox.askyesno("تصدير", "تم الحفظ في:\n%s\n\nفتح المجلد؟"
                                   % p):
                os.startfile(self.exp_dir)
        except Exception:
            messagebox.showinfo("تصدير", "تم الحفظ في:\n%s" % p)
        self.destroy()


# ================= النوافذ الجديدة =================
class ReportsWindow(tk.Toplevel):
    """صفحة التقارير والإحصائيات مع رسوم بيانية بسيطة."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.configure(bg=BG)
        self.title("التقارير والإحصائيات")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(860, int(sw * 0.8)), min(640, int(sh * 0.85))
        self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        self.minsize(700, 520)
        dialog_header(self, "التقارير والإحصائيات", school())

        self.sf = ScrollFrame(self)
        self.sf.pack(fill="both", expand=True)
        bind_mousewheel(self.sf.canvas, self.sf.on_wheel)
        body = ttk.Frame(self.sf.body, padding=(18, 14))
        body.pack(fill="both", expand=True)

        # 1) الدخل الشهري
        self._section(body, "الدخل الشهري (آخر 12 شهراً)")
        income = db.monthly_income(12)
        if income:
            mx = max(v for _, v in income) or 1
            for ym, v in income:
                row = ttk.Frame(body)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=ym, width=10).pack(side="right")
                barw = int(360 * (v / mx))
                tk.Frame(row, bg=NAVY, width=max(barw, 2), height=16).pack(
                    side="right", padx=6)
                ttk.Label(row, text="%s %s" % (fmt_money(v), currency())
                          ).pack(side="right")
        else:
            ttk.Label(body, text="لا توجد دفعات مسجّلة بعد.",
                      foreground=MUTED).pack(anchor="e")

        # 2) المترشحون حسب الصنف
        self._section(body, "المترشحون حسب صنف الرخصة")
        cats = db.category_counts()
        if cats:
            cmax = max(n for _, n in cats) or 1
            for cat, n in cats:
                row = ttk.Frame(body)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=cat, width=8).pack(side="right")
                tk.Frame(row, bg=GOLD, width=int(300 * (n / cmax)),
                         height=16).pack(side="right", padx=6)
                ttk.Label(row, text=str(n)).pack(side="right")
        else:
            ttk.Label(body, text="لا يوجد مترشحون.",
                      foreground=MUTED).pack(anchor="e")

        # 3) توزيع النتائج
        self._section(body, "توزيع النتائج")
        res = db.results_distribution()
        total = sum(n for _, n in res) or 1
        colors = {"ناجح": OK, "راسب": DANGER, "قيد الدراسة": MUTED}
        bar = tk.Frame(body, bg=CARD, height=28)
        bar.pack(fill="x", pady=4)
        for label, n in res:
            if n <= 0:
                continue
            wpx = max(int(700 * (n / total)), 8)
            tk.Frame(bar, bg=colors.get(label, MUTED), width=wpx,
                     height=28).pack(side="right", padx=1)
        leg = ttk.Frame(body)
        leg.pack(fill="x")
        for label, n in res:
            tk.Frame(leg, bg=colors.get(label, MUTED), width=12,
                     height=12).pack(side="right", padx=(12, 3))
            ttk.Label(leg, text="%s: %d" % (label, n)).pack(side="right")

        # 4) متأخرو الدفع
        self._section(body, "متأخرو الدفع (%d)" % len(db.debtors()))
        debtors = db.debtors()
        if debtors:
            tbl = ttk.Treeview(body, columns=("name", "rem"),
                               show="headings", height=min(len(debtors), 8))
            tbl.heading("name", text="المترشح")
            tbl.heading("rem", text="المتبقي")
            tbl.column("name", width=320, anchor="e")
            tbl.column("rem", width=140, anchor="center")
            for d in sorted(debtors,
                            key=lambda x: -DB.remaining(x))[:20]:
                tbl.insert("", "end", values=(
                    d.get("full_name", ""),
                    "%s %s" % (fmt_money(DB.remaining(d)), currency())))
            tbl.pack(fill="x")
        else:
            ttk.Label(body, text="لا يوجد متأخرون — جميع الحسابات مسدّدة.",
                      foreground=OK).pack(anchor="e")

    def _section(self, parent, title):
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(14, 6))
        ttk.Label(parent, text=title, font=F_HEAD, foreground=NAVY
                  ).pack(anchor="e")


AR_MONTHS = ("يناير", "فبراير", "مارس", "أبريل", "ماي", "يونيو",
             "يوليوز", "غشت", "شتنبر", "أكتوبر", "نونبر", "دجنبر")
# السبت أولاً (بداية الأسبوع المعتادة)
AR_WEEKDAYS = ("السبت", "الأحد", "الاثنين", "الثلاثاء",
               "الأربعاء", "الخميس", "الجمعة")


class ExamsWindow(tk.Toplevel):
    """تقويم شهري (جدول) للامتحانات مع تفاصيل كل يوم."""

    CELL_H = 76
    ST_COLORS = {"ok": OK, "fail": DANGER, "late": "#C0392B",
                 "today": GOLD_DARK, "soon": NAVY}

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.configure(bg=BG)
        self.title("تقويم الامتحانات")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(960, int(sw * 0.82)), min(700, int(sh * 0.86))
        self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        self.minsize(840, 600)
        today = date.today()
        self.year, self.month = today.year, today.month
        self.selected = None
        self._exams = []
        self._by_day = {}

        dialog_header(self, "تقويم الامتحانات", "جدول الامتحانات الشهري")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=(10, 14))
        tab_cal = ttk.Frame(nb, padding=10)
        tab_debt = ttk.Frame(nb, padding=14)
        nb.add(tab_cal, text="  التقويم  ")
        nb.add(tab_debt, text="  متأخرو الدفع  ")

        # ---- شريط التنقّل بين الشهور + دليل الألوان ----
        bar = tk.Frame(tab_cal, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        self.month_lbl = tk.Label(bar, text="", bg=BG, fg=NAVY,
                                  font=(FONT, 14, "bold"))
        self.month_lbl.pack(side="right")

        def nav_btn(text, cmd):
            b = tk.Button(bar, text=text, command=cmd, bg=CARD, fg=NAVY,
                          activebackground=NAVY_HOVER, activeforeground="white",
                          relief="flat", bd=0, highlightthickness=1,
                          highlightbackground=BORDER, font=(FONT, 11, "bold"),
                          width=3, cursor="hand2")
            b.pack(side="right", padx=(6, 0))
            return b

        nav_btn("‹", self.next_month)   # الأحدث نحو اليسار (RTL)
        nav_btn("›", self.prev_month)   # الأقدم نحو اليمين
        tk.Button(bar, text="هذا الشهر", command=self._this_month,
                  bg=GOLD, fg="#2E2409", activebackground=GOLD_DARK,
                  activeforeground="white", relief="flat", bd=0,
                  font=(FONT, 9, "bold"), padx=10, cursor="hand2").pack(
            side="right", padx=(0, 4))

        leg = tk.Frame(bar, bg=BG)
        leg.pack(side="left")
        for color, text in ((NAVY, "قادم"), (GOLD_DARK, "اليوم"),
                            (DANGER, "متأخر"), (OK, "ناجح"),
                            ("#7A2E2E", "راسب")):
            tk.Label(leg, text="●", bg=BG, fg=color,
                     font=(FONT, 9)).pack(side="right")
            tk.Label(leg, text=text, bg=BG, fg=MUTED, font=F_SMALL).pack(
                side="right", padx=(0, 10))

        # ---- جدول التقويم ----
        cal_card = tk.Frame(tab_cal, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1)
        cal_card.pack(fill="both", expand=True)
        head = tk.Frame(cal_card, bg=NAVY)
        head.pack(fill="x")
        for i in range(7):
            head.grid_columnconfigure(6 - i, weight=1)
            tk.Label(head, text=AR_WEEKDAYS[i], bg=NAVY, fg=GOLD,
                     font=(FONT, 9, "bold"), pady=5).grid(
                row=0, column=6 - i, sticky="nsew")
        self.cal_grid = tk.Frame(cal_card, bg=BORDER)
        self.cal_grid.pack(fill="both", expand=True, padx=1, pady=(1, 1))
        for c in range(7):
            self.cal_grid.grid_columnconfigure(c, weight=1, minsize=70)
        for r in range(1, 7):
            self.cal_grid.grid_rowconfigure(r, weight=1, minsize=self.CELL_H)
        # ---- تفاصيل اليوم/الشهر المختار ----
        det = tk.Frame(tab_cal, bg=BG)
        det.pack(fill="both", expand=True, pady=(10, 0))

        top = tk.Frame(det, bg=BG)
        top.pack(fill="x")
        self.det_title = tk.Label(top, text="", bg=BG, fg=NAVY, font=F_HEAD)
        self.det_title.pack(side="right")
        tk.Label(top,
                 text="انقر يوماً في التقويم • انقر مزدوجاً على المترشح لفتح بطاقته",
                 bg=BG, fg=MUTED, font=F_SMALL).pack(side="left")

        tbl_box = tk.Frame(det, bg=BG)
        tbl_box.pack(fill="both", expand=True, pady=(6, 0))
        self.det_tbl = ttk.Treeview(
            tbl_box, columns=("name", "label", "status", "phone"),
            show="headings", height=8)
        for c, t, wdt, anc in (("name", "المترشح", 250, "e"),
                               ("label", "النوع", 100, "center"),
                               ("status", "الحالة", 140, "center"),
                               ("phone", "الهاتف", 130, "center")):
            self.det_tbl.heading(c, text=t)
            self.det_tbl.column(c, width=wdt, anchor=anc)
        for kind, color in self.ST_COLORS.items():
            self.det_tbl.tag_configure(kind, foreground=color)
        vsb = ttk.Scrollbar(tbl_box, orient="vertical",
                            command=self.det_tbl.yview)
        self.det_tbl.configure(yscrollcommand=vsb.set)
        self.det_tbl.pack(side="right", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        self.det_tbl.bind("<Double-1>", self._open_candidate)
        self.det_tbl.bind("<ButtonRelease-1>", self._open_candidate)

        # ---- تبويب متأخرو الدفع ----
        self.debt_sum = tk.Label(tab_debt, text="", bg=BG, fg=DANGER,
                                 font=F_HEAD, anchor="e")
        self.debt_sum.pack(fill="x", pady=(0, 8))
        self.debt_tbl = ttk.Treeview(
            tab_debt, columns=("name", "phone", "rem"), show="headings",
            height=14)
        for c, t, wdt, anc in (("name", "المترشح", 300, "e"),
                               ("phone", "الهاتف", 160, "center"),
                               ("rem", "المتبقي", 140, "center")):
            self.debt_tbl.heading(c, text=t)
            self.debt_tbl.column(c, width=wdt, anchor=anc)
        self.debt_tbl.tag_configure("rem", foreground=DANGER)
        self.debt_tbl.pack(fill="both", expand=True)

        self.reload()

    # ---------- البيانات ----------
    def reload(self):
        """إعادة جلب الامتحانات ورسم التقويم والتبويبات."""
        self._exams = self.db.all_exams()
        self._by_day = {}
        for e in self._exams:
            self._by_day.setdefault(e["date"], []).append(e)
        self._render_month()
        self._render_debts()

    def _render_debts(self):
        debtors = self.db.debtors()
        total = sum(DB.remaining(d) for d in debtors)
        self.debt_sum.config(text="العدد: %d  •  المجموع: %s %s"
                             % (len(debtors), fmt_money(total), currency()))
        self.debt_tbl.delete(*self.debt_tbl.get_children())
        for d in sorted(debtors, key=lambda x: -DB.remaining(x)):
            self.debt_tbl.insert("", "end", tags=("rem",), values=(
                d.get("full_name", ""), d.get("phone", ""),
                fmt_money(DB.remaining(d))))

    # ---------- التنقّل ----------
    def prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self.selected = None
        self._render_month()

    def next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self.selected = None
        self._render_month()

    def _this_month(self):
        t = date.today()
        self.month, self.year = t.month, t.year
        self.selected = None
        self._render_month()
    # ---------- رسم التقويم ----------
    def _render_month(self):
        self.month_lbl.config(text="%s %d" % (AR_MONTHS[self.month - 1],
                                              self.year))
        for w in self.cal_grid.winfo_children():
            w.destroy()
        weeks = _calendar.Calendar(firstweekday=5).monthdayscalendar(
            self.year, self.month)   # 5 = السبت
        today = date.today()
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                col = 6 - c   # السبت في أقصى اليمين (RTL)
                if day == 0:
                    cell = tk.Frame(self.cal_grid, bg="#E4E9EF",
                                    highlightthickness=1,
                                    highlightbackground=BORDER)
                else:
                    cell = self._day_cell(day, today)
                cell.grid(row=r, column=col, sticky="nsew", padx=1, pady=1)
        self._render_day_details()

    def _day_cell(self, day, today):
        """خلية يوم واحد: رقم اليوم + أقراص حالة الامتحانات."""
        d = date(self.year, self.month, day)
        ds = d.isoformat()
        exams = self._by_day.get(ds, [])
        is_today = (d == today)
        is_sel = (self.selected == ds)
        if is_sel:
            bg, bd = "#DCE9F5", NAVY
        elif is_today:
            bg, bd = "#FBEFD6", GOLD
        else:
            bg, bd = CARD, BORDER
        cell = tk.Frame(self.cal_grid, bg=bg, highlightthickness=1,
                        highlightbackground=bd, cursor="hand2")
        cell.rowconfigure(1, weight=1)
        cell.columnconfigure(0, weight=1)
        tk.Label(cell, text=str(day), bg=bg,
                 fg=NAVY if is_today else TEXT,
                 font=(FONT, 10, "bold"), anchor="e").grid(
            row=0, column=0, sticky="ne", padx=5, pady=(3, 0))
        strip = tk.Frame(cell, bg=bg)
        strip.grid(row=1, column=0, sticky="n", pady=(2, 0))
        for e in exams[:3]:
            st = self._status_of(e)
            tk.Label(strip, text="●", bg=bg, fg=self.ST_COLORS[st],
                     font=(FONT, 9)).pack(side="right", padx=1)
        if len(exams) > 3:
            tk.Label(strip, text="+%d" % (len(exams) - 3), bg=bg,
                     fg=MUTED, font=(FONT, 7, "bold")).pack(side="right")
        if exams:
            tk.Label(cell, text=str(len(exams)), bg=bg, fg=MUTED,
                     font=(FONT, 7), anchor="center").grid(
                row=2, column=0, sticky="s", pady=(0, 1))
        for w in (cell,) + tuple(cell.winfo_children()):
            w.bind("<Button-1>",
                   lambda ev, k=ds: self._pick_day(k), add="+")
        return cell

    @staticmethod
    def _status_of(e):
        """حالة الامتحان: ok / fail / late / today / soon."""
        if e["result"] == "ناجح":
            return "ok"
        if e["result"] == "راسب":
            return "fail"
        today = date.today()
        if e["dt"] < today:
            return "late"
        if e["dt"] == today:
            return "today"
        return "soon"

    _ST_TEXT = {"ok": "ناجح", "fail": "راسب", "late": "لم يُؤدَّ (متأخر)",
                "today": "اليوم", "soon": "قادم"}

    def _pick_day(self, ds):
        """عند النقر على يوم في التقويم: Öffnen بطاقة المترشح مباشرة إذا وجد امتحان."""
        exams = self._by_day.get(ds, [])
        if not exams:
            self.selected = None
            self._render_month()
            return
        # إذا كان هناك امتحان واحد فقط، افتح بطاقة المترشح مباشرة
        if len(exams) == 1:
            cand = exams[0]["cand"]
            if cand and cand.get("id") is not None:
                self.selected = ds
                self._render_month()
                if not any(isinstance(c, CandidateDialog) for c in self.winfo_children()):
                    dlg = CandidateDialog(self, self.db, int(cand["id"]), self.reload)
                    dlg.grab_set()
            else:
                self.selected = None
                self._render_month()
            return
        # إذا كان هناك عدة امتحانات في نفس اليوم، افتح أول بطاقة
        cand = exams[0]["cand"]
        if cand and cand.get("id") is not None:
            self.selected = ds
            self._render_month()
            dlg = CandidateDialog(self, self.db, int(cand["id"]), self.reload)
            dlg.grab_set()
        else:
            self.selected = None
            self._render_month()

    def _render_day_details(self):
        if self.selected:
            rows = self._by_day.get(self.selected, [])
            d = datetime.strptime(self.selected, "%Y-%m-%d").date()
            self.det_title.config(
                text="امتحانات %d %s %d (%d):"
                % (d.day, AR_MONTHS[d.month - 1], d.year, len(rows)))
        else:
            rows = [e for e in self._exams
                    if e["dt"].year == self.year
                    and e["dt"].month == self.month]
            self.det_title.config(text="امتحانات الشهر (%d):" % len(rows))
        self.det_tbl.delete(*self.det_tbl.get_children())
        for e in sorted(rows, key=lambda x: (x["date"], x["label"])):
            st = self._status_of(e)
            self.det_tbl.insert("", "end", iid="%s|%s" % (e["date"],
                                                          e["label"]),
                                tags=(st,), values=(
                                    e["cand"].get("full_name", ""),
                                    e["label"], self._ST_TEXT[st],
                                    e["cand"].get("phone", "")))

    def _open_candidate(self, e=None):
        """فتح بطاقة المترشح من جدول تفاصيل اليوم (نقر مفرد أو مزدوج)."""
        try:
            # تحديد الصف الذي تم النقر عليه إن وُجد حدث ماوس
            if e is not None:
                row = self.det_tbl.identify_row(e.y)
                if row:
                    self.det_tbl.selection_set(row)
                    self.det_tbl.focus(row)
                    self.det_tbl.see(row)
            sel = self.det_tbl.selection()
            if not sel:
                children = self.det_tbl.get_children()
                messagebox.showinfo(
                    APP_TITLE,
                    "الجدول يحتوي على %d صفاً، لكن لم يتم تحديد أي صف.\n"
                    "يرجى النقر مباشرة على اسم المترشح في الجدول." % len(children))
                return
            ds, label = sel[0].split("|", 1)
            cand = next((x["cand"] for x in self._exams
                         if x["date"] == ds and x["label"] == label), None)
            if cand is None:
                messagebox.showwarning(
                    APP_TITLE,
                    "لم يتم العثور على بيانات المترشح للتاريخ %s والنوع %s" % (ds, label))
                return
            if cand.get("id") is None:
                messagebox.showwarning(
                    APP_TITLE,
                    "معرف المترشح غير موجود في البيانات.")
                return
            if any(isinstance(c, CandidateDialog) for c in self.winfo_children()):
                return
            dlg = CandidateDialog(self, self.db, int(cand["id"]), self.reload)
            dlg.grab_set()
        except Exception as ex:
            messagebox.showerror(APP_TITLE, "فشل فتح بطاقة المترشح:\n%s" % ex)




class TrashWindow(tk.Toplevel):
    """سلة المهملات: استرجاع أو حذف نهائي."""

    def __init__(self, parent, db, on_change):
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.configure(bg=BG)
        self.title("سلة المهملات")
        self.geometry("560x460")
        self.minsize(480, 380)
        dialog_header(self, "سلة المهملات", "الحذف المؤجّل")

        body = ttk.Frame(self, padding=(16, 12))
        body.pack(fill="both", expand=True)
        self.tbl = ttk.Treeview(body, columns=("name", "when"),
                                show="headings", height=12)
        self.tbl.heading("name", text="المترشح")
        self.tbl.heading("when", text="تاريخ الحذف")
        self.tbl.column("name", width=280, anchor="e")
        self.tbl.column("when", width=160, anchor="center")
        self.tbl.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="استرجاع المحدد", style="Accent.TButton",
                   command=self.restore).pack(side="right")
        ttk.Button(btns, text="حذف نهائي للمحدد", style="Danger.TButton",
                   command=self.purge).pack(side="right", padx=(0, 8))
        ttk.Button(btns, text="إفراغ السلة", style="Tool.TButton",
                   command=self.purge_all).pack(side="left")
        self.load()

    def load(self):
        self.tbl.delete(*self.tbl.get_children())
        for r in self.db.list_trash():
            self.tbl.insert("", "end", iid=str(r["id"]),
                            values=(r["name"], r["deleted_at"]))

    def _sel(self):
        s = self.tbl.selection()
        return int(s[0]) if s else None

    def restore(self):
        tid = self._sel()
        if tid is None:
            messagebox.showinfo(APP_TITLE, "اختر صفاً أولاً.")
            return
        if self.db.restore_trash(tid):
            self.load()
            self.on_change()
            messagebox.showinfo(APP_TITLE, "تم الاسترجاع.")

    def purge(self):
        tid = self._sel()
        if tid is None:
            messagebox.showinfo(APP_TITLE, "اختر صفاً أولاً.")
            return
        if messagebox.askyesno("تأكيد", "حذف نهائي؟ لا يمكن التراجع."):
            self.db.purge_trash(tid)
            self.load()

    def purge_all(self):
        if messagebox.askyesno("تأكيد", "إفراغ السلة نهائياً؟"):
            self.db.purge_trash()
            self.load()


class SettingsWindow(tk.Toplevel):
    """الإعدادات القابلة للتعديل (تُحفظ في settings.json)."""

    def __init__(self, parent, on_change, app=None):
        super().__init__(parent)
        self.on_change = on_change
        self.app = app
        self.configure(bg=BG)
        self.title("الإعدادات")
        self.resizable(True, True)
        self.minsize(470, 440)
        self.transient(parent)
        self.grab_set()
        dialog_header(self, "الإعدادات", "تُحفظ تلقائياً")

        body = ttk.Frame(self, padding=(18, 14))
        body.pack(fill="both", expand=True)

        self.v_school = self._row(body, "اسم المؤسسة",
                                  SETTINGS.get("school_name", ""))
        self.v_cur = self._row(body, "العملة", SETTINGS.get("currency", "درهم"))
        self.v_days = self._row(body, "تنبيه الامتحانات (أيام)",
                                str(SETTINGS.get("exam_alert_days", 7)))
        self.v_keep = self._row(body, "عدد النسخ الاحتياطية المحفوظة",
                                str(SETTINGS.get("backup_keep", 30)))

        self.v_bstart = tk.BooleanVar(
            value=SETTINGS.get("backup_on_start", True))
        self.v_bexit = tk.BooleanVar(
            value=SETTINGS.get("backup_on_exit", True))
        ttk.Checkbutton(body, text="نسخة احتياطية عند الإقلاع",
                        variable=self.v_bstart).pack(anchor="e", pady=3)
        ttk.Checkbutton(body, text="نسخة احتياطية عند الإغلاق",
                        variable=self.v_bexit).pack(anchor="e", pady=3)

        ttk.Button(body, text="حفظ الإعدادات", style="Primary.TButton",
                   command=self.save).pack(fill="x", pady=(16, 0))
        ttk.Button(body, text="فتح مجلد النسخ الاحتياطية",
                   style="Tool.TButton", command=self.open_backups
                   ).pack(fill="x", pady=(6, 0))
        # حساب المقاس المناسب ثم التوسيط
        self.update_idletasks()
        reqw = max(self.winfo_reqwidth(), 480)
        reqh = max(self.winfo_reqheight(), 460)
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        w = min(reqw, sw - 40)
        h = min(reqh, sh - 80)
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry("%dx%d+%d+%d" % (w, h, max(0, px), max(0, py)))

    def _row(self, parent, label, value):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=4)
        ttk.Label(f, text=label, width=24, anchor="e").pack(side="right")
        var = tk.StringVar(value=value)
        ttk.Entry(f, textvariable=var, justify="right").pack(
            side="right", fill="x", expand=True, padx=6)
        return var

    def save(self):
        SETTINGS["school_name"] = self.v_school.get().strip() or SCHOOL_NAME
        SETTINGS["currency"] = self.v_cur.get().strip() or "درهم"
        try:
            SETTINGS["exam_alert_days"] = max(1, int(self.v_days.get()))
        except Exception:
            pass
        try:
            SETTINGS["backup_keep"] = max(1, int(self.v_keep.get()))
        except Exception:
            pass
        SETTINGS["backup_on_start"] = self.v_bstart.get()
        SETTINGS["backup_on_exit"] = self.v_bexit.get()
        save_settings(SETTINGS)
        audit("تعديل الإعدادات", json.dumps(SETTINGS, ensure_ascii=False))
        self.on_change()
        self.destroy()
        messagebox.showinfo(APP_TITLE, "تم حفظ الإعدادات.")

    def open_backups(self):
        try:
            os.startfile(backup_dir())
        except Exception:
            messagebox.showinfo(APP_TITLE, backup_dir())


class AboutWindow(tk.Toplevel):
    """نافذة «حول» مع رقم الإصدار."""

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg=BG)
        self.title("حول البرنامج")
        self.resizable(True, True)
        self.minsize(430, 320)
        self.transient(parent)
        self.grab_set()

        tk.Frame(self, bg=NAVY, height=90).pack(fill="x")
        tk.Label(self, text=APP_TITLE, bg=NAVY, fg="white",
                 font=F_TITLE).pack(pady=(18, 2))
        tk.Label(self, text="الإصدار %s" % APP_VERSION, bg=NAVY, fg=GOLD,
                 font=F_SUB).pack()
        tk.Frame(self, bg=GOLD, height=3).pack(fill="x")

        info = ttk.Frame(self, padding=20)
        info.pack(fill="both", expand=True)
        for label, value in (("المؤسسة", school()),
                             ("قاعدة البيانات", self.db_path(parent)),
                             ("النسخ الاحتياطية", backup_dir())):
            r = ttk.Frame(info)
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=label + ":", width=16, anchor="e",
                      foreground=MUTED).pack(side="right")
            ttk.Label(r, text=value, anchor="e").pack(side="right",
                                                      padx=6)
        ttk.Button(self, text="إغلاق", style="Primary.TButton",
                   command=self.destroy).pack(pady=(0, 14))
        # حساب المقاس المناسب ثم التوسيط
        self.update_idletasks()
        reqw = max(self.winfo_reqwidth(), 440)
        reqh = max(self.winfo_reqheight(), 330)
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        w = min(reqw, sw - 40)
        h = min(reqh, sh - 80)
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry("%dx%d+%d+%d" % (w, h, max(0, px), max(0, py)))

    def db_path(self, parent):
        try:
            return os.path.basename(parent.db.path)
        except Exception:
            return "driving_school.db"


# ---------------- تسجيل الدخول والإعداد الأولي ----------------
class LoginWindow(tk.Tk):
    """نافذة تسجيل الدخول (أو الإعداد الأولي لإنشاء المدير). نافذة مستقلة."""

    def __init__(self, auth, setup_mode=False):
        super().__init__()
        self.auth = auth
        self.setup_mode = setup_mode
        self.result = None          # (username, role, key)
        self.configure(bg=BG)

        self.title("الإعداد الأولي" if setup_mode else "تسجيل الدخول")
        self.resizable(True, True)
        self.minsize(440, 360)

        # إزالة التضليل الأزرق (focus border) على حقول الإدخال
        try:
            _ls = _stdttk.Style(self)
            _ls.theme_use("clam")
            _ls.configure("TEntry", fieldbackground=CARD, foreground="black",
                          bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                          insertcolor="black", padding=6)
            _ls.map("TEntry", bordercolor=[("focus", BORDER)],
                    lightcolor=[("focus", BORDER)], darkcolor=[("focus", BORDER)])
            _ls.configure("TLabel", background=BG, foreground="black")
            _ls.configure("TButton", foreground="black")
        except Exception:
            pass

        tk.Frame(self, bg=NAVY, height=100).pack(fill="x")
        tk.Label(self, text="🎓", bg=NAVY, fg=GOLD,
                 font=(FONT, 30)).pack(pady=(14, 0))
        tk.Label(self, text=("إنشاء حساب المدير" if setup_mode
                             else "تسجيل الدخول"),
                 bg=NAVY, fg="white", font=F_TITLE).pack()
        tk.Label(self, text=school(), bg=NAVY, fg=GOLD,
                 font=F_SUB, wraplength=380, justify="center").pack(
            pady=(0, 8), padx=12)
        tk.Frame(self, bg=GOLD, height=3).pack(fill="x")

        body = _stdttk.Frame(self, padding=(28, 18))
        body.pack(fill="both", expand=True)
        self.v_user = self._field(body, "اسم المستخدم")
        self.v_pass = self._field(body, "كلمة المرور", show="•")
        self.v_role = None
        if setup_mode:
            self.v_confirm = self._field(body, "تأكيد كلمة المرور",
                                         show="•")
            self.v_role = tk.StringVar(value="admin")
            rf = _stdttk.Frame(body)
            rf.pack(fill="x", pady=(6, 0))
            _stdttk.Label(rf, text="الصلاحية:", width=16,
                      anchor="e").pack(side="right")
            _stdttk.Combobox(rf, textvariable=self.v_role, state="readonly",
                         values=["admin", "employee"], width=14,
                         justify="center").pack(side="right", padx=6)
            _stdttk.Label(rf, text="(admin=مدير / employee=موظف)",
                      foreground="black").pack(side="right", padx=4)

        self.bind("<Return>", lambda e: self.submit())
        _stdttk.Button(body, text="دخول" if not setup_mode else "إنشاء الحساب",
                   style="Accent.TButton", command=self.submit
                   ).pack(fill="x", pady=(18, 0))
        if not setup_mode:
            _stdttk.Button(body, text="إلغاء", style="Tool.TButton",
                       command=self.destroy).pack(fill="x", pady=(6, 0))
        self.v_user[1].focus_set()

        # حساب المقاس المناسب للمحتوى ثم التوسيط
        self.update_idletasks()
        reqw = max(self.winfo_reqwidth(), 460)
        reqh = max(self.winfo_reqheight(), 380)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(reqw, sw - 40)
        h = min(reqh, sh - 80)
        self.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2,
                                       max(20, (sh - h) // 3)))

    def _field(self, parent, label, show=None):
        f = _stdttk.Frame(parent)
        f.pack(fill="x", pady=5)
        _stdttk.Label(f, text=label, width=16, anchor="e").pack(side="right")
        var = tk.StringVar()
        e = _stdttk.Entry(f, textvariable=var, show=show or "", justify="right")
        e.pack(side="right", fill="x", expand=True, padx=6)
        return var, f.winfo_children()[-1]

    def submit(self):
        u = self.v_user[0].get().strip()
        p = self.v_pass[0].get()
        if not u or not p:
            messagebox.showwarning(APP_TITLE, "أدخل اسم المستخدم وكلمة المرور.",
                                   parent=self)
            return
        if self.setup_mode:
            if p != self.v_confirm[0].get():
                messagebox.showwarning(APP_TITLE, "كلمتا المرور غير متطابقتين.",
                                       parent=self)
                return
            key = Fernet.generate_key() if CRYPTO_OK else None
            ok, msg = self.auth.create_user(u, p, self.v_role.get(), key)
            if not ok:
                messagebox.showwarning(APP_TITLE, msg, parent=self)
                return
            self.result = (u, self.v_role.get(), key)
            self.destroy()
        else:
            ok, role, key = self.auth.verify(u, p)
            if not ok:
                messagebox.showwarning(APP_TITLE, "بيانات الدخول غير صحيحة.",
                                       parent=self)
                return
            self.result = (u, role, key)
            self.destroy()


def run_setup(auth):
    """الإعداد الأولي: إنشاء حساب المدير. يعيد True عند النجاح."""
    w = LoginWindow(auth, setup_mode=True)
    w.mainloop()
    return w.result is not None


def run_login(auth):
    """نافذة الدخول. تعيد (user, role, key) أو None عند الإلغاء."""
    w = LoginWindow(auth, setup_mode=False)
    w.mainloop()
    return w.result


# ---------------- إدارة المستخدمين (للمدير) ----------------
class UsersWindow(tk.Toplevel):
    """إضافة/حذف المستخدمين وتغيير كلمة المرور (للمدير فقط)."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.auth = app.auth
        self.configure(bg=BG)
        self.title("إدارة المستخدمين")
        self.resizable(True, True)
        self.minsize(520, 460)
        self.transient(parent)
        self.grab_set()
        dialog_header(self, "إدارة المستخدمين", "الصلاحيات والحسابات")

        body = ttk.Frame(self, padding=(16, 12))
        body.pack(fill="both", expand=True)

        self.lst = ttk.Treeview(body, columns=("user", "role"),
                                show="headings", height=8)
        self.lst.heading("user", text="اسم المستخدم")
        self.lst.heading("role", text="الصلاحية")
        self.lst.column("user", width=240, anchor="e")
        self.lst.column("role", width=140, anchor="center")
        self.lst.pack(fill="x")
        self.load()

        # إضافة مستخدم جديد
        add = ttk.LabelFrame(body, text="إضافة مستخدم", padding=10)
        add.pack(fill="x", pady=(12, 0))
        self.v_u = self._row(add, "اسم المستخدم")
        self.v_p = self._row(add, "كلمة المرور", show="•")
        self.v_r = tk.StringVar(value="employee")
        rf = ttk.Frame(add)
        rf.pack(fill="x", pady=4)
        ttk.Label(rf, text="الصلاحية:", width=14, anchor="e").pack(side="right")
        ttk.Combobox(rf, textvariable=self.v_r, state="readonly",
                     values=["admin", "employee"], width=14,
                     justify="center").pack(side="right", padx=6)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="إضافة", style="Accent.TButton",
                   command=self.add_user).pack(side="right")
        ttk.Button(btns, text="حذف المحدد", style="Danger.TButton",
                   command=self.del_user).pack(side="right", padx=(0, 8))
        ttk.Button(btns, text="تغيير كلمة مروري", style="Tool.TButton",
                   command=self.change_my_pw).pack(side="left")

        # حساب المقاس المناسب للمحتوى ثم التوسيط
        self.update_idletasks()
        reqw = max(self.winfo_reqwidth(), 540)
        reqh = max(self.winfo_reqheight(), 480)
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        w = min(reqw, sw - 40)
        h = min(reqh, sh - 80)
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry("%dx%d+%d+%d" % (w, h, max(0, px), max(0, py)))

    def _row(self, parent, label, show=None):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=4)
        ttk.Label(f, text=label, width=14, anchor="e").pack(side="right")
        var = tk.StringVar()
        ttk.Entry(f, textvariable=var, show=show or "", justify="right"
                  ).pack(side="right", fill="x", expand=True, padx=6)
        return var

    def load(self):
        self.lst.delete(*self.lst.get_children())
        for name, role in self.auth.list_users():
            self.lst.insert("", "end", iid=name,
                            values=(name, ROLE_LABELS.get(role, role)))

    def add_user(self):
        u = self.v_u.get().strip()
        p = self.v_p.get()
        if not u or not p:
            messagebox.showwarning(APP_TITLE, "أدخل الاسم وكلمة المرور.",
                                   parent=self)
            return
        ok, msg = self.auth.create_user(u, p, self.v_r.get(),
                                        self.app.db_key)
        if ok:
            self.load()
            self.v_u.set("")
            self.v_p.set("")
            audit("إنشاء مستخدم", "%s (%s)" % (u, self.v_r.get()))
            messagebox.showinfo(APP_TITLE, msg, parent=self)
        else:
            messagebox.showwarning(APP_TITLE, msg, parent=self)

    def del_user(self):
        s = self.lst.selection()
        if not s:
            return
        name = s[0]
        if name == self.app.username:
            messagebox.showwarning(APP_TITLE, "لا يمكنك حذف حسابك الحالي.",
                                   parent=self)
            return
        if len(self.auth.list_users()) <= 1:
            messagebox.showwarning(APP_TITLE, "يجب إبقاء مستخدم واحد على الأقل.",
                                   parent=self)
            return
        if messagebox.askyesno("تأكيد", "حذف المستخدم «%s»؟" % name,
                               parent=self):
            self.auth.delete_user(name)
            self.load()
            audit("حذف مستخدم", name)

    def change_my_pw(self):
        ChangePasswordDialog(self, self.auth, self.app.username,
                             self.app.db_key)


class ChangePasswordDialog(tk.Toplevel):
    """تغيير كلمة المرور للمستخدم الحالي."""

    def __init__(self, parent, auth, username, key):
        super().__init__(parent)
        self.auth = auth
        self.username = username
        self.key = key
        self.configure(bg=BG)
        self.title("تغيير كلمة المرور")
        self.resizable(True, True)
        self.minsize(430, 280)
        self.transient(parent)
        self.grab_set()
        dialog_header(self, "تغيير كلمة المرور", username)
        body = ttk.Frame(self, padding=(24, 14))
        body.pack(fill="both", expand=True)
        self.v_old = self._row(body, "كلمة المرور الحالية", show="•")
        self.v_new = self._row(body, "كلمة المرور الجديدة", show="•")
        self.v_cf = self._row(body, "تأكيد كلمة المرور", show="•")
        ttk.Button(body, text="حفظ", style="Primary.TButton",
                   command=self.save).pack(fill="x", pady=(14, 0))
        # حساب المقاس المناسب ثم التوسيط
        self.update_idletasks()
        reqw = max(self.winfo_reqwidth(), 440)
        reqh = max(self.winfo_reqheight(), 290)
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        w = min(reqw, sw - 40)
        h = min(reqh, sh - 80)
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry("%dx%d+%d+%d" % (w, h, max(0, px), max(0, py)))

    def _row(self, parent, label, show=None):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=5)
        ttk.Label(f, text=label, width=18, anchor="e").pack(side="right")
        var = tk.StringVar()
        ttk.Entry(f, textvariable=var, show=show or "", justify="right"
                  ).pack(side="right", fill="x", expand=True, padx=6)
        return var

    def save(self):
        o, n, c = self.v_old.get(), self.v_new.get(), self.v_cf.get()
        if not o or not n:
            messagebox.showwarning(APP_TITLE, "املأ الحقول.", parent=self)
            return
        if n != c:
            messagebox.showwarning(APP_TITLE, "كلمتا المرور غير متطابقتين.",
                                   parent=self)
            return
        ok, msg = self.auth.change_password(self.username, o, n, self.key)
        messagebox.showinfo(APP_TITLE, msg, parent=self)
        if ok:
            audit("تغيير كلمة مرور", self.username)
            self.destroy()


def main():
    auth = Auth()
    while True:
        # إنشاء حساب المدير عند التشغيل الأول
        if not auth.has_users():
            if not run_setup(auth):
                return
        creds = run_login(auth)
        if not creds:
            return
        username, role, key = creds
        app = App(role=role, key=key, auth=auth, username=username)
        app.mainloop()
        # عند طلب تسجيل الخروج تُعاد الحلقة؛ وعند الإغلاق العادي تنتهي
        if not getattr(app, "logout_requested", False):
            return


if __name__ == "__main__":
    main()
