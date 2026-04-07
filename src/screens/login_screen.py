import pygame
import config
import ui_elements
import requests
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox

# ==========================================
# CẤU HÌNH API
# ==========================================
SUPABASE_URL = "https://hwqlvikkzeybssocyjjn.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3cWx2aWtremV5YnNzb2N5ampuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyMjI0MjIsImV4cCI6MjA5MDc5ODQyMn0.TbE6dcFZsCWh0267JpDm4dQFbWEgIgU3EN5OUXM5CLg"

# Biến lưu trạng thái để Pygame và Tkinter không bị xung đột
bg_image = None
login_state = {
    "window_open": False
}

# ==========================================
# CỬA SỔ TKINTER (GIAO DIỆN ĐĂNG NHẬP NATIVE)
# ==========================================
def launch_tkinter_login(game_state, switch_screen_callback):
    """Mở cửa sổ Tkinter để hưởng lợi từ bộ gõ tiếng Việt native của hệ điều hành"""
    root = tk.Tk()
    root.title("GEMXCEL - Đăng Nhập")
    
    # Cấu hình kích thước và căn giữa màn hình Desktop
    w, h = 360, 460
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = int((ws/2) - (w/2))
    y = int((hs/2) - (h/2))
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.resizable(False, False)
    
    # Bảng màu đồng bộ
    BG_COLOR = "#281A13"   # Nền nâu đậm
    FG_COLOR = "#EED4B6"   # Chữ màu da/kem
    INPUT_BG = "#412A1E"   # Nền ô input
    BTN_BG   = "#B97232"   # Nút bấm cam/nâu
    
    root.configure(bg=BG_COLOR)
    
    # Tiêu đề
    tk.Label(root, text="ĐĂNG NHẬP", font=("Helvetica", 22, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(30, 25))
    
    # ================= KHU VỰC NHẬP EMAIL =================
    tk.Label(root, text="Email / Tài khoản:", font=("Helvetica", 10, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", padx=35)
    
    # SỬA LỖI BÔI TRẮNG: Cấu hình lại màu chọn (selectbackground) và ràng buộc bỏ chọn khi click
    email_entry = tk.Entry(root, font=("Helvetica", 13), bg=INPUT_BG, fg="white", insertbackground="white", 
                           bd=0, highlightthickness=1, highlightbackground="#5e3c2b", highlightcolor="#B97232",
                           selectbackground=BTN_BG, selectforeground="white")
    email_entry.pack(fill="x", padx=35, pady=(5, 15), ipady=8)
    email_entry.bind("<FocusIn>", lambda e: email_entry.selection_clear()) # Xóa bôi đen
    
    # ================= KHU VỰC NHẬP MẬT KHẨU =================
    tk.Label(root, text="Mật khẩu:", font=("Helvetica", 10, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", padx=35)
    
    pass_frame = tk.Frame(root, bg=BG_COLOR)
    pass_frame.pack(fill="x", padx=35, pady=(5, 5))
    
    # SỬA LỖI MẬT KHẨU BỊ HIỆN: show="*" luôn được ép làm giá trị mặc định khởi tạo
    pass_entry = tk.Entry(pass_frame, font=("Helvetica", 13), bg=INPUT_BG, fg="white", insertbackground="white", 
                          bd=0, highlightthickness=1, highlightbackground="#5e3c2b", highlightcolor="#B97232", 
                          show="*", selectbackground=BTN_BG, selectforeground="white")
    pass_entry.pack(side="left", fill="x", expand=True, ipady=8)
    pass_entry.bind("<FocusIn>", lambda e: pass_entry.selection_clear()) # Xóa bôi đen
    
    # Tính năng Ẩn / Hiện mật khẩu (Mặc định: False -> Ẩn)
    show_pwd = tk.BooleanVar(value=False) 
    def toggle_pwd():
        if show_pwd.get():
            pass_entry.config(show="") # Hiện chữ
        else:
            pass_entry.config(show="*") # Ẩn bằng dấu sao
            
    tk.Checkbutton(pass_frame, text="Hiện", variable=show_pwd, command=toggle_pwd, 
                   bg=BG_COLOR, fg=FG_COLOR, selectcolor=INPUT_BG, activebackground=BG_COLOR, 
                   activeforeground=FG_COLOR, cursor="hand2").pack(side="right", padx=(10, 0))
    
    # Nhãn trạng thái
    lbl_status = tk.Label(root, text="", font=("Helvetica", 10), bg=BG_COLOR, fg="#ff6b6b")
    lbl_status.pack(pady=5)
    
    # ================= LOGIC XỬ LÝ SERVER =================
    def attempt_login():
        email = email_entry.get().strip()
        pwd = pass_entry.get().strip()
        
        if not email or not pwd:
            lbl_status.config(text="Vui lòng nhập đủ Email và Mật khẩu!", fg="#ff6b6b")
            return
            
        lbl_status.config(text="Đang kiểm tra...", fg="#8ce874")
        root.update()
        
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
        data = {"email": email, "password": pwd}
        
        try:
            res = requests.post(url, headers=headers, json=data, timeout=10)
            res_data = res.json()
            
            if res.status_code == 200 and "access_token" in res_data:
                data_dir = os.path.dirname(config.DATA_FILE_PATH)
                os.makedirs(data_dir, exist_ok=True)
                session_file = os.path.join(data_dir, "auth_session.json")
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "access_token": res_data["access_token"],
                        "refresh_token": res_data.get("refresh_token", ""),
                        "type": "login_native"
                    }, f, indent=4)
                
                game_state.check_login_status()
                
                # Bỏ popup messagebox khó chịu
                root.destroy()
                switch_screen_callback(config.SCREEN_HOME)
            else:
                err = res_data.get("error_description", "Sai tài khoản hoặc mật khẩu!")
                lbl_status.config(text=err, fg="#ff6b6b")
        except requests.exceptions.ConnectionError:
            lbl_status.config(text="Lỗi kết nối mạng!", fg="#ff6b6b")
        except Exception as e:
            lbl_status.config(text=f"Lỗi: {str(e)[:25]}", fg="#ff6b6b")

    # ================= NÚT BẤM =================
    tk.Button(root, text="ĐĂNG NHẬP", font=("Helvetica", 12, "bold"), bg=BTN_BG, fg="white", bd=0, 
              activebackground="#9A5B23", activeforeground="white", cursor="hand2", 
              command=attempt_login).pack(fill="x", padx=35, pady=(10, 5), ipady=6)
    
    def on_back():
        root.destroy()
        switch_screen_callback(config.SCREEN_HOME)
        
    tk.Button(root, text="QUAY LẠI TỪ TRANG CHỦ", font=("Helvetica", 10), bg="#412A1E", fg=FG_COLOR, bd=0, 
              activebackground="#5e3c2b", activeforeground=FG_COLOR, cursor="hand2", 
              command=on_back).pack(fill="x", padx=35, pady=5, ipady=5)

    root.protocol("WM_DELETE_WINDOW", on_back)
    
    # Focus an toàn vào ô email khi mở lên mà không bị bôi trắng
    email_entry.focus_set()
    email_entry.selection_clear()
    
    root.mainloop()
    login_state["window_open"] = False

# ==========================================
# PYGAME: MÀN HÌNH CHỜ (PHÍA SAU TKINTER)
# ==========================================
def handle_events(event):
    pass

def draw_login(screen, font_title, font, colors, game_state, switch_screen_callback):
    global bg_image
    
    if bg_image is None:
        try:
            bg_path  = os.path.join(config.ASSETS_DIR, "setting", "back.png")
            loaded   = pygame.image.load(bg_path).convert()
            bg_image = pygame.transform.scale(loaded, (config.WIDTH, config.HEIGHT))
        except Exception:
            bg_image = False
            
    if bg_image:
        screen.blit(bg_image, (0, 0))
    else:
        screen.fill((28, 18, 12))
        
    ov = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200)) 
    screen.blit(ov, (0, 0))
    
    ui_elements.draw_text_centered(screen, "VUI LÒNG THAO TÁC TRÊN CỬA SỔ ĐĂNG NHẬP...", 
                                   config.WIDTH//2, config.HEIGHT//2, font, (238, 212, 182))
    
    if not login_state["window_open"]:
        login_state["window_open"] = True
        threading.Thread(target=launch_tkinter_login, args=(game_state, switch_screen_callback), daemon=True).start()
        
    return []