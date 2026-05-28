from fastapi import APIRouter
from database import db


router = APIRouter(prefix="/api", tags=["Bảng điều khiển & Thống kê"])


@router.get("/statistics")
def read_statistics():
    """
    API lấy dữ liệu thống kê cho Module 2.
    """
    return db.get_dashboard_stats()
