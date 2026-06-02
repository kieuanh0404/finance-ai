import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finance_ai.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Tạo bảng transactions
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT
        )
    ''')

    # Phòng trường hợp DB cũ chưa có cột username
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN username TEXT DEFAULT 'default_user'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# Thêm giao dịch mới
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


# Lấy toàn bộ lịch sử theo tài khoản
def get_all_transactions(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT *
        FROM transactions
        WHERE username = ?
        ORDER BY date DESC, id DESC
        ''',
        (username,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# Lọc giao dịch theo tài khoản, loại giao dịch, khoảng thời gian
def filter_transactions(username, transaction_type=None, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transactions WHERE username = ?"
    params = [username]

    if transaction_type:
        query += " AND type = ?"
        params.append(transaction_type)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# Tính tổng tiền theo loại giao dịch, có thể lọc theo tài khoản
def get_total_amount(type_input, username=None):
    conn = get_connection()
    cursor = conn.cursor()

    thang_hien_tai = datetime.now().strftime("%Y-%m")

    if username:
        cursor.execute(
            '''
            SELECT SUM(amount)
            FROM transactions
            WHERE username = ? AND type = ? AND date LIKE ?
            ''',
            (username, type_input, f"{thang_hien_tai}%")
        )
    else:
        cursor.execute(
            '''
            SELECT SUM(amount)
            FROM transactions
            WHERE type = ? AND date LIKE ?
            ''',
            (type_input, f"{thang_hien_tai}%")
        )

    result = cursor.fetchone()[0]
    conn.close()

    return result if result else 0


# Thống kê tổng tiền theo danh mục, có thể lọc theo tài khoản
def get_summary_by_category(type_input, username=None):
    try:
        thang_hien_tai = datetime.now().strftime("%Y-%m")
        conn = get_connection()
        cursor = conn.cursor()

        if username:
            query = '''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE username = ? AND type = ? AND date LIKE ?
                GROUP BY category
                ORDER BY total DESC
            '''
            cursor.execute(query, (username, type_input, f"{thang_hien_tai}%"))
        else:
            query = '''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type = ? AND date LIKE ?
                GROUP BY category
                ORDER BY total DESC
            '''
            cursor.execute(query, (type_input, f"{thang_hien_tai}%"))

        rows = cursor.fetchall()
        conn.close()

        return [
            {"category": row["category"], "total": row["total"]}
            for row in rows
        ]

    except Exception as e:
        print(f"Lỗi database (get_summary_by_category): {e}")
        return []


# Xóa sạch dữ liệu test
def clear_database_phien_ban_safari():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")

    conn.commit()
    conn.close()

    print("--- Đã quét sạch Database SQLite thật rồi nha! ---")


# Xóa 1 giao dịch theo ID và tài khoản
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


# Dashboard stats, có thể lọc theo tài khoản
def get_dashboard_stats(username=None):
    tong_thu = get_total_amount("Thu", username=username)
    tong_chi = get_total_amount("Chi", username=username)
    so_du = tong_thu - tong_chi
    danh_muc_chi = get_summary_by_category("Chi", username=username)

    return {
        "tong_thu": tong_thu,
        "tong_chi": tong_chi,
        "so_du": so_du,
        "danh_muc_chi": danh_muc_chi
    }


if __name__ == "__main__":
    init_db()
    print("Database đã được khởi tạo/cập nhật thành công!")