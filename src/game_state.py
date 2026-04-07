import os
import json
import time
from datetime import date, timedelta, datetime
import random
import config
import threading
import requests
import base64

SUPABASE_URL = "https://hwqlvikkzeybssocyjjn.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3cWx2aWtremV5YnNzb2N5ampuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyMjI0MjIsImV4cCI6MjA5MDc5ODQyMn0.TbE6dcFZsCWh0267JpDm4dQFbWEgIgU3EN5OUXM5CLg"

class GameState:
    def __init__(self, file_path):
        self.max_streak = 0
        self.total_quests_completed = 0
        self.click_sound = None
        self.current_music = "bg.mp3"
        self.music_volume = 0.4
        self.owned_avatars = []
        self.avatar_path = os.path.join(config.AVATAR_DIR, "default_avatar.png")
        self.file_path = file_path
        
        self.completed_lessons = []
        self.exercise_state = None
        self.point = None
        self.energy = None
        self.streak = None
        self.the_streak = None
        self.last_day = None
        self.collected_gems = []
        self.lessons_hash = None  
        self.viewing_gem = None
        self.just_closed_detail = False

        self.purchase_message = ""
        self.message_timer = 0
        self.buatangtoc_timer = None
        self.last_point_pack_time = 0

        self.current_screen = "home"
        self.current_lesson_id = 1
        self.current_page_index = 0
        self.quiz_state = {
            "bai": 1, "index": 0, "feedback": "", "answered": False, "selected": None
        }

        # --- CÁC BIẾN CHO ĐĂNG NHẬP & THỐNG KÊ ---
        self.is_logged_in = False
        self.access_token = None
        self.refresh_token = None # Thêm biến này để làm mới token
        self.user_email = ""
        self.user_name = ""
        self.user_id = ""
        
        self.playtime_minutes = 0
        self.total_answered = 0
        self.correct_answers = 0

        self.check_login_status()
        self.read_data()

        from config import GEM_TYPES
        self.GEM_TYPES = GEM_TYPES

        threading.Thread(target=self.track_playtime_and_sync, daemon=True).start()

    def set_temp_screen(self, screen_name):
        self.temp_screen = screen_name

    def read_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.completed_lessons = data.get("completed_lessons", [])
                self.daily_quests = data.get("daily_quests", None)
                self.point = data.get("point", 99999)
                self.max_streak = data.get("max_streak", 0)
                self.total_quests_completed = data.get("total_quests_completed", 0)
                self.energy = data.get("energy", 10)
                self.streak = data.get("streak", 1)
                self.the_streak = data.get("the_streak", 0)
                self.owned_avatars = data.get("owned_avatars", [self.avatar_path])
                self.lessons_hash = data.get("lessons_hash", None)
                
                avatar_name = data.get("avatar_path", "default_avatar.png")
                self.avatar_path = os.path.join(config.AVATAR_DIR, avatar_name)
                
                self.current_music = data.get("current_music", "bg.mp3")
                self.music_volume = data.get("music_volume", 0.4)

                self.playtime_minutes = data.get("playtime_minutes", 0)
                self.total_answered = data.get("total_answered", 0)
                self.correct_answers = data.get("correct_answers", 0)

                last_day_str = data.get("last_day", date.today().isoformat())
                try:
                    self.last_day = date.fromisoformat(last_day_str)
                except ValueError:
                    self.last_day = date.today()

                self.collected_gems = data.get("collected_gems", [])
            except Exception:
                self._set_default_data()
        else:
            self._set_default_data()
            self.write_data()

    def _set_default_data(self):
        self.completed_lessons = []
        self.max_streak = 0
        self.total_quests_completed = 0
        self.point = 99999
        self.energy = 10
        self.streak = 1
        self.the_streak = 0
        self.last_day = date.today()
        self.collected_gems = []
        self.owned_avatars = [self.avatar_path]
        self.avatar_path = config.DEFAULT_DIR
        self.current_music = "bg.mp3"
        self.music_volume = 0.4
        self.playtime_minutes = 0
        self.total_answered = 0
        self.correct_answers = 0

    def write_data(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            data_to_save = {
                "completed_lessons": self.completed_lessons,
                "lessons_hash": self.lessons_hash,
                "point": self.point,
                "daily_quests": getattr(self, 'daily_quests', None),
                "energy": self.energy,
                "streak": self.streak,
                "the_streak": self.the_streak,
                "last_day": (self.last_day.isoformat() if self.last_day else date.today().isoformat()),
                "owned_avatars": self.owned_avatars,
                "avatar_path": os.path.basename(self.avatar_path),
                "collected_gems": [{k: v for k, v in gem.items() if k != "rect"} for gem in self.collected_gems],
                "current_music": self.current_music,
                "music_volume": self.music_volume,
                "playtime_minutes": self.playtime_minutes,
                "total_answered": self.total_answered,
                "correct_answers": self.correct_answers,
                "max_streak": self.max_streak,
                "total_quests_completed": self.total_quests_completed
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi khi ghi dữ liệu: {e}")

    # ==========================================
    # CÁC HÀM XỬ LÝ ĐĂNG NHẬP / TOKEN / SUPABASE
    # ==========================================
    
    def check_login_status(self):
        # Lấy thư mục chứa dữ liệu game an toàn
        data_dir = os.path.dirname(self.file_path)
        auth_file = os.path.join(data_dir, "auth_session.json")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session_data = data.get("session", data) 
                    self.access_token = session_data.get("access_token")
                    self.refresh_token = session_data.get("refresh_token")
                    
                    if self.access_token:
                        self.is_logged_in = True
                        self._decode_jwt(self.access_token)
            except Exception as e:
                print(f"Lỗi đọc auth_session.json: {e}")

    def _decode_jwt(self, token):
        try:
            payload = token.split('.')[1]
            payload += '=' * (-len(payload) % 4)
            decoded = base64.b64decode(payload).decode('utf-8')
            data = json.loads(decoded)
            self.user_email = data.get('email', '')
            self.user_id = data.get('sub', '')
            user_metadata = data.get('user_metadata', {})
            self.user_name = user_metadata.get('username', '')
        except Exception:
            pass

    def logout(self):
        self.is_logged_in = False
        self.access_token = None
        self.refresh_token = None
        self.user_email = ""
        self.user_name = ""
        self.user_id = ""
        
        # --- BẮT ĐẦU ĐOẠN CẦN SỬA ---
        data_dir = os.path.dirname(self.file_path)
        auth_file = os.path.join(data_dir, "auth_session.json")
        # --- KẾT THÚC ĐOẠN CẦN SỬA ---
        
        if os.path.exists(auth_file):
            try: os.remove(auth_file)
            except Exception: pass

    # ==========================================
    # THỐNG KÊ (HỒ SƠ HỌC TẬP)
    # ==========================================

    def track_playtime_and_sync(self):
        while True:
            time.sleep(60) 
            self.playtime_minutes += 1
            self.write_data()
            
            # --- FIX 1: LIÊN TỤC KIỂM TRA ĐĂNG NHẬP NẾU CHƯA CÓ ---
            # Để khi auth_server.py vừa lưu file json, game sẽ nhận diện được ngay lập tức
            if not self.is_logged_in:
                self.check_login_status()

            if self.is_logged_in and self.user_id:
                self.sync_stats_to_supabase()

    def record_answer(self, is_correct):
        self.total_answered += 1
        if is_correct:
            self.correct_answers += 1
        self.write_data()

    def sync_stats_to_supabase(self):
        if not getattr(self, 'user_id', None) or not self.access_token:
            return

        # --- FIX 2: THÊM on_conflict ĐỂ BIẾT GHI ĐÈ LÊN DÒNG NÀO ---
        url = f"{SUPABASE_URL}/rest/v1/student_stats?on_conflict=user_id"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates, return=representation" 
        }
        
        data = {
            "user_id": self.user_id,
            "email": self.user_email,
            "username": self.user_name,
            "point": self.point,
            "streak": self.streak,
            "completed_lessons_count": len(self.completed_lessons),
            "total_answered": self.total_answered,
            "correct_answers": self.correct_answers,
            "playtime_minutes": self.playtime_minutes,
            "max_streak": self.max_streak, # Cột mới
            "total_quests_completed": self.total_quests_completed, # Cột mới
            "collected_gems_count": len(self.collected_gems), # Tính toán từ list ngọc
            "owned_avatars_count": len(self.owned_avatars), # Tính toán từ list avatar
            "last_active_date": datetime.now().isoformat() # Thời điểm hiện tại
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            
            # --- FIX 3: IN LỖI ĐỂ KIỂM TRA NẾU DATABASE CHẶN QUYỀN ---
            if response.status_code not in [200, 201]:
                print(f"❌ Lỗi đồng bộ Supabase ({response.status_code}): {response.text}")
            else:
                print("✅ Đồng bộ Supabase thành công!")
            
            # --- XỬ LÝ LỖI HẾT HẠN TOKEN ---
            if response.status_code == 401 and getattr(self, 'refresh_token', None):
                print("🔄 Token hết hạn! Hệ thống đang tự động làm mới...")
                refresh_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
                refresh_data = {"refresh_token": self.refresh_token}
                refresh_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
                
                try:
                    res = requests.post(refresh_url, headers=refresh_headers, json=refresh_data, timeout=5)
                    if res.status_code == 200:
                        new_auth = res.json()
                        self.access_token = new_auth.get("access_token")
                        self.refresh_token = new_auth.get("refresh_token")
                        
                        # --- BẮT ĐẦU ĐOẠN CẦN SỬA ---
                        data_dir = os.path.dirname(self.file_path)
                        auth_file = os.path.join(data_dir, "auth_session.json")
                        # --- KẾT THÚC ĐOẠN CẦN SỬA ---
                        
                        with open(auth_file, "w", encoding="utf-8") as f:
                            json.dump(new_auth, f)
                            
                        print("✅ Làm mới Token thành công. Đang gửi lại dữ liệu...")
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        requests.post(url, headers=headers, json=data, timeout=5)
                        return
                    else:
                        # 🔴 THÊM DÒNG NÀY ĐỂ IN RA LỖI CHI TIẾT TỪ SUPABASE
                        print(f"❌ Làm mới token thất bại ({res.status_code}): {res.text}")
                        
                        # Tự động đăng xuất để làm sạch file json, yêu cầu user login lại
                        self.logout() 
                        return
                except Exception as e:
                    print(f"❌ Lỗi mạng khi gọi refresh token: {e}")
                    return

        except Exception as e:
            print(f"❌ Lỗi mạng khi đồng bộ: {e}")


    # --- Background Update Threads ---
    def update_energy_thread(self):
        while True:
            time.sleep(60 * 20)
            if self.energy < 10:
                self.energy += 1
            self.write_data()

    def update_point_thread(self):
        while True:
            sleep_time = 1 if self.buatangtoc_timer and time.time() < self.buatangtoc_timer else 5
            time.sleep(sleep_time)
            if self.point < 999999:
                self.point += 1
            self.write_data()

    def update_streak_thread(self):
        while True:
            time.sleep(10)
            today = date.today()
            if today != self.last_day:
                if today - self.last_day == timedelta(days=1):
                    self.streak += 1
                    self.point += 10
                else:
                    if self.the_streak > 0:
                        self.the_streak -= 1
                    else:
                        self.streak = 1
                self.last_day = today
                self.write_data()
            if self.streak > self.max_streak:
                self.max_streak = self.streak
                self.write_data()    

    def purchase_item(self, item_name, price):
        if self.point < price:
            self.show_message("Không đủ điểm!")
            return
            
        if item_name == "Thẻ bảo vệ streak":
            self.the_streak += 1
            self.point -= price
            self.show_message("Đã mua thẻ bảo vệ streak!")
            
        elif item_name == "Tinh thể kỳ ảo(V.I.P)":
            missing_gems = [g for g in self.GEM_TYPES if not any(cg["id"] == g["id"] for cg in self.collected_gems)]
            if missing_gems:
                new_gem = random.choice(missing_gems).copy()
                new_gem["collected_date"] = date.today().isoformat()
                self.collected_gems.append(new_gem)
                self.point -= price
                self.show_message(f"Bạn nhận được: {new_gem['name']}!")
            else:
                self.show_message("Bạn đã sưu tập đủ 9 viên đá!")
                
        elif item_name == "Tinh thể kỳ ảo":
            # --- FIX: Kiểm tra xem đã đủ 9 viên chưa TRƯỚC KHI bốc ---
            unique_collected = set(g["id"] for g in self.collected_gems)
            if len(unique_collected) >= len(self.GEM_TYPES):
                self.show_message("Bạn đã sưu tập đủ 9 viên đá!")
                return # Dừng ngay tại đây, không bốc thêm đá và không đụng tới tiền!
                
            # Nếu chưa đủ 9 viên, tiến hành bốc random (có thể ra trùng)
            new_gem = random.choice(self.GEM_TYPES).copy()
            new_gem["collected_date"] = date.today().isoformat()
            self.collected_gems.append(new_gem)
            self.point -= price
            
            # Kiểm tra xem viên vừa bốc có phải là viên cuối cùng để hoàn thành bộ sưu tập không
            unique_after = set(g["id"] for g in self.collected_gems)
            if len(unique_after) >= len(self.GEM_TYPES):
                self.show_message(f"Bạn nhận được: {new_gem['name']}! Đã đủ 9 viên!")
            else:
                self.show_message(f"Bạn nhận được: {new_gem['name']}!")
                
        elif item_name == "Gói điểm":
            current_time = time.time()
            if current_time - self.last_point_pack_time >= 10:
                bonus = random.randint(0, 200)
                self.point += bonus - price
                self.last_point_pack_time = current_time
                self.show_message(f"Bạn nhận được {bonus} điểm!")
            else:
                remaining = int(10 - (current_time - self.last_point_pack_time))
                self.show_message(f"Vui lòng đợi {remaining} giây")
                
        elif item_name == "Hồi năng lượng":
            if self.energy >= 10:
                self.show_message("Năng lượng đã đầy!")
            else:
                self.energy = 10
                self.point -= price
                self.show_message("Đã hồi đầy năng lượng!")
                
        elif item_name == "Thuốc tăng tốc điểm":
            self.buatangtoc_timer = time.time() + 60
            self.point -= price
            self.show_message("Điểm sẽ tăng nhanh trong 60 giây!")
            
        self.write_data()
    def complete_lesson(self, lesson_id):
        if lesson_id not in self.completed_lessons:
            self.completed_lessons.append(lesson_id)
            self.write_data()
            
    def start_lesson(self, lesson_id):
        if self.energy > 0:
            self.energy -= 1
            self.current_lesson_id = lesson_id
            self.current_page_index = 0
            self.write_data()
            return True
        else:
            self.show_message("Không đủ năng lượng!")
            return False

    def goto_next_page(self):
        if hasattr(self, "lesson_spreads") and self.current_page_index < len(self.lesson_spreads) - 1:
            self.current_page_index += 1

    def goto_prev_page(self):
        if hasattr(self, "lesson_spreads") and self.current_page_index > 0:
            self.current_page_index -= 1

    def start_quiz(self, lesson_id):
        self.quiz_state["bai"] = lesson_id
        self.quiz_state["index"] = 0
        self.reset_quiz_question_state()

    def reset_quiz_question_state(self):
        self.quiz_state["feedback"] = ""
        self.quiz_state["answered"] = False
        self.quiz_state["selected"] = None

    def quiz_next_question(self):
        self.quiz_state["index"] += 1
        self.reset_quiz_question_state()

    def quiz_finish_session(self, quiz_passed_bonus=0):
        self.point += quiz_passed_bonus
        if self.quiz_state["bai"] not in self.completed_lessons:
            self.completed_lessons.append(self.quiz_state["bai"])
        self.show_message("Hoàn thành bài tập!")
        self.reset_quiz_question_state()
        self.write_data()
        
    def switch_to_lesson_screen(self, screen_name):
        self.current_screen = screen_name
        self.quiz_state = {"bai": None, "index": 0, "answered": False, "selected": None, "feedback": ""}
        self.write_data()

    def show_message(self, msg, duration=3):
        self.purchase_message = msg
        self.message_timer = time.time()

    def check_daily_reset(self):
        today = date.today().isoformat()
        # Nếu ngày hiện tại khác ngày cuối cùng mở game, reset nhiệm vụ
        if getattr(self, 'last_quest_reset_day', "") != today:
            from setting_screen import _generate_quests
            self.daily_quests = _generate_quests(self)
            self.last_quest_reset_day = today
            self.write_data()