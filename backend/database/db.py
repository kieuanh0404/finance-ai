import sqlite3
from datetime import datetime

def get_connection():
    conn = sqlite3.connect('finance_ai.db')
    conn.row_factory = sqlite3.Row  # Lay du lieu dang dictionary
    return conn

# Tao bang transactions
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
def insert_transaction(type, amount, category, date, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (type, amount, category, date, note)
        VALUES (?, ?, ?, ?, ?)
    ''', (type, amount, category, date, note))
    conn.commit()
    conn.close()

# Ham get-all: Lay toan bo lich su(sap xep moi nhat truoc)
def get_all_transactions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions ORDER BY date DESC, id DESC')
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
def get_total_amount(type_input):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = ?", (type_input,))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0
def get_summary_by_category(type_input):
    """
    Hàm lấy thống kê tổng số tiền theo từng danh mục (Dùng cho biểu đồ và tư vấn AI)
    """
    import sqlite3
    try:
        conn = sqlite3.connect("finance_ai.db")
        conn.row_factory = sqlite3.Row # Dòng này quan trọng để trả về dạng dict
        cursor = conn.cursor()
        
        # Câu lệnh SQL để nhóm dữ liệu theo category và tính tổng tiền
        query = """
            SELECT category, SUM(amount) as total 
            FROM transactions 
            WHERE type = ? 
            GROUP BY category 
            ORDER BY total DESC
        """
        cursor.execute(query, (type_input,))
        rows = cursor.fetchall()
        
        # Chuyển đổi dữ liệu sang dạng danh sách dễ dùng
        result = [{"category": row["category"], "total": row["total"]} for row in rows]
        
        conn.close()
        return result
    except Exception as e:
        print(f"Lỗi database (get_summary_by_category): {e}")
        return []
# Chay khoi tao bang khi file duoc thuc thi
if __name__ == "__main__":
    init_db()
    print("Database đã được khởi tạo thành công!")