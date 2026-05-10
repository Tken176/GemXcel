import json
import os
import config

LESSON_DATA_FILE_PATH = config.LESSON_DATA_FILE_PATH

quiz_data = {}
try:
    if os.path.exists(LESSON_DATA_FILE_PATH):
        with open(LESSON_DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            lessons = data.get("lessons", [])
            quiz_data = {}
            for index, lesson in enumerate(lessons):
                parsed_questions = []
                for q_index, q in enumerate(lesson.get("questions", [])):
                    q_type = q.get("type", "mcq")

                    choices = q.get("choices", [])
                    if q_type == "tf" and not choices:
                        choices = ["Đúng", "Sai"]
                    elif q_type in ["fill", "drag"] and "words" in q:
                        choices = q["words"]

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
    else:
        quiz_data = {}

# FIX: Đặt các except cụ thể TRƯỚC except Exception chung
# (Trong code cũ, FileNotFoundError và JSONDecodeError là unreachable do bị chặn bởi except Exception phía trên)
except FileNotFoundError:
    config.logger.warning("Không tìm thấy file dữ liệu câu hỏi tại %s.", LESSON_DATA_FILE_PATH)
    quiz_data = {}
except json.JSONDecodeError:
    config.logger.warning("Không thể giải mã dữ liệu từ %s.", LESSON_DATA_FILE_PATH)
    quiz_data = {}
except Exception as e:
    config.logger.warning("Lỗi không xác định khi tải dữ liệu: %s", e)
    quiz_data = {}