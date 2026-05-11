import axios from 'axios';

const API_BASE_URL = "http://127.0.0.1:8000";
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export const FinanceAPI = {
    /**
     * 1. CHATBOT AI
     * Gửi câu nói của người dùng để AI bóc tách và tự động lưu.
     */
    sendChatMessage: async (message) => {
        try {
            const response = await apiClient.post('api/chatbot/chat', {
    tin_nhan: message
});
            return response.data; // Trả về: { trang_thai, y_dinh, phan_hoi }
        } catch (error) {
            console.error("Lỗi Chatbot:", error);
            throw error;
        }
    },

    /**
     * 2. LẤY LỊCH SỬ GIAO DỊCH
     * Hiển thị danh sách các khoản đã thu/chi.
     */
    getTransactions: async () => {
        try {
            const response = await apiClient.get('/api/transactions');
            return response.data; // Trả về danh sách mảng các giao dịch
        } catch (error) {
            console.error("Lỗi lấy lịch sử:", error);
            throw error;
        }
    },

    /**
     * 3. THÊM GIAO DỊCH THỦ CÔNG
     * Dùng khi người dùng không muốn chat mà muốn nhập Form.
     */
    addTransaction: async (transactionData) => {
        try {
            const response = await apiClient.post('/api/transactions', transactionData);
            return response.data;
        } catch (error) {
            console.error("Lỗi thêm giao dịch:", error);
            throw error;
        }
    },

    /**
     * 4. LẤY DỮ LIỆU THỐNG KÊ (Cho phần của Kiều Anh)
     * Dùng để vẽ biểu đồ Dashboard.
     */
    getSummary: async () => {
        try {
            // Lưu ý: Đảm bảo bên Backend đã định nghĩa endpoint /api/summary
            const response = await apiClient.get('/api/summary');
            return response.data;
        } catch (error) {
            console.error("Lỗi lấy thống kê:", error);
            throw error;
        }
    }
};

export default FinanceAPI;