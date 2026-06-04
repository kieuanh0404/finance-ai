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
    lam_sach_ghi_chu_loi,
)

try:
    from services.groq_service import client
except ImportError:
    client = None


router = APIRouter(prefix="/api/chatbot", tags=["Trợ Lý Tài Chính AI"])


class TinNhanNguoiDung(BaseModel):
    tin_nhan: str
    username: str = "default_user"
    lich_su: List[Any] = []
    giao_dich: List[Any] = []
    thong_ke: Dict[str, Any] = {}


def la_cau_hoi_tu_van(cau_noi: str) -> bool:
    """
    Nhận diện câu hỏi xin lời khuyên/quyết định.
    Các câu này KHÔNG được lưu thành giao dịch dù có số tiền.
    """
    text = cau_noi.lower()

    tu_khoa_tu_van = [
        "có nên",
        "co nen",
        "nên không",
        "nen khong",
        "nên mua",
        "nen mua",
        "có nên mua",
        "co nen mua",
        "có đáng",
        "co dang",
        "đáng mua",
        "dang mua",
        "hợp lý không",
        "hop ly khong",
        "ổn không",
        "on khong",
        "được không",
        "duoc khong",
        "có được không",
        "co duoc khong",
        "nên làm gì",
        "nen lam gi",
        "chi tiêu như nào",
        "chi tieu nhu nao",
        "chi tiêu thế nào",
        "chi tieu the nao",
        "mua sắm thoải mái",
        "mua sam thoai mai",
        "thoải mái không",
        "thoai mai khong",
        "đầu tư",
        "dau tu",
        "gửi tiết kiệm",
        "gui tiet kiem",
        "so sánh",
        "so sanh",
        "nên chọn",
        "nen chon",
        "cái nào tốt hơn",
        "cai nao tot hon",
        "cái nào hợp lý hơn",
        "cai nao hop ly hon",
    ]

    return any(kw in text for kw in tu_khoa_tu_van)


@router.post("/chat")
def tro_ly_ai_nhan_tin(request: TinNhanNguoiDung):
    cau_noi = request.tin_nhan.strip()
    username = request.username.strip() if request.username else "default_user"

    intent_data = phan_tich_y_dinh(cau_noi)
    y_dinh = intent_data.get("intent", "unknown")

    phan_hoi = ""
    du_lieu_giao_dich = []

    # Chặn sớm: nếu là câu hỏi tư vấn thì không cho rule-based lưu giao dịch
    if la_cau_hoi_tu_van(cau_noi):
        y_dinh = "chat"

    if y_dinh == "add":
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
                note=ghi_chu_sach_rules,
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
        phan_hoi = xu_ly_tu_van(username=username)

    if not phan_hoi or y_dinh in ["unknown", "chat"]:
        if not client:
            return {
                "trang_thai": "thanh_cong",
                "y_dinh": "chat",
                "phan_hoi": "Mình chưa hiểu rõ ý bạn. Bạn thử nhập kiểu: 'ăn phở 50k' hoặc 'tổng chi hôm nay bao nhiêu' nhé!",
                "du_lieu_giao_dich": [],
            }

        try:
            hien_tai = datetime.now().strftime("%Y-%m-%d")

            prompt = f"""
Bạn là Trợ lý Tài chính thông minh. Người dùng chat: "{cau_noi}"
Tài khoản hiện tại: "{username}"
Ngữ cảnh ví hiện tại: {request.thong_ke}

Nhiệm vụ:
1. Nếu người dùng nói họ ĐÃ chi/ĐÃ nhận tiền, hãy bóc tách giao dịch.
2. Nếu người dùng đang hỏi ý kiến như "có nên", "nên không", "hợp lý không", "mua được không", "nên", "có đủ" thì KHÔNG coi là giao dịch.
3. Nếu không phải giao dịch, hãy trả lời tự nhiên đưa ra lời khuyên dựa trên số dư tổng, hài hước, ngắn gọn bằng tiếng Việt.
4. Chỉ trả về CHUỖI JSON DUY NHẤT, không bọc trong ```json.
5. Nếu không phải giao dịch thì "is_transaction" là false và "data" là null.

Cấu trúc JSON bắt buộc:
{{
    "phan_hoi": "Câu trả lời thân thiện",
    "is_transaction": true hoặc false,
    "data": {{
        "amount": số tiền dạng số,
        "category": "Ăn uống hoặc Di chuyển hoặc Giải trí hoặc Thể thao hoặc Học tập & Công việc hoặc Lương hoặc Mua sắm hoặc Khác",
        "type": "expense hoặc income",
        "date": "{hien_tai}",
        "note": "ghi chú khoản tiền"
    }}
}}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            clean_json = response.choices[0].message.content
            clean_json = clean_json.replace("```json", "").replace("```", "").strip()

            try:
                res_dict = json.loads(clean_json)
            except json.JSONDecodeError:
                phan_hoi = clean_json
                y_dinh = "chat"
                return {
                    "trang_thai": "thanh_cong",
                    "y_dinh": y_dinh,
                    "phan_hoi": phan_hoi,
                    "du_lieu_giao_dich": [],
                }

            phan_hoi = res_dict.get("phan_hoi", "")

            # Chặn lần 2:
            # Nếu là câu hỏi tư vấn thì dù Groq trả is_transaction=true cũng KHÔNG lưu DB.
            if (
                res_dict.get("is_transaction")
                and res_dict.get("data")
                and not la_cau_hoi_tu_van(cau_noi)
            ):
                gd = res_dict["data"]

                ghi_chu_sach_groq = lam_sach_ghi_chu_loi(gd.get("note", ""))

                db_type = "Chi" if gd.get("type") == "expense" else "Thu"

                real_id = db.insert_transaction(
                    username=username,
                    type=db_type,
                    amount=gd["amount"],
                    category=gd["category"],
                    date=gd.get("date", hien_tai),
                    note=ghi_chu_sach_groq,
                )

                gd_copy = {
                    "id": real_id,
                    "username": username,
                    "type": db_type,
                    "amount": gd["amount"],
                    "category": gd["category"],
                    "date": gd.get("date", hien_tai),
                    "note": ghi_chu_sach_groq,
                }

                du_lieu_giao_dich.append(gd_copy)
                y_dinh = "add"
            else:
                y_dinh = "chat"

        except Exception as e:
            print(f"❌ Lỗi luồng Groq Router: {str(e)}")
            phan_hoi = "Mình đang suy nghĩ một chút, bạn thử lại câu khác nhé! 😅"
            y_dinh = "unknown"

    return {
        "trang_thai": "thanh_cong",
        "y_dinh": y_dinh,
        "phan_hoi": phan_hoi,
        "du_lieu_giao_dich": du_lieu_giao_dich,
    }