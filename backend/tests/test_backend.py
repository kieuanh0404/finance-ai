import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException

# Add backend directory to path for imports when running tests from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.bo_nao_ai import normalize_text, extract_and_clean_date, parse_amount, FinanceAgent, phan_tich_y_dinh
from services.chuyen_vien_xu_ly import (
    lam_sach_ghi_chu_loi,
    xu_ly_them_moi,
    xu_ly_truy_van_nang_cao,
    xu_ly_ngan_sach,
    xu_ly_tu_van,
)
from services.gemini_service import goi_gemini_tu_van
from routes.api_tro_ly_chat import tro_ly_ai_nhan_tin, TinNhanNguoiDung
from routes.auth import dang_ky_tai_khoan, dang_nhap_tai_khoan, ThongTinTaiKhoan
from routes.transaction import add_transaction, get_transactions, filter_transactions_api, delete_transaction_api
from models.transaction import TransactionRequest


# ==================== TESTS FOR bo_nao_ai.py ====================
class TestNormalizeText:
    def test_normalizes_accents(self):
        assert normalize_text("Hôm nay ăn phở") == "hom nay an pho"

    def test_handles_empty_string(self):
        assert normalize_text("") == ""

    def test_handles_special_chars(self):
        assert normalize_text("đi xe máy") == "di xe may"


class TestExtractAndCleanDate:
    def test_text_date(self):
        date_str, cleaned = extract_and_clean_date("25 tháng 5 mua nước")
        assert len(date_str) == 10
        assert "mua nước" in cleaned

    def test_numeric_date(self):
        date_str, cleaned = extract_and_clean_date("19/05/2026 mua nước")
        assert date_str == "2026-05-19"
        assert "mua nước" in cleaned

    def test_hom_qua(self):
        date_str, cleaned = extract_and_clean_date("hôm qua ăn phở")
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert date_str == expected
        assert "ăn phở" in cleaned

    def test_hom_kia(self):
        date_str, cleaned = extract_and_clean_date("hôm kia đi chơi")
        expected = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert date_str == expected
        assert "đi chơi" in cleaned


class TestParseAmount:
    def test_plain_number(self):
        assert parse_amount("10000", "") == 10000.0

    def test_k_suffix(self):
        assert parse_amount("50", "k") == 50000.0

    def test_tr_suffix(self):
        assert parse_amount("1.2", "tr") == 1200000.0

    def test_m_suffix(self):
        assert parse_amount("1.5", "m") == 1500000.0


class TestFinanceAgent:
    def test_fuzzy_classify_unknown(self):
        agent = FinanceAgent()
        cat, t_type, kw, score = agent._fuzzy_classify("giao dịch lạ")
        assert cat == "Khác"
        assert t_type == "Chi"

    def test_parse_add_intent(self):
        agent = FinanceAgent()
        result = agent.parse("ăn phở 50k")
        assert result["intent"] == "add"
        assert len(result["data"]) > 0
        assert result["data"][0]["amount"] == 50000.0

    def test_parse_query_intent(self):
        agent = FinanceAgent()
        result = agent.parse("tổng chi hôm nay bao nhiêu")
        assert result["intent"] == "query"

    def test_parse_budget_intent(self):
        agent = FinanceAgent()
        result = agent.parse("ngân sách tháng này")
        assert result["intent"] == "budget"

    def test_parse_advice_intent(self):
        agent = FinanceAgent()
        result = agent.parse("tư vấn tiết kiệm")
        assert result["intent"] == "advice"

    def test_parse_chat_intent(self):
        agent = FinanceAgent()
        result = agent.parse("chào bạn")
        assert result["intent"] == "chat"


class TestPhanTichYDinh:
    def test_wrapper(self):
        result = phan_tich_y_dinh("ăn phở 50k")
        assert "intent" in result
        assert "data" in result


# ==================== TESTS FOR chuyen_vien_xu_ly.py ====================
class TestLamSachGhiChuLoi:
    def test_removes_garbage_words(self):
        assert "phở" in lam_sach_ghi_chu_loi("tớ mua phở hôm nay")

    def test_handles_empty_input(self):
        assert lam_sach_ghi_chu_loi("") == "Giao dịch"

    def test_handles_none_input(self):
        assert lam_sach_ghi_chu_loi(None) == "Giao dịch"


