import pygame
import json
import os
import config
import time
import hashlib

pygame.init()
pygame.font.init()
pygame.mixer.init()

# Biến global
lesson_click_areas = []
click_sound = None
main_click_sound = None
last_modified_time = 0
list_lesson = []
lessons_content_hash = None  # Hash của nội dung bài học

# Load âm thanh click
click_sound_path = os.path.join(config.ASSETS_DIR, "sounds", "click.wav")
if os.path.exists(click_sound_path):
    click_sound = pygame.mixer.Sound(click_sound_path)


def set_click_sound(sound):
    """Thiết lập âm thanh click từ main.py"""
    global main_click_sound
    main_click_sound = sound


def calculate_lessons_hash(lessons_data):
    """Tính hash của nội dung bài học để phát hiện thay đổi"""
    try:
        # Chuyển lessons data thành string và tính hash
        lessons_str = json.dumps(lessons_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(lessons_str.encode('utf-8')).hexdigest()
    except Exception as e:
        return None


def load_lessons_data():
    """Load lesson data từ JSON"""
    if not os.path.exists(config.LESSON_DATA_FILE_PATH):
        return []
    try:
        with open(config.LESSON_DATA_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file).get("lessons", [])
    except Exception as e:
        return []


def check_for_updates(game_state):
    """Kiểm tra file dữ liệu có thay đổi không và reset completed_lessons nếu cần"""
    global last_modified_time, lessons_content_hash
    
    try:
        current_time = os.path.getmtime(config.LESSON_DATA_FILE_PATH)
        
        # Nếu file đã được modify
        if current_time > last_modified_time:
            last_modified_time = current_time
            
            # Load lessons mới
            new_lessons = load_lessons_data()
            new_hash = calculate_lessons_hash(new_lessons)

            if new_hash:
                # Nếu hash khác hash đã lưu trong game_state
                if game_state.lessons_hash and game_state.lessons_hash != new_hash:
                    game_state.completed_lessons = []
                    game_state.write_data()

                # Cập nhật lại hash hiện tại
                game_state.lessons_hash = new_hash
                lessons_content_hash = new_hash
                game_state.write_data()
            
            return True
    except Exception as e:    
        return False


def wrap_text(text, font, max_width):
    """Chia text thành nhiều dòng theo chiều rộng max_width"""
    words = text.split()
    lines, current_line = [], ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return lines


def draw_wrapped_text(surface, text, font, color, rect, line_height=5):
    """Vẽ text xuống dòng trong một rect"""
    lines = wrap_text(text, font, rect.width)
    y = rect.top
    for line in lines:
        rendered = font.render(line, True, color)
        surface.blit(rendered, (rect.left, y))
        y += font.get_height() + line_height


def handle_lesson_click(mouse_pos, game_state, switch_screen_callback):
    """Xử lý click vào bài học"""
    for area in lesson_click_areas:
        if area["rect"].collidepoint(mouse_pos):
            if main_click_sound:
                main_click_sound.play()
            elif click_sound:
                click_sound.play()
            if game_state.start_lesson(area["lesson_id"]):
                switch_screen_callback(config.SCREEN_KNOWLEDGE_PAGE)
            return True
    return False


def draw_lesson(screen, font_path, font_title, font, colors, game_state, switch_screen_callback, handle_button_click_callback):
    global list_lesson, lesson_click_areas

    screen_width = screen.get_width()
    lesson_click_areas = []  # reset mỗi lần vẽ

    # Fonts
    font_path = os.path.join(config.ASSETS_DIR, "font", "svn.otf")
    header_font = pygame.font.Font(font_path, 40)
    name_font = pygame.font.Font(font_path, 28)
    title_font = pygame.font.Font(font_path, 22)

    # Load dữ liệu mới nếu có cập nhật (sẽ tự động reset completed nếu nội dung thay đổi)
    if check_for_updates(game_state):
        list_lesson = load_lessons_data()
    lessons_data = list_lesson

    # Nếu không có bài học
    if not lessons_data:
        # Tiêu đề chính
        main_title = pygame.font.SysFont("arial", 60, bold=True).render("XIN CHÀO", True, colors["text"])
        screen.blit(main_title, main_title.get_rect(center=(260, 130)))
        # Giới thiệu ngắn
        intro_text = (
            "Gemxcel là ứng dụng học tập tương tác giúp bạn vừa học kiến thức, "
            "vừa trải nghiệm game. Thu thập gem, làm bài tập, và khám phá thế giới học tập thú vị."
        )
        for i, line in enumerate(wrap_text(intro_text, font, 350)):
            surface = font.render(line, True, colors["text"])
            rect = surface.get_rect(center=(260, 200 + i * (surface.get_height() + 5)))
            screen.blit(surface, rect)
        no_data_msg = "Chưa có bài học nào. Hãy đưa cho tôi bài học của bạn ở 'Nạp File'."
        for i, line in enumerate(wrap_text(no_data_msg, font, 335)):
            surface = font.render(line, True, colors["text"])
            rect = surface.get_rect(center=(700, 200 + i * (surface.get_height() + 5)))
            screen.blit(surface, rect)
        return

    # Vẽ tiêu đề "Bài học"
    screen.blit(header_font.render("Bài học", True, colors["text"]), (200, 70))
    pygame.draw.line(screen, colors["text"], (150, 130), (370, 130), 5)

    # Layout
    left_x, right_x = 100, screen_width // 2 + 60
    start_y, spacing_y, max_width = 160, 140, 350
    mouse_pos = pygame.mouse.get_pos()

    for i, lesson in enumerate(lessons_data[:5]):  # tối đa 5 bài
        lesson_id = i + 1
        x = left_x if i < 2 else right_x
        # Tính vị trí y
        if i < 2:
            y = start_y + i * spacing_y
        else:
            y = start_y + (i - 2) * spacing_y
            if i >= 2:   # bài 3 (index = 2)
                y -= 50  # hạ xuống thêm 30px


        rect = pygame.Rect(x, y, max_width, 100)
        is_hover = rect.collidepoint(mouse_pos)
        
        # Kiểm tra bài học đã hoàn thành
        is_completed = lesson_id in game_state.completed_lessons
        
        # Màu trắng nếu đã hoàn thành, màu hover nếu đang hover, màu text mặc định nếu chưa hoàn thành
        if is_completed:
            color = (0, 150, 0)  # xanh cho bài đã hoàn thành
        elif is_hover:
            color = (90, 60, 40)  # nâu đậm khi hover
        else:
            color = colors["hover_button"]  # Màu mặc định

        draw_wrapped_text(screen, lesson.get("name", f"Bài {i+1}"), name_font, color, pygame.Rect(x, y, max_width, 50))
        draw_wrapped_text(screen, lesson.get("title", "Không có tiêu đề"), title_font, color, pygame.Rect(x, y + 40, max_width, 60))

        lesson_click_areas.append({"rect": rect, "lesson_id": lesson_id})