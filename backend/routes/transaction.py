from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from database import db
from models.transaction import TransactionRequest, TransactionResponse

router = APIRouter(prefix="/api", tags=["Quản lý Giao dịch"])


@router.post("/transactions")
def add_transaction(transaction: TransactionRequest):
    """API Thêm giao dịch (Trả về ID thật để Frontend dùng khi Xóa/Sửa)"""
    real_id = db.insert_transaction(
        username=transaction.username,
        type=transaction.type,
        amount=transaction.amount,
        category=transaction.category,
        date=transaction.date,
        note=transaction.note,
    )
    return {"status": "success", "message": "Thêm giao dịch thành công!", "id": real_id}


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(username: str = Query(...)):
    """API Lấy danh sách lịch sử (Tương ứng: GET /transactions)"""
    return db.get_all_transactions(username)


@router.get("/transactions/filter", response_model=List[TransactionResponse])
def filter_transactions_api(
    username: str = Query(...),
    transaction_type: Optional[str] = Query(None, alias="type", description="Lọc theo 'Thu' hoặc 'Chi'"),
    start_date: Optional[str] = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Đến ngày (YYYY-MM-DD)"),
):
    """API Lọc dữ liệu (Tương ứng: GET /transactions/filter)"""
    data = db.filter_transactions(
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
    )
    return data


@router.delete("/transactions/{transaction_id}")
def delete_transaction_api(transaction_id: int, username: str = Query(...)):
    """API Xóa giao dịch"""
    deleted_count = db.delete_transaction(transaction_id, username)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch!")

    return {"status": "success", "message": "Đã xóa giao dịch thành công"}
