import re
import unicodedata
from datetime import datetime, timedelta
from rapidfuzz import process, fuzz

# --- 1. CONFIGURATION & DICTIONARY ---
RAW_DICTIONARY = {
    "Ăn uống": [
        "an", "uong", "tra sua", "pho", "com", "cafe", "nhau", "nuoc",
        "bun", "bua", "lau", "nuong", "snack", "banh trang", "mixue",
        "tocotoco", "banh", "banh mi"
    ],
    "Di chuyển": [
        "xang", "grab", "xe", "taxi", "be", "bus", "gui xe", "bom", "va",
        "do xang", "xe om", "ve tau", "bao duong"
    ],
    "Giải trí": [
        "xem phim", "cgv", "netflix", "game", "choi", "bida", "net",
        "nap game", "tft", "minecraft", "steam", "nap the"
    ],
    "Thể thao": [
        "cau long", "thue san", "mua vot", "cang luoi", "da bong",
        "gym", "boi", "the thao", "cuoc"
    ],
    "Học tập & Công việc": [
        "hoc phi", "mua sach", "in an", "photo", "khoa hoc",
        "do an", "mua giao trinh", "github", "thi lai"
    ],
    "Lương": [
        "luong", "thuong", "nhan", "lai", "thu nhap", "tieu vat",
        "bo me cho", "ting ting", "nhan tien", "duoc cho",
        "co tien", "kiem duoc", "thu ve"
    ],
    "Mua sắm": [
        "mua sam", "ao", "quan", "giay", "shopee", "my pham",
        "lazada", "op lung", "cap sac", "chuot", "ban phim"
    ]
}

ALL_KEYWORDS = []
KEYWORD_TO_CAT = {}

for cat, kws in RAW_DICTIONARY.items():
    for kw in kws:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CAT[kw] = cat


# --- 2. UTILS ---
def normalize_text(text: str):
    if not text:
        return ""

    s1 = unicodedata.normalize("NFD", text.lower())
    s2 = "".join([c for c in s1 if unicodedata.category(c) != "Mn"])
    return s2.replace("đ", "d").strip()


def extract_and_clean_date(raw_text: str):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    cleaned_text = raw_text

    text_no_accent_for_date = normalize_text(raw_text)

    # Bắt ngày dạng chữ:
    # "ngày 25 tháng 5", "25 tháng 5", "ngày 25 tháng 5 năm 2026"
    match_text_date = re.search(
        r"\b(?:ngay\s*)?(\d{1,2})\s*thang\s*(\d{1,2})(?:\s*nam\s*(\d{2,4}))?\b",
        text_no_accent_for_date
    )

    if match_text_date:
        try:
            day = int(match_text_date.group(1))
            month = int(match_text_date.group(2))
            year_raw = match_text_date.group(3)

            year = int(year_raw) if year_raw else today.year
            if year < 100:
                year += 2000

            date_obj = datetime(year, month, day)
            date_str = date_obj.strftime("%Y-%m-%d")

            # Xóa cụm ngày khỏi câu gốc, bao gồm cả dạng thiếu chữ "ngày":
            # "25 tháng 5 mua nước 10000" -> "mua nước 10000"
            cleaned_text = re.sub(
                r"\b(?:ngày|ngay)?\s*\d{1,2}\s*(?:tháng|thang)\s*\d{1,2}(?:\s*(?:năm|nam)\s*\d{2,4})?\b",
                " ",
                raw_text,
                flags=re.IGNORECASE
            )

            return date_str, cleaned_text.strip()
        except ValueError:
            pass

    # Bắt ngày dạng số:
    # 19/05, 19/05/2026, 19-05-2026
    date_pattern = r"\b(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?\b"
    match_date = re.search(date_pattern, raw_text)

    if match_date:
        day = int(match_date.group(1))
        month = int(match_date.group(2))
        year_raw = match_date.group(3)

        try:
            year = int(year_raw) if year_raw else today.year
            if year < 100:
                year += 2000

            date_obj = datetime(year, month, day)
            date_str = date_obj.strftime("%Y-%m-%d")
            cleaned_text = raw_text[:match_date.start()] + " " + raw_text[match_date.end():]
        except ValueError:
            cleaned_text = raw_text.replace(match_date.group(0), " ")

        return date_str, cleaned_text.strip()

    text_no_accent = normalize_text(raw_text)

    if "hom qua" in text_no_accent:
        date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        cleaned_text = re.sub(r"hôm qua|hom qua", " ", raw_text, flags=re.IGNORECASE)

    elif "hom kia" in text_no_accent:
        date_str = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        cleaned_text = re.sub(r"hôm kia|hom kia", " ", raw_text, flags=re.IGNORECASE)

    return date_str, cleaned_text.strip()


def parse_amount(amount_str: str, suffix: str):
    suffix = (suffix or "").lower()

    if suffix in ["k", "nghin", "ngan", "m", "trieu", "tr"]:
        amount = float(amount_str.replace(",", "."))
    else:
        amount = float(amount_str.replace(".", "").replace(",", ""))

    if suffix in ["k", "nghin", "ngan"]:
        amount *= 1000
    elif suffix in ["m", "trieu", "tr"]:
        amount *= 1000000

    return amount


