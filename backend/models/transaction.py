from pydantic import BaseModel
from typing import Optional

# Dinh nghia du lieu gui len khi tao giao dich (Request)
class TransactionRequest(BaseModel):
    type: str          # "Thu" hoặc "Chi"
    amount: float      # Số tiền giao dịch
    category: str      # Danh mục (Ăn uống, Di chuyển, Lương, Mua sắm...)
    date: str          # Định dạng YYYY-MM-DD
    note: Optional[str] = None # Ghi chú có thể để trống

# Dinh nghia du lieu tra ve sau khi tao/lấy giao dich (Response)
class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    category: str
    date: str
    note: Optional[str]

    class Config:
        from_attributes = True # Cho phep chuyen doi tu dict/sqlite row sang model