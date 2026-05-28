import json
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from database import db

from services.bo_nao_ai import phan_tich_y_dinh
from services.chuyen_vien_xu_ly import (
    xu_ly_them_moi,
    xu_ly_truy_van_nang_cao,
    xu_ly_ngan_sach,
    xu_ly_tu_van,
    lam_sach_ghi_chu_loi
)

try:
    from services.gemini_service import client
except ImportError:
    client = None


router = APIRouter(prefix="/api/chatbot", tags=["Trợ Lý Tài Chính AI"])


class TinNhanNguoiDung(BaseModel):
    tin_nhan: str
    username: str = "default_user"
    lich_su: List[Any] = []
    giao_dich: List[Any] = []
    thong_ke: Dict[str, Any] = {}


@router.post("/chat")
def tro_ly_ai_nhan_tin(request: TinNhanNguoiDung):
    cau_noi = request.tin_nhan.strip()
    username = request.username.strip() if request.username else "default_user"

    # 1. Gọi bộ lọc phân loại ý định bằng Rules/Regex
    intent_data = phan_tich_y_dinh(cau_noi)
    y_dinh = intent_data.get("intent", "unknown")

    phan_hoi = ""
    du_lieu_giao_dich = []

    # 2. Xử lý nghiệp vụ theo quy tắc cứng
    if y_dinh == "add":
        # Hàm này chỉ sinh câu phản hồi, KHÔNG insert DB
        phan_hoi = xu_ly_them_moi(intent_data)

        data = intent_data.get("data", [])
        if not isinstance(data, list):
            data = [data]

        for gd in data:
            ghi_chu_sach_rules = lam_sach_ghi_chu_loi(gd.get("note", ""))

            real_id = db.insert_transaction(
                username=username,
                type=gd["type"],
                amount=gd["amount"],
                category=gd["category"],
                date=gd["date"],
                note=ghi_chu_sach_rules
            )

            gd_copy = gd.copy()
            gd_copy["id"] = real_id
            gd_copy["note"] = ghi_chu_sach_rules
            gd_copy["username"] = username
            du_lieu_giao_dich.append(gd_copy)

    elif y_dinh == "query":
        phan_hoi = xu_ly_truy_van_nang_cao(cau_noi, username=username)

    elif y_dinh == "budget":
        phan_hoi = xu_ly_ngan_sach()

    elif y_dinh == "advice":
        phan_hoi = xu_ly_tu_van()

    # 3. Fallback Gemini nếu Rules không hiểu
    if not phan_hoi or y_dinh in ["unknown", "chat"]:
        if not client:
            return {
                "trang_thai": "thanh_cong",
                "y_dinh": "chat",
                "phan_hoi": "Mình chưa hiểu rõ ý bạn. Bạn thử nhập kiểu: 'ăn phở 50k' hoặc 'tổng chi hôm nay bao nhiêu' nhé!",
                "du_lieu_giao_dich": []
            }

        try:
            hien_tai = datetime.now().strftime("%Y-%m-%d")

            prompt = f"""
Bạn là Trợ lý Tài chính thông minh. Người dùng chat: "{cau_noi}"
Tài khoản hiện tại: "{username}"
Ngữ cảnh ví hiện tại: {request.thong_ke}

Nhiệm vụ:
1. Nếu câu chat là một giao dịch tài chính, hãy bóc tách dữ liệu.
2. Nếu không phải giao dịch, hãy trả lời tự nhiên, ngắn gọn bằng tiếng Việt.
3. Chỉ trả về CHUỖI JSON DUY NHẤT, không bọc trong ```json.

Cấu trúc JSON bắt buộc:
{{
    "phan_hoi": "Câu trả lời thân thiện",
    "is_transaction": true hoặc false,
    "data": {{
        "amount": số tiền dạng số,
        "category": "Ăn uống hoặc Di chuyển hoặc Giải trí hoặc Thể thao hoặc Học tập & Công việc hoặc Lương hoặc Mua sắm",
        "type": "expense hoặc income",
        "date": "{hien_tai}",
        "note": "ghi chú khoản tiền"
    }}
}}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            res_dict = json.loads(clean_json)

            phan_hoi = res_dict.get("phan_hoi", "")

            if res_dict.get("is_transaction") and res_dict.get("data"):
                gd = res_dict["data"]

                ghi_chu_sach_gemini = lam_sach_ghi_chu_loi(gd.get("note", ""))

                db_type = "Chi" if gd.get("type") == "expense" else "Thu"

                real_id = db.insert_transaction(
                    username=username,
                    type=db_type,
                    amount=gd["amount"],
                    category=gd["category"],
                    date=gd.get("date", hien_tai),
                    note=ghi_chu_sach_gemini
                )

                gd_copy = {
                    "id": real_id,
                    "username": username,
                    "type": db_type,
                    "amount": gd["amount"],
                    "category": gd["category"],
                    "date": gd.get("date", hien_tai),
                    "note": ghi_chu_sach_gemini
                }

                du_lieu_giao_dich.append(gd_copy)
                y_dinh = "add"

        except Exception as e:
            print(f"❌ Lỗi luồng Gemini Router: {str(e)}")
            phan_hoi = "Mình đang suy nghĩ một chút, bạn thử lại câu khác nhé! 😅"
            y_dinh = "unknown"

    return {
        "trang_thai": "thanh_cong",
        "y_dinh": y_dinh,
        "phan_hoi": phan_hoi,
        "du_lieu_giao_dich": du_lieu_giao_dich
    }