import re  # Đã thêm import re để không văng lỗi NameError
import sqlite3
from datetime import datetime, timedelta
from database.db import get_connection

def lam_sach_ghi_chu_loi(note_raw: str) -> str:
    """
    Bộ lọc Regex: Quét sạch cả cụm từ rác thời gian, hành động, không lo bị băm nát chữ.
    """
    if not note_raw:
        return "Giao dịch"
    text = note_raw.lower().strip()
    cum_tu_rac = [
        r"\bhôm nay\b", r"\bhom nay\b", r"\bhôm qua\b", r"\bhom qua\b", r"\bhôm kia\b", r"\bhom kia\b",
        r"\bngày ngày\b", r"\bngay ngay\b", r"\btớ mua\b", r"\bto mua\b", r"\bmình mua\b", r"\bminh mua\b",
        r"\bmua hộ\b", r"\bmua ho\b", r"\bnhận được\b", r"\bnhan duoc\b", r"\bhết sạch\b", r"\bhet sach\b"
    ]
    for pattern in cum_tu_rac:
        text = re.sub(pattern, "", text)
    tu_don_rac = [
        "nay", "qua", "kia", "ngày", "ngay", "tháng", "thang", "năm", "nam",
        "tớ", "to", "mình", "minh", "bạn", "ban", "ta", "tớ", "hết", "het",
        "mua", "bán", "nhận", "nhan", "trả", "tra", "tiêu", "tieu", "đốt", "dot",
        "đi", "di", "cho", "vào", "vao", "của", "cua", "hộ", "ho", "được", "duoc"
    ]
    words = text.split()
    clean_words = [w for w in words if w not in tu_don_rac]
    note_clean = " ".join(clean_words).strip()
    return note_clean.capitalize() if note_clean else "Giao dịch"


def xu_ly_them_moi(intent_data: dict) -> str:
    """
    Xử lý intent 'add': Sinh text phản hồi sạch sẽ từ gốc.
    """
    danh_sach_gd = intent_data.get("data", [])

    if not danh_sach_gd:
        return "⚠️ Không tìm thấy giao dịch nào trong tin nhắn của bạn. Bạn thử nhập lại nhé!"

    ket_qua = []

    for gd in danh_sach_gd:
        try:
            tien_format = "{:,.0f}".format(gd["amount"])
            type_raw = str(gd["type"]).lower()
            
            # 🌟 VÁ LỖI 1: Ép chạy qua bộ lọc để câu trả lời của chatbot không bị dính từ rác
            ghi_chu_sach = lam_sach_ghi_chu_loi(gd["note"])

            loai = "💸 Chi" if type_raw in ["chi", "expense"] else "💰 Thu"
            ket_qua.append(
                f"✅ {loai} {tien_format}đ — '{ghi_chu_sach}' (Danh mục: {gd['category']})"
            )
        except Exception as e:
            ket_qua.append(f"⚠️ Không xử lý được giao dịch '{gd.get('note', '?')}': {str(e)}")

    return "\n".join(ket_qua)


def xu_ly_truy_van_nang_cao(cau_noi: str, username: str = "ka") -> str:
    """
    Xử lý intent 'query' thông minh: Tự động phân biệt hỏi theo NGÀY hay theo THÁNG.
    🌟 VÁ LỖI 2: Đã thêm tham số username để tránh tính nhầm tiền của tài khoản khác!
    🌟 VÁ LỖI 3: TÍNH ĐÚNG SỐ DƯ TỔNG ĐỂ KHỚP VỚI GIAO DIỆN BẤT CHẤP THÊM/XÓA
    """
    from services.bo_nao_ai import normalize_text
    text_clean = normalize_text(cau_noi)
    
    today = datetime.now()
    target_date = None
    pham_vi = "tháng này"
    
    if "hom nay" in text_clean:
        target_date = today.strftime("%Y-%m-%d")
        pham_vi = "hôm nay"
    elif "hom qua" in text_clean:
        target_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        pham_vi = "hôm qua"
    elif "hom kia" in text_clean:
        target_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        pham_vi = "hôm kia"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # --- BƯỚC 1: LẤY SỐ DƯ TỔNG TÍCH LŨY (Mọi thời đại, khớp 100% với góc trái Dashboard) ---
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Thu', 'income') AND username = ?", (username,))
    tong_thu_all = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Chi', 'expense') AND username = ?", (username,))
    tong_chi_all = cursor.fetchone()[0] or 0
    
    so_du_tong = tong_thu_all - tong_chi_all
    
    # --- BƯỚC 2: LẤY THỐNG KÊ RIÊNG THEO THÁNG/NGÀY ---
    if target_date:
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Chi', 'expense') AND date = ? AND username = ?", (target_date, username))
        tong_chi = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Thu', 'income') AND date = ? AND username = ?", (target_date, username))
        tong_thu = cursor.fetchone()[0] or 0
    else:
        thang_hien_tai = today.strftime("%Y-%m")
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Chi', 'expense') AND date LIKE ? AND username = ?", (f"{thang_hien_tai}%", username))
        tong_chi = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type IN ('Thu', 'income') AND date LIKE ? AND username = ?", (f"{thang_hien_tai}%", username))
        tong_thu = cursor.fetchone()[0] or 0
        
    conn.close()
    
    # Format số tiền chuẩn VNĐ
    so_du_tong_format = "{:,.0f}".format(so_du_tong)
    chi_format = "{:,.0f}".format(tong_chi)
    thu_format = "{:,.0f}".format(tong_thu)
    
    trang_thai = "còn dư" if so_du_tong >= 0 else "đang âm"
    emoji = "😊" if so_du_tong >= 0 else "😬"
    
    return (
        f"🏦 Số dư tổng (Tích lũy) của bạn {trang_thai}: {so_du_tong_format}đ {emoji}\n"
        f"-------------------\n"
        f"📊 Thống kê {pham_vi}:\n"
        f"   • Thu vào: {thu_format}đ\n"
        f"   • Chi ra: {chi_format}đ"
    )

# Các hàm phía dưới giữ nguyên của cậu...
def xu_ly_ngan_sach() -> str:
    return "💰 Trạng thái ngân sách: Bạn vẫn đang kiểm soát tốt, chưa bị 'cháy túi' đâu!"

def xu_ly_tu_van() -> str:
    from database.db import get_summary_by_category
    try:
        top_chi = get_summary_by_category("Chi")
        if not top_chi or len(top_chi) == 0:
            top_chi = get_summary_by_category("expense")
        if not top_chi or len(top_chi) == 0:
            return "🤔 Hiện tại mình chưa thấy dữ liệu chi tiêu nào trong tháng này để tư vấn cho bạn cả!"
        top_1 = top_chi[0]
        tien = top_1.get("total", 0)
        tien_format = "{:,.0f}".format(tien if tien else 0)
        phan_hoi = f"💡 Lời khuyên AI: Bạn đang 'đốt' nhiều tiền nhất vào mục '{top_1['category']}' với tổng {tien_format}đ.\n   Hãy tiết chế lại đam mê này nhé!"
        if len(top_chi) > 1:
            phan_hoi += "\n\n📋 Top danh mục chi tiêu:"
            for i, item in enumerate(top_chi[:3], start=1):
                val = item.get("total", 0)
                val_format = "{:,.0f}".format(val if val else 0)
                phan_hoi += f"\n   {i}. {item['category']} — {val_format}đ"
        return phan_hoi
    except Exception as e:
        return f"⚠️ Không thể phân tích dữ liệu tư vấn: {str(e)}"