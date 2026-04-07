import json
import os
from config import LESSON_DATA_FILE_PATH

quiz_data = {}
try:
    with open(LESSON_DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "lessons" in data:
            quiz_data = {}
            for index, lesson in enumerate(data["lessons"]):
                parsed_questions = []
                for q_index, q in enumerate(lesson.get("questions", [])):
                    # Xác định loại câu hỏi, mặc định là mcq (Trắc nghiệm)
                    q_type = q.get("type", "mcq")
                    
                    # Tự động tạo choices nếu là dạng Đúng/Sai hoặc Điền từ/Kéo thả
                    choices = q.get("choices", [])
                    if q_type == "tf" and not choices:
                        choices = ["Đúng", "Sai"]
                    elif q_type in ["fill", "drag"] and "words" in q:
                        choices = q["words"]
                        
                    # Chỉ lấy câu hỏi nếu có choices
                    if choices:
                        parsed_questions.append({
                            "id": q_index,
                            "type": q_type,
                            "question": q["question"],
                            "choices": choices,
                            "answer": q.get("correct_answer", 0),
                            "explanation": q.get("explanation", ""),
                            "difficulty": q.get("difficulty", "medium")
                        })
                
                quiz_data[index + 1] = parsed_questions
                
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file dữ liệu câu hỏi tại {LESSON_DATA_FILE_PATH}.")
except json.JSONDecodeError:
    print(f"Lỗi: Không thể giải mã dữ liệu từ {LESSON_DATA_FILE_PATH}.")
except Exception as e:
    print(f"Lỗi không xác định khi tải dữ liệu: {str(e)}")