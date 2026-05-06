from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Import các router từ thư mục routes
from routes.transaction import router as transaction_router
from routes.dashboard import router as dashboard_router  # <--- THIỆN ĐÃ MỞ KHÓA Ở ĐÂY[cite: 1]

from models.transaction import TransactionRequest, TransactionResponse

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Finance AI API")

# 2. Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Cắm các router vào hệ thống chính
app.include_router(transaction_router)
app.include_router(dashboard_router) # <--- THIỆN ĐÃ MỞ KHÓA Ở ĐÂY[cite: 1]

# 4. Cổng chào mặc định
@app.get("/")
def read_root():
    return {"message": "Hệ thống Backend Finance AI đã hoạt động thành công!"}

# 5. Đoạn code kiểm tra model
@app.post("/check-an", response_model=TransactionResponse)
def check_an(data: TransactionRequest):
    return data