# --- 3. FINANCE AGENT ---
class FinanceAgent:
    def __init__(self):
        self.threshold = 75
        self.base_confidence = 0.5

    def _fuzzy_classify(self, note_clean: str):
        note_no_accent = normalize_text(note_clean)

        if not note_no_accent or note_no_accent == "giao dich":
            return "Khác", "Chi", None, 0.4

        # Ưu tiên keyword dài trước
        for kw in sorted(ALL_KEYWORDS, key=len, reverse=True):
            if kw in note_no_accent:
                cat = KEYWORD_TO_CAT[kw]
                t_type = "Thu" if cat == "Lương" else "Chi"
                return cat, t_type, kw, 1.0

        match = process.extractOne(
            note_no_accent,
            ALL_KEYWORDS,
            scorer=fuzz.partial_ratio
        )

        if match and match[1] >= self.threshold:
            kw = match[0]
            cat = KEYWORD_TO_CAT[kw]
            t_type = "Thu" if cat == "Lương" else "Chi"
            return cat, t_type, kw, round(match[1] / 100, 2)

        return "Khác", "Chi", None, 0.5

    def _clean_note(self, note: str):
        note = re.sub(r"^[,\.\-\s/]+|[,\.\-\s/]+$", "", note)
        return re.sub(r"\s+", " ", note).strip()

    def parse(self, raw_text: str):
        date_detected, clean_text_for_money = extract_and_clean_date(raw_text)
        text_no_accent = normalize_text(clean_text_for_money)

        # -------------------------------------------------------------
        # 🛡️ BẮT CÂU HỎI TƯ VẤN VÀ CHUYỂN CHO GEMINI (Sửa thành "chat")
        # -------------------------------------------------------------
        if "?" in raw_text:
            return self._build_response("chat", {"raw_query": raw_text})

        cac_tu_hoi = [
            "co the", "co nen", "duoc ko", "duoc khong", 
            "dc ko", "dc khong", "co ko", "co khong", 
            "lam sao", "nhi", "ha", "khoang bao nhieu"
        ]
        if any(tu_hoi in text_no_accent for tu_hoi in cac_tu_hoi) or ("khoang" in text_no_accent and "tr" in text_no_accent.lower()):
            return self._build_response("chat", {"raw_query": raw_text})
        # -------------------------------------------------------------

        # Intent không phải thêm giao dịch
        if any(kw in text_no_accent for kw in ["tong ket", "bao cao", "xem lai thang"]):
            return self._build_response("report", {"period": "current_month"})

        if any(kw in text_no_accent for kw in ["bao nhieu", "tong chi", "thong ke", "het bao tien", "tong thu"]):
            return self._build_response("query", {"raw_query": raw_text})

        if any(kw in text_no_accent for kw in ["han muc", "ngan sach", "chay tui"]):
            return self._build_response("budget", {"raw_query": raw_text})

        if any(kw in text_no_accent for kw in ["loi khuyen", "tu van", "tiet kiem"]):
            return self._build_response("advice", {"raw_query": raw_text})

        # Bóc tách số tiền
        # Quan trọng: đây là regex tiền, không phải regex ngày tháng
        pattern = r"\b(\d+(?:[\.,]\d+)?)\s*(k|nghin|ngan|m|trieu|tr|d|vnd)?\b"
        matches = list(re.finditer(pattern, clean_text_for_money, re.IGNORECASE))

        if matches:
            transactions = []

            base_note = re.sub(
                pattern,
                "",
                clean_text_for_money,
                flags=re.IGNORECASE
            ).strip()
            base_note = self._clean_note(base_note)

            last_end = 0

            for match in matches:
                amount_str = match.group(1)
                suffix = (match.group(2) or "").lower()

                try:
                    amount = parse_amount(amount_str, suffix)
                except ValueError:
                    continue

                start, end = match.span()

                raw_note = clean_text_for_money[last_end:start].strip()
                raw_note = self._clean_note(
                    re.sub(pattern, "", raw_note, flags=re.IGNORECASE)
                )

                note = raw_note if (raw_note and len(raw_note) > 1) else base_note
                if not note:
                    note = "Giao dịch"

                cat, t_type, kw, fuzzy_score = self._fuzzy_classify(note)
                conf = self.base_confidence + (0.2 if kw else 0) + (0.1 if amount > 0 else 0)

                transactions.append({
                    "amount": amount,
                    "category": cat,
                    "note": note,
                    "type": t_type,
                    "date": date_detected,
                    "entities": {
                        "keyword": kw,
                        "amount_raw": match.group(0)
                    },
                    "confidence": min(conf + (fuzzy_score * 0.2), 1.0)
                })

                last_end = end

            return self._build_response("add", transactions)

        return self._build_response("chat", {
            "message": "Chuyển giao quyền lực cho Gemini"
        })

    def _build_response(self, intent, data):
        return {
            "intent": intent,
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "agent_version": "2.6-date-text-fixed",
                "status": "success"
            }
        }


def phan_tich_y_dinh(cau_noi):
    agent = FinanceAgent()
    return agent.parse(cau_noi)


if __name__ == "__main__":
    agent = FinanceAgent()

    print(agent.parse("25 tháng 5 mua nước 10000"))
    print(agent.parse("ngày 21 tháng 5 tớ đổ xăng hết 50000"))
    print(agent.parse("19/05/2026 tớ mua nước 20000"))
    print(agent.parse("hôm qua ăn bún chả 40k, mua vợt 1.2tr"))