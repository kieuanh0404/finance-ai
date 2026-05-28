# System Architecture & Data Flow

## Overview
Hệ thống Finance AI được thiết kế theo kiến trúc Client-Server, tách biệt rõ ràng giữa Frontend (Giao diện người dùng), Backend (Xử lý nghiệp vụ & API), và AI Services (Xử lý ngôn ngữ tự nhiên & Tư vấn).

## Tech Stack
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript (`frontend/index.html`, `frontend/api.js`)
- **Backend**: Python 3.10+, FastAPI (`backend/main.py`)
- **Database**: SQLite (`backend/database/db.py`)
- **AI/ML**: Custom NLP Agent (`backend/services/bo_nao_ai.py`), Google Gemini SDK (`backend/services/gemini_service.py`)
- **Testing**: Pytest (`backend/tests/test_backend.py`)

## Architecture Diagram
