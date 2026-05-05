import re
import unicodedata
from datetime import datetime, timedelta
from rapidfuzz import process, fuzz

# --- 1. CONFIGURATION & DICTIONARY ---
RAW_DICTIONARY = {
    "Ăn uống": ["an", "uong", "tra sua", "pho", "com", "cafe", "nhau", "nuoc", "bun", "bua", "lau", "nuong", "snack", "banh trang", "mixue", "tocotoco"],
    "Di chuyển": ["xang", "grab", "xe", "taxi", "be", "bus", "gui xe", "bom", "va", "do xang", "xe om", "ve tau", "bao duong"],
    "Giải trí": ["xem phim", "cgv", "netflix", "game", "choi", "bida", "net", "nap game", "tft", "minecraft", "steam", "nap the"],
    "Thể thao": ["cau long", "thue san", "mua vot", "cang luoi", "da bong", "gym", "boi", "the thao", "cuoc"],
    "Học tập & Công việc": ["hoc phi", "mua sach", "in an", "photo", "khoa hoc", "do an", "mua giao trinh", "github", "thi lai"],
    "Lương": ["luong", "thuong", "nhan", "lai", "thu nhap", "tieu vat", "bo me cho", "ting ting"],
    "Mua sắm": ["mua sam", "ao", "quan", "giay", "shopee", "my pham", "lazada", "mua", "op lung", "cap sac", "chuot", "ban phim"]
}

# Tạo Flat Map để tra cứu nhanh
ALL_KEYWORDS = []
KEYWORD_TO_CAT = {}
for cat, kws in RAW_DICTIONARY.items():
    for kw in kws:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CAT[kw] = cat

# --- 2. UTILS ---
def normalize_text(text: str):
    if not text: return ""
    s1 = unicodedata.normalize('NFD', text.lower())
    s2 = "".join([c for c in s1 if unicodedata.category(c) != 'Mn'])
    return s2.replace('đ', 'd').strip()

def get_transaction_date(text_no_accent: str):
    today = datetime.now()
    if "hom qua" in text_no_accent:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    if "hom kia" in text_no_accent:
        return (today - timedelta(days=2)).strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

# --- 3. FINANCE AGENT V2.1 (OPTIMIZED) ---
class FinanceAgent:
    def __init__(self):
        self.threshold = 75  # Độ chính xác cho fuzzy matching
        self.base_confidence = 0.5

    def _fuzzy_classify(self, note_clean: str):
        note_no_accent = normalize_text(note_clean)
        if not note_no_accent:
            return "Khác", "Chi", None, 0.4

        # Sử dụng partial_ratio để bắt các từ khóa nằm trong câu
        match = process.extractOne(note_no_accent, ALL_KEYWORDS, scorer=fuzz.partial_ratio)

        if match and match[1] >= self.threshold:
            kw = match[0]
            cat = KEYWORD_TO_CAT[kw]
            t_type = "Thu" if cat == "Lương" else "Chi"
            return cat, t_type, kw, round(match[1] / 100, 2)

        return "Khác", "Chi", None, 0.5

    def _clean_note(self, note: str):
        note = re.sub(r'^[,\.\-\s]+|[,\.\-\s]+$', '', note)
        return re.sub(r'\s+', ' ', note).strip()

    def parse(self, raw_text: str):
        text_no_accent = normalize_text(raw_text)
        date_detected = get_transaction_date(text_no_accent)
        
        # 1. ROUTING INTENT (Report & Query)
        if any(kw in text_no_accent for kw in ["tong ket", "bao cao", "xem lai thang"]):
            return self._build_response("report", {"period": "current_month"})
        
        if any(kw in text_no_accent for kw in ["bao nhieu", "tong chi", "thong ke", "het bao tien"]):
            return self._build_response("query", {"raw_query": raw_text})

        # 2. ENTITY EXTRACTION (Add Transaction)
        # Regex hỗ trợ các định dạng tiền phổ biến ở VN
        pattern = r'(\d+[\d\.\,]*)\s*(k|nghin|ngan|m|trieu|tr|d|vnd)?'
        matches = list(re.finditer(pattern, raw_text, re.IGNORECASE))
        
        if matches:
            transactions = []
            last_end = 0
            for match in matches:
                # Xử lý số tiền
                amount_str = match.group(1).replace('.', '').replace(',', '')
                suffix = (match.group(2) or "").lower()
                try:
                    amount = float(amount_str)
                except: continue

                if suffix in ['k', 'nghin', 'ngan']: amount *= 1000
                elif suffix in ['m', 'trieu', 'tr']: amount *= 1000000
                
                # Bóc tách note dựa trên khoảng cách giữa các số tiền
                start, end = match.span()
                raw_note = raw_text[last_end:start].strip()
                note = self._clean_note(raw_note) or "Giao dịch"
                
                # Phân loại danh mục
                cat, t_type, kw, fuzzy_score = self._fuzzy_classify(note)
                
                # Tính toán confidence
                conf = self.base_confidence + (0.2 if kw else 0) + (0.1 if amount > 0 else 0)
                
                transactions.append({
                    "amount": amount,
                    "category": cat,
                    "note": note,
                    "type": t_type,
                    "date": date_detected,
                    "entities": {"keyword": kw, "amount_raw": match.group(0)},
                    "confidence": min(conf + (fuzzy_score * 0.2), 1.0)
                })
                last_end = end
            
            return self._build_response("add", transactions)

        # 3. FALLBACK
        return self._build_response("chat", {"message": "Mình chưa hiểu ý bạn hoặc không tìm thấy số tiền, bạn thử nói rõ hơn nhé!"})

    def _build_response(self, intent, data):
        return {
            "intent": intent,
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "agent_version": "2.1-stable",
                "status": "success"
            }
        }

# --- TEST DRIVE ---
if __name__ == "__main__":
    agent = FinanceAgent()
    
    # Test case 1: Đa giao dịch + ngày tháng
    print("Test 1:", agent.parse("Hôm qua ăn bún chả 40k, mua vợt 1.2tr"))
    
    # Test case 2: Sai chính tả nhẹ (Fuzzy test)
    print("\nTest 2:", agent.parse("mua trà sữa mixue 25k"))
    
    # Test case 3: Report
    print("\nTest 3:", agent.parse("Tổng kết tháng này cho mình với"))