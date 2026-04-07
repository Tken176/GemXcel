import os
import json
import re
import time
import hashlib
import signal
import requests
import chardet
from typing import List, Dict, Optional, Tuple, Set 
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import config
import random

SUPABASE_URL = "https://hwqlvikkzeybssocyjjn.supabase.co"
# FIX: Chỉ trỏ tới function root — KHÔNG có sub-path.
# Supabase không forward sub-path vào req.url, gây lỗi 404.
# Model/path được truyền qua body field "geminiPath" thay thế.
PROXY_URL = f"{SUPABASE_URL}/functions/v1/gemini-proxy"
GEMINI_PATH = "/v1beta/models/gemini-2.5-flash-lite:generateContent"

class TimeoutException(Exception):
    """Custom timeout exception"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutException("Operation timed out")


class GeminiClient:

    def __init__(self):
        # Không cần đọc API_AI.json nữa — key được giữ trên server
        # Lấy access token Supabase của user (đã đăng nhập)
        self.access_token = self._load_access_token()
        self.session = requests.Session()

    def _load_access_token(self) -> str:
        
        # 1. Trỏ đúng vào thư mục AppData/Roaming giống setting_screen.py
        appdata_path = os.environ.get('APPDATA')
        token_file = os.path.join(appdata_path, "GemxelProject", "auth_session.json")
        
        if os.path.exists(token_file):
            with open(token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 2. Lấy token an toàn từ object "session"
                session_data = data.get("session", data)
                access_token = session_data.get("access_token", "")
                
                if access_token:
                    return access_token
                    
        raise ValueError("Chưa đăng nhập! Vui lòng đăng nhập vào ứng dụng trước.")

    def chat_completions_create(self, messages, temperature=0.7, **kwargs):
        if isinstance(messages, list) and len(messages) > 0:
            prompt = messages[-1].get("content", "")
        else:
            prompt = str(messages)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",  # <-- JWT thay cho API key
        }

        data = {
            "geminiPath": GEMINI_PATH,   # FIX: server đọc field này để biết endpoint cần gọi
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
                "topP": 0.8,
                "topK": 10
            }
        }

        try:
            response = self.session.post(
                PROXY_URL,        # <-- gọi proxy, không phải Gemini trực tiếp
                headers=headers,
                json=data,
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                return GeminiResponse(content)
            elif response.status_code == 401:
                raise Exception("Token hết hạn, vui lòng đăng nhập lại.")
            else:
                raise Exception(f"Proxy error {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            raise Exception("Gemini proxy timeout")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request error: {e}")


class GeminiResponse:
    def __init__(self, content):
        self.choices = [GeminiChoice(content)]

class GeminiChoice:
    def __init__(self, content):
        self.message = GeminiMessage(content)

class GeminiMessage:
    def __init__(self, content):
        self.content = content

class GeminiChatCompletions:
    def __init__(self, client):
        self.client = client
        
    def create(self, model=None, messages=None, temperature=0.7, **kwargs):
        return self.client.chat_completions_create(messages=messages, temperature=temperature, **kwargs)

class GeminiChat:
    def __init__(self, client):
        self.completions = GeminiChatCompletions(client)


class ContentProcessor:
    def __init__(self, lessons_count: int = 5, questions_per_lesson: int = 6, quiz_questions: int = 10):
        self.gemini_client = GeminiClient()
        self.client = type('Client', (), {'chat': GeminiChat(self.gemini_client)})()
        
        self.lessons_path = config.LESSON_DATA_FILE_PATH
        self.quiz_path = config.QUIZ_DATA_FILE_PATH

        self.supported_formats = ['.txt', '.docx', '.md', '.pdf']
        self.max_retries = 3
        self.timeout = 45 
        self.total_timeout = 300 

        self.lessons_count = max(1, min(lessons_count, 20))
        self.questions_per_lesson = max(3, min(questions_per_lesson, 15))
        self.quiz_questions = max(5, min(quiz_questions, 50))

        self.content_cache = {}
        os.makedirs(config.ASSETS_DIR, exist_ok=True)
        self.should_stop = False
        self.used_questions = set()
        self.used_quiz_questions = set()

    def is_supported(self, file_path: str) -> bool:
        return any(file_path.lower().endswith(ext) for ext in self.supported_formats)

    def process_file(self, file_path: str) -> Tuple[bool, str]:
        start_time = time.time()
        self.used_questions.clear()
        self.used_quiz_questions.clear()
        
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.total_timeout)

        try:
            if not self.is_supported(file_path):
                return False, f"Định dạng file không được hỗ trợ. Các định dạng hỗ trợ: {', '.join(self.supported_formats)}"

            if not os.path.exists(file_path):
                return False, f"File không tồn tại: {file_path}"

            try:
                content = self.read_file_content(file_path)
            except Exception as e:
                return False, f"Không thể đọc file: {e}"
            
            if not content or not content.strip():
                return False, "Không thể đọc nội dung từ file (file rỗng hoặc định dạng không đúng)."

            if len(content.strip()) < 200:
                return False, "Nội dung file quá ngắn để xử lý (cần ít nhất 200 ký tự)."

            content = self._preprocess_content(content)
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash in self.content_cache:
                lessons, quiz_questions = self.content_cache[content_hash]
            else:
                chunks = self._intelligent_chunking(content, target_chunks=self.lessons_count)
                lessons = self.generate_lessons_with_timeout(chunks)
                
                if not lessons: return False, "Không thể tạo bài học từ nội dung này."

                lessons = [lesson for lesson in lessons if lesson is not None]
                if not lessons: return False, "Không thể tạo bài học hợp lệ từ nội dung này."

                quiz_questions = self.generate_quiz_with_timeout(lessons, total_questions=self.quiz_questions)
                self.content_cache[content_hash] = (lessons, quiz_questions)

            success = self._safe_save_data_files(lessons, quiz_questions)
            if not success:
                return False, "Không thể lưu dữ liệu. Vui lòng kiểm tra quyền ghi file."

            elapsed_time = time.time() - start_time
            total_questions = sum(len(lesson.get('questions', [])) for lesson in lessons)
            total_quiz = sum(len(q) for q in quiz_questions.values()) if isinstance(quiz_questions, dict) else 0

            return True, f"Xử lý thành công trong {elapsed_time:.1f}s! Đã tạo {len(lessons)} bài học ({total_questions} câu hỏi) và {total_quiz} câu hỏi quiz."

        except TimeoutException:
            elapsed_time = time.time() - start_time
            return False, f"Timeout sau {elapsed_time:.1f}s! Quá trình xử lý mất quá nhiều thời gian."
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return False, f"Timeout sau {elapsed_time:.1f}s! Server AI phản hồi chậm."
            else:
                return False, f"Lỗi sau {elapsed_time:.1f}s: {error_msg}"
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)


    def _detect_encoding(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                confidence = result.get('confidence', 0)
                encoding = result.get('encoding', 'utf-8')
                
                if confidence < 0.7 or not encoding: return 'utf-8'
                    
                encoding_map = {'utf-16': 'utf-16', 'utf-16le': 'utf-16-le', 'utf-16be': 'utf-16-be', 'windows-1252': 'cp1252', 'iso-8859-1': 'latin-1'}
                return encoding_map.get(encoding.lower(), encoding)
        except Exception:
            return 'utf-8'

    def _preprocess_content(self, content: str) -> str:
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        cleaned_chars = [ch for ch in content if ch == '\n' or ch == '\t' or ch.isprintable()]
        return ''.join(cleaned_chars).strip()

    def read_file_content(self, file_path: str) -> Optional[str]:
        try:
            if not self.is_supported(file_path): raise ValueError(f"Định dạng file không được hỗ trợ: {file_path}")

            if file_path.lower().endswith('.txt'):
                detected_encoding = self._detect_encoding(file_path)
                encodings = [detected_encoding, 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'cp1252', 'latin-1', 'gbk', 'big5']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                            if content.strip(): return content
                    except (UnicodeDecodeError, UnicodeError): continue
                
                try:
                    with open(file_path, 'rb') as f: raw_data = f.read()
                    for encoding in ['utf-8', 'cp1252', 'latin-1']:
                        try:
                            content = raw_data.decode(encoding, errors='replace')
                            if content.strip() and not self._is_binary_garbage(content): return content
                        except Exception: continue
                except Exception: pass
                raise ValueError("Không thể đọc file .txt với các encoding thông dụng")

            elif file_path.lower().endswith('.docx'):
                try:
                    import docx
                    if not os.path.exists(file_path): raise ValueError("File không tồn tại")
                    if os.path.getsize(file_path) == 0: raise ValueError("File DOCX rỗng")
                    try: doc = docx.Document(file_path)
                    except Exception as e: raise ValueError(f"File DOCX bị lỗi: {e}")
                    
                    paragraphs_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                    tables_text = []
                    for table in doc.tables:
                        for row in table.rows:
                            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                            if row_text: tables_text.append(" | ".join(row_text))
                    
                    content = "\n\n".join(paragraphs_text + tables_text)
                    if not content.strip(): raise ValueError("File DOCX không chứa text có thể đọc được")
                    if self._is_binary_garbage(content): raise ValueError("Nội dung DOCX chứa dữ liệu binary không hợp lệ")
                    return content
                except ImportError: raise ValueError("Cần cài đặt python-docx: pip install python-docx")

            elif file_path.lower().endswith('.md'):
                detected_encoding = self._detect_encoding(file_path)
                for encoding in [detected_encoding, 'utf-8', 'cp1252', 'latin-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                            if content.strip():
                                content = re.sub(r'(^|\n)#{1,6}\s*', r'\1', content)
                                content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
                                content = re.sub(r'\*(.*?)\*', r'\1', content)
                                content = re.sub(r'`{1,3}([^`]+)`{1,3}', r'\1', content)
                                return content
                    except (UnicodeDecodeError, UnicodeError): continue
                raise ValueError("File Markdown không đọc được với các encoding thông dụng")

            elif file_path.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        pages_text = []
                        for page in reader.pages:
                            try:
                                text = page.extract_text()
                                if text and text.strip(): pages_text.append(text)
                            except Exception: continue
                        content = "\n".join(pages_text)
                        if not content.strip(): raise ValueError("Không thể trích xuất text từ PDF")
                        return content
                except ImportError: raise ValueError("Cần cài đặt PyPDF2: pip install PyPDF2")

        except Exception as e:
            print(f"Lỗi đọc file {file_path}: {e}")
            return None

    def _is_binary_garbage(self, content: str) -> bool:
        if not content: return True
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        total_chars = len(content)
        if total_chars > 0:
            return (printable_chars / total_chars) < 0.8
        return True

    def _intelligent_chunking(self, content: str, target_chunks: int = 5) -> List[str]:
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) <= target_chunks:
            words = content.split()
            chunk_size = max(80, len(words) // max(1, target_chunks))
            chunks = []
            for i in range(target_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(words))
                if start_idx < len(words):
                    chunk = ' '.join(words[start_idx:end_idx])
                    if chunk.strip(): chunks.append(chunk)
            return chunks
        else:
            base = len(paragraphs) // target_chunks
            rem = len(paragraphs) % target_chunks
            chunks, start = [], 0
            for i in range(target_chunks):
                take = base + (1 if i < rem else 0)
                end = start + take
                chunk = '\n\n'.join(paragraphs[start:end]).strip()
                if chunk: chunks.append(chunk)
                start = end
            return chunks

    def generate_lessons_with_timeout(self, chunks: List[str]) -> List[Dict]:
        results = [None] * len(chunks)
        completed_count = 0

        def _lesson_callback(future, lesson_num):
            nonlocal completed_count
            try:
                result = future.result(timeout=self.timeout)
                results[lesson_num - 1] = result
                completed_count += 1
            except Exception as e:
                results[lesson_num - 1] = self._create_fallback_lesson(
                    lesson_num, chunks[lesson_num - 1] if lesson_num - 1 < len(chunks) else ""
                )
                completed_count += 1

        with ThreadPoolExecutor(max_workers=min(3, len(chunks))) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                if self.should_stop: break
                future = executor.submit(self._generate_single_lesson_safe, chunk, i + 1)
                future.add_done_callback(lambda f, num=i + 1: _lesson_callback(f, num))
                futures.append(future)

            try:
                for _ in as_completed(futures, timeout=self.timeout * len(chunks)):
                    if self.should_stop: break
            except TimeoutError: pass

        return [r for r in results if r is not None]

    def _generate_unique_question_hash(self, question: str, options: List[str]) -> str:
        normalized_question = re.sub(r'\s+', ' ', question.strip().lower())
        normalized_options = [re.sub(r'\s+', ' ', opt.strip().lower()) for opt in options]
        combined = normalized_question + '|' + '|'.join(normalized_options)
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def _is_question_unique(self, question: str, options: List[str], used_set: Set[str]) -> bool:
        return self._generate_unique_question_hash(question, options) not in used_set

    def _add_question_to_used(self, question: str, options: List[str], used_set: Set[str]):
        used_set.add(self._generate_unique_question_hash(question, options))

    def _generate_single_lesson_safe(self, chunk: str, lesson_number: int) -> Dict:
        for attempt in range(self.max_retries):
            try:
                if self.should_stop: break

                max_chunk_length = 1500 
                chunk_for_prompt = (chunk[:max_chunk_length] + "...") if len(chunk) > max_chunk_length else chunk

                prompt = f"""
