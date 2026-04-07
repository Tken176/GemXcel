import pygame
import config
import ui_elements
import time
import os
import json
import importlib

correct_sound = None
wrong_sound = None

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

def set_sounds(correct, wrong):
    global correct_sound, wrong_sound
    correct_sound = correct
    wrong_sound = wrong

def _wrap_text(text: str, font: pygame.font.Font, max_width: int):
    if not text: return [""]
    lines = []
    paragraphs = str(text).split("\n")
    for para in paragraphs:
        words = para.split(" ")
        cur_line = ""
        for w in words:
            test = (cur_line + " " + w) if cur_line else w
            if font.size(test)[0] <= max_width:
                cur_line = test
            else:
                if cur_line: lines.append(cur_line)
                cur_line = w
        if cur_line: lines.append(cur_line)
    return lines or [""]

def _ensure_quiz_state(game_state):
    if not hasattr(game_state, "quiz_state") or not isinstance(game_state.quiz_state, dict):
        game_state.quiz_state = {"bai": getattr(game_state, "current_lesson_id", None), "index": 0, "answered": False, "selected": None, "feedback": ""}

def draw_quiz_screen(screen, font_title, font, font_small, colors, game_state, handle_button_click_callback, all_quiz_data):
    _ensure_quiz_state(game_state)

    current_bai = game_state.quiz_state.get("bai")
    if not isinstance(all_quiz_data, dict) or current_bai not in all_quiz_data or not all_quiz_data.get(current_bai):
        ui_elements.draw_text_centered(screen, "Không có bài tập cho bài này.", config.WIDTH // 2, config.HEIGHT // 2, font, colors.get("text", (0, 0, 0)))
        return []

    current_index = game_state.quiz_state.get("index", 0)
    total_q = len(all_quiz_data[current_bai])
    if current_index >= total_q: current_index = 0
    q = all_quiz_data[current_bai][current_index]

    # LAYOUT
    margin = 40
    page_width = (config.WIDTH - margin * 3) // 2
    left_x = margin + 50
    right_x = left_x + page_width + margin - 25
    top_y = 150
    content_width = page_width - 70

    # --- VẼ CÂU HỎI BÊN TRÁI ---
    title_text = f"Câu {current_index + 1}"
    title_surf = font_title.render(title_text, True, (80, 120, 80))
    screen.blit(title_surf, (left_x, top_y - title_surf.get_height() - 20))

    q_lines = _wrap_text(q.get("question", ""), font, content_width)
    ly = top_y
    for line in q_lines:
        t_surf = font.render(line, True, (70, 70, 70))
        screen.blit(t_surf, (left_x, ly))
        ly += font.get_linesize()

    # --- VẼ ĐÁP ÁN BÊN PHẢI ---
    buttons = []
    choices = q.get("choices", [])
    
    max_choice_len = max([len(str(c)) for c in choices]) if choices else 0
    is_grid = (len(choices) in [2, 4]) and (max_choice_len <= 35)

    choice_top_y = top_y
    choice_spacing = 15
    y_offset = choice_top_y

    for idx, choice_text in enumerate(choices):
        wrapped_c = _wrap_text(str(choice_text), font_small, (content_width//2 - 10) if is_grid else (content_width - 10))
        text_height = max(1, len(wrapped_c)) * font_small.get_linesize()
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

        # Màu sắc khi đã trả lời
        if game_state.quiz_state.get("answered"):
            if idx == q.get("answer"): color = (100, 200, 100)
            elif idx == game_state.quiz_state.get("selected"): color = (255, 120, 120)
            else: color = (230, 230, 230)
        else:
            color = (250, 235, 215)

        # Sử dụng MultilineButton để vẽ cả nền lẫn text
        btn = MultilineButton(
            btn_x, btn_y, btn_w, btn_h,
            lambda i=idx, bai=current_bai, idx_q=current_index: handle_button_click_callback(check_answer_mcq, game_state, bai, idx_q, i),
            color, 8, None, wrapped_c, font_small
        )
        buttons.append(btn)

    # --- VẼ FEEDBACK VÀ NÚT NEXT ---
    if game_state.quiz_state.get("answered"):
        feedback = game_state.quiz_state.get("feedback", "")
        feedback_color = (80, 160, 80) if feedback == "Chính xác!" else (200, 80, 80)
        fb_surf = font.render(feedback, True, feedback_color)
        screen.blit(fb_surf, (right_x + (content_width - fb_surf.get_width()) // 2, y_offset + 10))

        btn_w, btn_h = 160, 45
        btn_x = right_x + (content_width - btn_w) // 2
        btn_y = config.HEIGHT - btn_h - 40

        if current_index < total_q - 1:
            nxt_btn = ui_elements.Button(btn_x, btn_y, btn_w, btn_h, "Câu tiếp theo", lambda: handle_button_click_callback(next_quiz_question, game_state), (100, 180, 100), 10, None)
            nxt_btn.draw(screen)
            buttons.append(nxt_btn)
        else:
            fin_btn = ui_elements.Button(btn_x, btn_y, btn_w, btn_h, "Hoàn thành", lambda: handle_button_click_callback(finish_quiz_session, game_state), (100, 180, 100), 10, None)
            fin_btn.draw(screen)
            buttons.append(fin_btn)

    # Hiển thị số câu (VD: Câu 1/10)
    prog_surf = font_small.render(f"Câu {current_index + 1}/{total_q}", True, (0, 0, 0))
    screen.blit(prog_surf, (10, config.HEIGHT - prog_surf.get_height() - 10))

    return buttons

def reload_quiz_data(game_state):
    pass

def check_answer_mcq(game_state, bai, idx, selected):
    if game_state.quiz_state.get("answered"): return

    try: from quiz_data import quiz_data as all_quiz_data
    except Exception: return

    if bai not in all_quiz_data or idx >= len(all_quiz_data.get(bai, [])): return
    q = all_quiz_data[bai][idx]

    is_correct = (q.get("answer") == selected)
    game_state.quiz_state.update({
        "selected": selected,
        "answered": True,
        "feedback": "Chính xác!" if is_correct else "Sai rồi."
    })

    if hasattr(game_state, 'record_answer'):
        game_state.record_answer(is_correct)

    if is_correct:
        try: game_state.point += 10
        except Exception: pass
        if correct_sound:
            try: correct_sound.play()
            except Exception: pass
    else:
        if wrong_sound:
            try: wrong_sound.play()
            except Exception: pass

    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'force_redraw': True}))

def finish_quiz_session(game_state, bonus_points=50):
    try: game_state.point += bonus_points
    except Exception: pass
    try: game_state.completed_lessons.append(game_state.quiz_state.get("bai"))
    except Exception: pass
    game_state.quiz_state = {"bai": None, "index": 0, "answered": False, "selected": None, "feedback": ""}
    game_state.current_screen = config.SCREEN_LESSON
    try: game_state.write_data()
    except Exception: pass

def next_quiz_question(game_state):
    game_state.quiz_state["index"] += 1
    game_state.quiz_state["answered"] = False
    game_state.quiz_state["selected"] = None
    game_state.quiz_state["feedback"] = ""
    try: game_state.write_data()
    except Exception: pass
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'force_redraw': True}))