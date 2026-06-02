import re
from datetime import datetime, timedelta
from database.db import get_connection, get_summary_by_category


def lam_sach_ghi_chu_loi(note_raw: str) -> str:
    """
    Làm sạch ghi chú giao dịch: bỏ các từ rác như hôm nay, tớ mua, hết...
    """
    if not note_raw:
        return "Giao dịch"

    text = note_raw.lower().strip()

    cum_tu_rac = [
        r"\bhôm nay\b", r"\bhom nay\b",
        r"\bhôm qua\b", r"\bhom qua\b",
        r"\bhôm kia\b", r"\bhom kia\b",
        r"\bngày ngày\b", r"\bngay ngay\b",
        r"\btớ mua\b", r"\bto mua\b",
        r"\bmình mua\b", r"\bminh mua\b",
        r"\bmua hộ\b", r"\bmua ho\b",
        r"\bnhận được\b", r"\bnhan duoc\b",
        r"\bhết sạch\b", r"\bhet sach\b",
    ]

    for pattern in cum_tu_rac:
        text = re.sub(pattern, "", text)

    tu_don_rac = [
        "nay", "qua", "kia",
        "ngày", "ngay", "tháng", "thang", "năm", "nam",
        "tớ", "to", "mình", "minh", "bạn", "ban", "ta",
        "hết", "het", "mua", "bán", "ban", "nhận", "nhan",
        "trả", "tra", "tiêu", "tieu", "đốt", "dot",
        "đi", "di", "cho", "vào", "vao", "của", "cua",
        "hộ", "ho", "được", "duoc",
    ]

    words = text.split()
    clean_words = [w for w in words if w not in tu_don_rac]
    note_clean = " ".join(clean_words).strip()

    return note_clean.capitalize() if note_clean else "Giao dịch"


def xu_ly_them_moi(intent_data: dict) -> str:
    """
    Xử lý intent 'add': sinh phản hồi xác nhận thêm giao dịch.
    Hàm này KHÔNG lưu database.
    """
    danh_sach_gd = intent_data.get("data", [])

    if not danh_sach_gd:
        return "⚠️ Không tìm thấy giao dịch nào trong tin nhắn của bạn. Bạn thử nhập lại nhé!"

    if not isinstance(danh_sach_gd, list):
        danh_sach_gd = [danh_sach_gd]

    ket_qua = []

    for gd in danh_sach_gd:
        try:
            tien_format = "{:,.0f}".format(gd["amount"])
            type_raw = str(gd["type"]).lower()
            ghi_chu_sach = lam_sach_ghi_chu_loi(gd.get("note", ""))

            loai = "💸 Chi" if type_raw in ["chi", "expense"] else "💰 Thu"

            ket_qua.append(
                f"✅ {loai} {tien_format}đ — '{ghi_chu_sach}' (Danh mục: {gd['category']})"
            )

        except Exception as e:
            ket_qua.append(
                f"⚠️ Không xử lý được giao dịch '{gd.get('note', '?')}': {str(e)}"
            )

    return "\n".join(ket_qua)


def xu_ly_truy_van_nang_cao(cau_noi: str, username: str = "default_user") -> str:
    """
    Xử lý intent 'query': thống kê theo hôm nay / hôm qua / hôm kia / tháng này.
    Có lọc theo username để không lẫn dữ liệu tài khoản khác.
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

    if target_date:
        cursor.execute(
            """
            SELECT SUM(amount)
            FROM transactions
            WHERE username = ?
              AND type IN ('Chi', 'expense')
              AND date = ?
            """,
            (username, target_date)
        )
        tong_chi = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT SUM(amount)
            FROM transactions
            WHERE username = ?
              AND type IN ('Thu', 'income')
              AND date = ?
            """,
            (username, target_date)
        )
        tong_thu = cursor.fetchone()[0] or 0

    else:
        thang_hien_tai = today.strftime("%Y-%m")

        cursor.execute(
            """
            SELECT SUM(amount)
            FROM transactions
            WHERE username = ?
              AND type IN ('Chi', 'expense')
              AND date LIKE ?
            """,
            (username, f"{thang_hien_tai}%")
        )
        tong_chi = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT SUM(amount)
            FROM transactions
            WHERE username = ?
              AND type IN ('Thu', 'income')
              AND date LIKE ?
            """,
            (username, f"{thang_hien_tai}%")
        )
        tong_thu = cursor.fetchone()[0] or 0

    conn.close()

    con_lai = tong_thu - tong_chi

    chi_format = "{:,.0f}".format(tong_chi)
    thu_format = "{:,.0f}".format(tong_thu)
    con_lai_format = "{:,.0f}".format(abs(con_lai))

    trang_thai = "còn dư" if con_lai >= 0 else "đã âm"
    emoji = "😊" if con_lai >= 0 else "😬"

    return (
        f"📊 Thống kê tổng hợp {pham_vi}:\n"
        f"   • Tổng thu: {thu_format}đ\n"
        f"   • Tổng chi: {chi_format}đ\n"
        f"   • {emoji} Bạn {trang_thai} {con_lai_format}đ!"
    )


def xu_ly_ngan_sach() -> str:
    """
    Xử lý intent 'budget'.
    """
    return "💰 Trạng thái ngân sách: Bạn vẫn đang kiểm soát tốt, chưa bị 'cháy túi' đâu!"


def xu_ly_tu_van(username: str = None) -> str:
    """
    Xử lý intent 'advice': tư vấn dựa trên danh mục chi nhiều nhất.
    Có thể lọc theo username nếu được truyền vào.
    """
    try:
        top_chi = get_summary_by_category("Chi", username=username)

        if not top_chi or len(top_chi) == 0:
            top_chi = get_summary_by_category("expense", username=username)

        if not top_chi or len(top_chi) == 0:
            return "🤔 Hiện tại mình chưa thấy dữ liệu chi tiêu nào trong tháng này để tư vấn cho bạn cả!"

        top_1 = top_chi[0]
        tien = top_1.get("total", 0)
        tien_format = "{:,.0f}".format(tien if tien else 0)

        phan_hoi = (
            f"💡 Lời khuyên AI: Bạn đang chi nhiều nhất vào mục "
            f"'{top_1['category']}' với tổng {tien_format}đ.\n"
            f"   Bạn có thể cân nhắc đặt hạn mức cho danh mục này nhé!"
        )

        if len(top_chi) > 1:
            phan_hoi += "\n\n📋 Top danh mục chi tiêu:"
            for i, item in enumerate(top_chi[:3], start=1):
                val = item.get("total", 0)
                val_format = "{:,.0f}".format(val if val else 0)
                phan_hoi += f"\n   {i}. {item['category']} — {val_format}đ"

        return phan_hoi

    except Exception as e:
        return f"⚠️ Không thể phân tích dữ liệu tư vấn: {str(e)}"