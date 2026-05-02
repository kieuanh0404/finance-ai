from pydantic import BaseModel
from typing import Optional

# Dinh nghia du lieu gui len khi tao giao dich (Request)
class TransactionRequest(BaseModel):
    type: str          # "Thu" hoac "Chi"
    amount: float      # So tien giao dich
    category: str      # Danh muc (An uong, Di chuyen, Luong, Mua sam...)
    date: str          # Đinh dang YYYY-MM-DD
    note: Optional[str] = None # Ghi chu co the de trong

# Dinh nghia du lieu tra ve sau khi tao/lay giao dich (Response)
class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    category: str
    date: str
    note: Optional[str]

    class Config:
        from_attributes = True # Cho phep chuyen doi tu dict/sqlite row sang model