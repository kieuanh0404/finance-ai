import os
from dotenv import load_dotenv
from openai import OpenAI

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_path = os.path.join(backend_dir, ".env")

load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    GROQ_API_KEY = GROQ_API_KEY.strip().replace('"', "").replace("'", "")

client = None

if GROQ_API_KEY:
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    print("--- [SUCCESS] Đã kết nối Groq SDK! ---")
else:
    print("⚠️ Cảnh báo: Chưa cấu hình GROQ_API_KEY trong file .env")


def goi_groq_tu_van(user_message: str, context_data: dict | None = None) -> str:
    if not client:
        return "Hệ thống AI chưa được cấu hình Groq API Key, bạn kiểm tra lại nhé!"

    prompt = f"""
Bạn là Trợ lý Tài chính thông minh của ứng dụng Finance AI.
Câu hỏi của người dùng: "{user_message}"
Dữ liệu tài chính hiện tại: {context_data}

Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt.
Xưng "mình", gọi người dùng là "bạn".
Nếu câu hỏi không liên quan tài chính, hãy trả lời vui vẻ và khéo léo dẫn về quản lý chi tiêu.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Lỗi kết nối Groq: {str(e)}")
        return "Mình đang bận suy nghĩ một chút, bạn thử hỏi lại câu khác nhé!"