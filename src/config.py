#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config file cho Gemxel Project
Xử lý đường dẫn tương thích với PyInstaller
"""

import pygame
import os
import sys

# ===============================
# KHỞI TẠO VÀ THIẾT LẬP CƠ BẢN
# ===============================

# Khởi tạo pygame font system trước khi sử dụng
pygame.font.init()

# Kích thước màn hình
WIDTH, HEIGHT = 960, 640

# ===============================
# XỬ LÝ ĐƯỜNG DẪN CHO PYINSTALLER
# ===============================

def get_resource_path(relative_path):
    """
    Lấy đường dẫn tuyệt đối đến resource (assets), hoạt động cho cả dev và PyInstaller
    Dành cho các file không thay đổi như font, icon, âm thanh
    
    Args:
        relative_path (str): Đường dẫn tương đối từ thư mục gốc
    
    Returns:
        str: Đường dẫn tuyệt đối đến file
    """
    try:
        # PyInstaller tạo temp folder và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Khi chạy bình thường (không đóng gói)
        if getattr(sys, 'frozen', False):
            # Nếu là exe file
            base_path = os.path.dirname(sys.executable)
        else:
            # Khi development
            base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def get_data_path(relative_path):
    """
    Lấy đường dẫn cho data files (có thể ghi/đọc được)
    Dành cho các file dữ liệu như JSON, save files
    
    Args:
        relative_path (str): Đường dẫn tương đối
    
    Returns:
        str: Đường dẫn tuyệt đối có thể ghi được
    """
    if getattr(sys, 'frozen', False):
        # Khi chạy từ exe, lưu data cùng thư mục với exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Khi development, lưu cùng thư mục với script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    data_path = os.path.join(base_path, relative_path)
    
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    return data_path

def get_user_data_path(relative_path):
    """
    Lấy đường dẫn trong thư mục user data (AppData trên Windows)
    Tốt nhất cho việc lưu dữ liệu người dùng
    
    Args:
        relative_path (str): Đường dẫn tương đối
    
    Returns:
        str: Đường dẫn trong thư mục user data
    """
    app_name = "GemxelProject"
    
    if sys.platform == "win32":
        # Windows: %APPDATA%\GemxelProject\
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        base_path = os.path.join(appdata, app_name)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/GemxelProject/
        base_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:
        # Linux: ~/.local/share/GemxelProject/
        base_path = os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)
    
    data_path = os.path.join(base_path, relative_path)
    
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    return data_path

# ===============================
# ĐƯỜNG DẪN CÁC THƯ MỤC VÀ FILE
# ===============================

# Thư mục chính
# đường dẫn file bundle (read-only) trong assets
BUNDLED_DATA_PATH = get_resource_path('assets/tai_nguyen/game_data.json')

# đường dẫn save dùng khi chạy (dev hoặc exe)
# (trong dev -> <project>/src/data/game_data.json ; khi frozen/onedir -> vào thư mục exe)
DATA_SAVE_PATH = get_user_data_path('game_data.json')

BASE_DIR = get_resource_path('')
ASSETS_DIR = get_resource_path('assets/tai_nguyen')

# Các file RESOURCE (không thay đổi) - sử dụng get_resource_path
FONT_PATH = get_resource_path('assets/tai_nguyen/Roboto.ttf')
ICON_PATH = get_resource_path('assets/tai_nguyen/icon.ico')
ICON_DIR = get_resource_path('assets/tai_nguyen/NotoColorEmoji.ttf')
DEFAULT_DIR = get_resource_path('assets/tai_nguyen/setting/default_avatar.png')

# Thư mục con (resources)
AVATAR_DIR = get_resource_path('assets/tai_nguyen/setting')
AI_DIR = get_resource_path('screens/GEM_AI/chatbot_app.py')

# File âm thanh (resources)
SOUND_CORRECT_PATH = get_resource_path('assets/tai_nguyen/audio/success.wav')
SOUND_WRONG_PATH = get_resource_path('assets/tai_nguyen/audio/error.wav')

# ===============================
# ĐƯỜNG DẪN DATA FILES (CÓ THỂ GHI ĐƯỢC)
# ===============================

# Các file DATA (có thể thay đổi) - sử dụng get_data_path hoặc get_user_data_path
DATA_FILE_PATH = get_user_data_path('game_data.json')
QUIZ_DATA_FILE_PATH = get_user_data_path('quiz.json')
LESSON_DATA_FILE_PATH = get_user_data_path('lessons.json')

BUNDLED_GAME_DATA_PATH = get_resource_path('assets/tai_nguyen/game_data.json')
BUNDLED_QUIZ_DATA_PATH = get_resource_path('assets/tai_nguyen/quiz.json')
BUNDLED_LESSON_DATA_PATH = get_resource_path('assets/tai_nguyen/lessons.json')


# ===============================
# KHỞI TẠO FONT VÀ ICON AN TOÀN
# ===============================

def load_font_safely(font_path, size):
    """Load font một cách an toàn, fallback nếu không tìm thấy"""
    try:
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, size)
        else:
            print(f"⚠️ Không tìm thấy font: {font_path}")
            return pygame.font.Font(None, size)  # Sử dụng system font
    except Exception as e:
        print(f"⚠️ Lỗi khi load font: {e}")
        return pygame.font.Font(None, size)

def load_icon_safely(icon_path):
    """Load icon một cách an toàn"""
    try:
        if os.path.exists(icon_path):
            return pygame.image.load(icon_path)
        else:
            print(f"⚠️ Không tìm thấy icon: {icon_path}")
            # Tạo icon mặc định (surface trống)
            icon = pygame.Surface((32, 32))
            icon.fill((255, 255, 255))
            return icon
    except Exception as e:
        print(f"⚠️ Lỗi khi load icon: {e}")
        icon = pygame.Surface((32, 32))
        icon.fill((255, 255, 255))
        return icon

# Khởi tạo font
FONT_SMALL = load_font_safely(FONT_PATH, 22)
FONT = load_font_safely(FONT_PATH, 26)
FONT_TITLE = load_font_safely(FONT_PATH, 47)

# Khởi tạo icon
ICON = load_icon_safely(ICON_PATH)

# ===============================
# ĐỊNH NGHĨA CÁC SCREEN
# ===============================

# Màn hình chính
SCREEN_HOME = "home"
SCREEN_LESSON = "lesson"
SCREEN_SHOP = "shop"
SCREEN_ACCOUNT = "account"
SCREEN_COLLECTION = "collection"
SCREEN_KNOWLEDGE_PAGE = "knowledge_page"
SCREEN_SETTING = "setting"
SCREEN_LOAD = "load"
SCREEN_LOGIN = "login"
# Màn hình quiz/bài tập
SCREEN_QUIZ_SCREEN = "quiz_screen"
SCREEN_QUIZ_EASY = "quiz_easy"
SCREEN_QUIZ_MEDIUM = "quiz_medium"
SCREEN_QUIZ_HARD = "quiz_hard"
SCREEN_EXERCISE = "exercise"
SCREEN_EXERCISE_QUIZ = "exercise_quiz"

# ===============================
# BẢNG MÀU
# ===============================

COLORS = {
    # Màu độ khó
    "difficulty_easy": (100, 200, 100),
    "difficulty_medium": (255, 180, 50),
    "difficulty_hard": (255, 100, 100),
    
    # Màu UI elements
    "card_bg": (255, 255, 255),
    "card_border": (220, 220, 220),
    "text_secondary": (100, 100, 100),
    "progress_bg": (220, 220, 220),
    "progress_fill": (100, 180, 100),
    
    # Màu chủ đạo
    "old_yellow": (220, 200, 100),
    "grellow": (200, 200, 50),
    "yellow": (240, 215, 120),
    "bg": (235, 255, 235),
    "panel": (200, 240, 200),
    "accent": (137, 95, 72),
    "button": (190, 230, 190),
    "hover": (90, 160, 90),
    
    # Màu cơ bản
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "text": (120, 80, 60),
    "text_hover":(99,62,42),
    "hover_button": (137, 95, 72),
    "completed":(128,85,66),
    # Màu chức năng
    "lesson_color": (150, 200, 150),
    "correct": (0, 150, 0),
    "wrong": (200, 0, 0),
}

# ===============================
# DỮ LIỆU CÁC LOẠI ĐÁ QUÝ
# ===============================

GEM_TYPES = [
    {
        "id": 1, 
        "name": "Garnet", 
        "color": (128, 0, 0),
        "description": "Viên đá của lòng dũng cảm. Ánh đỏ rực rỡ, biểu tượng cho sức mạnh, nhiệt huyết và sự lãnh đạo."
    },
    {
        "id": 2, 
        "name": "Sapphire", 
        "color": (220, 220, 220),
        "description": "Viên đá của trí tuệ. Xanh sâu thẳm như đại dương, tượng trưng cho tri thức và sự khôn ngoan."
    },
    {
        "id": 3, 
        "name": "Ruby", 
        "color": (178, 34, 34),
        "description": "Viên đá của sự hồi sinh. Màu xanh ngọc lục bảo đại diện cho sự sống, chữa lành và lòng từ bi."
    },
    {
        "id": 4, 
        "name": "Emerald", 
        "color": (255, 200, 0),
        "description": "Viên đá của may mắn. Ánh sáng vàng óng mang năng lượng tích cực, giúp thu hút vận may và cơ hội."
    },
    {
        "id": 5, 
        "name": "Aluminium", 
        "color": (25, 25, 25),
        "description": "Viên đá của sự tỉnh thức. Tím huyền bí, đại diện cho bình an và trí tuệ tâm linh."
    },
    {
        "id": 6, 
        "name": "Amethyst", 
        "color": (138, 43, 226),
        "description": "Viên đá của ý chí bất diệt. Trong suốt và kiên cố, biểu tượng cho sức mạnh nội tại."
    },
    {
        "id": 7, 
        "name": "Sapphire", 
        "color": (127, 255, 212),
        "description": "Viên đá của bí ẩn và bảo vệ. Màu đen sâu thẳm, giúp xua tan tiêu cực và tăng khả năng tập trung."
    },
    {
        "id": 8, 
        "name": "Peridot", 
        "color": (154, 205, 50),
        "description": "Viên đá của sự tươi mới. Màu xanh non, tượng trưng cho sự đổi mới, niềm vui và phát triển cá nhân."
    },
    {
        "id": 9, 
        "name": "Topaz", 
        "color": (255, 215, 0),
        "description": "Viên đá của cảm hứng. Lấp lánh nhiều màu sắc, giúp kích thích sáng tạo và biểu đạt cảm xúc."
    },
]

# ===============================
# FUNCTION HELPERS CHO DATA MIGRATION
# ===============================

def migrate_old_data():
    """
    Di chuyển dữ liệu từ đường dẫn cũ (nếu có) sang đường dẫn mới
    Chạy hàm này khi khởi động ứng dụng
    """
    old_paths = [
        get_resource_path('assets/tai_nguyen/game_data.json'),
        get_resource_path('assets/tai_nguyen/quiz.json'),
        get_resource_path('assets/tai_nguyen/lessons.json')
    ]
    
    new_paths = [
        DATA_FILE_PATH,
        QUIZ_DATA_FILE_PATH,
        LESSON_DATA_FILE_PATH
    ]
    
    for old_path, new_path in zip(old_paths, new_paths):
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                import shutil
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copy2(old_path, new_path)
                print(f"✅ Đã di chuyển data: {os.path.basename(old_path)}")
            except Exception as e:
                print(f"⚠️ Lỗi khi di chuyển {old_path}: {e}")

def ensure_data_directories():
    """
    Đảm bảo các thư mục data tồn tại
    """
    data_files = [DATA_FILE_PATH, QUIZ_DATA_FILE_PATH, LESSON_DATA_FILE_PATH]
    for file_path in data_files:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

# ===============================
# HIỂN THỊ THÔNG TIN DEBUG
# ===============================

def print_config_info():
    """In thông tin cấu hình để debug"""
    print("=" * 50)
    print("🔧 GEMXEL PROJECT CONFIG")
    print("=" * 50)
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"🎨 Assets Directory: {ASSETS_DIR}")
    print(f"🔤 Font Path: {FONT_PATH}")
    print(f"🖼️ Icon Path: {ICON_PATH}")
    print(f"📊 Screen Size: {WIDTH}x{HEIGHT}")
    print(f"🎮 Pygame Font Initialized: {pygame.font.get_init()}")
    print("--- DATA PATHS ---")
    print(f"💾 Game Data: {DATA_FILE_PATH}")
    print(f"📝 Quiz Data: {QUIZ_DATA_FILE_PATH}")
    print(f"📚 Lesson Data: {LESSON_DATA_FILE_PATH}")
    print(f"🔄 Frozen: {getattr(sys, 'frozen', False)}")
    if hasattr(sys, '_MEIPASS'):
        print(f"📦 PyInstaller Temp: {sys._MEIPASS}")
    print("=" * 50)

# Khởi tạo data directories khi import module
ensure_data_directories()

# Uncomment dòng dưới nếu muốn debug
# print_config_info()