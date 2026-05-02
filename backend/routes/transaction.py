from fastapi import APIRouter, Query
from typing import List, Optional

# Import các file đã thống nhất của team
from database import db
from models.transaction import TransactionRequest, TransactionResponse

# Tạo bộ định tuyến cho các API giao dịch
router = APIRouter(prefix="/api", tags=["Quản lý Giao dịch"])

# 1. API Thêm giao dịch (Tương ứng: POST /add-transaction)
@router.post("/add-transaction")
def add_transaction(transaction: TransactionRequest):
    # Gọi hàm insert_transaction từ file db.py
    db.insert_transaction(
        type=transaction.type,
        amount=transaction.amount,
        category=transaction.category,
        date=transaction.date,
        note=transaction.note
    )
    return {
        "status": "success", 
        "message": "Thêm giao dịch thành công!"
    }

# 2. API Lấy danh sách lịch sử (Tương ứng: GET /transactions)
# Dùng response_model để FastAPI tự động ép kiểu dữ liệu trả về theo TransactionResponse
@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions():
    # Gọi hàm get_all_transactions từ file db.py
    data = db.get_all_transactions()
    return data

# 3. API Lọc dữ liệu (Tương ứng: GET /transactions/filter)
@router.get("/transactions/filter", response_model=List[TransactionResponse])
def filter_transactions_api(
    # Lấy các tham số từ trên thanh URL (Query parameter)
    transaction_type: Optional[str] = Query(None, alias="type", description="Lọc theo 'Thu' hoặc 'Chi'"),
    start_date: Optional[str] = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Đến ngày (YYYY-MM-DD)")
):
    # Gọi hàm filter_transactions từ file db.py
    data = db.filter_transactions(
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    return data