Tạo bài học số {lesson_number} từ nội dung sau:
{chunk_for_prompt}

Yêu cầu:
1. Tạo bài học theo thứ tự hợp lý. Tiêu đề ngắn gọn. Nội dung tóm tắt 200-350 từ.
2. Tạo ĐÚNG {self.questions_per_lesson} câu hỏi. PHẢI BAO GỒM ĐA DẠNG CÁC LOẠI CÂU HỎI SAU:
   - "mcq" (Trắc nghiệm 4 đáp án)
   - "tf" (Đúng/Sai)
   - "fill" (Điền từ vào chỗ trống)

Trả về CHỈ JSON hợp lệ theo mẫu chính xác sau:
{{
  "name": "Bài {lesson_number}",
  "title": "[Tiêu đề cụ thể về nội dung]",
  "content": "[Nội dung tóm tắt chi tiết]",
  "questions": [
    {{
      "type": "mcq",
      "question": "Câu hỏi trắc nghiệm 4 đáp án?",
      "choices": ["A. Lựa chọn 1", "B. Lựa chọn 2", "C. Lựa chọn 3", "D. Lựa chọn 4"],
      "correct_answer": 0,
      "difficulty": "medium"
    }},
    {{
      "type": "tf",
      "question": "Nhận định này đúng hay sai?",
      "correct_answer": 0,
      "difficulty": "easy"
    }},
    {{
      "type": "fill",
      "question": "Vệ tinh tự nhiên của Trái Đất là ___.",
      "words": ["Mặt trăng", "Mặt trời", "Sao mộc", "Sao kim"],
      "correct_answer": 0,
      "difficulty": "hard"
    }}
  ]
}}
LƯU Ý: correct_answer là vị trí index (0, 1, 2, 3) của đáp án đúng trong mảng choices hoặc words. Với "tf", 0 = Đúng, 1 = Sai.
"""
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7, 
                )

                response_text = (response.choices[0].message.content or "").strip()
                if not response_text: raise ValueError("Response rỗng từ AI")

                lesson = self._safe_parse_json(response_text)
                if not lesson: raise ValueError("Không parse được JSON từ response")

                return self._validate_lesson(lesson, lesson_number, chunk)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return self._create_fallback_lesson(lesson_number, chunk)
                time.sleep(min(2 ** attempt, 5))

    def _safe_parse_json(self, text: str) -> Optional[Dict]:
        try:
            # FIX CỦA CÔNG CỤ COPY-PASTE LỖI (Tránh dùng r'```')
            cleaned = text.replace('`'*3 + 'json', '').replace('`'*3, '').strip(" \n")
            
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                if self._is_valid_lesson_structure(parsed[0]): return parsed[0]
                for item in parsed:
                    if isinstance(item, dict) and self._is_valid_lesson_structure(item): return item
                return parsed[0]
            if isinstance(parsed, dict) and self._is_valid_lesson_structure(parsed): return parsed
        except Exception: 
            pass

        json_candidates = self._extract_json_objects(text)
        for candidate in json_candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and self._is_valid_lesson_structure(parsed): return parsed
                if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict): return parsed[0]
            except json.JSONDecodeError: continue

        return None

    def _is_valid_lesson_structure(self, data: Dict) -> bool:
        required_fields = ['name', 'title', 'content', 'questions']
        if not all(field in data for field in required_fields): return False
        if not isinstance(data['questions'], list): return False
        return True

    def _extract_json_objects(self, text: str) -> List[str]:
        results = []
        stack, in_string, escape, start_idx = 0, False, False, None

        for i, ch in enumerate(text):
            if in_string:
                if escape: escape = False
                elif ch == '\\': escape = True
                elif ch == '"': in_string = False
                continue
            else:
                if ch == '"': in_string = True; continue
                if ch == '{':
                    if stack == 0: start_idx = i
                    stack += 1
                elif ch == '}':
                    if stack > 0:
                        stack -= 1
                        if stack == 0 and start_idx is not None:
                            results.append(text[start_idx:i + 1])
                            start_idx = None
        return results

    def _validate_lesson(self, lesson: Dict, lesson_number: int, chunk: str) -> Dict:
        lesson.setdefault("name", f"Bài {lesson_number}")
        lesson.setdefault("title", f"Bài học {lesson_number}")
        lesson.setdefault("content", chunk[:300] + "..." if len(chunk) > 300 else chunk)

        if "questions" not in lesson or not isinstance(lesson["questions"], list):
            lesson["questions"] = []

        unique_questions = []
        for q in lesson["questions"]:
            if not isinstance(q, dict): continue
            
            # --- KIỂM TRA TYPE CÂU HỎI VÀ XỬ LÝ OPTIONS ---
            q_type = q.get("type", "mcq")
            if q_type not in ["mcq", "tf", "fill", "drag"]:
                q["type"] = "mcq"
                q_type = "mcq"

            if q_type == "mcq":
                if not isinstance(q.get("choices"), list) or len(q["choices"]) < 2:
                    q["choices"] = ["A. Đúng", "B. Sai", "C. Không xác định", "D. Tất cả đều sai"]
                options = q["choices"]
            elif q_type == "tf":
                q["choices"] = ["Đúng", "Sai"]
                if q.get("correct_answer") not in [0, 1]: q["correct_answer"] = 0
                options = q["choices"]
            elif q_type in ["fill", "drag"]:
                if not isinstance(q.get("words"), list) or len(q["words"]) < 2:
                    q["words"] = ["Từ đúng", "Từ sai 1", "Từ sai 2"]
                q["choices"] = q["words"] 
                options = q["words"]

            for idx, choice in enumerate(options):
                if len(choice) > 50:
                    prefix = choice[:2] if choice.startswith(('A.', 'B.', 'C.', 'D.')) else ""
                    content = choice[2:].strip() if prefix else choice
                    options[idx] = prefix + " " + content[:47-len(prefix)] if prefix else content[:50]
                    
            question_text = q.get("question", "")
            
            if not isinstance(q.get("correct_answer"), int) or q["correct_answer"] < 0 or q["correct_answer"] >= len(options):
                q["correct_answer"] = 0
                
            q.setdefault("difficulty", "medium")

            if self._is_question_unique(question_text, options, self.used_questions):
                self._add_question_to_used(question_text, options, self.used_questions)
                unique_questions.append(q)

        lesson["questions"] = unique_questions

        while len(lesson["questions"]) < self.questions_per_lesson:
            new_question = self._create_default_question(len(lesson["questions"]) + 1, lesson_number, chunk)
            if self._is_question_unique(new_question["question"], new_question["choices"], self.used_questions):
                self._add_question_to_used(new_question["question"], new_question["choices"], self.used_questions)
                lesson["questions"].append(new_question)
            else:
                new_question = self._create_varied_question(len(lesson["questions"]) + 1, lesson_number, chunk)
                self._add_question_to_used(new_question["question"], new_question.get("choices", new_question.get("words", [])), self.used_questions)
                lesson["questions"].append(new_question)

        lesson["questions"] = lesson["questions"][:self.questions_per_lesson]
        return lesson

    def _create_varied_question(self, q_num: int, lesson_num: int, content: str) -> Dict:
        difficulties = ["easy", "medium", "hard"]
        difficulty = difficulties[(q_num - 1) % 3]

        question_templates = [
            f"Theo bài {lesson_num}, yếu tố quan trọng được nhấn mạnh là gì?",
            f"Khái niệm chủ đạo trong bài {lesson_num} liên quan đến?",
            f"Nội dung bài {lesson_num} tập trung giải thích về?",
            f"Điểm cốt lõi của bài {lesson_num} là gì?"
        ]
        answer_templates = [
            ["Nguyên lý cơ bản", "Phương pháp ứng dụng", "Quy trình thực hiện", "Kết quả đạt được"],
            ["Lý thuyết nền tảng", "Thực tiễn áp dụng", "Kinh nghiệm rút ra", "Hướng phát triển"]
        ]
        
        if random.random() > 0.7:
            return {
                "type": "tf",
                "question": f"Khái niệm chủ đạo trong bài {lesson_num} là hoàn toàn chính xác. Đúng hay Sai?",
                "choices": ["Đúng", "Sai"],
                "correct_answer": random.randint(0, 1),
                "difficulty": difficulty
            }
            
        return {
            "type": "mcq",
            "question": random.choice(question_templates),
            "choices": [f"{'ABCD'[i]}. {ans}" for i, ans in enumerate(random.choice(answer_templates))],
            "correct_answer": random.randint(0, 3),
            "difficulty": difficulty
        }

    def _create_default_question(self, q_num: int, lesson_num: int, content: str) -> Dict:
        difficulties = ["easy", "medium", "hard"]
        difficulty = difficulties[(q_num - 1) % 3]

        return {
            "type": "mcq",
            "question": f"Nội dung bài {lesson_num} chủ yếu đề cập đến vấn đề gì?",
            "choices": ["A. Nội dung chính", "B. Ý tưởng chính", "C. Khái niệm cốt lõi", "D. Điểm quan trọng"],
            "correct_answer": random.randint(0, 3),
            "difficulty": difficulty
        }

    def _create_fallback_lesson(self, lesson_number: int, chunk: str) -> Dict:
        content = chunk[:350] + "..." if len(chunk) > 350 else chunk
        words = chunk.split()[:8]
        title = " ".join(words) if words else f"Bài học {lesson_number}"
        if len(title) > 45: title = title[:42] + "..."

        questions = []
        for i in range(self.questions_per_lesson):
            new_question = self._create_varied_question(i + 1, lesson_number, chunk)
            self._add_question_to_used(new_question["question"], new_question.get("choices", ["Đúng", "Sai"]), self.used_questions)
            questions.append(new_question)

        return {"name": f"Bài {lesson_number}", "title": title, "content": content, "questions": questions}

    # =========================
    # QUIZ GENERATION
    # =========================

    def generate_quiz_with_timeout(self, lessons: List[Dict], total_questions: int = 10) -> Dict:
        try:
            return self.generate_quiz(lessons, total_questions)
        except Exception as e:
            return self._create_fallback_quiz(lessons, total_questions)

    def generate_quiz(self, lessons: List[Dict], total_questions: int = 10) -> Dict:
        quiz = {"easy": [], "medium": [], "hard": []}
        min_questions_per_difficulty = 10
        easy_count = max(min_questions_per_difficulty, int(total_questions * 0.4))
        medium_count = max(min_questions_per_difficulty, int(total_questions * 0.4))
        hard_count = max(min_questions_per_difficulty, total_questions - easy_count - medium_count)

        question_id = 1
        for diff, count in [("easy", easy_count), ("medium", medium_count), ("hard", hard_count)]:
            for _ in range(count):
                question = self._generate_unique_quiz_question(question_id, diff, lessons)
                if question:
                    quiz[diff].append(question)
                    question_id += 1
        return quiz

    def _generate_unique_quiz_question(self, q_id: int, difficulty: str, lessons: List[Dict]) -> Dict:
        for attempt in range(10):
            question = self._generate_quiz_question(q_id, difficulty, lessons)
            opts = question.get("choices", question.get("words", ["Đúng", "Sai"]))
            if self._is_question_unique(question["question"], opts, self.used_quiz_questions):
                self._add_question_to_used(question["question"], opts, self.used_quiz_questions)
                return question
            
            question = self._generate_varied_quiz_question(q_id, difficulty, lessons, attempt)
            opts = question.get("choices", question.get("words", ["Đúng", "Sai"]))
            if self._is_question_unique(question["question"], opts, self.used_quiz_questions):
                self._add_question_to_used(question["question"], opts, self.used_quiz_questions)
                return question
        return self._generate_quiz_question(q_id, difficulty, lessons)

    def _generate_varied_quiz_question(self, q_id: int, difficulty: str, lessons: List[Dict], variation: int) -> Dict:
        lesson = random.choice(lessons) if lessons else None
        if not lesson: return self._generate_default_quiz_question(q_id, difficulty)

        title = lesson.get("title", f"Bài {q_id}")
        
        if variation % 4 == 0:
            return {
                "id": q_id, "type": "tf", "difficulty": difficulty,
                "question": f"Khái niệm trong {title} là sai lệch hoàn toàn. Đúng hay Sai?",
                "choices": ["Đúng", "Sai"], "correct_answer": 1
            }
            
        question_templates = [f"Theo {title}, khái niệm cơ bản là gì?", f"Điểm đặc trưng của {title} là?"]
        answer_pools = [["Khái niệm nền tảng", "Phương pháp cơ bản", "Nguyên lý vận hành", "Quy trình thực hiện"]]
        
        return {
            "id": q_id, "type": "mcq", "difficulty": difficulty,
            "question": question_templates[variation % len(question_templates)],
            "choices": [f"{'ABCD'[i]}. {a}" for i, a in enumerate(answer_pools[0])],
            "correct_answer": (variation + q_id) % 4
        }

    def _generate_quiz_question(self, q_id: int, difficulty: str, lessons: List[Dict]) -> Dict:
        lesson = random.choice(lessons) if lessons else None
        if not lesson: return self._generate_default_quiz_question(q_id, difficulty)

        content = lesson.get("content", "")
        title = lesson.get("title", f"Bài {q_id}")
        words = content.split()
        
        if random.random() > 0.8:
            fill_word = words[random.randint(0, min(20, len(words)-1))] if words else "từ khóa"
            return {
                "id": q_id, "type": "fill", "difficulty": difficulty,
                "question": f"Điền vào chỗ trống: Nội dung chính liên quan đến ___.",
                "words": [fill_word, "khái niệm sai 1", "khái niệm sai 2", "khái niệm sai 3"],
                "choices": [fill_word, "khái niệm sai 1", "khái niệm sai 2", "khái niệm sai 3"],
                "correct_answer": 0
            }

        correct_answer = random.randint(0, 3)
        choices = []
        for i in range(4):
            if i == correct_answer and len(words) >= 8:
                choices.append(f"{'ABCD'[i]}. " + " ".join(words[:8])[:50])
            else:
                choices.append(f"{'ABCD'[i]}. Đáp án sai ngẫu nhiên")

        return {"id": q_id, "type": "mcq", "difficulty": difficulty, "question": f"Theo {title}, điểm chính là gì?", "choices": choices, "correct_answer": correct_answer}

    def _generate_default_quiz_question(self, q_id: int, difficulty: str) -> Dict:
        return {"id": q_id, "type": "mcq", "difficulty": difficulty, "question": f"Câu hỏi {q_id} ({difficulty})", "choices": ["A", "B", "C", "D"], "correct_answer": 0}

    def _create_fallback_quiz(self, lessons: List[Dict], total_questions: int) -> Dict:
        quiz = {"easy": [], "medium": [], "hard": []}
        question_id = 1
        for diff, count in [("easy", int(total_questions * 0.4)), ("medium", int(total_questions * 0.4)), ("hard", total_questions - int(total_questions * 0.8))]:
            for _ in range(count):
                q = self._generate_unique_quiz_question(question_id, diff, lessons)
                if q: quiz[diff].append(q); question_id += 1
        return quiz

    def _safe_save_data_files(self, lessons: List[Dict], quiz: Dict) -> bool:
        try:
            total_lesson_questions = sum(len(lesson.get('questions', [])) for lesson in lessons)
            total_quiz_questions = sum(len(q) for q in quiz.values()) if isinstance(quiz, dict) else 0

            lessons_backup = self.lessons_path + '.backup'
            quiz_backup = self.quiz_path + '.backup'

            if os.path.exists(self.lessons_path):
                try: import shutil; shutil.copy2(self.lessons_path, lessons_backup)
                except: pass
            if os.path.exists(self.quiz_path):
                try: import shutil; shutil.copy2(self.quiz_path, quiz_backup)
                except: pass

            lessons_data = {
                "metadata": {
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_lessons": len(lessons),
                    "total_questions": total_lesson_questions,
                },
                "lessons": lessons
            }

            quiz_data = {"metadata": {"total_questions": total_quiz_questions}, **quiz}

            try:
                json.dumps(lessons_data, ensure_ascii=False)
                json.dumps(quiz_data, ensure_ascii=False)
            except: return False

            temp_lessons_path = self.lessons_path + '.tmp'
            with open(temp_lessons_path, 'w', encoding='utf-8') as f: json.dump(lessons_data, f, ensure_ascii=False, indent=2)
            if os.name == 'nt' and os.path.exists(self.lessons_path): os.remove(self.lessons_path)
            os.rename(temp_lessons_path, self.lessons_path)

            temp_quiz_path = self.quiz_path + '.tmp'
            with open(temp_quiz_path, 'w', encoding='utf-8') as f: json.dump(quiz_data, f, ensure_ascii=False, indent=2)
            if os.name == 'nt' and os.path.exists(self.quiz_path): os.remove(self.quiz_path)
            os.rename(temp_quiz_path, self.quiz_path)

            return True
        except Exception:
            try:
                if os.path.exists(lessons_backup): import shutil; shutil.copy2(lessons_backup, self.lessons_path)
                if os.path.exists(quiz_backup): import shutil; shutil.copy2(quiz_backup, self.quiz_path)
            except: pass
            return False

    def stop_processing(self): self.should_stop = True
    def cleanup_cache(self): self.content_cache.clear(); self.used_questions.clear(); self.used_quiz_questions.clear()