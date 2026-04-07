import pygame
import json
import config


# =======================
#  Load dữ liệu bài học
# =======================
def load_lessons_data():
    """Tải dữ liệu bài học từ file JSON"""
    try:
        with open(config.LESSON_DATA_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get("lessons", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# =======================
#  Xử lý chia văn bản
# =======================
def wrap_text(content, font, max_width):
    """Chia văn bản thành các dòng vừa với max_width"""
    words = content.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] > max_width:
            if current_line.strip():
                lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line = test_line

    if current_line.strip():
        lines.append(current_line.strip())

    return lines


def wrap_title_text(title_text, font, max_width):
    """Tự động xuống dòng tiêu đề nếu quá dài"""
    return wrap_text(title_text, font, max_width)


# =======================
#  Đếm số trang (spread)
# =======================
def get_page_count(game_state):
    """Lấy tổng số trang (spread) của bài học hiện tại"""
    if hasattr(game_state, 'lesson_spreads'):
        return len(game_state.lesson_spreads)
    return 0


# =======================
#  Vẽ màn hình kiến thức
# =======================
def draw_knowledge_page(screen, font_title, font, colors, game_state, handle_button_click_callback, switch_screen_callback):
    """Vẽ màn hình kiến thức với sách 2 mặt (trái + phải)"""
    lessons_data = load_lessons_data()
    if not lessons_data:
        error_text = font.render("Không tải được dữ liệu bài học", True, colors["text"])
        screen.blit(error_text, (config.WIDTH // 2 - error_text.get_width() // 2, config.HEIGHT // 2))
        return

    lesson_id = game_state.current_lesson_id
    spread_index = game_state.current_page_index  # giờ là spread index

    if not (1 <= lesson_id <= len(lessons_data)):
        error_text = font.render("Bài học không tồn tại", True, colors["text"])
        screen.blit(error_text, (config.WIDTH // 2 - error_text.get_width() // 2, config.HEIGHT // 2))
        return

    current_lesson = lessons_data[lesson_id - 1]

    # -----------------------------
    # Cấu hình vùng hiển thị
    # -----------------------------
    margin_x = 100   # lề trái/phải
    margin_y = 80    # lề trên
    gutter = 150      # khoảng cách giữa 2 mặt giấy
    content_width = (config.WIDTH - margin_x * 2 - gutter) // 2  # chiều rộng mỗi mặt

    # -----------------------------
    # Cache nội dung theo dòng
    # -----------------------------
    if not hasattr(game_state, 'lesson_lines_dict'):
        game_state.lesson_lines_dict = {}

    if lesson_id not in game_state.lesson_lines_dict:
        all_lines = []
        for paragraph in current_lesson["content"].split("\n"):
            if paragraph.strip():
                all_lines.extend(wrap_text(paragraph, font, content_width))
                all_lines.append("")  # dòng trống
        game_state.lesson_lines_dict[lesson_id] = all_lines
        game_state.current_page_index = 0

    all_lines = game_state.lesson_lines_dict[lesson_id]

    # -----------------------------
    # Tính số dòng mỗi mặt
    # -----------------------------
    line_height = font.get_linesize() + 5
    usable_height = config.HEIGHT - margin_y * 2 - 80  # chừa chỗ cho footer
    max_lines_per_face = max(1, usable_height // line_height)

    # -----------------------------
    # Cache spreads
    # -----------------------------
    if not hasattr(game_state, 'lesson_spreads_dict'):
        game_state.lesson_spreads_dict = {}

    if lesson_id not in game_state.lesson_spreads_dict:
        faces = []
        idx = 0
        face_index = 0
        while idx < len(all_lines):
            if face_index == 0:
                # mặt trái đầu tiên có tiêu đề
                title_text = f"{current_lesson['name']}: {current_lesson['title']}"
                title_lines = wrap_title_text(title_text, font_title, content_width)
                title_reserved_lines = len(title_lines) + 1  # +1 dòng trống
                max_lines_this_face = max(1, max_lines_per_face - title_reserved_lines)
            else:
                # các mặt sau: chỉ chừa ít thôi
                bottom_reserved_lines = -1   # thử 1 dòng, hoặc chỉnh về 0 nếu muốn sát mép
                max_lines_this_face = max(1, max_lines_per_face - bottom_reserved_lines)

            faces.append(all_lines[idx:idx + max_lines_this_face])
            idx += max_lines_this_face
            face_index += 1


        # Gom 2 mặt thành 1 spread
        spreads = []
        for i in range(0, len(faces), 2):
            left_face = faces[i]
            right_face = faces[i + 1] if i + 1 < len(faces) else []
            spreads.append((left_face, right_face))

        game_state.lesson_spreads_dict[lesson_id] = spreads
    else:
        spreads = game_state.lesson_spreads_dict[lesson_id]

    game_state.lesson_spreads = spreads

    if spread_index >= len(spreads):
        spread_index = len(spreads) - 1
        game_state.current_page_index = spread_index

    # -----------------------------
    # Vẽ tiêu đề (chỉ trang đầu)
    # -----------------------------
    extra_offset = 0
    if spread_index == 0:
        title_text = f"{current_lesson['name']}: {current_lesson['title']}"
        title_lines = wrap_title_text(title_text, font_title, content_width)
        for i, line in enumerate(title_lines):
            title_surface = font_title.render(line, True, colors["text"])
            screen.blit(title_surface, (margin_x, margin_y + i * (font_title.get_linesize() + 5)))
        extra_offset = len(title_lines) * (font_title.get_linesize() + 5) + 20

    # -----------------------------
    # Vẽ mặt trái
    # -----------------------------
    left_face, right_face = spreads[spread_index]

    y_offset_left = margin_y + extra_offset
    for i, line in enumerate(left_face):
        if line.strip():
            text_surface = font.render(line, True, colors["text"])
            screen.blit(text_surface, (margin_x, y_offset_left + i * line_height))

    # -----------------------------
    # Vẽ mặt phải
    # -----------------------------
    x_offset_right = margin_x + content_width + gutter
    y_offset_right = margin_y
    for i, line in enumerate(right_face):
        if line.strip():
            text_surface = font.render(line, True, colors["text"])
            screen.blit(text_surface, (x_offset_right, y_offset_right + i * line_height))

    # -----------------------------
    # Hiển thị số trang
    # -----------------------------
    page_text = f"Trang {spread_index + 1}/{len(spreads)}"
    page_surface = font.render(page_text, True, colors["text"])
    screen.blit(page_surface, (config.WIDTH - 220, config.HEIGHT - 80))


# =======================
#  Kết thúc & sang quiz
# =======================
def finish_lesson_and_start_quiz(game_state, lesson_id, switch_screen_callback):
    """Kết thúc bài học và chuyển sang màn hình quiz"""
    lessons_data = load_lessons_data()
    if not (1 <= lesson_id <= len(lessons_data)):
        return

    current_lesson = lessons_data[lesson_id - 1]
    quiz_questions = current_lesson.get("questions", [])

    if quiz_questions:
        game_state.quiz_state = {
            "bai": lesson_id,
            "index": 0,
            "answered": False,
            "selected": None,
            "feedback": ""
        }
        switch_screen_callback(config.SCREEN_QUIZ_SCREEN)
    else:
        game_state.point += 50
        if lesson_id not in game_state.completed_lessons:
            game_state.completed_lessons.append(lesson_id)
        game_state.show_message("Bạn đã hoàn thành bài học!")
        switch_screen_callback(config.SCREEN_LESSON)
