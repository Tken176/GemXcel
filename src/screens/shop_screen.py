# shop_screen.py
import pygame
import config
import os

_images_loaded = False

# Danh sách sản phẩm (chỉ định tên ảnh, giá, tên hiển thị)
shop_items = [
    {"name": "Thẻ bảo vệ streak", "price": 150, "image": "item1.png", "hover": "item1_hover.png"},
    {"name": "Tinh thể kỳ ảo(V.I.P)", "price": 550, "image": "item2.png", "hover": "item2_hover.png"},
    {"name": "Tinh thể kỳ ảo", "price": 470, "image": "item3.png", "hover": "item3_hover.png"},
    {"name": "Gói điểm", "price": 50, "image": "item4.png", "hover": "item4_hover.png"},
    {"name": "Hồi năng lượng", "price": 120, "image": "item5.png", "hover": "item5_hover.png"},
    {"name": "Thuốc tăng tốc điểm", "price": 80, "image": "item6.png", "hover": "item6_hover.png"},
]

def load_item_images():
    """Load và resize ảnh cho các sản phẩm theo tỉ lệ gốc."""
    global _images_loaded
    if _images_loaded:
        return
        
    max_w, max_h = 350, 170  # Giới hạn khung ảnh bên trong ô
    
    for item in shop_items:
        try:
            path_normal = os.path.join(config.ASSETS_DIR, "setting", item["image"])
            path_hover = os.path.join(config.ASSETS_DIR, "setting", item["hover"])
            
            img_normal = pygame.image.load(path_normal).convert_alpha()
            img_hover = pygame.image.load(path_hover).convert_alpha()

            def scale_keep_ratio(img):
                w, h = img.get_size()
                ratio = min(max_w / w, max_h / h)
                return pygame.transform.smoothscale(img, (int(w * ratio), int(h * ratio)))

            item["img_normal"] = scale_keep_ratio(img_normal)
            item["img_hover"] = scale_keep_ratio(img_hover)
        except pygame.error as e:
            print(f"Không thể load ảnh cho {item['name']}: {e}")
            
    _images_loaded = True

def draw_shop(screen, font_title, font, colors, game_state, handle_button_click_callback, items):
    menu_width = 190
    shop_x = menu_width

    # Title
    title = font_title.render("CỬA HÀNG", True, (30, 30, 30))
    title_main = font_title.render("CỬA HÀNG", True, (255, 215, 0))
    screen.blit(title, (shop_x, 50))
    screen.blit(title_main, (shop_x - 3, 52))
    pygame.draw.line(screen, (255, 215, 0), (shop_x - 20, 110), (shop_x + 200, 110), 4)

    item_width, item_height = 300, 170
    item_margin = 140
    items_per_row = 2
    total_row_width = items_per_row * item_width + (items_per_row - 1) * item_margin
    start_x = 110

    for i, item in enumerate(items):
        col = i % items_per_row
        row = i // items_per_row
        x = start_x + col * (item_width + item_margin)
        y = 110 + row * (item_height - 50)

        rect = pygame.Rect(x, y, item_width, item_height)

        img_normal = item.get("img_normal")
        img_hover = item.get("img_hover")

        if img_normal:  # chỉ khi có ảnh mới tính rect
            img_rect = img_normal.get_rect(center=(x + item_width // 2, y + 60))
            mouse_pos = pygame.mouse.get_pos()
            hover = img_rect.collidepoint(mouse_pos)

            # chọn ảnh dựa trên hover
            img = img_hover if hover else img_normal
            screen.blit(img, img_rect)
        else:
            hover = False


        # Tên sản phẩm
        name_text = config.FONT_SMALL.render(item["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(x + item_width // 2 + 30, y + 35))
        screen.blit(name_text, name_rect)

        # Giá sản phẩm
        price_text = font.render(f"{item['price']}", True, (255, 255, 0))
        price_rect = price_text.get_rect(center=(x + item_width // 2 + 25, y + 75))
        screen.blit(price_text, price_rect)

        coin_icon = font.render("$", True, (255, 255, 0))
        screen.blit(coin_icon, (price_rect.right + 3, price_rect.top))

