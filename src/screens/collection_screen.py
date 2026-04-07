import pygame
import math
import time
import config
import datetime
import os

# ==== Utility functions ====

def draw_shadow_text(screen, text, font, color, pos, shadow_offset=(2,2), shadow_color=(0,0,0,100)):
    """Vẽ text có bóng đổ"""
    surface = font.render(text, True, shadow_color)
    screen.blit(surface, (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]))
    surface = font.render(text, True, color)
    screen.blit(surface, pos)

def draw_polygon_pattern(screen, rect, color, lighten=30, thickness=1):
    """Vẽ hoa văn hình lục giác"""
    cx, cy = rect.center
    size = min(rect.width, rect.height) // 4
    points = [(cx + math.cos(i * math.pi / 3) * size,
               cy + math.sin(i * math.pi / 3) * size) for i in range(6)]
    lighter = tuple(min(255, c + lighten) for c in color)
    pygame.draw.polygon(screen, lighter, points)
    pygame.draw.polygon(screen, (255, 255, 255, 100), points, thickness)

def draw_rect_with_border(screen, rect, bg_color, border_color=None, border_thickness=2, radius=8):
    """Vẽ hình chữ nhật có bo góc và viền"""
    pygame.draw.rect(screen, bg_color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, border_thickness, border_radius=radius)

def load_gem_image(gem_index):
    """Load ảnh gem thật từ thư mục assets/setting"""
    try:
        img_path = os.path.join(config.ASSETS_DIR, "setting", f"gem{gem_index}.png")
        if os.path.exists(img_path):
            return pygame.image.load(img_path)
    except:
        pass
    return None

def draw_gem_glow_effect(screen, center, size, color, now):
    """Vẽ hiệu ứng phát sáng đặc biệt cho viên đá"""
    # Hiệu ứng nhiều vòng tròn gradient từ trong ra ngoài
    num_circles = 6
    base_alpha = int(abs(math.sin(now * 2)) * 40 + 30)
    
    for i in range(num_circles):
        radius = size // 3 + i * 8
        alpha = max(0, base_alpha - i * 10)
        glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        glow_color = (*color, alpha)
        pygame.draw.circle(glow_surface, glow_color, (radius, radius), radius)
        glow_rect = glow_surface.get_rect(center=center)
        screen.blit(glow_surface, glow_rect)
    
    # Thêm các tia sáng xung quanh
    num_rays = 8
    ray_alpha = int(abs(math.sin(now * 3)) * 30 + 20)
    for i in range(num_rays):
        angle = (now * 50 + i * 360 / num_rays) % 360
        rad = math.radians(angle)
        ray_length = size // 2 + 15
        end_x = center[0] + math.cos(rad) * ray_length
        end_y = center[1] + math.sin(rad) * ray_length
        
        ray_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        points = [
            center,
            (center[0] + math.cos(rad - 0.1) * ray_length * 0.3, center[1] + math.sin(rad - 0.1) * ray_length * 0.3),
            (end_x, end_y),
            (center[0] + math.cos(rad + 0.1) * ray_length * 0.3, center[1] + math.sin(rad + 0.1) * ray_length * 0.3)
        ]
        ray_color = (*color, ray_alpha)
        pygame.draw.polygon(ray_surface, ray_color, [(p[0] - center[0] + size, p[1] - center[1] + size) for p in points])
        ray_rect = ray_surface.get_rect(center=center)
        screen.blit(ray_surface, ray_rect)

# ==== Collection Screen ====

def draw_collection(screen, font_title, font, font_small, colors, gem_types, game_state, handle_button_click_callback, draw_multiline_text_func):
    draw_book_header(screen, font_title, colors)
    draw_gems_book_layout(screen, gem_types, game_state, font_small, colors)

    if game_state.viewing_gem:
        draw_gem_detail_right_page(screen, font_title, font, font_small, colors, gem_types, game_state, draw_multiline_text_func)
    else:
        draw_collection_stats_right_page(screen, font, font_small, colors, gem_types, game_state)

def draw_book_header(screen, font_title, colors):
    title = "BỘ SƯU TẬP GEM"
    rect = font_title.render(title, True, colors["accent"]).get_rect(center=(260, 80))
    draw_shadow_text(screen, title, font_title, colors["accent"], rect.topleft)

