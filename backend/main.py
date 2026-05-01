from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Finance AI API")

# Cấu hình CORS để Frontend (HTML/JS) gọi API không bị lỗi chặn bảo mật
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi nguồn gọi tới (phù hợp lúc làm đồ án)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE...
    allow_headers=["*"],
)

# Cổng chào mặc định để kiểm tra server có chạy hay không
@app.get("/")
def read_root():
    return {"message": "Hệ thống Backend Finance AI đã hoạt động thành công!"}