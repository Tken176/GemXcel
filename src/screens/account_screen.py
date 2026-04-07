import pygame
import config
import ui_elements
import os
import time

click_sound = None

def set_click_sound(sound):
    global click_sound
    click_sound = sound

def draw_account(screen, font_title, font, colors, game_state):
    # --- ĐỊNH VỊ 2 TRANG SÁCH ---
    center_x = config.WIDTH // 2
    left_page_center_x = center_x - 220
    right_page_center_x = center_x + 220
    right_page_start_x = center_x + 40

    # Màu mực in cổ điển
    ink_color = (80, 50, 30)

    # Biến kiểm tra popup có đang mở không
    is_popup_open = getattr(game_state, 'show_logout_confirm', False)

    # ==================== TRANG TRÁI ====================
    
    # 1. AVATAR (Góc trên bên trái)
    avatar_x = left_page_center_x
    avatar_y = 160 
    
    pygame.draw.circle(screen, (0, 0, 0, 30), (avatar_x + 2, avatar_y + 3), 55) 
    try:
        avatar_image = pygame.image.load(game_state.avatar_path)
        avatar_image = pygame.transform.scale(avatar_image, (100, 100))
        avatar_rect = avatar_image.get_rect(center=(avatar_x, avatar_y))
        screen.blit(avatar_image, avatar_rect)
        pygame.draw.circle(screen, ink_color, (avatar_x, avatar_y), 50, 3) 
    except Exception:
        pygame.draw.circle(screen, (220, 200, 180), (avatar_x, avatar_y), 50)
        pygame.draw.circle(screen, ink_color, (avatar_x, avatar_y), 50, 3)

    # 2. KHU VỰC TÚI ĐỒ (Vật phẩm)
    inventory_y = avatar_y + 90
    pygame.draw.line(screen, (200, 180, 150), (left_page_center_x - 80, inventory_y - 15), (left_page_center_x + 80, inventory_y - 15), 1)

    # 2.1 Thẻ bảo vệ streak
    shield_count = getattr(game_state, 'the_streak', 0)
    shield_text = font.render(f"Thẻ bảo vệ: {shield_count}", True, ink_color)
    shield_text = pygame.transform.scale(shield_text, (int(shield_text.get_width() * 0.75), int(shield_text.get_height() * 0.75)))
    screen.blit(shield_text, (left_page_center_x - shield_text.get_width()//2, inventory_y))

    # 2.2 Thuốc tăng tốc điểm
    boost_timer = getattr(game_state, 'buatangtoc_timer', None)
    current_time = time.time()
    if boost_timer and current_time < boost_timer:
        remains = int(boost_timer - current_time)
        boost_str = f"Tăng tốc: {remains}s"
        boost_color = (200, 80, 40) # Chữ chuyển sang màu cam
    else:
        boost_str = "Tăng tốc: 0"
        boost_color = ink_color

    boost_text = font.render(boost_str, True, boost_color)
    boost_text = pygame.transform.scale(boost_text, (int(boost_text.get_width() * 0.75), int(boost_text.get_height() * 0.75)))
    screen.blit(boost_text, (left_page_center_x - boost_text.get_width()//2, inventory_y + 35))

    # 3. THANH NĂNG LƯỢNG
    energy = getattr(game_state, 'energy', 0)
    max_energy = 10
    energy_y = inventory_y + 90
    bar_w = 200
    bar_h = 28
    bar_x = left_page_center_x - bar_w // 2

    # Viền và Nền thanh năng lượng
    pygame.draw.rect(screen, (0, 0, 0, 20), (bar_x + 2, energy_y + 2, bar_w, bar_h), border_radius=14) 
    pygame.draw.rect(screen, (230, 220, 200), (bar_x, energy_y, bar_w, bar_h), border_radius=14) 
    pygame.draw.rect(screen, (160, 130, 100), (bar_x, energy_y, bar_w, bar_h), width=2, border_radius=14) 

    # Thanh màu hiển thị Năng lượng
    if energy > 0:
        fill_w = int((energy / max_energy) * (bar_w - 4))
        fill_w = max(fill_w, 14) 
        fill_color = (50, 180, 220) if energy > 2 else (220, 80, 80) 
        pygame.draw.rect(screen, fill_color, (bar_x + 2, energy_y + 2, fill_w, bar_h - 4), border_radius=12)

    # Chỉ số Text
    energy_str = f"Năng lượng: {energy}/{max_energy}"
    en_surf = font.render(energy_str, True, (255, 255, 255) if energy > 3 else ink_color)
    en_surf = pygame.transform.scale(en_surf, (int(en_surf.get_width() * 0.65), int(en_surf.get_height() * 0.65)))
    
    en_shadow = font.render(energy_str, True, (0, 0, 0, 80))
    en_shadow = pygame.transform.scale(en_shadow, (int(en_shadow.get_width() * 0.65), int(en_shadow.get_height() * 0.65)))
    
    screen.blit(en_shadow, (left_page_center_x - en_shadow.get_width()//2 + 1, energy_y + bar_h//2 - en_shadow.get_height()//2 + 1))
    screen.blit(en_surf, (left_page_center_x - en_surf.get_width()//2, energy_y + bar_h//2 - en_surf.get_height()//2))


    # 4. NÚT ĐĂNG XUẤT
    logout_w, logout_h = 130, 45
    logout_rect = pygame.Rect(left_page_center_x - logout_w//2, 530-100, logout_w, logout_h)
    mouse_pos = pygame.mouse.get_pos()
    
    # Chỉ cho phép hover khi popup không mở
    is_hover_logout = logout_rect.collidepoint(mouse_pos) and not is_popup_open
    
    btn_color = (200, 60, 60) if is_hover_logout else (160, 40, 40)
    pygame.draw.rect(screen, (0, 0, 0, 30), logout_rect.move(2, 3), border_radius=8) 
    pygame.draw.rect(screen, btn_color, logout_rect, border_radius=8)
    pygame.draw.rect(screen, ink_color, logout_rect, width=2, border_radius=8)
    
    logout_txt = font.render("Đăng xuất", True, (255, 240, 230))
    logout_txt = pygame.transform.scale(logout_txt, (int(logout_txt.get_width()*0.75), int(logout_txt.get_height()*0.75)))
    screen.blit(logout_txt, (logout_rect.centerx - logout_txt.get_width()//2, logout_rect.centery - logout_txt.get_height()//2))

    if is_hover_logout and pygame.mouse.get_pressed()[0]:
        if click_sound: click_sound.play()
        game_state.show_logout_confirm = True
        pygame.time.delay(200)


    # ==================== TRANG PHẢI ====================

    # 5. TÊN NGƯỜI DÙNG
    raw_name = getattr(game_state, 'user_name', "")
    raw_email = getattr(game_state, 'user_email', "")
    
    # Ưu tiên 1: Tên hiển thị (user_name). Ưu tiên 2: Cắt phần đầu của Gmail. Ưu tiên 3: "Học sinh"
    if raw_name:
        display_name = raw_name
    elif raw_email:
        display_name = raw_email.split('@')[0]
    else:
        display_name = "Học sinh"

    name_surf = font_title.render(display_name, True, ink_color)
    
    max_name_width = 340
    if name_surf.get_width() > max_name_width:
        scale_ratio = max_name_width / name_surf.get_width()
        name_surf = pygame.transform.scale(name_surf, (int(name_surf.get_width() * scale_ratio), int(name_surf.get_height() * scale_ratio)))
    else:
        name_surf = pygame.transform.scale(name_surf, (int(name_surf.get_width() * 0.6), int(name_surf.get_height() * 0.6)))
        
    name_x = right_page_center_x - name_surf.get_width()//2
    name_y = 120
    screen.blit(name_surf, (name_x, name_y))

    # Gạch dưới phân cách
    pygame.draw.line(screen, (180, 150, 120), (right_page_start_x + 20, name_y + 40), (right_page_start_x + 360, name_y + 40), 2)

    # 6. CHỈ SỐ HỌC TẬP (Lưới 2x3)
    total_q = getattr(game_state, 'total_answered', 0)
    correct_q = getattr(game_state, 'correct_answers', 0)
    accuracy = int((correct_q / total_q * 100)) if total_q > 0 else 0
    playtime = getattr(game_state, 'playtime_minutes', 0)

    account_info = [
        {"label": "Chuỗi ngày", "value": f"{game_state.streak} ngày", "color": (210, 80, 30)},
        {"label": "Tổng điểm", "value": str(game_state.point), "color": (180, 120, 0)},
        {"label": "Bài đã học", "value": str(len(game_state.completed_lessons)), "color": (30, 120, 180)},
        {"label": "Đã trả lời", "value": f"{total_q} câu", "color": (130, 60, 180)},
        {"label": "Tỉ lệ đúng", "value": f"{accuracy}%", "color": (40, 140, 80)},
        {"label": "Thời lượng", "value": f"{playtime} phút", "color": (200, 60, 100)},
    ]

    grid_y_start = name_y + 60
    box_w = 160
    box_h = 60
    gap_x = 20
    gap_y = 15
    grid_start_x = right_page_center_x - (box_w + gap_x // 2)

    for idx, info in enumerate(account_info):
        col = idx % 2 
        row = idx // 2 
        bx = grid_start_x + col * (box_w + gap_x)
        by = grid_y_start + row * (box_h + gap_y)

        s_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(s_bg, (255, 250, 235, 200), s_bg.get_rect(), border_radius=8)
        screen.blit(s_bg, (bx, by))
        pygame.draw.rect(screen, (200, 180, 150), (bx, by, box_w, box_h), width=2, border_radius=8)

        lbl_surf = font.render(info["label"], True, (120, 90, 70))
        lbl_surf = pygame.transform.scale(lbl_surf, (int(lbl_surf.get_width()*0.7), int(lbl_surf.get_height()*0.7)))
        screen.blit(lbl_surf, (bx + box_w//2 - lbl_surf.get_width()//2, by + 5))

        val_surf = font.render(info["value"], True, info["color"])
        val_surf = pygame.transform.scale(val_surf, (int(val_surf.get_width()*0.9), int(val_surf.get_height()*0.9)))
        screen.blit(val_surf, (bx + box_w//2 - val_surf.get_width()//2, by + 25))

    # 7. HUY CHƯƠNG & DANH HIỆU
    medal_y = grid_y_start + 3 * (box_h + gap_y) + 20
    draw_static_medal(screen, right_page_center_x - 90, medal_y + 35, game_state, font)
    draw_static_achievement(screen, game_state, font, font_title, right_page_center_x + 60, medal_y + 35)


    # ==================== POPUP XÁC NHẬN ĐĂNG XUẤT ====================
    if is_popup_open:
        # Lớp phủ mờ
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Hộp thoại
        box_w, box_h = 380, 180
        box_rect = pygame.Rect(config.WIDTH//2 - box_w//2, config.HEIGHT//2 - box_h//2, box_w, box_h)
        pygame.draw.rect(screen, (255, 250, 240), box_rect, border_radius=15) 
        pygame.draw.rect(screen, ink_color, box_rect, width=3, border_radius=15) 

        # Text thông báo
        msg = font.render("Bạn có chắc muốn đăng xuất?", True, ink_color)
        msg = pygame.transform.scale(msg, (int(msg.get_width() * 0.9), int(msg.get_height() * 0.9)))
        screen.blit(msg, (box_rect.centerx - msg.get_width()//2, box_rect.y + 40))

        # Nút bấm
        btn_w, btn_h = 110, 45
        yes_rect = pygame.Rect(box_rect.x + 50, box_rect.y + 100, btn_w, btn_h)
        no_rect = pygame.Rect(box_rect.right - 160, box_rect.y + 100, btn_w, btn_h)

        m_x, m_y = pygame.mouse.get_pos()
        hover_yes = yes_rect.collidepoint((m_x, m_y))
        hover_no = no_rect.collidepoint((m_x, m_y))

        # Vẽ nút ĐỒNG Ý
        pygame.draw.rect(screen, (200, 60, 60) if hover_yes else (160, 40, 40), yes_rect, border_radius=8)
        yes_txt = font.render("Có", True, (255,255,255))
        screen.blit(yes_txt, (yes_rect.centerx - yes_txt.get_width()//2, yes_rect.centery - yes_txt.get_height()//2))

        # Vẽ nút HỦY
        pygame.draw.rect(screen, (140, 130, 120) if hover_no else (110, 100, 90), no_rect, border_radius=8)
        no_txt = font.render("Không", True, (255,255,255))
        screen.blit(no_txt, (no_rect.centerx - no_txt.get_width()//2, no_rect.centery - no_txt.get_height()//2))

        # Xử lý click
        if pygame.mouse.get_pressed()[0]:
            if hover_yes:
                if click_sound: click_sound.play()
                game_state.show_logout_confirm = False
                if hasattr(game_state, 'logout'):
                    game_state.logout() 
                else:
                    game_state.is_logged_in = False
                game_state.current_screen = config.SCREEN_HOME
            elif hover_no:
                if click_sound: click_sound.play()
                game_state.show_logout_confirm = False 
            pygame.time.delay(200)


def draw_static_medal(screen, x, y, game_state, font):
    streak = game_state.streak
    if streak < 2: return  

    if 2 <= streak <= 5: 
        outer_color, inner_color, accent_color = (205, 127, 50), (255, 198, 140), (139, 90, 43)
    elif 6 <= streak <= 14: 
        outer_color, inner_color, accent_color = (169, 169, 169), (240, 240, 240), (105, 105, 105)
    else: 
        outer_color, inner_color, accent_color = (218, 165, 32), (255, 223, 0), (184, 134, 11)

    ribbon_w, ribbon_h = 16, 45
    ribbon_y = y + 20
    for offset_x in [-15, 15]:
        pygame.draw.polygon(screen, (180, 30, 30), [
            (x + offset_x - ribbon_w//2, ribbon_y),
            (x + offset_x + ribbon_w//2, ribbon_y),
            (x + offset_x + ribbon_w//2, ribbon_y + ribbon_h),
            (x + offset_x, ribbon_y + ribbon_h - 10),
            (x + offset_x - ribbon_w//2, ribbon_y + ribbon_h)
        ])
        pygame.draw.polygon(screen, (120, 20, 20), [ 
            (x + offset_x - ribbon_w//2, ribbon_y),
            (x + offset_x + ribbon_w//2, ribbon_y),
            (x + offset_x + ribbon_w//2, ribbon_y + ribbon_h),
            (x + offset_x, ribbon_y + ribbon_h - 10),
            (x + offset_x - ribbon_w//2, ribbon_y + ribbon_h)
        ], 2)

    pygame.draw.circle(screen, (0, 0, 0, 30), (x + 2, y + 3), 35) 
    pygame.draw.circle(screen, outer_color, (x, y), 35)
    pygame.draw.circle(screen, inner_color, (x, y), 28)
    pygame.draw.circle(screen, accent_color, (x, y), 28, 3)

    streak_surf = font.render(str(streak), True, (50, 40, 30))
    screen.blit(streak_surf, (x - streak_surf.get_width()//2, y - streak_surf.get_height()//2))


def draw_static_achievement(screen, game_state, font, font_title, center_x, center_y):
    collected = {g["id"] for g in game_state.collected_gems}
    count = len(collected)

    if count < 3: return  

    if 3 <= count <= 5: title, subtitle, border, bg, text = "NEWBIE", "lấp lánh", (160, 160, 170), (250, 250, 250), (50, 50, 70)
    elif 6 <= count <= 8: title, subtitle, border, bg, text = "HUNTER", "đá quý", (230, 180, 0), (255, 252, 240), (100, 70, 0)
    else: title, subtitle, border, bg, text = "MASTER", "sưu tầm", (220, 40, 60), (255, 245, 245), (120, 20, 40)

    box_w, box_h = 160, 80
    box_x = center_x - box_w // 2
    box_y = center_y - box_h // 2
    
    pygame.draw.rect(screen, (0, 0, 0, 20), (box_x+2, box_y+3, box_w, box_h), border_radius=12) 
    pygame.draw.rect(screen, bg, (box_x, box_y, box_w, box_h), border_radius=12)
    pygame.draw.rect(screen, border, (box_x, box_y, box_w, box_h), width=3, border_radius=12)
    
    title_surf = font_title.render(title, True, text)
    title_surf = pygame.transform.scale(title_surf, (int(title_surf.get_width() * 0.5), int(title_surf.get_height() * 0.5)))
    screen.blit(title_surf, (box_x + box_w//2 - title_surf.get_width()//2, box_y + 10))
    
    sub_surf = font.render(subtitle, True, text)
    sub_surf = pygame.transform.scale(sub_surf, (int(sub_surf.get_width() * 0.6), int(sub_surf.get_height() * 0.6)))
    screen.blit(sub_surf, (box_x + box_w//2 - sub_surf.get_width()//2, box_y + 35))
    
    info_surf = font.render(f"Đã sưu tầm: {count} ngọc", True, text)
    info_surf = pygame.transform.scale(info_surf, (int(info_surf.get_width() * 0.6), int(info_surf.get_height() * 0.6)))
    screen.blit(info_surf, (box_x + box_w//2 - info_surf.get_width()//2, box_y + 55))