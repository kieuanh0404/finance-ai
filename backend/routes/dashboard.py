from fastapi import APIRouter
from database import db # Kết nối tới database

# CỰC KỲ QUAN TRỌNG: Tên biến phải là 'router' (viết thường hết)
router = APIRouter(prefix="/api", tags=["Bảng điều khiển & Thống kê"])

@router.get("/statistics")
def read_statistics():
    """
    API lấy dữ liệu thống kê cho Module 2.
    """
    return db.get_dashboard_stats()