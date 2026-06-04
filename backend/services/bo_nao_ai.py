import re
import unicodedata
from datetime import datetime, timedelta
from rapidfuzz import process, fuzz
from typing import Tuple, Dict, List, Any, Optional


# --- 1. CONFIGURATION & DICTIONARY ---
RAW_DICTIONARY = {

    "Ăn uống": [
        "an", "uong", "pho", "bun", "com", "chao", "mi", "hu tieu",
        "tra sua", "cafe", "nuoc", "nuoc ngot", "banh", "banh mi",
        "ga ran", "kfc", "lotteria", "jollibee", "do an vat", "nhau"
    ],

    "Đi lại": [
        "xang", "do xang", "grab", "be", "taxi", "xe om",
        "bus", "xe buyt", "gui xe", "ve tau", "ve xe",
        "bao duong", "sua xe", "thay lop", "cau duong",
        "di lai", "xe", "oto", "xe may", "di chuyen"
    ],

    "Mua sắm": [
        "mua sam", "shopee", "lazada", "tiki", "ao",
        "quan", "giay", "dep", "tui", "balo",
        "chuot", "ban phim", "op lung", "cap sac",
        "tai nghe", "dong ho", "may tinh", "phu kien",
        "mua do", "shopping"
    ],

    "Giải trí": [
        "xem phim", "cgv", "netflix", "youtube premium",
        "spotify", "game", "choi game", "steam",
        "nap game", "lien minh", "tft", "minecraft",
        "bida", "karaoke", "du lich", "ca nhac",
        "rap phim", "giai tri", "ve phim", "ve xem"
    ],

    "Giáo dục": [
        "hoc phi", "mua sach", "giao trinh", "photo",
        "in an", "khoa hoc", "udemy", "coursera",
        "thi", "thi lai", "chung chi", "toeic",
        "ielts", "lap trinh", "github", "tai lieu",
        "hoc them", "sach", "hoc tap", "giao duc"
    ],

    "Điện thoại": [
        "nap the", "goi cuoc", "4g", "5g", "data",
        "viettel", "vinaphone", "mobifone", "sim",
        "internet", "wifi", "dang ky mang",
        "cuoc dien thoai", "sms", "nap tien",
        "thue bao", "dien thoai", "mang", "cuoc phi", "data mobile"
    ],

    "Sức khỏe": [
        "thuoc", "kham", "benh vien", "vien phi",
        "nha khoa", "rang", "mat", "kham suc khoe",
        "xet nghiem", "vitamin", "thuoc cam",
        "thuoc ho", "bac si", "bao hiem",
        "thuoc bo", "thuoc dau", "phong kham",
        "suc khoe", "kham benh", "y te"
    ],

    "Làm đẹp": [
        "son", "my pham", "spa", "cat toc",
        "lam toc", "goi dau", "duong da",
        "serum", "kem duong", "makeup",
        "nuoc hoa", "mat na", "duong toc",
        "nail", "lam mong", "tham my",
        "lam dep", "trang diem", "duong moi", "duong mat"
    ],

    "Thú cưng": [
        "cho", "meo", "cat", "dog",
        "thuc an cho", "thuc an meo",
        "thu y", "kham thu y", "tam cho",
        "tam meo", "cat tia long", "phu kien cho",
        "phu kien meo", "do choi thu cung",
        "thu cung", "vaccine cho", "vaccine meo",
        "hat", "cat ve sinh", "chuong"
    ],

    "Quà tặng": [
        "qua", "qua tang", "tang",
        "sinh nhat", "hoa", "gau bong",
        "qua cho ban gai",
        "qua cho ban trai", "qua cho me",
        "qua cho bo", "qua cho ban",
        "socola", "qua ky niem",
        "qua valentine", "qua tet",
        "qua trung thu", "qua cuoi",
        "hoa tuoi", "qua mung"
    ]
}
ALL_KEYWORDS = []
KEYWORD_TO_CAT = {}

for cat, kws in RAW_DICTIONARY.items():
    for kw in kws:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CAT[kw] = cat


# --- 2. UTILS ---
def normalize_text(text: str) -> str:
    """Chuẩn hóa văn bản: chuyển sang chữ thường, bỏ dấu thanh."""
    if not text:
        return ""

    s1 = unicodedata.normalize("NFD", text.lower())
    s2 = "".join([c for c in s1 if unicodedata.category(c) != "Mn"])
    return s2.replace("đ", "d").strip()


