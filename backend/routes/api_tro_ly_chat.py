from fastapi import APIRouter
from pydantic import BaseModel

from services.bo_nao_ai import phan_tich_y_dinh
from services.chuyen_vien_xu_ly import xu_ly_them_moi, xu_ly_truy_van, xu_ly_ngan_sach, xu_ly_tu_van

# Khởi tạo Router cho phần Chatbot
router = APIRouter(prefix="/api/chatbot", tags=["Trợ Lý Tài Chính AI"])

# Khuôn mẫu quy định Frontend sẽ gửi lên dữ liệu gì (Chỉ cần 1 câu text)
class TinNhanNguoiDung(BaseModel):
    tin_nhan: str

@router.post("/chat")
def tro_ly_ai_nhan_tin(request: TinNhanNguoiDung):
    cau_noi = request.tin_nhan.strip()
    
    intent_data = phan_tich_y_dinh(cau_noi)
    y_dinh = intent_data["intent"]
    
    if y_dinh == "add":
        phan_hoi = xu_ly_them_moi(intent_data)
    elif y_dinh == "query":
        phan_hoi = xu_ly_truy_van()
    elif y_dinh == "budget":
        phan_hoi = xu_ly_ngan_sach()
    elif y_dinh == "advice":
        phan_hoi = xu_ly_tu_van()
    else:
        phan_hoi = "Câu này khó quá, bạn có thể nhập rõ số tiền (VD: đổ xăng 50k) hoặc hỏi về 'tổng chi', 'lời khuyên' được không?"

    return {
        "trang_thai": "thanh_cong",
        "y_dinh": y_dinh,
        "phan_hoi": phan_hoi
    }
