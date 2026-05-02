from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Import các router từ thư mục routes
from routes.transaction import router as transaction_router
# Tạm thời comment dòng dưới lại, bao giờ Kiều Anh code xong file dashboard.py thì mở ra
# from routes.dashboard import router as dashboard_router 

from models.transaction import TransactionRequest, TransactionResponse

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Finance AI API")

# 2. Cấu hình CORS (Nên đặt ngay sau khi khởi tạo app để có tác dụng với mọi Router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi nguồn gọi tới (phù hợp lúc làm đồ án)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE...
    allow_headers=["*"],
)

# 3. Cắm các router vào hệ thống chính
app.include_router(transaction_router)
# app.include_router(dashboard_router) # Mở comment dòng này khi xong phần thống kê

# 4. Cổng chào mặc định để kiểm tra server
@app.get("/")
def read_root():
    return {"message": "Hệ thống Backend Finance AI đã hoạt động thành công!"}

# 5. Đoạn code này để An kiểm tra xem Model có chạy không
@app.post("/check-an", response_model=TransactionResponse)
def check_an(data: TransactionRequest):
    return data