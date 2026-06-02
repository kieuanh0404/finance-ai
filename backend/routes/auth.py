import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.db import get_connection

router = APIRouter(prefix="/api/auth", tags=["Xác thực Người dùng"])


class ThongTinTaiKhoan(BaseModel):
    name: str
    pass_word: str


@router.post("/register")
def dang_ky_tai_khoan(user: ThongTinTaiKhoan):
    """API ĐĂNG KÝ"""
    username = user.name.strip()
    password = user.pass_word.strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Không được để trống tên hoặc mật khẩu!")

    conn = get_connection()
    cursor = conn.cursor()

    # Tạo bảng users nếu chưa tồn tại
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """
    )
    conn.commit()

    # Kiểm tra tài khoản tồn tại chưa
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Tài khoản này đã tồn tại rồi sếp ơi!")

    # Chèn user mới vào hệ thống
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Đăng ký tài khoản thành công!"}


@router.post("/login")
def dang_nhap_tai_khoan(user: ThongTinTaiKhoan):
    """API ĐĂNG NHẬP"""
    username = user.name.strip()
    password = user.pass_word.strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Đảm bảo bảng users tồn tại
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """
    )
    conn.commit()

    # Xác thực tài khoản mật khẩu
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    found_user = cursor.fetchone()
    conn.close()

    if not found_user:
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu rồi!")

    return {"status": "success", "message": "Đăng nhập thành công!", "username": username}
