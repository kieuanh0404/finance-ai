from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db

from routes.transaction import router as transaction_router
from routes.dashboard import router as dashboard_router
from routes.api_tro_ly_chat import router as chat_router
from routes.auth import router as auth_router

from models.transaction import TransactionRequest, TransactionResponse

# Khởi tạo database
init_db()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Finance AI API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cắm router
app.include_router(transaction_router)
app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(auth_router)


@app.get("/")
def read_root():
    """Điểm khởi động mặc định của API."""
    return {"message": "Hệ thống Backend Finance AI đã hoạt động thành công!"}


@app.post("/check-an", response_model=TransactionResponse)
def check_an(data: TransactionRequest):
    """API test model."""
    return data