def draw_collection_stats_right_page(screen, font, font_small, colors, gem_types, game_state):
    collected = {g["id"] for g in game_state.collected_gems}
    count, total = len(collected), len(gem_types)
    percent = (count / total) * 100 if total else 0

    cx = (config.WIDTH * 3) // 4 - 30
    cy = 250

    # Title
    title = font.render("TIẾN TRÌNH SƯU TẬP", True, colors["text"])
    screen.blit(title, title.get_rect(centerx=cx, y=cy))

    # Circle progress
    r = 40
    pygame.draw.circle(screen, colors["progress_bg"], (cx, cy+80), r, 6)
    if percent > 0:
        draw_progress_arc(screen, (cx, cy+80), r, -90, -90 + percent*3.6, colors["difficulty_easy"], 6)

    # Percent text
    pct = font.render(f"{percent:.0f}%", True, colors["accent"])
    screen.blit(pct, pct.get_rect(center=(cx, cy+80)))

    # Stats
    stats = font_small.render(f"{count}/{total} viên đã thu thập", True, colors["text"])
    screen.blit(stats, stats.get_rect(centerx=cx, y=cy+80+r+20))

def draw_gems_book_layout(screen, gem_types, game_state, font_small, colors):
    size, margin_y, spacing = 90, 120, 25
    left_center = config.WIDTH // 4
    margin_x = left_center - (3 * (size + spacing)) // 2 + 30
    now = time.time()

    for i, gem in enumerate(gem_types[:9]):
        row, col = divmod(i, 3)
        x, y = margin_x + col*(size+spacing), margin_y + row*(size+spacing)
        owned = any(g["id"] == gem["id"] for g in game_state.collected_gems)
        draw_gem_card(screen, gem, (x,y), size, owned, now, i, font_small, colors)

