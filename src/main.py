import pygame
import sys
import time
import threading
import os
import json
import importlib

import config
from game_state import GameState
import ui_elements
import quiz_data as quiz_data_module

# Import các màn hình (Screens)
import screens.home_screen
import screens.login_screen
import screens.lesson_screen
import screens.shop_screen
import screens.account_screen
import screens.collection_screen
import screens.knowledge_page_screen
import screens.exercise_screen
import screens.setting_screen
import screens.load_screen as load_screen
from screens.quiz_screen import draw_quiz_screen

# ==========================================
# KHỞI TẠO HỆ THỐNG & ĐƯỜNG DẪN
# ==========================================

def get_resource_path(relative_path):
    """Lấy đường dẫn đúng đến resource file (Hỗ trợ PyInstaller --onefile)"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def initialize_app():
    """Khởi tạo cấu trúc thư mục và migrate data nếu cần"""
    config.migrate_old_data()
    config.ensure_data_directories()

if __name__ == "__main__":
    initialize_app()

pygame.init()
pygame.mixer.init()

# Cấu hình cửa sổ
SCREEN = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("GEMXCEL")

# Load Icon
icon_path = get_resource_path("icon.ico")
if os.path.exists(icon_path):
    pygame.display.set_icon(pygame.image.load(icon_path))

# ==========================================
# LOAD TÀI NGUYÊN (ÂM THANH & GAME STATE)
# ==========================================

# Âm thanh
click_sound = pygame.mixer.Sound(os.path.join(config.ASSETS_DIR, "audio", "click.mp3"))
correct_sound = pygame.mixer.Sound(config.SOUND_CORRECT_PATH)
wrong_sound = pygame.mixer.Sound(config.SOUND_WRONG_PATH)

# Set âm thanh cho các module
screens.exercise_screen.set_click_sound(click_sound)
screens.lesson_screen.set_click_sound(click_sound)
screens.quiz_screen.set_sounds(correct_sound, wrong_sound)
screens.exercise_screen.set_sounds(correct_sound, wrong_sound)
screens.shop_screen.load_item_images()

# Trạng thái Game
game_state = GameState(file_path=config.DATA_FILE_PATH)

# Phát nhạc nền
# Bạn tìm đoạn code cũ tương tự như vầy và thay thế:

if game_state.current_music:  # <-- Thêm dòng kiểm tra này
    music_path = os.path.join(config.ASSETS_DIR, "audio", game_state.current_music)
    if os.path.exists(music_path):
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(game_state.music_volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Lỗi load nhạc: {e}")

# ==========================================
# BIẾN TOÀN CỤC & HÀM TIỆN ÍCH
# ==========================================

last_click_time = 0
IMAGE_CACHE = {}

def switch_screen(screen_name):
    """Chuyển đổi màn hình"""
    game_state.current_screen = screen_name

def handle_button_click(callback_function, *args):
    """Xử lý nhấn nút chống spam click (delay 200ms)"""
    global last_click_time
    now = time.time()
    if now - last_click_time > 0.2:
        callback_function(*args)
        last_click_time = now

def get_cached_image(name, size=None):
    """Cache hình ảnh để tránh load lại từ ổ cứng mỗi khung hình"""
    key = f"{name}_{size}"
    if key not in IMAGE_CACHE:
        path = os.path.join(config.ASSETS_DIR, "setting", name)
        try:
            img = pygame.image.load(path).convert_alpha()
            if size: img = pygame.transform.scale(img, size)
            IMAGE_CACHE[key] = img
        except Exception:
            IMAGE_CACHE[key] = pygame.Surface(size if size else (50, 50))
    return IMAGE_CACHE[key]

# ==========================================
# CÁC HÀM TẠO GIAO DIỆN (UI GENERATORS)
# ==========================================

SIDEBAR_BUTTONS = []

def init_sidebar_buttons():
    """Tạo sẵn các nút thanh công cụ bên trái một lần duy nhất"""
    global SIDEBAR_BUTTONS
    SIDEBAR_BUTTONS = [
        ui_elements.RecButton(-3, 120, get_cached_image("bai_hoc.png", (75, 47)), get_cached_image("bai_hoc_hover.png", (75, 47)), lambda: switch_screen(config.SCREEN_LESSON), click_sound),
        ui_elements.RecButton(-3, 220, get_cached_image("cua_hang.png", (75, 47)), get_cached_image("cua_hang_hover.png", (74, 47)), lambda: switch_screen(config.SCREEN_SHOP), click_sound),
        ui_elements.RecButton(-3, 320, get_cached_image("tai_khoan.png", (75, 47)), get_cached_image("tai_khoan_hover.png", (75, 47)), lambda: switch_screen(config.SCREEN_ACCOUNT), click_sound),
        ui_elements.RecButton(-3, 420, get_cached_image("bo_suu_tap.png", (75, 47)), get_cached_image("bo_suu_tap_hover.png", (75, 47)), lambda: switch_screen(config.SCREEN_COLLECTION), click_sound)
    ]

# Gọi hàm khởi tạo Sidebar
init_sidebar_buttons()

def get_lesson_buttons():
    """Lấy danh sách các nút riêng cho màn hình Bài học"""
    buttons = []
    quiz_file_exists = os.path.exists(config.QUIZ_DATA_FILE_PATH)
    
    if quiz_file_exists:
        buttons.append(ui_elements.Button(config.WIDTH - 240, 530, 130, 50, "Bài tập", lambda: switch_screen(config.SCREEN_EXERCISE), color=config.COLORS["text"], border_radius=10, click_sound=click_sound))

    load_x = config.WIDTH - 315 if quiz_file_exists else config.WIDTH - 370
    load_y = 42 if quiz_file_exists else 320  
    load_w = 130 if quiz_file_exists else 200
    load_h = 50 if quiz_file_exists else 80
    buttons.append(ui_elements.Button(load_x, load_y, load_w, load_h, "NẠP FILE", lambda: switch_screen(config.SCREEN_LOAD), color=config.COLORS["text"], border_radius=10, click_sound=click_sound))
    
    lessons = screens.lesson_screen.load_lessons_data()
    if lessons:
        for index, lesson in enumerate(lessons):
            lesson_id = index + 1
            buttons.append(ui_elements.TextButton(
                240, 100 + index * 100, "",
                lambda lid=lesson_id: switch_screen(config.SCREEN_KNOWLEDGE_PAGE) if game_state.start_lesson(lid) else None,
                click_sound=click_sound
            ))
    return buttons

def get_knowledge_page_buttons():
    """Lấy các nút điều hướng trong trang lý thuyết"""
    buttons = []
    lesson_id = game_state.current_lesson_id
    spread_index = game_state.current_page_index

    if spread_index > 0:
        buttons.append(ui_elements.Button(config.WIDTH//2 - 150, config.HEIGHT - 110, 100, 50, "Trước", lambda: handle_button_click(game_state.goto_prev_page), config.COLORS["text"], click_sound=click_sound))

    if hasattr(game_state, "lesson_spreads") and spread_index < len(game_state.lesson_spreads) - 1:
        buttons.append(ui_elements.Button(config.WIDTH//2 + 50, config.HEIGHT - 110, 100, 50, "Tiếp", lambda: handle_button_click(game_state.goto_next_page), config.COLORS["text"], click_sound=click_sound))
    else:
        buttons.append(ui_elements.Button(config.WIDTH//2 + 50, config.HEIGHT - 110, 100, 50, "Bài tập", lambda: handle_button_click(screens.knowledge_page_screen.finish_lesson_and_start_quiz, game_state, lesson_id, switch_screen), config.COLORS["text"], click_sound=click_sound))
    return buttons

def update_shop_item_rects():
    """Tính toán và cập nhật lại tọa độ các item trong Shop"""
    screens.shop_screen.item_rects = []
    item_width, item_height = 300, 170
    item_margin, items_per_row = 130, 2
    start_x, start_y = 110, 120

    for index, item in enumerate(screens.shop_screen.shop_items):
        col, row = index % items_per_row, index // items_per_row
        rect = pygame.Rect(start_x + col * (item_width + item_margin), start_y + row * (item_height - 50), item_width, item_height - 83)
        screens.shop_screen.item_rects.append({"rect": rect, "name": item["name"], "price": item["price"]})

# Nút Cài đặt toàn cục
setting_button = ui_elements.CircleButton(
    829, 67, 25, lambda: switch_screen(config.SCREEN_SETTING),
    config.COLORS["text"], hover_color=config.COLORS["text_hover"], click_sound=click_sound
)

# Khởi tạo các Background Threads
threading.Thread(target=game_state.update_energy_thread, daemon=True).start()
threading.Thread(target=game_state.update_point_thread, daemon=True).start()
threading.Thread(target=game_state.update_streak_thread, daemon=True).start()

# ==========================================
# PHÂN LOẠI MÀN HÌNH ĐỂ HIỂN THỊ UI
# ==========================================
SCREENS_WITH_SIDEBAR = [config.SCREEN_LESSON, config.SCREEN_SHOP, config.SCREEN_ACCOUNT, config.SCREEN_COLLECTION]
SCREENS_WITH_STATS = [config.SCREEN_LESSON, config.SCREEN_SHOP, config.SCREEN_COLLECTION]
SCREENS_WITH_SETTING_BTN = [config.SCREEN_LESSON, config.SCREEN_SHOP, config.SCREEN_ACCOUNT, config.SCREEN_COLLECTION, config.SCREEN_SETTING]

# ==========================================
# VÒNG LẶP GAME CHÍNH
# ==========================================

running = True
clock = pygame.time.Clock()
active_buttons = [] # Nút hiện tại trên màn hình
back_bg = pygame.transform.scale(pygame.image.load(os.path.join(config.ASSETS_DIR, "setting", "background.png")), (960, 640))
setting_icon_img = pygame.transform.scale(pygame.image.load(os.path.join(config.ASSETS_DIR, "setting", "setting_icon.png")), (40, 40))

while running:
    # ---------------------------------------------------------
    # 1. XỬ LÝ SỰ KIỆN (Bắt phím, chuột)
    # ---------------------------------------------------------
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Sự kiện click đặc biệt tùy theo màn hình
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.current_screen == config.SCREEN_LESSON:
                screens.lesson_screen.handle_lesson_click(event.pos, game_state, switch_screen)
            elif game_state.current_screen == config.SCREEN_SHOP:
                for item in screens.shop_screen.item_rects:
                    if item["rect"].collidepoint(mouse_pos):
                        game_state.purchase_item(item["name"], item["price"])
            elif game_state.current_screen == config.SCREEN_COLLECTION:
                for gem in config.GEM_TYPES:
                    if "rect" in gem and gem["rect"].collidepoint(event.pos):
                        if any(g["id"] == gem["id"] for g in game_state.collected_gems):
                            if game_state.viewing_gem is None or game_state.viewing_gem["id"] != gem["id"]:
                                game_state.viewing_gem = gem
                                game_state.just_closed_detail = False
                            break

        # Truyền sự kiện bàn phím/chuột vào màn hình Đăng Nhập
        if game_state.current_screen == config.SCREEN_LOGIN:
            screens.login_screen.handle_events(event)

        # Các sự kiện Hệ thống
        if event.type == pygame.USEREVENT + 1:
            screens.exercise_screen.check_timer_event(game_state, switch_screen, event)
        if event.type == pygame.USEREVENT and hasattr(event, 'force_redraw'):
            pass
        if event.type == pygame.USEREVENT + 2: 
            importlib.reload(quiz_data_module)
            
        # Nút cài đặt góc phải
        if game_state.current_screen in SCREENS_WITH_SETTING_BTN:
            setting_button.handle_event(event)

        # Cập nhật các nút tương tác từ frame trước
        for button in active_buttons:
            button.handle_event(event)

    # ---------------------------------------------------------
    # 2. VẼ GIAO DIỆN (Draw Loop)
    # ---------------------------------------------------------
    SCREEN.fill(config.COLORS["bg"])
    SCREEN.blit(back_bg, (0, 0))
    
    # Danh sách nút mới cho frame này
    current_frame_buttons = []

    # --- Vẽ Nội dung từng màn hình ---
    if game_state.current_screen == config.SCREEN_HOME:
        screens.home_screen.draw_home(SCREEN, game_state, switch_screen)
    
    elif game_state.current_screen == config.SCREEN_LOGIN:
        current_frame_buttons.extend(screens.login_screen.draw_login(SCREEN, config.FONT_TITLE, config.FONT, config.COLORS, game_state, switch_screen) or [])
    
    elif game_state.current_screen == config.SCREEN_LESSON:
        screens.lesson_screen.draw_lesson(SCREEN, config.FONT_PATH, config.FONT_TITLE, config.FONT, config.COLORS, game_state, switch_screen, handle_button_click)
        current_frame_buttons.extend(get_lesson_buttons())
        
    elif game_state.current_screen == config.SCREEN_SHOP:
        update_shop_item_rects()
        screens.shop_screen.draw_shop(SCREEN, config.FONT_TITLE, config.FONT, config.COLORS, game_state, handle_button_click, screens.shop_screen.shop_items)
        
    elif game_state.current_screen == config.SCREEN_ACCOUNT:
        screens.account_screen.draw_account(SCREEN, config.FONT_TITLE, config.FONT, config.COLORS, game_state)
        
    elif game_state.current_screen == config.SCREEN_COLLECTION:
        screens.collection_screen.draw_collection(SCREEN, config.FONT_TITLE, config.FONT, config.FONT_SMALL, config.COLORS, config.GEM_TYPES, game_state, handle_button_click, ui_elements.draw_multiline_text)
        if game_state.viewing_gem is not None:
            current_frame_buttons.append(ui_elements.Button(550, 140, 40, 40, "<", lambda: screens.collection_screen.set_viewing_gem_to_none(game_state), click_sound=click_sound))
            
    elif game_state.current_screen == config.SCREEN_KNOWLEDGE_PAGE:
        screens.knowledge_page_screen.draw_knowledge_page(SCREEN, config.FONT_TITLE, config.FONT, config.COLORS, game_state, handle_button_click, switch_screen)
        current_frame_buttons.extend(get_knowledge_page_buttons())
        
    elif game_state.current_screen == config.SCREEN_EXERCISE:
        current_frame_buttons.extend(screens.exercise_screen.draw_exercise(SCREEN, game_state, switch_screen) or [])
        
    elif game_state.current_screen == config.SCREEN_EXERCISE_QUIZ:
        if not hasattr(game_state, 'exercise_state') or game_state.exercise_state is None:
            switch_screen(config.SCREEN_EXERCISE)
        else:
            current_frame_buttons.extend(screens.exercise_screen.draw_exercise_quiz(SCREEN, game_state, switch_screen) or [])
            
    elif game_state.current_screen == config.SCREEN_QUIZ_SCREEN:
        current_frame_buttons.extend(draw_quiz_screen(SCREEN, config.FONT_TITLE, config.FONT, config.FONT_SMALL, config.COLORS, game_state, handle_button_click, quiz_data_module.quiz_data) or [])
        
    elif game_state.current_screen == config.SCREEN_SETTING:
        if hasattr(game_state, 'temp_screen') and game_state.temp_screen == "avatar_selection":
            current_frame_buttons.extend(screens.setting_screen.draw_avatar_selection(screen=SCREEN, game_state=game_state, click_sound=click_sound) or [])
        elif hasattr(game_state, 'temp_screen') and game_state.temp_screen == "music_selection":
            current_frame_buttons.extend(screens.setting_screen.draw_music_selection(screen=SCREEN, game_state=game_state, click_sound=click_sound) or [])
        else:
            current_frame_buttons.extend(screens.setting_screen.draw_setting(screen=SCREEN, game_state=game_state, click_sound=click_sound) or [])
            
    elif game_state.current_screen == config.SCREEN_LOAD:
        if load_screen.run(SCREEN, switch_screen, click_sound) == "quit":
            running = False

    # --- Vẽ Global UI (Thông số, Avatar, Thanh Sidebar, Cài đặt) ---
    if game_state.current_screen in SCREENS_WITH_SETTING_BTN:
        setting_button.draw(SCREEN)
        SCREEN.blit(setting_icon_img, (810, 50))

    if game_state.current_screen in SCREENS_WITH_SIDEBAR:
        current_frame_buttons.extend(SIDEBAR_BUTTONS)

    if game_state.current_screen in SCREENS_WITH_STATS:
        try:
            avatar_img = pygame.transform.scale(pygame.image.load(game_state.avatar_path), (100, 100))
            SCREEN.blit(avatar_img, (320, 470))
        except Exception:
            pygame.draw.circle(SCREEN, config.COLORS["accent"], (65, 60), 50)
        
        SCREEN.blit(config.FONT.render(f"Điểm: {game_state.point}", True, config.COLORS["text"]), (80, config.HEIGHT - 110))
        SCREEN.blit(config.FONT.render(f"Năng lượng: {game_state.energy}", True, config.COLORS["text"]), (80, config.HEIGHT - 150))

    # --- Vẽ các nút bấm thu thập được trong Frame này ---
    for button in current_frame_buttons:
        button.draw(SCREEN)

    # --- Vẽ Thông báo Nổi (Nếu có) ---
    if game_state.purchase_message and time.time() - game_state.message_timer < 3:
        ui_elements.draw_message(SCREEN, game_state.purchase_message, config.FONT, config.COLORS, config.WIDTH, config.HEIGHT)

    # ---------------------------------------------------------
    # 3. KẾT THÚC FRAME
    # ---------------------------------------------------------
    pygame.display.flip()
    
    # Cập nhật mảng Nút bấm cho vòng lặp sự kiện tiếp theo
    active_buttons = current_frame_buttons
    
    # Giới hạn tốc độ khung hình (60 FPS)
    clock.tick(60)

# ==========================================
# LƯU TRẠNG THÁI & THOÁT
# ==========================================
game_state.write_data()
pygame.quit()
sys.exit()