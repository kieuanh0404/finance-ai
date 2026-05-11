from database.db import insert_transaction, get_total_amount, get_summary_by_category


def xu_ly_them_moi(intent_data: dict) -> str:
    """
    Xử lý intent 'add': lưu toàn bộ giao dịch vào DB và trả về phản hồi.
    FIX: intent_data["data"] là một LIST các giao dịch, không phải dict phẳng.
    """
    danh_sach_gd = intent_data.get("data", [])

    if not danh_sach_gd:
        return "⚠️ Không tìm thấy giao dịch nào trong tin nhắn của bạn. Bạn thử nhập lại nhé!"

    ket_qua = []

    for gd in danh_sach_gd:
        try:
            insert_transaction(
                gd["type"],
                gd["amount"],
                gd["category"],
                gd["date"],
                gd["note"]
            )
            tien_format = "{:,.0f}".format(gd["amount"])
            loai = "💸 Chi" if gd["type"] == "Chi" else "💰 Thu"
            ket_qua.append(
                f"✅ {loai} {tien_format}đ — '{gd['note']}' (Danh mục: {gd['category']})"
            )
        except Exception as e:
            ket_qua.append(f"⚠️ Không lưu được giao dịch '{gd.get('note', '?')}': {str(e)}")

    return "\n".join(ket_qua)


def xu_ly_truy_van() -> str:
    """
    Xử lý intent 'query': thống kê tổng chi tiêu từ trước đến nay.
    """
    try:
        tong_chi = get_total_amount("Chi") or 0
        tong_thu = get_total_amount("Thu") or 0
        con_lai = tong_thu - tong_chi

        chi_format = "{:,.0f}".format(tong_chi)
        thu_format = "{:,.0f}".format(tong_thu)
        con_lai_format = "{:,.0f}".format(abs(con_lai))

        trang_thai = "còn dư" if con_lai >= 0 else "đã âm"
        emoji = "😊" if con_lai >= 0 else "😬"

        return (
            f"📊 Thống kê tổng hợp:\n"
            f"   • Tổng thu: {thu_format}đ\n"
            f"   • Tổng chi: {chi_format}đ\n"
            f"   • {emoji} Bạn {trang_thai} {con_lai_format}đ!"
        )
    except Exception as e:
        return f"⚠️ Không thể truy vấn dữ liệu: {str(e)}"


def xu_ly_ngan_sach() -> str:
    """
    Xử lý intent 'budget': phản hồi về tình trạng ngân sách.
    (Tính năng đầy đủ có thể mở rộng sau.)
    """
    return "💰 Trạng thái ngân sách: Bạn vẫn đang kiểm soát tốt, chưa bị 'cháy túi' đâu!"


def xu_ly_tu_van() -> str:
    """
    Xử lý intent 'advice': lấy top danh mục chi tiêu và đưa ra lời khuyên.
    """
    try:
        top_chi = get_summary_by_category("Chi")
        if not top_chi or len(top_chi) == 0:
            return "🤔 Hiện tại mình chưa thấy dữ liệu chi tiêu nào trong tháng này để tư vấn cho bạn cả!"

        top_1 = top_chi[0]
        tien = top_1.get("total", 0)
        tien_format = "{:,.0f}".format(tien if tien else 0)

        phan_hoi = (
            f"💡 Lời khuyên AI: Bạn đang 'đốt' nhiều tiền nhất vào mục "
            f"'{top_1['category']}' với tổng {tien_format}đ.\n"
            f"   Hãy tiết chế lại đam mê này nhé!"
        )

        # Bonus: liệt kê top 3 nếu có
        if len(top_chi) > 1:
            phan_hoi += "\n\n📋 Top danh mục chi tiêu:"
            for i, item in enumerate(top_chi[:3], start=1):
                phan_hoi += "\n   {}. {} — {:,.0f}đ".format(i, item["category"], item["total"])

        return phan_hoi

    except Exception as e:
        return f"⚠️ Không thể phân tích dữ liệu: {str(e)}"
def handle_chatbot(intent_data: dict) -> str:
    """
    Hàm điều phối chính: Nhận intent từ Gemini và gọi hàm xử lý tương ứng.
    """
    intent = intent_data.get("intent", "unknown")
    
    if intent == "add":
        return xu_ly_them_moi(intent_data)
    elif intent == "query":
        return xu_ly_truy_van()
    elif intent == "budget":
        return xu_ly_ngan_sach()
    elif intent == "advice":
        return xu_ly_tu_van()
    else:
        return "🤖 Xin lỗi, mình chưa hiểu ý bạn. Bạn có thể nói rõ hơn về việc thu hay chi không?"