def draw_gem_card(screen, gem, pos, size, owned, now, index, font_small, colors):
    """Dùng cho gem nhỏ bên trái"""
    offset = math.sin(now*1.5 + index*0.2) * 3 if owned else 0
    rect = pygame.Rect(pos[0], pos[1]+offset, size, size)
    gem["rect"] = rect

    if owned:
        bg = tuple(min(255, c+80) for c in gem["color"])
        draw_rect_with_border(screen, rect, bg, gem["color"])
        
        # Vẽ ảnh gem thật (index + 1 vì gem1.png, gem2.png,...)
        gem_img = load_gem_image(index + 1)
        if gem_img:
            img_size = int(size * 0.9)
            gem_img_scaled = pygame.transform.scale(gem_img, (img_size, img_size))
            img_rect = gem_img_scaled.get_rect(center=rect.center)
            screen.blit(gem_img_scaled, img_rect)
        else:
            draw_polygon_pattern(screen, rect, gem["color"])
        
        if size >= 60:
            name = font_small.render(gem["name"][:8], True, colors["text"])
            nb = name.get_rect(centerx=rect.centerx, bottom=rect.bottom-5)
            pygame.draw.rect(screen, (255,255,255,180), nb.inflate(6,4), border_radius=3)
            screen.blit(name, nb)
    else:
        draw_rect_with_border(screen, rect, (60,50,40), (40,35,30))
        qf = pygame.font.Font(None, size//2)
        q = qf.render("?", True, (200,180,150))
        screen.blit(q, q.get_rect(center=rect.center))

def draw_progress_arc(screen, center, radius, start_angle, end_angle, color, thickness):
    if end_angle <= start_angle: return
    for i in range(20):
        a1 = math.radians(start_angle + (end_angle-start_angle)*i/20)
        a2 = math.radians(start_angle + (end_angle-start_angle)*(i+1)/20)
        p1 = (center[0]+math.cos(a1)*radius, center[1]+math.sin(a1)*radius)
        p2 = (center[0]+math.cos(a2)*radius, center[1]+math.sin(a2)*radius)
        pygame.draw.line(screen, color, p1, p2, thickness)

def draw_gem_detail_right_page(screen, font_title, font, font_small, colors, gem_types, game_state, draw_multiline_text_func):
    gem = game_state.viewing_gem
    # Tìm index của gem trong danh sách gem_types
    gem_index = next((i for i, g in enumerate(gem_types) if g["id"] == gem["id"]), 0)
    
    panel = pygame.Rect(config.WIDTH//2+40, 120, config.WIDTH//2-80, config.HEIGHT-180)

    # Gem lớn - chỉ hiện ảnh
    size = 140
    gem_center_x = panel.centerx
    gem_center_y = panel.y + 20 + size // 2
    
    # Hiệu ứng lên xuống nhẹ nhàng
    now = time.time()
    float_offset = math.sin(now * 1.5) * 8
    
    # Hiệu ứng xoay nhẹ
    rotation_angle = math.sin(now * 0.8) * 5
    
    # Áp dụng offset lên xuống cho animation
    animated_center_y = gem_center_y + float_offset
    
    # Vẽ hiệu ứng phát sáng đặc biệt phía sau gem
    draw_gem_glow_effect(screen, (gem_center_x, animated_center_y), size, gem["color"], now)
    
    # Vẽ ảnh gem thật (index + 1 vì gem1.png, gem2.png,...)
    gem_img = load_gem_image(gem_index + 1)
    if gem_img:
        img_size = int(size * 1.5)  # Tăng kích thước ảnh
        gem_img_scaled = pygame.transform.scale(gem_img, (img_size, img_size))
        # Xoay ảnh nhẹ
        gem_img_rotated = pygame.transform.rotate(gem_img_scaled, rotation_angle)
        img_rect = gem_img_rotated.get_rect(center=(gem_center_x, animated_center_y))
        screen.blit(gem_img_rotated, img_rect)
        # Tính vị trí tĩnh cho phần thông tin bên dưới (không bị ảnh hưởng animation)
        name_y = gem_center_y + int(size * 1.5) // 2 + 15
    else:
        # Fallback nếu không có ảnh
        gem_rect = pygame.Rect(gem_center_x - size//2, animated_center_y - size//2, size, size)
        draw_rect_with_border(screen, gem_rect, gem["color"], colors["white"], 3, 12)
        draw_polygon_pattern(screen, gem_rect, gem["color"], 50, 2)
        name_y = gem_center_y + size//2 + 40

    # Tên
    name = font_title.render(gem["name"], True, gem["color"])
    name_rect = name.get_rect(centerx=panel.centerx-5, y=name_y-  40)
    screen.blit(name, name_rect)

    # Ngày thu thập
    data = next((g for g in game_state.collected_gems if g["id"] == gem["id"]), None)
    if data and "collected_date" in data:
        try:
            dt = datetime.datetime.strptime(data["collected_date"], "%Y-%m-%d")
            date_str = dt.strftime("%d/%m/%Y")
        except ValueError:
            date_str = data["collected_date"]
        date_rect = pygame.Rect(panel.x, name_rect.bottom + 1, panel.width-40, 35)
        draw_rect_with_border(screen, date_rect, gem["color"], None, 0, 8)
        txt = font_small.render(f"Thu thập ngày: {date_str}", True, colors["white"])
        screen.blit(txt, txt.get_rect(center=date_rect.center))
        desc_y = date_rect.bottom + 5
    else:
        desc_y = name_rect.bottom + 40

    # Mô tả
    desc = pygame.Rect(panel.x, desc_y, panel.width - 40, 190)
    draw_rect_with_border(screen, desc, (235, 225, 210), colors["card_border"], 5, 20)

    # Tính chiều cao đoạn mô tả (nhiều dòng)
    words = gem["description"].split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if font.size(test_line)[0] <= desc.width - 40:  # chừa lề 20px mỗi bên
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Tính tổng chiều cao nội dung
    line_height = font.get_height() + 5
    total_text_height = len(lines) * line_height

    # Điểm bắt đầu để canh giữa theo chiều dọc
    start_y = desc.y + (desc.height - total_text_height) // 2

    # Vẽ từng dòng, canh giữa theo chiều ngang
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, colors["text"])
        text_rect = text_surface.get_rect(centerx=desc.centerx, y=start_y + i * line_height)
        screen.blit(text_surface, text_rect)

    
def set_viewing_gem_to_none(game_state):
    game_state.viewing_gem = None
    game_state.just_closed_detail = True