import pygame
import config
import os
import webbrowser
import time
from typing import Callable

# --- KHỞI TẠO ÂM THANH ---
try:
    CLICK_SOUND = pygame.mixer.Sound(os.path.join(config.ASSETS_DIR, "audio", "click.mp3"))
except Exception:
    CLICK_SOUND = None

# ==========================================
# HÀM HỖ TRỢ VẼ UI
# ==========================================

def draw_brown_button(screen: pygame.Surface, rect: pygame.Rect, text: str, font: pygame.font.Font, is_hover: bool):
    """Vẽ nút bấm phong cách 3D màu nâu gỗ"""
    color_normal = (140, 80, 25)
    color_hover = (180, 110, 45)
    color_border = (90, 45, 10)
    color_shadow = (60, 30, 10)
    color_highlight = (190, 120, 50)
    color_text = (245, 230, 210)

    bg_color = color_hover if is_hover else color_normal

    # 1. Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(screen, color_shadow, shadow_rect, border_radius=12)

    # 2. Main Body
    pygame.draw.rect(screen, bg_color, rect, border_radius=12)

    # 3. 3D Highlight
    highlight_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width - 6, 4)
    pygame.draw.rect(screen, (210, 140, 60) if is_hover else color_highlight, highlight_rect, border_radius=4)

    # 4. Border
    pygame.draw.rect(screen, color_border, rect, width=2, border_radius=12)

    # 5. Text
    text_surf = font.render(text, True, color_text)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

# ==========================================
# LOGIC XỬ LÝ CHÍNH
# ==========================================

last_login_check = 0

def handle_start_game(game_state, switch_screen_callback):
    """Kiểm tra dữ liệu và nhiệm vụ trước khi vào game"""
    if CLICK_SOUND: 
        CLICK_SOUND.play()
    
    # Đảm bảo nhiệm vụ hằng ngày đã được khởi tạo để tránh lỗi hiển thị ở màn hình sau
    # Thay vì: from setting_screen import init_daily_quests
    try:
        from screens.setting_screen import init_daily_quests
    except ImportError:
        from setting_screen import init_daily_quests # Phòng hờ nếu chạy trực tiếp file trong thư mục
    init_daily_quests(game_state)
    
    # Chuyển đến màn hình học tập
    switch_screen_callback(config.SCREEN_LESSON)

def draw_home(screen: pygame.Surface, game_state, switch_screen_callback: Callable):
    global last_login_check

    # --- CẬP NHẬT TRẠNG THÁI ---
    current_time = time.time()
    if current_time - last_login_check > 2.0: # Kiểm tra mỗi 2 giây để tránh lag
        game_state.check_login_status()
        last_login_check = current_time

    # --- VẼ NỀN & LOGO ---
    try:
        bg = pygame.image.load(os.path.join(config.ASSETS_DIR, "setting", "back.png"))
        screen.blit(pygame.transform.scale(bg, (config.WIDTH, config.HEIGHT)), (0, 0))
    except Exception:
        screen.fill((50, 30, 20))

    try:
        logo = pygame.image.load(os.path.join(config.ASSETS_DIR, "setting", "home_logo.png"))
        screen.blit(pygame.transform.scale(logo, (850, 370)), (70, 50))
    except Exception:
        pass

    # --- QUẢN LÝ CHUỘT ---
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]

    # --- HIỂN THỊ NÚT BẤM ---
    if game_state.is_logged_in:
        # 1. NÚT BẮT ĐẦU (Dùng hình ảnh)
        try:
            btn_img_path = os.path.join(config.ASSETS_DIR, "setting", "button.png")
            btn_hover_path = os.path.join(config.ASSETS_DIR, "setting", "hover_button.png")
            
            img = pygame.image.load(btn_img_path)
            img = pygame.transform.scale(img, (196, 94))
            rect = img.get_rect(topleft=(390, 450))

            if rect.collidepoint(mouse_pos):
                hover_img = pygame.image.load(btn_hover_path)
                screen.blit(pygame.transform.scale(hover_img, (196, 94)), rect)
                if mouse_click:
                    handle_start_game(game_state, switch_screen_callback)
                    pygame.time.delay(200)
            else:
                screen.blit(img, rect)
        except Exception:
            # Fallback nếu thiếu file ảnh
            start_rect = pygame.Rect(390, 450, 196, 70)
            draw_brown_button(screen, start_rect, "BẮT ĐẦU", config.FONT, start_rect.collidepoint(mouse_pos))
            if start_rect.collidepoint(mouse_pos) and mouse_click:
                handle_start_game(game_state, switch_screen_callback)

        # 2. NÚT ĐỔI TÀI KHOẢN
        switch_rect = pygame.Rect(380, 560, 216, 48)
        is_hover = switch_rect.collidepoint(mouse_pos)
        draw_brown_button(screen, switch_rect, "Đổi Tài Khoản", config.FONT, is_hover)
        
        if is_hover and mouse_click:
            if CLICK_SOUND: CLICK_SOUND.play()
            switch_screen_callback("login")
            pygame.time.delay(300)

    else:
        # CHƯA ĐĂNG NHẬP
        login_rect = pygame.Rect(270, 480, 190, 52)
        reg_rect = pygame.Rect(500, 480, 190, 52)

        # Nút Đăng Nhập
        hover_l = login_rect.collidepoint(mouse_pos)
        draw_brown_button(screen, login_rect, "Đăng Nhập", config.FONT, hover_l)
        if hover_l and mouse_click:
            if CLICK_SOUND: CLICK_SOUND.play()
            switch_screen_callback("login")
            pygame.time.delay(300)

        # Nút Đăng Ký (Mở Web)
        hover_r = reg_rect.collidepoint(mouse_pos)
        draw_brown_button(screen, reg_rect, "Đăng Ký", config.FONT, hover_r)
        if hover_r and mouse_click:
            if CLICK_SOUND: CLICK_SOUND.play()
            webbrowser.open("https://gemxcel.pages.dev/")
            pygame.time.delay(300)