class TestXuLyThemMoi:
    def test_valid_data(self):
        intent_data = {"data": [{"amount": 50000, "type": "Chi", "note": "ăn phở", "category": "Ăn uống"}]}
        result = xu_ly_them_moi(intent_data)
        assert "✅ Chi" in result
        assert "50,000đ" in result

    def test_empty_data(self):
        intent_data = {"data": []}
        result = xu_ly_them_moi(intent_data)
        assert "⚠️ Không tìm thấy giao dịch" in result

    def test_invalid_data(self):
        intent_data = {"data": [{"note": "lỗi"}]}
        result = xu_ly_them_moi(intent_data)
        assert "⚠️ Không xử lý được" in result


class TestXuLyTruyVanNangCao:
    @patch('services.chuyen_vien_xu_ly.get_connection')
    def test_hom_nay(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (100000,)
        mock_get_conn.return_value.cursor.return_value = mock_cursor
        result = xu_ly_truy_van_nang_cao("hôm nay")
        assert "hôm nay" in result

    @patch('services.chuyen_vien_xu_ly.get_connection')
    def test_hom_qua(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_get_conn.return_value.cursor.return_value = mock_cursor
        result = xu_ly_truy_van_nang_cao("hom qua")
        assert "hôm qua" in result

    @patch('services.chuyen_vien_xu_ly.get_connection')
    def test_default_month(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_get_conn.return_value.cursor.return_value = mock_cursor
        result = xu_ly_truy_van_nang_cao("tổng chi")
        assert "tháng này" in result


class TestXuLyNganSach:
    def test_returns_string(self):
        result = xu_ly_ngan_sach()
        assert isinstance(result, str)
        assert "ngân sách" in result.lower()


class TestXuLyTuVan:
    @patch('services.chuyen_vien_xu_ly.get_summary_by_category')
    def test_with_data(self, mock_summary):
        mock_summary.return_value = [{"category": "Ăn uống", "total": 500000}]
        result = xu_ly_tu_van()
        assert "Lời khuyên AI" in result

    @patch('services.chuyen_vien_xu_ly.get_summary_by_category')
    def test_without_data(self, mock_summary):
        mock_summary.return_value = []
        result = xu_ly_tu_van()
        assert "chưa thấy dữ liệu" in result


# ==================== TESTS FOR gemini_service.py ====================
class TestGoiGeminiTuVan:
    @patch('services.gemini_service.client')
    def test_with_client(self, mock_client):
        mock_client.models.generate_content.return_value.text = "Đây là câu trả lời."
        result = goi_gemini_tu_van("test")
        assert result == "Đây là câu trả lời."

    @patch('services.gemini_service.client', None)
    def test_without_client(self):
        result = goi_gemini_tu_van("test")
        assert "chưa được cấu hình" in result

    @patch('services.gemini_service.client')
    def test_with_exception(self, mock_client):
        mock_client.models.generate_content.side_effect = Exception("API Error")
        result = goi_gemini_tu_van("test")
        assert "đang bận suy nghĩ" in result


# ==================== TESTS FOR ROUTES ====================
@pytest.fixture
def mock_db():
    with patch('routes.api_tro_ly_chat.db') as mock:
        yield mock

@pytest.fixture
def mock_db_auth():
    with patch('routes.auth.db') as mock:
        yield mock

@pytest.fixture
def mock_db_transaction():
    with patch('routes.transaction.db') as mock:
        yield mock

class TestTroLyAiNhanTin:
    def test_add_intent(self, mock_db):
        mock_intent = {
            "intent": "add",
            "data": [{"type": "Chi", "amount": 50000, "category": "Ăn uống", "note": "phở", "date": "2023-01-01"}]
        }
        with patch('routes.api_tro_ly_chat.phan_tich_y_dinh', return_value=mock_intent):
            mock_db.insert_transaction.return_value = 1
            request = TinNhanNguoiDung(tin_nhan="ăn phở 50k", username="test")
            result = tro_ly_ai_nhan_tin(request)
            assert result["y_dinh"] == "add"
            assert result["du_lieu_giao_dich"][0]["id"] == 1

    def test_query_intent(self, mock_db):
        mock_intent = {"intent": "query", "data": {}}
        with patch('routes.api_tro_ly_chat.phan_tich_y_dinh', return_value=mock_intent):
            request = TinNhanNguoiDung(tin_nhan="tổng chi hôm nay", username="test")
            result = tro_ly_ai_nhan_tin(request)
            assert result["y_dinh"] == "query"

    def test_fallback_chat(self, mock_db):
        mock_intent = {"intent": "chat", "data": {}}
        with patch('routes.api_tro_ly_chat.phan_tich_y_dinh', return_value=mock_intent):
            request = TinNhanNguoiDung(tin_nhan="chào bạn", username="test")
            result = tro_ly_ai_nhan_tin(request)
            assert result["y_dinh"] == "chat"

    def test_gemini_fallback(self, mock_db):
        with patch('routes.api_tro_ly_chat.phan_tich_y_dinh', return_value={"intent": "unknown", "data": {}}):
            with patch('routes.api_tro_ly_chat.client') as mock_client:
                mock_client.models.generate_content.return_value.text = '{"phan_hoi": "Hi", "is_transaction": false, "data": null}'
                request = TinNhanNguoiDung(tin_nhan="chào", username="test")
                result = tro_ly_ai_nhan_tin(request)
                assert result["y_dinh"] == "unknown"


class TestAuthRoutes:
    def test_register_success(self, mock_db_auth):
        mock_db_auth.get_connection.return_value.cursor.return_value.fetchone.return_value = None
        user = ThongTinTaiKhoan(name="newuser", pass_word="pass123")
        result = dang_ky_tai_khoan(user)
        assert result["status"] == "success"

    def test_register_duplicate(self, mock_db_auth):
        mock_db_auth.get_connection.return_value.cursor.return_value.fetchone.return_value = (1,)
        user = ThongTinTaiKhoan(name="existing", pass_word="pass123")
        with pytest.raises(HTTPException) as exc_info:
            dang_ky_tai_khoan(user)
        assert "đã tồn tại" in str(exc_info.value.detail)

    def test_login_success(self, mock_db_auth):
        mock_db_auth.get_connection.return_value.cursor.return_value.fetchone.return_value = (1,)
        user = ThongTinTaiKhoan(name="user", pass_word="pass123")
        result = dang_nhap_tai_khoan(user)
        assert result["status"] == "success"

    def test_login_fail(self, mock_db_auth):
        mock_db_auth.get_connection.return_value.cursor.return_value.fetchone.return_value = None
        user = ThongTinTaiKhoan(name="user", pass_word="wrong")
        with pytest.raises(HTTPException) as exc_info:
            dang_nhap_tai_khoan(user)
        assert "Sai tên" in str(exc_info.value.detail)


class TestTransactionRoutes:
    def test_add_transaction(self, mock_db_transaction):
        mock_db_transaction.insert_transaction.return_value = 10
        txn = TransactionRequest(username="test", type="Chi", amount=50000, category="Ăn uống", date="2023-01-01", note="phở")
        result = add_transaction(txn)
        assert result["status"] == "success"
        assert result["id"] == 10

    def test_get_transactions(self, mock_db_transaction):
        mock_db_transaction.get_all_transactions.return_value = [{"id": 1}]
        result = get_transactions(username="test")
        assert result == [{"id": 1}]

    def test_filter_transactions(self, mock_db_transaction):
        mock_db_transaction.filter_transactions.return_value = [{"id": 1}]
        result = filter_transactions_api(username="test", transaction_type="Chi", start_date="2023-01-01", end_date="2023-01-31")
        assert result == [{"id": 1}]

    def test_delete_transaction_success(self, mock_db_transaction):
        mock_db_transaction.delete_transaction.return_value = 1
        result = delete_transaction_api(transaction_id=1, username="test")
        assert result["status"] == "success"

    def test_delete_transaction_not_found(self, mock_db_transaction):
        mock_db_transaction.delete_transaction.return_value = 0
        with pytest.raises(HTTPException) as exc_info:
            delete_transaction_api(transaction_id=1, username="test")
        assert "Không tìm thấy" in str(exc_info.value.detail)
