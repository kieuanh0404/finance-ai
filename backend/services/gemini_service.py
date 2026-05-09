import google.generativeai as genai
import os
from dotenv import load_dotenv

# Tải API Key từ file .env để bảo mật
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("⚠️ Cảnh báo: Thiện chưa điền GEMINI_API_KEY vào file .env rồi!")

def goi_gemini_tu_van(user_message, context_data=None):
    """Gửi câu hỏi cho Gemini khi Rules không xử lý được."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Bạn là Trợ lý Tài chính thông minh. 
    Câu hỏi: "{user_message}"
    Dữ liệu người dùng: {context_data}
    
    Hãy trả lời ngắn gọn, thân thiện. Xưng 'mình', gọi người dùng là 'bạn'.
    Nếu người dùng hỏi linh tinh không liên quan tài chính, hãy khéo léo dẫn dắt họ quay lại việc quản lý chi tiêu.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "Mình đang bận suy nghĩ một chút, bạn thử hỏi lại câu khác nhé! 😅"