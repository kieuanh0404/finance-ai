import os
from dotenv import load_dotenv
from google import genai

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    API_KEY = API_KEY.strip().replace('"', "").replace("'", "")

client = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)
    print("--- [SUCCESS] Đã kết nối Gemini SDK! ---")
else:
    print("⚠️ Cảnh báo: Chưa cấu hình GEMINI_API_KEY trong file .env")


def goi_gemini_tu_van(user_message: str, context_data=None) -> str:
    if not client:
        return "Hệ thống AI chưa được cấu hình API Key, bạn kiểm tra lại nhé!"

    prompt = f"""
    Bạn là Trợ lý Tài chính thông minh của ứng dụng Finance AI.
    Câu hỏi của người dùng: "{user_message}"
    Dữ liệu tài chính hiện tại: {context_data}

    Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt.
    Xưng "mình", gọi người dùng là "bạn".
    Nếu câu hỏi không liên quan tài chính, hãy trả lời vui vẻ và khéo léo dẫn về quản lý chi tiêu.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"❌ Lỗi kết nối Google GenAI: {str(e)}")
        return "Mình đang bận suy nghĩ một chút, bạn thử hỏi lại câu khác nhé!"


if __name__ == "__main__":
    print("--- TEST GEMINI ---")
    ket_qua_test = goi_gemini_tu_van(
        user_message="Cho mình mẹo tiết kiệm tiền ăn uống?",
        context_data={"thong_ke_vi": "Đang có 60,000đ"}
    )
    print(ket_qua_test)