import pygame
import ui_elements
import config
import json
import os
import time
import random

# Khai báo biến toàn cục
exercise_data = None
correct_sound = None
wrong_sound = None
click_sound = None
transition_timer = None

# Custom Button để xử lý nhiều dòng text không bị main.py vẽ đè lên
class MultilineButton(ui_elements.Button):
    def __init__(self, x, y, w, h, callback, color, border_radius, click_sound, wrapped_text, font, text_color=(70, 70, 70)):
        super().__init__(x, y, w, h, "", callback, color, border_radius, click_sound)
        self.wrapped_text = wrapped_text
        self.font = font
        self.text_color = text_color

    def draw(self, surface):
        super().draw(surface) # Vẽ nền và hiệu ứng hover
        # Vẽ text lên trên cùng
        text_height = max(1, len(self.wrapped_text)) * self.font.get_linesize()
        line_y = self.rect.y + (self.rect.height - text_height) // 2
        for line in self.wrapped_text:
            c_surf = self.font.render(line, True, self.text_color)
            surface.blit(c_surf, (self.rect.x + (self.rect.width - c_surf.get_width()) // 2, line_y))
            line_y += self.font.get_linesize()

def _wrap_text(text: str, font: pygame.font.Font, max_width: int):
    if not text: return [""]
    lines = []
    paragraphs = str(text).split("\n")
    for para in paragraphs:
        words = para.split(" ")
        cur_line = ""
        for w in words:
            test = (cur_line + " " + w) if cur_line else w
            if font.size(test)[0] <= max_width: cur_line = test
            else:
                if cur_line: lines.append(cur_line)
                cur_line = w
        if cur_line: lines.append(cur_line)
    return lines or [""]

def draw_mode_description(screen, start_y=400, max_width=600):
    lines = [
        "1.Chế độ dễ: Các câu hỏi cơ bản, giúp làm quen và ôn tập kiến thức. Mỗi câu đúng 10 điểm.",
        "2.Chế độ trung bình: Vận dụng lý thuyết và suy luận. Mỗi câu đúng 15 điểm.", 
        "3.Chế độ khó: Đòi hỏi phân tích sâu và tư duy phản biện. Mỗi câu đúng 20 điểm."
    ]
    y = start_y
    for line in lines:
        wrapped = _wrap_text(line, config.FONT_SMALL, max_width)
        for w in wrapped:
            txt = config.FONT_SMALL.render(w, True, (60, 60, 60))
            screen.blit(txt, (540, y))
            y += config.FONT_SMALL.get_linesize()
        y += 15

def set_sounds(correct, wrong):
    global correct_sound, wrong_sound
    correct_sound = correct
    wrong_sound = wrong

def set_click_sound(sound):
    global click_sound
    click_sound = sound

def load_exercise_data():
    global exercise_data
    try:
        with open(config.QUIZ_DATA_FILE_PATH, 'r', encoding='utf-8') as file:
            exercise_data = json.load(file)
            for difficulty in ["easy", "medium", "hard"]:
                if difficulty in exercise_data:
                    for question in exercise_data[difficulty]:
                        if "points" not in question:
                            question["points"] = 10 if difficulty == "easy" else (15 if difficulty == "medium" else 20)
                        
                        q_type = question.get("type", "mcq")
                        if q_type == "tf" and "choices" not in question:
                            question["choices"] = ["Đúng", "Sai"]
                        elif q_type in ["fill", "drag"] and "choices" not in question:
                            question["choices"] = question.get("words", [])
    except Exception as e:
        print(f"Error loading exercise data: {e}")
        exercise_data = {"easy": [], "medium": [], "hard": []}

def create_difficulty_callback(difficulty, game_state, switch_screen_callback):
    def callback():
        if game_state.energy < 1:
            game_state.purchase_message = "Không đủ năng lượng!"
            game_state.message_timer = time.time()
        else:
            start_exercise_session(game_state, difficulty, switch_screen_callback)
    return callback

def draw_exercise(screen, game_state, switch_screen_callback):
    global exercise_data
    if exercise_data is None: load_exercise_data()

    buttons = []
    draw_mode_description(screen, 150, config.WIDTH - 620)

    back_button = ui_elements.Button(100, 50, 120, 50, "Quay lại", lambda: switch_screen_callback(config.SCREEN_LESSON), (120, 80, 60), 10, click_sound)
    buttons.append(back_button)

    difficulty_levels = [
        {"name": "DỄ", "desc": "10 điểm/câu", "diff": "easy", "color": (100, 200, 100)},
        {"name": "TRUNG BÌNH", "desc": "15 điểm/câu", "diff": "medium", "color": (255, 180, 50)},
        {"name": "KHÓ", "desc": "20 điểm/câu", "diff": "hard", "color": (255, 100, 100)},
    ]

    card_y = 120
    for level in difficulty_levels:
        btn = ui_elements.Button(100, card_y + 20, 300, 60, level["name"], create_difficulty_callback(level["diff"], game_state, switch_screen_callback), level["color"], 10, click_sound)
        buttons.append(btn)
        desc = config.FONT_SMALL.render(level["desc"], True, (100, 100, 100))
        screen.blit(desc, (100, card_y + 90))
        card_y += 150

    energy_text = config.FONT_SMALL.render(f"Năng lượng: {game_state.energy}", True, (0, 0, 0))
    screen.blit(energy_text, (config.WIDTH - energy_text.get_width() - 110, 40))

    for button in buttons: button.draw(screen)
    return buttons

def draw_exercise_quiz(screen, game_state, switch_screen_callback):
    global transition_timer
    buttons = []
    exercise_state = game_state.exercise_state

    if not exercise_state or exercise_state["completed"]:
        if transition_timer:
            pygame.time.set_timer(transition_timer, 0)
            transition_timer = None
        switch_screen_callback(config.SCREEN_EXERCISE)
        return buttons

    current_question = exercise_state["questions"][exercise_state["current_question"]]

    # LAYOUT
    margin = 40
    page_width = (config.WIDTH - margin * 3) // 2
    left_x = margin + 50
    right_x = left_x + page_width + margin - 25
    top_y = 150
    content_width = page_width - 70

    # Tiến độ
    counter = config.FONT_SMALL.render(f"Câu {exercise_state['current_question']+1}/{len(exercise_state['questions'])}", True, (80, 120, 80))
    screen.blit(counter, (config.WIDTH - counter.get_width() - 100, config.HEIGHT - 50))

    # --- VẼ CÂU HỎI BÊN TRÁI ---
    title_text = f"Câu {exercise_state['current_question'] + 1}"
    title_surf = config.FONT_TITLE.render(title_text, True, (80, 120, 80))
    screen.blit(title_surf, (left_x, top_y - title_surf.get_height() - 20))

    q_lines = _wrap_text(current_question.get("question", ""), config.FONT, content_width)
    ly = top_y
    for line in q_lines:
        t_surf = config.FONT.render(line, True, (70, 70, 70))
        screen.blit(t_surf, (left_x, ly))
        ly += config.FONT.get_linesize()

    # --- VẼ ĐÁP ÁN BÊN PHẢI ---
    choices = current_question.get("choices", [])
    max_choice_len = max([len(str(c)) for c in choices]) if choices else 0
    is_grid = (len(choices) in [2, 4]) and (max_choice_len <= 35)

    choice_top_y = top_y
    choice_spacing = 15
    y_offset = choice_top_y

    for idx, choice_text in enumerate(choices):
        wrapped_c = _wrap_text(str(choice_text), config.FONT_SMALL, (content_width//2 - 10) if is_grid else (content_width - 10))
        text_height = max(1, len(wrapped_c)) * config.FONT_SMALL.get_linesize()
        btn_h = max(50, text_height + 15)

        if is_grid:
            col = idx % 2
            row = idx // 2
            btn_w = (content_width - choice_spacing) // 2
            btn_x = right_x + col * (btn_w + choice_spacing)
            btn_y = choice_top_y + row * (btn_h + choice_spacing)
            y_offset = max(y_offset, btn_y + btn_h + choice_spacing)
        else:
            btn_w = content_width
            btn_x = right_x
            btn_y = y_offset
            y_offset += btn_h + choice_spacing

        # Màu sắc
        if exercise_state.get("answered", False):
            if idx == current_question["correct_answer"]: color = (100, 200, 100)
            elif idx == exercise_state.get("user_answer"): color = (255, 120, 120)
            else: color = (250, 235, 215)
        else: color = (255, 228, 196)

        # Sử dụng MultilineButton để vẽ cả nền lẫn text
        btn = MultilineButton(
            btn_x, btn_y, btn_w, btn_h,
            lambda i=idx: handle_answer_selection(game_state, i, switch_screen_callback),
            color, 8, click_sound, wrapped_c, config.FONT_SMALL
        )
        buttons.append(btn)

    # Hiển thị feedback
    if exercise_state.get("answered", False):
        is_correct = exercise_state.get("user_answer") == current_question["correct_answer"]
        feedback = "Chính xác!" if is_correct else "Sai rồi."
        feedback_color = (80, 160, 80) if is_correct else (200, 80, 80)
        fb_surf = config.FONT.render(feedback, True, feedback_color)
        screen.blit(fb_surf, (right_x + (content_width - fb_surf.get_width()) // 2, y_offset + 10))

    return buttons

def handle_answer_selection(game_state, answer_index, switch_screen_callback):
    global transition_timer
    state = game_state.exercise_state
    if state.get("answered", False): return
    
    question = state["questions"][state["current_question"]]
    state["user_answer"] = answer_index
    state["answered"] = True

    is_correct = (answer_index == question["correct_answer"])

    if hasattr(game_state, 'record_answer'):
        game_state.record_answer(is_correct)

    if is_correct:
        points = question.get("points", 10 if state["difficulty"] == "easy" else 15 if state["difficulty"] == "medium" else 20)
        state["score"] += points
        if correct_sound: correct_sound.play()
    else:
        if wrong_sound: wrong_sound.play()
    
    if transition_timer: pygame.time.set_timer(transition_timer, 0)
    transition_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(transition_timer, 1500)

def check_timer_event(game_state, switch_screen_callback, event):
    global transition_timer
    if event.type == transition_timer:
        pygame.time.set_timer(transition_timer, 0)
        transition_timer = None
        state = game_state.exercise_state
        if state["current_question"] < len(state["questions"]) - 1:
            state["current_question"] += 1
            state["answered"] = False
            state["user_answer"] = None
        else:
            state["completed"] = True
            show_result(game_state, switch_screen_callback)

def start_exercise_session(game_state, difficulty, switch_screen_callback):
    global exercise_data, transition_timer
    if transition_timer:
        pygame.time.set_timer(transition_timer, 0)
        transition_timer = None
    if game_state.energy < 1:
        game_state.purchase_message = "Không đủ năng lượng!"
        game_state.message_timer = time.time()
        return
    if exercise_data is None: load_exercise_data()

    questions = exercise_data.get(difficulty, [])
    if not questions:
        game_state.purchase_message = f"Không có câu hỏi {difficulty}!"
        game_state.message_timer = time.time()
        return

    game_state.energy -= 1
    game_state.write_data()

    selected = random.sample(questions, min(10, len(questions)))
    game_state.exercise_state = {
        "difficulty": difficulty, "questions": selected, "current_question": 0,
        "score": 0, "completed": False, "user_answer": None, "answered": False,
    }
    switch_screen_callback(config.SCREEN_EXERCISE_QUIZ)

def show_result(game_state, switch_screen_callback):
    state = game_state.exercise_state
    game_state.point += state["score"]
    game_state.purchase_message = f"Hoàn thành! Điểm: {state['score']}"
    game_state.message_timer = time.time()
    switch_screen_callback(config.SCREEN_EXERCISE)