def extract_and_clean_date(raw_text: str) -> Tuple[str, str]:
    """Trích xuất và làm sạch ngày tháng từ văn bản."""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    cleaned_text = raw_text

    text_no_accent_for_date = normalize_text(raw_text)

    # Bắt ngày dạng chữ: "ngày 25 tháng 5", "25 tháng 5", "ngày 25 tháng 5 năm 2026"
    match_text_date = re.search(
        r"\b(?:ngay\s*)?(\d{1,2})\s*thang\s*(\d{1,2})(?:\s*nam\s*(\d{2,4}))?\b",
        text_no_accent_for_date,
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

            # Xóa cụm ngày khỏi câu gốc
            cleaned_text = re.sub(
                r"\b(?:ngày|ngay)?\s*\d{1,2}\s*(?:tháng|thang)\s*\d{1,2}(?:\s*(?:năm|nam)\s*\d{2,4})?\b",
                " ",
                raw_text,
                flags=re.IGNORECASE,
            )

            return date_str, cleaned_text.strip()
        except ValueError:
            pass

    # Bắt ngày dạng số: 19/05, 19/05/2026, 19-05-2026
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


def parse_amount(amount_str: str, suffix: str) -> float:
    """Phân tích số tiền và hậu tố (k, m, vnd, etc.)."""
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
    """Agent phân tích ý định và bóc tách giao dịch tài chính."""

    def __init__(self) -> None:
        self.threshold = 75
        self.base_confidence = 0.5

    def _fuzzy_classify(self, note_clean: str) -> Tuple[str, str, Optional[str], float]:
        """Phân loại danh mục sử dụng fuzzy matching."""
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
            scorer=fuzz.partial_ratio,
        )

        if match and match[1] >= self.threshold:
            kw = match[0]
            cat = KEYWORD_TO_CAT[kw]
            t_type = "Thu" if cat == "Lương" else "Chi"
            return cat, t_type, kw, round(match[1] / 100, 2)

        return "Khác", "Chi", None, 0.5

    def _clean_note(self, note: str) -> str:
        """Làm sạch ghi chú: loại bỏ ký tự đặc biệt và khoảng trắng thừa."""
        note = re.sub(r"^[,\.\-\s/]+|[,\.\-\s/]+$", "", note)
        return re.sub(r"\s+", " ", note).strip()

    def parse(self, raw_text: str) -> Dict[str, Any]:
        """Hàm chính để phân tích văn bản đầu vào."""
        date_detected, clean_text_for_money = extract_and_clean_date(raw_text)
        text_no_accent = normalize_text(clean_text_for_money)

        # 1. Báo cáo/tổng kết: rule-based xử lý
        if any(kw in text_no_accent for kw in ["tong ket", "bao cao", "xem lai thang"]):
            return self._build_response("report", {"period": "current_month"})

        # 2. Truy vấn thống kê rõ ràng: rule-based xử lý
        if any(kw in text_no_accent for kw in ["bao nhieu", "tong chi", "thong ke", "het bao tien", "tong thu"]):
            return self._build_response("query", {"raw_query": raw_text})

        # 3. Ngân sách cơ bản: rule-based xử lý
        if any(kw in text_no_accent for kw in ["han muc", "ngan sach", "chay tui"]):
            return self._build_response("budget", {"raw_query": raw_text})
        
        # 4. Nếu là câu hỏi tư vấn/quyết định thì chuyển sang Groq,
        # KHÔNG được lưu thành giao dịch dù trong câu có số tiền.
        groq_advice_patterns = [
            "co nen",
            "co du",
            "nen khong",
            "nen mua",
            "co nen mua",
            "co dang",
            "dang mua",
            "hop ly khong",
            "on khong",
            "duoc khong",
            "co duoc khong",
            "nen lam gi",
            "nen chi tieu",
            "chi tieu nhu nao",
            "chi tieu the nao",
            "mua sam thoai mai",
            "thoai mai khong",
            "co nen dau tu",
            "nen dau tu",
            "dau tu vao",
            "gui tiet kiem",
            "so sanh",
            "nen chon",
            "cai nao tot hon",
            "cai nao hop ly hon",
        ]

        if any(pattern_kw in text_no_accent for pattern_kw in groq_advice_patterns):
            return self._build_response("chat", {
                "message": "Câu hỏi tư vấn, chuyển sang Groq xử lý",
            })
        # 5. Bóc tách số tiền: rule-based xử lý thêm giao dịch
        pattern = r"\b(\d+(?:[\.,]\d+)?)\s*(k|nghin|ngan|m|trieu|tr|d|vnd)?\b"
        matches = list(re.finditer(pattern, clean_text_for_money, re.IGNORECASE))

        if matches:
            transactions = []

            base_note = re.sub(
                pattern,
                "",
                clean_text_for_money,
                flags=re.IGNORECASE,
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
                        "amount_raw": match.group(0),
                    },
                    "confidence": min(conf + (fuzzy_score * 0.2), 1.0),
                })

                last_end = end

            return self._build_response("add", transactions)

        # 6. Còn lại: chuyển cho Groq xử lý hội thoại/tư vấn tự nhiên
        return self._build_response("chat", {
            "message": "Chuyển sang Groq xử lý",
        })

    def _build_response(self, intent: str, data: Dict[str, Any] | List[Any]) -> Dict[str, Any]:
        """Xây dựng cấu trúc phản hồi chuẩn."""
        return {
            "intent": intent,
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "agent_version": "2.6-date-text-fixed",
                "status": "success",
            },
        }


def phan_tich_y_dinh(cau_noi: str) -> Dict[str, Any]:
    """Hàm wrapper để khởi tạo agent và phân tích ý định."""
    agent = FinanceAgent()
    return agent.parse(cau_noi)


if __name__ == "__main__":
    agent = FinanceAgent()

    print(agent.parse("25 tháng 5 mua nước 10000"))
    print(agent.parse("ngày 21 tháng 5 tớ đổ xăng hết 50000"))
    print(agent.parse("19/05/2026 tớ mua nước 20000"))
    print(agent.parse("hôm qua ăn bún chả 40k, mua vợt 1.2tr"))
