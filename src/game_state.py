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
    def __init__(self, file_path=None):
        self.max_streak = 0
        self.total_quests_completed = 0
        self.click_sound = None
        self.current_music = "bg.mp3"
        self.music_volume = 0.4
        self.owned_avatars = []
        self.avatar_path = os.path.join(config.AVATAR_DIR, "default_avatar.png")
        
        # Use provided file_path or default to config.DATA_FILE_PATH
        if file_path and file_path.strip():
            self.file_path = file_path
        else:
            self.file_path = config.DATA_FILE_PATH
        
        config.logger.debug("[DEBUG] GameState file_path: %s", self.file_path)
        
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

        # Track daily study time
        self.session_study_start_time = datetime.now()
        self.daily_study_seconds = 0

        self.check_login_status()
        self.read_data()

        from config import GEM_TYPES
        self.GEM_TYPES = GEM_TYPES

    def check_login_status(self):
        """Kiểm tra trạng thái đăng nhập từ file auth_session.json"""
        auth_file = self.get_auth_file_path()
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                
                # Lấy session data
                session = session_data.get("session", session_data)
                access_token = session.get("access_token")
                refresh_token = session.get("refresh_token")
                user_data = session.get("user", {})
                
                if access_token and user_data:
                    self.is_logged_in = True
                    self.access_token = access_token
                    self.refresh_token = refresh_token
                    self.user_id = user_data.get("id")
                    self.user_email = user_data.get("email", "")
                    self.user_name = user_data.get("user_metadata", {}).get("username", "")
                    
                    config.logger.info("Tự động đăng nhập thành công cho user: %s", self.user_email)
                    return True
                else:
                    config.logger.warning("File auth_session.json tồn tại nhưng thiếu thông tin cần thiết")
            except Exception as e:
                config.logger.error("Lỗi đọc file auth_session.json: %s", e)
        
        self.is_logged_in = False
        self.access_token = None
        self.refresh_token = None
        self.user_id = ""
        self.user_email = ""
        self.user_name = ""
        return False

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

                # Load daily_study_seconds if same day, reset if new day
                today = date.today()
                if self.last_day == today:
                    self.daily_study_seconds = data.get("daily_study_seconds", 0)
                else:
                    self.daily_study_seconds = 0  # Reset for new day

                # Load timer data
                self.buatangtoc_timer = data.get("buatangtoc_timer", None)
                self.last_point_pack_time = data.get("last_point_pack_time", 0)

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
                "total_quests_completed": self.total_quests_completed,
                "buatangtoc_timer": self.buatangtoc_timer,
                "last_point_pack_time": self.last_point_pack_time,
                "daily_study_seconds": self.daily_study_seconds
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            config.logger.error("Lỗi khi ghi dữ liệu: %s", e)

    def get_auth_file_path(self):
        """Trả về đường dẫn auth_session.json để dùng chung trong toàn bộ GameState."""
        data_dir = os.path.dirname(self.file_path)
        return os.path.join(data_dir, "auth_session.json")

    def save_auth_session(self, session_data):
        """Lưu access_token và refresh_token vào auth_session.json."""
        try:
            auth_file = self.get_auth_file_path()
            os.makedirs(os.path.dirname(auth_file), exist_ok=True)
            with open(auth_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            config.logger.error("Lỗi lưu auth_session.json: %s", e)

    def save_on_exit(self):
        """Lưu dữ liệu local và đồng bộ chỉ khi người dùng thoát ứng dụng."""
        self.write_data()

        if self.is_logged_in and self.user_id:
            try:
                self.sync_stats_to_supabase()
            except Exception as e:
                config.logger.warning("Lỗi khi đồng bộ dữ liệu khi thoát: %s", e)

    # ==========================================
    # CÁC HÀM XỬ LÝ ĐĂNG NHẬP / TOKEN / SUPABASE
    # ==========================================
    
    def check_login_status(self):
        # Lấy thư mục chứa dữ liệu game an toàn
        auth_file = self.get_auth_file_path()
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session_data = data.get("session", data)
                    self.access_token = session_data.get("access_token")
                    self.refresh_token = session_data.get("refresh_token")
                    
                    # Debug: kiểm tra format token
                    if self.access_token:
                        token_parts = self.access_token.split('.')
                        config.logger.debug("[DEBUG] Token parts: %d (expected 3)", len(token_parts))
                        if len(token_parts) != 3:
                            config.logger.error("[DEBUG] ❌ Token format sai! Token: %s", self.access_token[:50])
                    
                    if self.access_token:
                        self.is_logged_in = True
                        self._decode_jwt(self.access_token)
            except Exception as e:
                config.logger.warning("Lỗi đọc auth_session.json: %s", e)

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

        auth_file = self.get_auth_file_path()
        if os.path.exists(auth_file):
            try:
                os.remove(auth_file)
            except Exception:
                pass

    def track_playtime_and_sync(self):
        """Tắt sync định kỳ. Sync chỉ xảy ra khi người dùng thoát ứng dụng."""
        config.logger.debug("[DEBUG] track_playtime_and_sync disabled; sync only on exit")
        return

    def log_daily_study_time(self, study_seconds):
        """Ghi thời gian học hằng ngày vào daily_stats"""
        if not getattr(self, 'user_id', None):
            config.logger.warning("[DEBUG] log_daily_study_time: thiếu user_id")
            return
        if not self.access_token:
            config.logger.warning("[DEBUG] log_daily_study_time: thiếu access_token")
            return

        today = datetime.now().date().isoformat()
        url = f"{SUPABASE_URL}/rest/v1/daily_stats"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "user_id": self.user_id,
            "date": today,
            "study_seconds": study_seconds
        }

        try:
            upsert_url = f"{url}?on_conflict=user_id,date"
            headers["Prefer"] = "return=minimal, resolution=merge-duplicates"
            
            config.logger.info("[DEBUG] Gửi upsert daily_stats cho %s...", today)
            response = requests.post(upsert_url, headers=headers, json=data, timeout=5)
            
            if response.status_code in [200, 201, 204]:
                config.logger.info("✅ Đã ghi daily stats cho ngày %s.", today)
            else:
                config.logger.error("❌ Lỗi ghi daily stats %s: %s", response.status_code, response.text)

        except Exception as e:
            config.logger.error("❌ Lỗi ghi daily stats: %s", e)

    def record_answer(self, is_correct):
        self.total_answered += 1
        if is_correct:
            self.correct_answers += 1

        # Track session counters for daily progress
        if not hasattr(self, 'session_questions_answered'):
            self.session_questions_answered = 0
        if not hasattr(self, 'session_correct_answers'):
            self.session_correct_answers = 0
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = datetime.now()

        self.session_questions_answered += 1
        if is_correct:
            self.session_correct_answers += 1

        # Track daily study time
        current_time = datetime.now()
        if hasattr(self, 'last_answer_time'):
            time_diff = (current_time - self.last_answer_time).total_seconds()
            # Only count if less than 5 minutes (avoid idle time)
            if time_diff < 300:
                self.daily_study_seconds += int(time_diff)
        self.last_answer_time = current_time

        self.write_data()

    def sync_stats_to_supabase(self):
        # 1. Kiểm tra auth
        if not getattr(self, 'user_id', None):
            config.logger.warning("[DEBUG] sync_stats_to_supabase: thiếu user_id")
            return
        if not self.access_token:
            config.logger.warning("[DEBUG] sync_stats_to_supabase: thiếu access_token")
            return
        
        config.logger.info("[DEBUG] Bắt đầu đồng bộ user_stats...")

        url = f"{SUPABASE_URL}/rest/v1/user_stats"
        config.logger.debug("[DEBUG] sync_stats_to_supabase - URL: %s", url)
        config.logger.debug("[DEBUG] sync_stats_to_supabase - Authorization token preview: %s...", self.access_token[:20])
        
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
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
            "max_streak": self.max_streak,
            "total_quests_completed": self.total_quests_completed,
            "collected_gems_count": len(self.collected_gems),
            "owned_avatars_count": len(self.owned_avatars),
            "last_active_date": datetime.now().isoformat()
        }
        config.logger.debug("[DEBUG] sync_stats_to_supabase - Data gửi: %s", data)

        try:
            # Use upsert to avoid update/insert race conditions and ensure row exists.
            upsert_url = f"{url}?on_conflict=user_id"
            config.logger.debug("[DEBUG] sync_stats_to_supabase - Upsert URL: %s", upsert_url)
            
            headers["Prefer"] = "return=minimal, resolution=merge-duplicates"
            config.logger.debug("[DEBUG] sync_stats_to_supabase - Prefer: %s", headers["Prefer"])
            
            config.logger.info("[DEBUG] Gửi upsert user_stats cho user %s...", self.user_id[:8])
            response = requests.post(upsert_url, headers=headers, json=data, timeout=5)
            config.logger.info("[DEBUG] Response status code: %s", response.status_code)

            if response.status_code in [200, 201, 204]:
                config.logger.info("✅ Đồng bộ Supabase thành công (upsert).")
                
                # Log daily study time
                if self.daily_study_seconds > 0:
                    self.log_daily_study_time(self.daily_study_seconds)
                    self.daily_study_seconds = 0  # Reset after logging
                
                return

            # Phân loại lỗi cụ thể
            if response.status_code == 409:
                config.logger.error("❌ Lỗi 409 Conflict (duplicate key): %s", response.text)
            elif response.status_code == 401:
                config.logger.error("❌ Lỗi 401 Unauthorized: Token có thể hết hạn")
            elif response.status_code == 400:
                config.logger.error("❌ Lỗi 400 Bad Request: %s", response.text)
            elif response.status_code == 500:
                config.logger.error("❌ Lỗi 500 Server Error: %s", response.text)
            else:
                config.logger.error("❌ Lỗi %s: %s", response.status_code, response.text)

            # Retry with token refresh if 401
            if response.status_code == 401 and getattr(self, 'refresh_token', None):
                config.logger.info("[DEBUG] Token hết hạn, cố gắng làm mới token...")
                refresh_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
                refresh_data = {"refresh_token": self.refresh_token}
                refresh_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
                config.logger.debug("[DEBUG] Refresh token URL: %s", refresh_url)

                try:
                    res = requests.post(refresh_url, headers=refresh_headers, json=refresh_data, timeout=5)
                    config.logger.info("[DEBUG] Refresh token response: %s", res.status_code)
                    
                    if res.status_code == 200:
                        new_auth = res.json()
                        self.access_token = new_auth.get("access_token")
                        self.refresh_token = new_auth.get("refresh_token")
                        
                        # Debug: kiểm tra token từ refresh response
                        if self.access_token:
                            token_parts = self.access_token.split('.')
                            config.logger.debug("[DEBUG] Refresh token parts: %d (expected 3)", len(token_parts))
                            if len(token_parts) != 3:
                                config.logger.error("[DEBUG] ❌ Refresh token format sai! Token: %s", self.access_token[:50])
                        
                        self.save_auth_session(new_auth)
                        config.logger.info("✅ Làm mới token thành công. Đang gửi lại dữ liệu...")
                        
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        config.logger.debug("[DEBUG] Retry upsert với token mới...")
                        retry_response = requests.post(upsert_url, headers=headers, json=data, timeout=5)
                        
                        if retry_response.status_code in [200, 201, 204]:
                            config.logger.info("✅ Retry thành công!")
                            return
                        else:
                            config.logger.error("❌ Retry thất bại (%s): %s", retry_response.status_code, retry_response.text)
                    else:
                        config.logger.error("❌ Làm mới token thất bại (%s): %s", res.status_code, res.text)
                        config.logger.warning("[DEBUG] Tự động đăng xuất, yêu cầu user login lại")
                        self.logout()
                        return
                        
                except requests.exceptions.Timeout:
                    config.logger.error("❌ Timeout khi làm mới token")
                except requests.exceptions.ConnectionError as e:
                    config.logger.error("❌ Lỗi kết nối khi làm mới token: %s", e)
                except Exception as e:
                    config.logger.error("❌ Lỗi không xác định khi làm mới token: %s", e)
                    
        except requests.exceptions.Timeout:
            config.logger.error("❌ Timeout khi đồng bộ (quá 5 giây)")
        except requests.exceptions.ConnectionError as e:
            config.logger.error("❌ Lỗi kết nối: %s", e)
        except Exception as e:
            config.logger.error("❌ Lỗi không xác định khi đồng bộ: %s - %s", type(e).__name__, e)


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
                # Reset session counters for new day
                self.session_questions_answered = 0
                self.session_correct_answers = 0
                self.session_start_time = datetime.now()

                # Reset daily quests for new day
                if hasattr(self, 'daily_quests') and self.daily_quests:
                    # Import here to avoid circular import
                    from screens.setting_screen import _generate_quests
                    self.daily_quests = _generate_quests(self)

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
            # Cộng dồn thời gian tăng tốc (mỗi bình thêm 60 giây)
            current_time = time.time()
            if self.buatangtoc_timer and self.buatangtoc_timer > current_time:
                # Nếu đang có timer, cộng thêm 60 giây
                self.buatangtoc_timer += 60
                remaining_time = int(self.buatangtoc_timer - current_time)
                self.show_message(f"Đã cộng thêm 60 giây! Tổng thời gian: {remaining_time} giây")
            else:
                # Nếu không có timer hoặc đã hết, set mới 60 giây
                self.buatangtoc_timer = current_time + 60
                self.show_message("Điểm sẽ tăng nhanh trong 60 giây!")
            self.point -= price
            
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
        # Track questions answered in this session
        session_questions = getattr(self, 'session_questions_answered', 0)
        session_correct = getattr(self, 'session_correct_answers', 0)

        self.point += quiz_passed_bonus
        if self.quiz_state["bai"] not in self.completed_lessons:
            self.completed_lessons.append(self.quiz_state["bai"])
        self.show_message("Hoàn thành bài tập!")

        # Reset session counters
        self.session_questions_answered = 0
        self.session_correct_answers = 0

        self.reset_quiz_question_state()
        self.current_screen = config.SCREEN_LESSON
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