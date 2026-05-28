import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finance_ai.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Tao bang transactions
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,         -- Thu hoac Chi
            amount REAL NOT NULL,       -- So tien
            category TEXT NOT NULL,     -- Danh mmuc (an uong,di chuyen, giai tri,mua sam...)
            date TEXT NOT NULL,         -- NgNgay thang (YYYY-MM-DD)
            note TEXT                   -- Ghi chu
        )
    ''')
    conn.commit()
    conn.close()

# Ham insert: Them giao dich moi
def insert_transaction(username, type, amount, category, date, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (username, type, amount, category, date, note)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, type, amount, category, date, note))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

# Ham get-all: Lay toan bo lich su(sap xep moi nhat truoc)
def get_all_transactions(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM transactions WHERE username = ? ORDER BY date DESC, id DESC',
        (username,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Ham filter: Loc theo loai giao dich, khoang thoi gian
def filter_transactions(transaction_type=None, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if transaction_type:
        query += " AND type = ?"
        params.append(transaction_type)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 🌟 FIX SỬA LỖI TÍNH SAI TIỀN: Giới hạn tính tổng trong tháng hiện tại (YYYY-MM)
def get_total_amount(type_input):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy chuỗi tháng năm hiện tại (Ví dụ: "2026-05")
    thang_hien_tai = datetime.now().strftime("%Y-%m")
    
    # Chỉ tính tổng các giao dịch có ngày bắt đầu bằng tháng này
    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE type = ? AND date LIKE ?", 
        (type_input, f"{thang_hien_tai}%")
    )
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# 🌟 FIX SỬA LỖI BIỂU ĐỒ: Lấy thống kê danh mục cũng giới hạn theo tháng hiện tại
def get_summary_by_category(type_input):
    """
    Hàm lấy thống kê tổng số tiền theo từng danh mục (Dùng cho biểu đồ và tư vấn AI)
    """
    try:
        thang_hien_tai = datetime.now().strftime("%Y-%m")
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT category, SUM(amount) as total 
            FROM transactions 
            WHERE type = ? AND date LIKE ?
            GROUP BY category 
            ORDER BY total DESC
        """
        cursor.execute(query, (type_input, f"{thang_hien_tai}%"))
        rows = cursor.fetchall()
        
        result = [{"category": row["category"], "total": row["total"]} for row in rows]
        conn.close()
        return result
    except Exception as e:
        print(f"Lỗi database (get_summary_by_category): {e}")
        return []

def clear_database_phien_ban_safari():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
    conn.commit()
    conn.close()
    print("--- Đã quét sạch bách Database SQLite thật rồi nha sếp! ---")

def delete_transaction(transaction_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id = ? AND username = ?",
        (transaction_id, username)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def get_dashboard_stats():
    tong_thu = get_total_amount("Thu")
    tong_chi = get_total_amount("Chi")
    so_du = tong_thu - tong_chi
    danh_muc_chi = get_summary_by_category("Chi")

    return {
        "tong_thu": tong_thu,
        "tong_chi": tong_chi,
        "so_du": so_du,
        "danh_muc_chi": danh_muc_chi
    }
# Chay khoi tao bang khi file duoc thuc thi
#if __name__ == "__main__":
    # BƯỚC 1: Cậu bỏ dấu thăng (#) ở dòng dưới này ra, rồi bấm RUN chạy file db.py để dọn rác
    #clear_database_phien_ban_safari()
    
    # BƯỚC 2: Sau khi chạy xong thấy chữ quét sạch rác, cậu thêm lại dấu thăng (#) vào dòng trên là xong
    # init_db()