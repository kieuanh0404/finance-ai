import re
from datetime import datetime, timedelta
from database.db import get_connection
from services.groq_service import goi_groq_tu_van


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
    print("🔥 DANG CHAY HAM TU VAN MOI")
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
    Tư vấn chi tiêu thông minh hơn:
    - Lấy tổng thu, tổng chi, số dư trong tháng hiện tại
    - Tìm danh mục chi nhiều nhất
    - Đưa ra lời khuyên theo tình hình tài chính thực tế
    """
    try:
        today = datetime.now()
        thang_hien_tai = today.strftime("%Y-%m")

        conn = get_connection()
        cursor = conn.cursor()

        # Tổng thu tháng này
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

        # Tổng chi tháng này
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

        # Top danh mục chi nhiều nhất
        cursor.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE username = ?
              AND type IN ('Chi', 'expense')
              AND date LIKE ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT 3
            """,
            (username, f"{thang_hien_tai}%")
        )
        rows = cursor.fetchall()
        conn.close()

        so_du = tong_thu - tong_chi

        thu_format = "{:,.0f}".format(tong_thu)
        chi_format = "{:,.0f}".format(tong_chi)
        so_du_format = "{:,.0f}".format(abs(so_du))

        if tong_thu > 0:
            ty_le_chi = tong_chi / tong_thu
            ty_le_tiet_kiem = max(0, so_du) / tong_thu
        else:
            ty_le_chi = 0
            ty_le_tiet_kiem = 0

        phan_hoi = (
            f"💡 Lời khuyên chi tiêu tháng này:\n"
            f"• Tổng thu: {thu_format}đ\n"
            f"• Tổng chi: {chi_format}đ\n"
        )

        if so_du >= 0:
            phan_hoi += f"• Số dư hiện tại: {so_du_format}đ\n"
        else:
            phan_hoi += f"• Bạn đang âm: {so_du_format}đ\n"

        if rows:
            phan_hoi += "\n📊 Danh mục chi nhiều nhất:"
            for i, row in enumerate(rows, start=1):
                category = row["category"]
                total = row["total"] or 0
                total_format = "{:,.0f}".format(total)
                phan_hoi += f"\n{i}. {category}: {total_format}đ"

        phan_hoi += "\n\n👉 Gợi ý: "

        if tong_thu == 0 and tong_chi == 0:
            phan_hoi += (
                "Bạn chưa có dữ liệu thu chi tháng này. Hãy nhập vài giao dịch "
                "như 'ăn phở 50k' hoặc 'nhận lương 3 triệu' để mình tư vấn chính xác hơn."
            )

        elif tong_thu == 0 and tong_chi > 0:
            phan_hoi += (
                "Bạn đang có chi tiêu nhưng chưa ghi nhận khoản thu nào. "
                "Bạn nên cập nhật thu nhập để hệ thống đánh giá tài chính chính xác hơn."
            )

        elif so_du < 0:
            phan_hoi += (
                "Tháng này bạn đang chi vượt thu nhập. Nên tạm dừng các khoản mua sắm không cần thiết "
                "và ưu tiên kiểm soát các danh mục chi nhiều nhất."
            )

        elif ty_le_chi <= 0.4:
            phan_hoi += (
                f"Bạn đang kiểm soát chi tiêu khá tốt, mới dùng khoảng {ty_le_chi * 100:.1f}% thu nhập. "
                f"Có thể dành khoảng {ty_le_tiet_kiem * 100:.1f}% thu nhập để tiết kiệm hoặc lập quỹ dự phòng."
            )

        elif ty_le_chi <= 0.7:
            phan_hoi += (
                f"Mức chi tiêu của bạn đang ở mức tương đối ổn, khoảng {ty_le_chi * 100:.1f}% thu nhập. "
                "Bạn nên đặt hạn mức cho các danh mục chi nhiều để giữ số dư cuối tháng."
            )

        else:
            phan_hoi += (
                f"Bạn đã dùng khoảng {ty_le_chi * 100:.1f}% thu nhập trong tháng. "
                "Nên giảm bớt các khoản chưa thật sự cần thiết và ưu tiên tiết kiệm trước khi mua sắm thêm."
            )

        context_data = {
        "tong_thu_thang": tong_thu,
        "tong_chi_thang": tong_chi,
        "so_du": so_du,
        "ty_le_chi": round(ty_le_chi * 100, 1),
        "ty_le_tiet_kiem": round(ty_le_tiet_kiem * 100, 1),
        "top_danh_muc_chi": [
            {
                "category": row["category"],
                "total": row["total"] or 0
            }
            for row in rows
        ],
    }

        prompt_tu_van = f"""
        Dựa trên dữ liệu tài chính tháng này của người dùng, hãy đưa ra lời khuyên chi tiêu thực tế.

        Yêu cầu:
        - Trả lời bằng tiếng Việt tự nhiên.
        - Tuyệt đối chỉ dùng tiếng Việt, không dùng tiếng Trung, tiếng Anh hoặc ký tự lạ.
        - Ngắn gọn nhưng đủ ý.
        - Nêu rõ tổng thu, tổng chi, số dư.
        - Nhận xét danh mục chi nhiều nhất.
        - Đưa 2-3 gợi ý hành động cụ thể.
        - Không bịa số liệu ngoài dữ liệu được cung cấp.

        Dữ liệu:
        {context_data}
        """

        phan_hoi_groq = goi_groq_tu_van(prompt_tu_van, context_data)

        if phan_hoi_groq:
            return phan_hoi_groq

        return phan_hoi

    except Exception as e:
        return f"⚠️ Không thể phân tích dữ liệu tư vấn: {str(e)}"