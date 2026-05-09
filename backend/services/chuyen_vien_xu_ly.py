from database import db
from datetime import datetime
from .gemini_service import goi_gemini_tu_van

# --- HELPER: Hàm lấy thông tin chi tiêu sâu ---
def get_detailed_stats():
    """Lấy dữ liệu chi tiêu tháng hiện tại và phân tích category."""
    all_data = db.get_all_transactions()
    thang_nay = datetime.now().strftime("%Y-%m")
    gd_thang_nay = [item for item in all_data if item['date'].startswith(thang_nay) and item['type'] == 'Chi']
    
    if not gd_thang_nay:
        return None, 0, {}

    stats = {}
    for gd in gd_thang_nay:
        cat = gd['category']
        stats[cat] = stats.get(cat, 0) + gd['amount']
    
    tong_chi = sum(stats.values())
    max_cat = max(stats, key=stats.get) if stats else None
    
    return tong_chi, max_cat, stats

# --- CÁC HÀM CHỨC NĂNG 6 NÂNG CẤP ---

def check_budget():
    """6.1 Cảnh báo ngân sách thông minh (Upgrade: Có ngữ cảnh và lời khuyên cụ thể)."""
    tong_chi, max_cat, stats = get_detailed_stats()
    
    if not tong_chi:
        return "Hiện tại mình chưa thấy dữ liệu chi tiêu nào trong tháng này để đánh giá ngân sách cho bạn."

    warnings = []
    for cat, amount in stats.items():
        ty_trong = (amount / tong_chi) * 100
        if ty_trong > 40:
            # Upgrade: Thêm ví dụ cụ thể cho từng category để tăng tính AI
            advice_map = {
                "Ăn uống": "Bạn nên hạn chế đặt đồ ăn ngoài hoặc trà sữa.",
                "Mua sắm": "Hãy xem xét lại các món đồ trong giỏ hàng Shopee nhé.",
                "Giải trí": "Có vẻ tháng này bạn 'vui chơi' hơi quá đà rồi đấy.",
                "Di chuyển": "Thử kiểm tra xem có thể tối ưu hóa lộ trình đi lại không."
            }
            advice = advice_map.get(cat, "Bạn nên cân nhắc điều chỉnh lại khoản này.")
            warnings.append(f"- **{cat}** đang chiếm {ty_trong:.1f}% tổng chi ({amount:,.0f}đ). {advice}")

    if warnings:
        return "⚠️ **Cảnh báo ngân sách:**\n" + "\n".join(warnings)
    return "✅ Ngân sách của bạn đang được kiểm soát rất tốt, không có hạng mục nào chi tiêu quá mức 40%."

def generate_advice():
    """6.2 Đưa ra lời khuyên (Upgrade: Phân tích dựa trên category chi nhiều nhất)."""
    tong_chi, max_cat, stats = get_detailed_stats()
    
    # Lấy thêm thông tin thu nhập để tính số dư
    all_data = db.get_all_transactions()
    tong_thu = sum(item['amount'] for item in all_data if item['type'] == 'Thu')
    so_du = tong_thu - tong_chi

    if not max_cat:
        return "Hãy bắt đầu nhập liệu để mình có thể đưa ra lời khuyên tài chính cá nhân hóa cho bạn nhé!"

    if so_du < 0:
        return f"🚨 Tình hình khá căng thẳng! Bạn đang chi vượt thu. Đặc biệt là khoản **{max_cat}** đang chiếm tỉ trọng lớn nhất. Hãy ưu tiên cắt giảm mục này ngay lập tức để cân bằng lại tài chính."
    
    if max_cat == "Ăn uống" and (stats[max_cat] / tong_chi) > 0.3:
        return f"💡 Lời khuyên: Bạn chi khá đậm cho **{max_cat}**. Việc tự nấu ăn tại nhà có thể giúp bạn tiết kiệm được một khoản đáng kể cho quỹ dự phòng đấy!"
    
    return f"🌟 Tình hình tài chính của bạn đang ổn định. Bạn đang chi nhiều nhất cho **{max_cat}**, hãy tiếp tục duy trì việc theo dõi để không bị mất kiểm soát nhé."

def generate_report():
    """6.3 Tạo báo cáo (Upgrade: Có nhận xét, highlight vấn đề và số dư)."""
    tong_chi, max_cat, stats = get_detailed_stats()
    all_data = db.get_all_transactions()
    thang_nay = datetime.now().strftime("%Y-%m")
    
    thu = sum(item['amount'] for item in all_data if item['date'].startswith(thang_nay) and item['type'] == 'Thu')
    so_du = thu - tong_chi
    
    status_icon = "📉" if so_du < 0 else "📈"
    
    report = f"""
📊 **BÁO CÁO TÀI CHÍNH THÁNG {datetime.now().month}**
---
- 💰 **Tổng Thu:** {thu:,.0f}đ
- 💸 **Tổng Chi:** {tong_chi:,.0f}đ
- {status_icon} **Số dư hiện tại:** {so_du:,.0f}đ
---
🔍 **Phân tích nhanh:**
- Hạng mục 'ngốn' tiền nhất: **{max_cat if max_cat else 'Chưa có'}**
- Nhận xét: {('Bạn cần tiết kiệm hơn vì số dư đang âm!' if so_du < 0 else 'Bạn đang quản lý tiền rất tốt.')}
"""
    return report

def handle_chatbot(intent_data):
    """
    6.4 Điều phối trợ lý: 
    ƯU TIÊN TUYỆT ĐỐI RULES -> CHỈ GỌI GEMINI KHI KHÔNG KHỚP RULES.
    """
    # 1. Lấy dữ liệu đầu vào từ Module 3
    raw_text = intent_data.get("raw_text", "").lower()
    y_dinh = intent_data.get("intent") # Ý định đã được bóc tách từ FinanceAgent

    # 2. TẦNG RULES: Kiểm tra các từ khóa quan trọng (Đảm bảo Rules luôn chạy trước)
    # Quy tắc Báo cáo
    if y_dinh in ["report", "query"] or any(k in raw_text for k in ["báo cáo", "tổng kết", "thống kê", "chi bao nhiêu"]):
        return generate_report()
    
    # Quy tắc Ngân sách
    if y_dinh == "budget" or any(k in raw_text for k in ["ngân sách", "cảnh báo", "vượt mức", "vượt 40%"]):
        return check_budget()

    # Quy tắc Lời khuyên mặc định (Rule-based)
    # Nếu bạn muốn lời khuyên từ Rules trước, hãy để nó ở đây. 
    # Nếu muốn lời khuyên linh hoạt từ AI ngay, hãy bỏ qua khối if này.
    if any(k in raw_text for k in ["nên làm gì", "tiết kiệm thế nào"]) and "tư vấn" not in raw_text:
        return generate_advice()

    # 3. TẦNG CẦU CỨU GEMINI (Chỉ chạy khi không khớp các Rules trên)
    # Lấy ngữ cảnh thực tế từ Database để Gemini trả lời "khôn" hơn
    tong_chi, max_cat, _ = get_detailed_stats()
    ngu_canh = f"Tháng này bạn chi {tong_chi:,.0f}đ. Mục chi đậm nhất là {max_cat}."
    
    # Gọi sang gemini_service bạn đã tạo
    return goi_gemini_tu_van(raw_text, ngu_canh)