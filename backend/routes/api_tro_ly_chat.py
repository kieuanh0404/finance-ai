from fastapi import APIRouter
from pydantic import BaseModel

# Import đúng tên hàm từ file 126 dòng của bạn
from services.bo_nao_ai import phan_tich_y_dinh
from services.chuyen_vien_xu_ly import handle_chatbot 

# Khởi tạo Router
router = APIRouter(prefix="/api/chatbot", tags=["Trợ Lý Tài Chính AI"])

class TinNhanNguoiDung(BaseModel):
    tin_nhan: str

@router.post("/chat")
def tro_ly_ai_nhan_tin(request: TinNhanNguoiDung):
    cau_noi = request.tin_nhan.strip()
    
    # 1. Dùng bộ não AI để phân tích ý định
    intent_data = phan_tich_y_dinh(cau_noi)
    
    # 2. Gọi hàm điều phối tổng (handle_chatbot) mà bạn đã viết ở dòng 126
    # Hàm này của bạn đã tự phân chia report/budget/gemini rồi
    phan_hoi = handle_chatbot(intent_data)

    return {
        "trang_thai": "thanh_cong",
        "y_dinh": intent_data.get("intent"),
        "phan_hoi": phan_hoi
    }