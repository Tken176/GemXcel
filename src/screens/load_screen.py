import pygame
import tkinter as tk
from tkinter import filedialog
import os
import threading
import math
import config
import ui_elements
from .content_processor import ContentProcessor

SCREEN = pygame.display.set_mode((config.WIDTH, config.HEIGHT))

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path
def render_multiline(text, font, color, x, y, max_width, surface):
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    for i, line in enumerate(lines):
        txt_surface = font.render(line, True, color)
        surface.blit(txt_surface, (x, y + i * (font.get_height() + 4)))

def simulate_cmd_questions(filepath, update_status_callback):
    try:
        processor = ContentProcessor()
        
        if not processor.is_supported(filepath):
            update_status_callback("Định dạng file không được hỗ trợ\n" +
                                 f"Chỉ chấp nhận: {', '.join(processor.supported_formats)}")
            return
            
        def processing_task():
            try:
                update_status_callback("Đang xử lý file...")
                success, message = processor.process_file(filepath)
                update_status_callback(message)
            except Exception as e:
                update_status_callback(f"Lỗi hệ thống: {str(e)}")
        
        # Khởi chạy trong thread riêng
        thread = threading.Thread(target=processing_task)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        update_status_callback(f"Lỗi khởi tạo: {str(e)}")

def run(screen, switch_screen, click_sound=None):
    running = True
    clock = pygame.time.Clock()
    
    title_font = pygame.font.Font(config.FONT_PATH, 42)
    status_font = pygame.font.Font(config.FONT_PATH, 25)
    
    angle = 0
    time_elapsed = 0
    
    should_return = [False]
    status_message = ""
    processing = False
    
    def update_status(message):
        nonlocal status_message
        status_message = message
    
    def back_callback():
        nonlocal should_return
        should_return[0] = True
        switch_screen(config.SCREEN_LESSON)
    
    back_button = ui_elements.Button(
        x=100,
        y=500,
        w=160,
        h=60,
        text="Quay lại",
        callback=back_callback,
        color=config.COLORS["completed"],
        border_radius=15,
        click_sound=click_sound,
    )

    # Vùng upload
    upload_rect = pygame.Rect(115, config.HEIGHT // 2 - 100, 300, 200)

    # Load 2 ảnh (normal + hover)
    normal_path = os.path.join(config.ASSETS_DIR, "setting", "load_icon.png")
    hover_path = os.path.join(config.ASSETS_DIR, "setting", "load_icon_hover.png")

    upload_img = pygame.image.load(normal_path).convert_alpha()
    upload_img = pygame.transform.smoothscale(upload_img, (upload_rect.w, upload_rect.h))

    upload_img_hover = pygame.image.load(hover_path).convert_alpha()
    upload_img_hover = pygame.transform.smoothscale(upload_img_hover, (upload_rect.w, upload_rect.h))

    # Rect ảnh
    upload_img_rect = upload_img.get_rect(center=upload_rect.center)

    while running:
        # Background
        background = os.path.join(config.ASSETS_DIR, "setting", "background.png")
        back_bg = pygame.image.load(background).convert()
        back_bg = pygame.transform.scale(back_bg, (960, 640))  
        SCREEN.blit(back_bg, (0, 0))
        
        time_elapsed += 1
        angle = (angle + 2) % 360

        # Tiêu đề
        title_text = title_font.render("TẢI LÊN TÀI LIỆU", True, config.COLORS["panel"])
        shadow_text = title_font.render("TẢI LÊN TÀI LIỆU", True, (120, 160, 120))
        screen.blit(shadow_text, (104, 102))
        screen.blit(title_text, (100, 100))
        
        long_notes = (
        "***Lưu ý: Chỉ tải lên các file văn bản có định dạng .txt, .docx hoặc .md. "
        "Không gửi file quá ngắn (< 200 từ) . "
        "Không hỗ trợ file nén (.zip, .rar). "
        "File phải sử dụng các dạng mã hóa thông dụng để đảm bảo hiển thị tiếng Việt chính xác."
        )

        render_multiline(
            long_notes, 
            status_font, 
            config.COLORS["completed"], 
            570, 140,   # vị trí x, y
            280,       # max_width: độ rộng tối đa
            screen
        )


        # Check hover
        mouse_pos = pygame.mouse.get_pos()
        if upload_img_rect.collidepoint(mouse_pos):
            screen.blit(upload_img_hover, upload_img_rect)
        else:
            screen.blit(upload_img, upload_img_rect)

        # Hiển thị trạng thái xử lý
        if status_message:
            color = (0, 150, 0) if "True" in status_message else (200, 0, 0)
            lines = status_message.split('\n')
            for i, line in enumerate(lines):
                status_line = status_font.render(line, True, color)
                screen.blit(status_line, (config.WIDTH // 2 - status_line.get_width() // 2, 400 + i * 25))
        
        # Hiệu ứng loading
        if processing:
            pygame.draw.arc(screen, config.COLORS["hover"], 
                          (config.WIDTH // 2 - 20, 450, 40, 40), 
                          math.radians(angle), math.radians(angle + 270), 3)
        
        back_button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            back_button.handle_event(event)
            
            if should_return[0]:
                return None
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Click vào icon upload
                if upload_img_rect.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    selected_file = choose_file()
                    if selected_file:
                        processing = True
                        simulate_cmd_questions(selected_file, lambda msg: (
                            update_status(msg),
                            setattr(type('obj', (object,), {}), 'processing', False)
                        ))

        pygame.display.flip()
        clock.tick(60)
