import pygame
import os
import config
from pygame import mixer
import subprocess
import sys
import time
import math
import random
from typing import List, Dict, Tuple, Optional, Callable
import ui_elements
import threading
import webbrowser
import tempfile
import json

# ==========================================
# BIẾN TOÀN CỤC & CACHE
# ==========================================
animation_time = 0
hover_states = {}

_image_cache: Dict[str, pygame.Surface] = {}
_scaled_cache: Dict[Tuple[str, int, int], pygame.Surface] = {}
_glow_cache: Dict[Tuple[int, int], pygame.Surface] = {}
_text_surface_cache: Dict[Tuple[str, int, Tuple[int, int, int]], pygame.Surface] = {}

try:
    SMALL_FONT = pygame.font.Font(None, 20)
except Exception:
    SMALL_FONT = config.FONT  

# ==========================================
# GEM AI HTML TEMPLATE
# ==========================================
# Đã fix lỗi Javascript không chạy và điều kiện token
GEM_AI_HTML = '''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="google" content="notranslate">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEM AI - Chat Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; background: #3d2817; background-image: repeating-linear-gradient(0deg, transparent, transparent 4px, rgba(0,0,0,.1) 4px, rgba(0,0,0,.1) 8px), repeating-linear-gradient(90deg, transparent, transparent 4px, rgba(0,0,0,.1) 4px, rgba(0,0,0,.1) 8px); height: 100vh; display: flex; align-items: center; justify-content: center; image-rendering: pixelated; }
        .chat-container { width: 90%; max-width: 800px; height: 90vh; background: #5c3d2e; border: 8px solid #2d1810; display: flex; flex-direction: column; overflow: hidden; box-shadow: inset 0 0 0 4px #7a5436, 8px 8px 0 rgba(0,0,0,0.3), 0 0 0 2px #4a2f1f; position: relative; }
        .chat-header { background: #4a2f1f; padding: 20px; text-align: center; border-bottom: 4px solid #2d1810; box-shadow: inset 0 -2px 0 #7a5436; position: relative; z-index: 1; }
        .chat-header h1 { color: #f4e4c1; font-size: 28px; margin-bottom: 5px; font-weight: 700; text-shadow: 3px 3px 0 #2d1810; letter-spacing: 2px; }
        .chat-header p { color: #d4b896; font-size: 14px; text-shadow: 2px 2px 0 #2d1810; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; background: #f4e4c1; background-image: repeating-linear-gradient(0deg, transparent, transparent 20px, rgba(139,90,43,.1) 20px, rgba(139,90,43,.1) 22px); position: relative; z-index: 1; }
        .message { display: flex; align-items: flex-start; gap: 12px; animation: fadeIn 0.5s ease-out; }
        .message.user { flex-direction: row-reverse; }
        .message-avatar { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #f4e4c1; font-size: 16px; flex-shrink: 0; border: 3px solid #2d1810; box-shadow: 3px 3px 0 rgba(0,0,0,0.3); image-rendering: pixelated; }
        .message.user .message-avatar { background: #8b5a2b; }
        .message.bot .message-avatar { background: #c19a6b; }
        .message-content { background: #fffef7; padding: 15px 20px; max-width: 70%; word-wrap: break-word; border: 3px solid #8b5a2b; box-shadow: 4px 4px 0 rgba(0,0,0,0.2); }
        .message.user .message-content { background: #f9e4b7; border-color: #a0826d; }
        .message-text { color: #2d1810; line-height: 1.5; white-space: pre-wrap; }
        .message-time { font-size: 12px; color: #8b5a2b; margin-top: 8px; }
        .chat-input-container { padding: 20px; background: #4a2f1f; border-top: 4px solid #2d1810; position: relative; z-index: 1; }
        .chat-input-wrapper { display: flex; gap: 10px; align-items: flex-end; }
        .chat-input { flex: 1; background: #f4e4c1; border: 3px solid #2d1810; padding: 15px 20px; color: #2d1810; font-size: 16px; resize: none; outline: none; min-height: 50px; max-height: 120px; transition: all 0.1s ease; font-family: 'Courier New', monospace; box-shadow: inset 2px 2px 0 rgba(0,0,0,0.1); }
        .chat-input:focus { border-color: #8b5a2b; background: #fffef7; }
        .send-button { background: #c19a6b; border: 3px solid #2d1810; width: 50px; height: 50px; color: #2d1810; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.1s ease; font-size: 20px; box-shadow: 4px 4px 0 rgba(0,0,0,0.3); image-rendering: pixelated; }
        .send-button:hover { transform: translate(2px, 2px); box-shadow: 2px 2px 0 rgba(0,0,0,0.3); background: #d4b896; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .chat-messages::-webkit-scrollbar { width: 12px; }
        .chat-messages::-webkit-scrollbar-track { background: #d4b896; border: 2px solid #8b5a2b; }
        .chat-messages::-webkit-scrollbar-thumb { background: #8b5a2b; border: 2px solid #5c3d2e; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header"><h1>💎 GEM AI</h1><p>Gia sư hỗ trợ bạn</p></div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-avatar">AI</div>
                <div class="message-content">
                    <div class="message-text">Xin chào! Mình là GEM_AI. Hãy hỏi mình bất cứ điều gì nhé!</div>
                </div>
            </div>
        </div>
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <textarea class="chat-input" id="chatInput" placeholder="Nhập tin nhắn..." rows="1"></textarea>
                <button class="send-button" id="sendButton">➤</button>
            </div>
        </div>
    </div>
    <script>
        class GemAIChatBot {
            constructor() {
                this.accessToken = '__ACCESS_TOKEN__';

                // FIX: URL chỉ trỏ tới function root, KHÔNG có sub-path.
                // Model và path được truyền qua body (field "geminiPath") để
                // tránh lỗi 404 do Supabase không forward sub-path vào req.url.
                this.proxyUrl = 'https://hwqlvikkzeybssocyjjn.supabase.co/functions/v1/gemini-proxy';

                // Model Gemini muốn dùng – thay đổi tại đây nếu cần
                this.geminiPath = '/v1beta/models/gemini-2.5-flash-lite:generateContent';

                this.chatMessages = document.getElementById('chatMessages');
                this.chatInput = document.getElementById('chatInput');
                this.sendButton = document.getElementById('sendButton');
                this.init();
            }

            init() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                this.chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.sendMessage(); }
                });
            }

            addMessage(text, sender) {
                const div = document.createElement('div');
                div.className = `message ${sender}`;
                div.innerHTML = `<div class="message-avatar">${sender === 'user' ? 'U' : 'AI'}</div>
                                 <div class="message-content"><div class="message-text">${text}</div></div>`;
                this.chatMessages.appendChild(div);
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }

            async sendMessage() {
                const message = this.chatInput.value.trim();
                if (!message) return;
                this.addMessage(message, 'user');
                this.chatInput.value = '';

                try {
                    const response = await fetch(this.proxyUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.accessToken}`,
                        },
                        body: JSON.stringify({
                            // Server đọc "geminiPath" để biết endpoint cần gọi
                            geminiPath: this.geminiPath,
                            contents: [{ parts: [{ text: message }] }]
                        })
                    });

                    const data = await response.json();

                    if (data.candidates && data.candidates[0]) {
                        this.addMessage(data.candidates[0].content.parts[0].text, 'bot');
                    } else {
                        this.addMessage("Lỗi: " + (data.error?.message || data.error || "Không có phản hồi từ máy chủ"), 'bot');
                    }
                } catch (e) {
                    this.addMessage("Lỗi kết nối proxy. Vui lòng kiểm tra mạng.", 'bot');
                }
            }
        }

        window.onload = () => { new GemAIChatBot(); };
    </script>
</body>
</html>'''

# ==========================================
# CÁC HÀM HỖ TRỢ CACHE & LOAD TÀI NGUYÊN
# ==========================================
def _load_image(path: str) -> Optional[pygame.Surface]:
    if not path: return None
    if path in _image_cache: return _image_cache[path]
    try:
        img = pygame.image.load(path).convert_alpha()
        _image_cache[path] = img
        return img
    except:
        _image_cache[path] = None
        return None

def _get_scaled_image(path: str, w: int, h: int) -> Optional[pygame.Surface]:
    key = (path, w, h)
    if key in _scaled_cache: return _scaled_cache[key]
    img = _load_image(path)
    if img is None: return None
    scaled = pygame.transform.smoothscale(img, (w, h))
    _scaled_cache[key] = scaled
    return scaled

def _render_text_cached(text: str, font: pygame.font.Font, color: Tuple[int, int, int]) -> pygame.Surface:
    key = (text, id(font), color)
    if key in _text_surface_cache: return _text_surface_cache[key]
    surf = font.render(text, True, color)
    _text_surface_cache[key] = surf
    return surf


# ==========================================
# GIAO DIỆN NÚT BẤM HIỆN ĐẠI
# ==========================================
class ModernButton(ui_elements.Button):
    def __init__(self, x, y, w, h, text, callback, color, icon_path=None, gradient_colors=None, click_sound=None):
        super().__init__(x, y, w, h, text, callback, color, 15, click_sound)
        self.icon_path = icon_path
        self.is_invisible = False 
        self._icon_surf = None
        if self.icon_path and os.path.exists(self.icon_path):
            img = _load_image(self.icon_path)
            if img:
                icon_h = max(16, int(self.rect.height * 0.6))
                self._icon_surf = pygame.transform.smoothscale(img, (icon_h, icon_h))

    def draw(self, surface: pygame.Surface) -> None:
        if self.is_invisible: return
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        rect = self.rect

        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 25), shadow.get_rect(), border_radius=12)
        surface.blit(shadow, (rect.x + 2, rect.y + 2))

        bg_color = (min(255, self.color[0] + 20), min(255, self.color[1] + 20), min(255, self.color[2] + 20)) if is_hovered else self.color
        pygame.draw.rect(surface, bg_color, rect, border_radius=12)
        
        border_color = (255, 255, 255, 180) if is_hovered else (200, 220, 200)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=12)

        if self._icon_surf:
            icon_rect = self._icon_surf.get_rect()
            icon_rect.left = rect.left + 12
            icon_rect.centery = rect.centery
            surface.blit(self._icon_surf, icon_rect)

        if self.text:
            text_color = (255, 255, 255) if is_hovered else config.COLORS.get("text", (240, 240, 240))
            text_surf = _render_text_cached(self.text, config.FONT, text_color)
            text_pos = (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2)
            if self._icon_surf:
                text_pos = (rect.left + 12 + self._icon_surf.get_width() + 10, text_pos[1])
            surface.blit(text_surf, text_pos)


# ==========================================
# HỆ THỐNG NHIỆM VỤ HẰNG NGÀY
# ==========================================
def _get_metric_value(game_state, q_id):
    if q_id == "point": return getattr(game_state, 'point', 0)
    if q_id == "playtime": return getattr(game_state, 'playtime_minutes', 0)
    if q_id == "answered": return getattr(game_state, 'total_answered', 0)
    if q_id == "correct": return getattr(game_state, 'correct_answers', 0)
    if q_id == "lessons": return len(getattr(game_state, 'completed_lessons', []))
    if q_id == "streak": return getattr(game_state, 'streak', 0)
    if q_id == "max_streak": return getattr(game_state, 'max_streak', 0)
    if q_id == "gems": return len(getattr(game_state, 'collected_gems', []))
    if q_id == "avatars": return len(getattr(game_state, 'owned_avatars', []))
    if q_id == "the_streak": return getattr(game_state, 'the_streak', 0)
    return 0

def _generate_quests(game_state) -> List[Dict]:
    possible_quests = []
    
    current_point = _get_metric_value(game_state, "point")
    possible_quests.append({"id": "point", "desc": "Kiếm thêm {delta} điểm", "start_val": current_point, "target": current_point + random.choice([50, 100, 150]), "reward": 30})

    current_playtime = _get_metric_value(game_state, "playtime")
    possible_quests.append({"id": "playtime", "desc": "Học thêm {delta} phút", "start_val": current_playtime, "target": current_playtime + random.choice([10, 15, 20]), "reward": 20})

    current_answered = _get_metric_value(game_state, "answered")
    possible_quests.append({"id": "answered", "desc": "Làm thêm {delta} câu hỏi", "start_val": current_answered, "target": current_answered + random.choice([10, 15, 20]), "reward": 25})

    current_correct = _get_metric_value(game_state, "correct")
    possible_quests.append({"id": "correct", "desc": "Trả lời đúng {delta} câu", "start_val": current_correct, "target": current_correct + random.choice([5, 10, 15]), "reward": 35})

    current_lessons = _get_metric_value(game_state, "lessons")
    possible_quests.append({"id": "lessons", "desc": "Hoàn thành bài học số {target}", "start_val": 0, "target": current_lessons + 1, "reward": 50})

    current_avatars = _get_metric_value(game_state, "avatars")
    if current_avatars < 4:
        possible_quests.append({"id": "avatars", "desc": "Sở hữu {target} Avatar", "start_val": 0, "target": current_avatars + 1, "reward": 80})

    current_gems = _get_metric_value(game_state, "gems")
    if current_gems < 9:
        delta_gem = random.randint(1, 2)
        target_gem = min(9, current_gems + delta_gem)
        possible_quests.append({"id": "gems", "desc": "Sưu tầm {target} ngọc kỳ ảo", "start_val": 0, "target": target_gem, "reward": 50 * (target_gem - current_gems)})

    current_streak = _get_metric_value(game_state, "streak")
    possible_quests.append({"id": "streak", "desc": "Đạt chuỗi học {target} ngày", "start_val": 0, "target": current_streak + 1, "reward": 40})
    
    current_max_streak = _get_metric_value(game_state, "max_streak")
    if current_streak >= current_max_streak and current_max_streak > 0:
        possible_quests.append({"id": "max_streak", "desc": "Phá kỷ lục: Đạt chuỗi {target} ngày", "start_val": 0, "target": current_max_streak + 1, "reward": 100})

    current_shields = _get_metric_value(game_state, "the_streak")
    possible_quests.append({"id": "the_streak", "desc": "Tích lũy {target} thẻ bảo vệ", "start_val": 0, "target": current_shields + 1, "reward": 30})

    selected_quests = random.sample(possible_quests, min(3, len(possible_quests)))
    
    for q in selected_quests:
        delta = q["target"] - q["start_val"] if q["start_val"] > 0 else q["target"]
        q["desc"] = q["desc"].replace("{delta}", str(delta)).replace("{target}", str(q["target"]))
        q["claimed"] = False
        
    return selected_quests

def init_daily_quests(game_state):
    if not hasattr(game_state, 'daily_quests') or game_state.daily_quests is None:
        game_state.daily_quests = _generate_quests(game_state)
        if hasattr(game_state, 'write_data'):
            game_state.write_data()

def claim_quest_reward(quest, game_state, click_sound):
    if click_sound: click_sound.play()
    if not quest["claimed"]:
        quest["claimed"] = True
        game_state.point += quest["reward"]
        
        if hasattr(game_state, 'total_quests_completed'):
            game_state.total_quests_completed += 1 
            
        # Tạm thời tắt auto-reset khi hoàn thành cả 3 để tránh lỗi UI nhấp nháy
        if hasattr(game_state, 'write_data'):
            game_state.write_data()

def reset_quests(game_state, click_sound):
    if game_state.point >= 20:
        if click_sound: click_sound.play()
        game_state.point -= 20
        game_state.daily_quests = _generate_quests(game_state)
        if hasattr(game_state, 'write_data'):
            game_state.write_data()
    else:
        try: game_state.show_message("Không đủ điểm để làm mới!")
        except: pass


# ==========================================
# GIAO DIỆN CÀI ĐẶT CHÍNH
# ==========================================
def draw_setting(screen: pygame.Surface, game_state: 'GameState', click_sound: pygame.mixer.Sound) -> List[ModernButton]:
    temp = getattr(game_state, "temp_screen", None)
    if temp == "music_selection": return draw_music_selection(screen, game_state, click_sound)
    elif temp == "avatar_selection": return draw_avatar_selection(screen, game_state, click_sound)

    global animation_time
    animation_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    buttons: List[ModernButton] = []

    # Tiêu đề
    title_surf = _render_text_cached("CÀI ĐẶT & NHIỆM VỤ", config.FONT_TITLE, config.COLORS.get("accent", (200, 200, 255)))
    screen.blit(title_surf, ((config.WIDTH - title_surf.get_width()) // 2, 40))

    # --- BẢNG NHIỆM VỤ ---
    init_daily_quests(game_state)
    panel_x, panel_y = 75, 120
    panel_w, panel_h = 380, 420

    q_title = _render_text_cached("NHIỆM VỤ HẰNG NGÀY", config.FONT, (137, 95, 72))
    screen.blit(q_title, (panel_x + panel_w//2 - q_title.get_width()//2, panel_y + 15))
    pygame.draw.line(screen, (180, 130, 80), (panel_x + 30, panel_y + 50), (panel_x + panel_w - 30, panel_y + 50), 2)

    quest_start_y = panel_y + 65
    
    # Kiểm tra an toàn trước khi lặp
    if hasattr(game_state, 'daily_quests') and game_state.daily_quests:
        for i, quest in enumerate(game_state.daily_quests):
            q_y = quest_start_y + i * 95
            q_rect = pygame.Rect(panel_x + 15, q_y, panel_w - 30, 85)

            desc_surf = _render_text_cached(quest["desc"], config.FONT_SMALL, (166, 142, 7))
            screen.blit(desc_surf, (q_rect.x + 15, q_rect.y - 2))

            reward_surf = _render_text_cached(f"Thưởng: {quest['reward']} điểm", config.FONT_SMALL, (34, 139, 34))
            screen.blit(reward_surf, (q_rect.x + 15, q_rect.y + 35))

            if quest["id"] == "max_streak":
                current_val = _get_metric_value(game_state, "streak")
            else:
                current_val = _get_metric_value(game_state, quest["id"])
                
            target_val = quest["target"]
            start_val = quest.get("start_val", 0)

            if start_val > 0:
                prog_current = max(0, current_val - start_val)
                prog_target = target_val - start_val
            else:
                prog_current = current_val
                prog_target = target_val

            progress = min(1.0, prog_current / prog_target) if prog_target > 0 else 1.0
            display_current = min(prog_current, prog_target)

            bar_w, bar_h = 160, 14
            bar_x, bar_y = q_rect.x + 15, q_rect.bottom - 22
            pygame.draw.rect(screen, (30, 20, 10), (bar_x, bar_y, bar_w, bar_h), border_radius=7)
            if progress > 0:
                fill_w = max(10, int(bar_w * progress))
                pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, fill_w, bar_h), border_radius=7)
            
            prog_txt = _render_text_cached(f"{display_current}/{prog_target}", SMALL_FONT, (255,255,255))
            screen.blit(prog_txt, (bar_x + bar_w + 10, bar_y - 2))

            btn_w, btn_h = 100, 35
            btn_x = q_rect.right - btn_w - 10
            btn_y = q_rect.centery - btn_h//2 + 30
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            if quest["claimed"]:
                pygame.draw.rect(screen, (80, 80, 80), btn_rect, border_radius=8)
                t_surf = _render_text_cached("Đã nhận", config.FONT_SMALL, (200, 200, 200))
                screen.blit(t_surf, (btn_rect.centerx - t_surf.get_width()//2, btn_rect.centery - t_surf.get_height()//2))
            elif progress >= 1.0:
                is_hover = btn_rect.collidepoint(mouse_pos)
                btn_color = (255, 180, 50) if is_hover else (220, 140, 30)
                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=8)
                t_surf = _render_text_cached("Nhận", config.FONT_SMALL, (50, 30, 10))
                screen.blit(t_surf, (btn_rect.centerx - t_surf.get_width()//2, btn_rect.centery - t_surf.get_height()//2))
                
                claim_btn = ModernButton(btn_x, btn_y, btn_w, btn_h, "", lambda q=quest: claim_quest_reward(q, game_state, click_sound), (0,0,0))
                claim_btn.is_invisible = True
                buttons.append(claim_btn)
            else:
                pygame.draw.rect(screen, (50, 70, 90), btn_rect, border_radius=8)
                t_surf = _render_text_cached("Chưa đạt", config.FONT_SMALL, (150, 180, 200))
                screen.blit(t_surf, (btn_rect.centerx - t_surf.get_width()//2, btn_rect.centery - t_surf.get_height()//2))

    # Nút Làm mới
    refresh_w, refresh_h = 200, 40
    refresh_x = panel_x + panel_w//2 - refresh_w//2
    refresh_y = panel_y + panel_h - refresh_h - 15
    refresh_rect = pygame.Rect(refresh_x, refresh_y, refresh_w, refresh_h)
    
    is_ref_hover = refresh_rect.collidepoint(mouse_pos)
    ref_color = (60, 140, 180) if is_ref_hover else (40, 100, 140)
    pygame.draw.rect(screen, ref_color, refresh_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 200, 255), refresh_rect, width=2, border_radius=10)
    
    ref_txt = _render_text_cached("Làm mới (20 Điểm)", config.FONT_SMALL, (255,255,255))
    screen.blit(ref_txt, (refresh_rect.centerx - ref_txt.get_width()//2, refresh_rect.centery - ref_txt.get_height()//2))
    
    ref_btn = ModernButton(refresh_x, refresh_y, refresh_w, refresh_h, "", lambda: reset_quests(game_state, click_sound), (0,0,0))
    ref_btn.is_invisible = True
    buttons.append(ref_btn)

    # --- CÁC NÚT BÊN PHẢI ---
    right_x = 600
    def make_btn(x, y, w, h, text, callback, color, icon_file=None, gradient=None):
        icon_path = os.path.join(config.ASSETS_DIR, "setting", icon_file) if icon_file else None
        if icon_path and not os.path.exists(icon_path): icon_path = None
        return ModernButton(x, y, w, h, text, callback, color, icon_path=icon_path, gradient_colors=gradient, click_sound=click_sound)

    avatar_btn = make_btn(right_x, 150, 220, 60, "Đổi Avatar", lambda: game_state.set_temp_screen("avatar_selection"), (100, 180, 255), "avatar_icon.png", [(100, 180, 255), (70, 150, 230)])
    sound_btn  = make_btn(right_x, 240, 220, 60, "Âm Thanh", lambda: open_music_selection(game_state), (255, 180, 100), "sound_icon.png", [(255, 180, 100), (230, 150, 80)])
    ai_btn     = make_btn(right_x, 330, 220, 60, "GEM AI", lambda: _open_integrated_gem_ai(game_state), (100, 220, 100), "ai_icon.png", [(100, 220, 100), (80, 200, 80)])
    back_btn   = make_btn(right_x, config.HEIGHT - 120, 150, 50, "Quay lại", lambda: setattr(game_state, 'current_screen', "lesson"), (220, 100, 100), None, [(220, 100, 100), (190, 70, 70)])

    for b in [avatar_btn, sound_btn, ai_btn, back_btn]:
        b.draw(screen)
        buttons.append(b)

    return buttons


# ==========================================
# GIAO DIỆN CHỌN NHẠC NỀN
# ==========================================
def draw_music_selection(screen: pygame.Surface, game_state: 'GameState', click_sound: pygame.mixer.Sound) -> List[ModernButton]:
    music_list = [
        {"name": "Không nhạc nền", "file": None, "color": (120, 120, 130)},
        {"name": "Thư giãn", "file": "mu1.mp3", "color": (180, 100, 220)},
        {"name": "Tập trung", "file": "mu2.mp3", "color": (100, 180, 230)},
        {"name": "Hồi tưởng", "file": "mu3.mp3", "color": (230, 150, 100)},
        {"name": "Sôi động", "file": "mu4.mp3", "color": (150, 200, 120)},
        {"name": "Giật giật", "file": "mu5.mp3", "color": (230, 120, 150)},
    ]

    title = _render_text_cached("CHỌN NHẠC NỀN", config.FONT_TITLE, (160, 100, 60))
    screen.blit(title, (265 - title.get_width() // 2, 40))

    buttons = []
    cols, rows = 2, 3
    card_width, card_height = 320, 85
    left_x = config.WIDTH // 2 - card_width - 60
    right_x = config.WIDTH // 2 + 60
    y_start = 150
    v_gap = 40
    mouse_pos = pygame.mouse.get_pos()

    if not hasattr(game_state, '_music_btn_pressed'): game_state._music_btn_pressed = {}
    if not hasattr(game_state, '_music_btn_press_time'): game_state._music_btn_press_time = {}

    for i, music in enumerate(music_list[:cols * rows]):
        col = i % cols
        row = i // cols
        x = left_x if col == 0 else right_x
        y = y_start + row * (card_height + v_gap)
        rect = pygame.Rect(x, y, card_width, card_height)

        is_current = game_state.current_music == music["file"]
        is_hovered = rect.collidepoint(mouse_pos)
        
        btn_id = f"music_{i}"
        is_pressed = game_state._music_btn_pressed.get(btn_id, False)
        press_time = game_state._music_btn_press_time.get(btn_id, 0)
        
        current_time = pygame.time.get_ticks()
        press_offset = 0
        if is_pressed and current_time - press_time < 150: 
            progress = (current_time - press_time) / 150
            press_offset = int(6 * (1 - abs(progress - 0.5) * 2)) 
        
        draw_rect = pygame.Rect(rect.x, rect.y + press_offset, rect.width, rect.height)
        base_color = music["color"]
        
        if is_current: bg_color = tuple(min(255, int(c * 1.1 + 15)) for c in base_color)
        elif is_hovered: bg_color = tuple(min(200, int(c * 1.15)) for c in base_color)
        else: bg_color = base_color

        shadow_offset = 4 - press_offset  
        if shadow_offset > 0:
            shadow_rect = draw_rect.copy()
            shadow_rect.y += shadow_offset
            pygame.draw.rect(screen, (40, 30, 30), shadow_rect, border_radius=12)

        border_col = tuple(min(255, c + 40) for c in bg_color)
        pygame.draw.rect(screen, border_col, draw_rect, border_radius=12)
        
        inner_rect = draw_rect.inflate(-6, -6)
        pygame.draw.rect(screen, bg_color, inner_rect, border_radius=10)

        switch_x = draw_rect.x + 20
        switch_y = draw_rect.centery
        switch_width = 50
        switch_height = 26
        
        switch_rect = pygame.Rect(switch_x, switch_y - switch_height // 2, switch_width, switch_height)
        switch_bg = (100, 200, 100) if is_current else (80, 80, 90)
        pygame.draw.rect(screen, switch_bg, switch_rect, border_radius=13)
        pygame.draw.rect(screen, (220, 220, 220), switch_rect, 2, border_radius=13)
        
        knob_radius = 10
        knob_x = switch_x + switch_width - 13 if is_current else switch_x + 13
        knob_y = switch_y
        pygame.draw.circle(screen, (240, 240, 250), (knob_x, knob_y), knob_radius)

        text_color = (40, 40, 50) if is_current else (240, 240, 250)
        name_surf = _render_text_cached(music["name"], config.FONT, text_color)
        screen.blit(name_surf, (switch_x + switch_width + 15, draw_rect.centery - name_surf.get_height() // 2))

        def _on_click(m=music, gs=game_state, bid=btn_id):
            gs._music_btn_pressed[bid] = True
            gs._music_btn_press_time[bid] = pygame.time.get_ticks()
            if m["file"] == gs.current_music: _select_music(None, gs)
            else: _select_music(m["file"], gs)

        click_btn = ModernButton(rect.x, rect.y, rect.width, rect.height, "", _on_click, (0, 0, 0))
        click_btn.is_invisible = True 
        buttons.append(click_btn)

    back_btn = ModernButton(config.WIDTH - 230, config.HEIGHT - 110, 150, 50, "Quay lại", lambda: setattr(game_state, "temp_screen", None), (200, 90, 70), click_sound=click_sound)
    back_btn.is_invisible = True
    buttons.append(back_btn)
    
    back_x, back_y = config.WIDTH - 230, config.HEIGHT - 110
    back_rect = pygame.Rect(back_x, back_y, 150, 50)
    is_back_hovered = back_rect.collidepoint(mouse_pos)
    back_color = (220, 100, 80) if is_back_hovered else (200, 90, 70)
    pygame.draw.rect(screen, (100, 45, 35), pygame.Rect(back_x, back_y + 3, 150, 50), border_radius=10)
    pygame.draw.rect(screen, back_color, back_rect, border_radius=10)
    pygame.draw.rect(screen, (250, 200, 180), back_rect, 3, border_radius=10)
    back_text = _render_text_cached("Quay lại", config.FONT, (255, 255, 255))
    screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))

    return buttons

# Đã fix lỗi treo luồng chính khi load nhạc
def _play_music_thread(music_path, vol):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(vol)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Lỗi phát nhạc nền: {e}")

def _select_music(music_file: str, game_state) -> None:
    try:
        if not music_file:
            game_state.current_music = None
            pygame.mixer.music.stop()
        else:
            music_path = os.path.join(config.ASSETS_DIR, "audio", music_file)
            if os.path.exists(music_path):
                game_state.current_music = music_file
                # Dùng Thread để chống treo game
                threading.Thread(target=_play_music_thread, args=(music_path, getattr(game_state, 'music_volume', 0.4)), daemon=True).start()
        
        if hasattr(game_state, 'write_data'):
            game_state.write_data()
    except Exception as e: 
        print(f"Lỗi chọn nhạc: {e}")


# ==========================================
# GIAO DIỆN CHỌN AVATAR
# ==========================================
def _purchase_avatar(avatar: Dict, game_state):
    price = avatar.get("price", 0)
    if getattr(game_state, "point", 0) >= price:
        game_state.point -= price
        if avatar["path"] not in game_state.owned_avatars: game_state.owned_avatars.append(avatar["path"])
        game_state.avatar_path = avatar["path"]
        if hasattr(game_state, 'write_data'): game_state.write_data()
    else:
        try: game_state.show_message("Không đủ điểm để mua avatar.")
        except: pass

def _use_avatar(avatar: Dict, game_state):
    if avatar["path"] in game_state.owned_avatars:
        game_state.avatar_path = avatar["path"]
        if hasattr(game_state, 'write_data'): game_state.write_data()
    else: _purchase_avatar(avatar, game_state)

def draw_avatar_selection(screen: pygame.Surface, game_state: 'GameState', click_sound: pygame.mixer.Sound) -> List[ModernButton]:
    title = _render_text_cached("CHỌN AVATAR", config.FONT_TITLE, config.COLORS.get("accent", (200, 200, 255)))
    screen.blit(title, (100, 50))

    avatar_options = [
        {"name": "Sách Thông Thái", "path": os.path.join(config.AVATAR_DIR, "avatar1.jpg"), "price": 100},
        {"name": "Mèo Vô Tri", "path": os.path.join(config.AVATAR_DIR, "avatar2.jpg"), "price": 300},
        {"name": "Cáo Tinh Nghịch", "path": os.path.join(config.AVATAR_DIR, "avatar3.jpg"), "price": 700},
        {"name": "Vô Cực", "path": os.path.join(config.AVATAR_DIR, "avatar4.jpg"), "price": 1000},
    ]

    buttons: List[ModernButton] = []
    card_width, card_height = 350, 110  
    cols, rows = 2, 2
    h_gap = max(20, (config.WIDTH - cols * card_width) // (cols + 1))  
    v_gap = 40 
    mouse_pos = pygame.mouse.get_pos()

    for i, avatar in enumerate(avatar_options):
        x = h_gap + (i % cols) * (card_width + h_gap)
        y = 160 + (i // cols) * (card_height + v_gap)  
        card_rect = pygame.Rect(x, y, card_width, card_height)

        owned = avatar["path"] in game_state.owned_avatars
        current = game_state.avatar_path == avatar["path"]
        is_hovered = card_rect.collidepoint(mouse_pos)

        bg_color = (128, 85, 66) if is_hovered else (150, 110, 90)
        border_color = (128, 85, 66)
        pygame.draw.rect(screen, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(screen, border_color, card_rect, 4 if (current or is_hovered) else 3, border_radius=8)

        img_size = card_height - 24
        img_rect = pygame.Rect(x + 12, y + 12, img_size, img_size)
        scaled = _get_scaled_image(avatar["path"], img_size, img_size)
        if scaled: screen.blit(scaled, img_rect)
        else: pygame.draw.rect(screen, (150, 150, 150), img_rect, border_radius=6)

        name_surf = _render_text_cached(avatar["name"], config.FONT, config.COLORS.get("white", (240, 240, 240)))
        screen.blit(name_surf, (img_rect.right + 12, y + 16))

        if current: status_text, status_color = "ĐANG DÙNG", (255, 215, 0)
        elif owned: status_text, status_color = "ĐÃ SỞ HỮU", (50, 180, 50)
        else: status_text, status_color = f"{avatar['price']} ĐIỂM", (220, 120, 50)

        status_surf = _render_text_cached(status_text, config.FONT, status_color)
        screen.blit(status_surf, (img_rect.right + 12, y + 55))

        cb = (lambda a=avatar: _use_avatar(a, game_state)) if owned else (lambda a=avatar: _purchase_avatar(a, game_state))
        btn = ModernButton(x, y, card_width, card_height, "", cb, (0, 0, 0))
        btn.is_invisible = True
        buttons.append(btn)

    back_btn = ModernButton(config.WIDTH - 250, config.HEIGHT - 120, 150, 50, "Quay lại", lambda: game_state.set_temp_screen(None), (220, 100, 100), click_sound=click_sound)
    buttons.append(back_btn)
    back_btn.draw(screen)

    return buttons


# ==========================================
# KHỞI CHẠY GEM AI (WEB CHATBOT)
# ==========================================
# ==========================================
# KHỞI CHẠY GEM AI (WEB CHATBOT)
# ==========================================
def _open_integrated_gem_ai(game_state: 'GameState') -> None:
    try:
        # 1. Đọc refresh_token từ file auth_session.json
        appdata_path = os.environ.get('APPDATA')
        auth_file = os.path.join(appdata_path, "GemxelProject", "auth_session.json")
        
        refresh_token = ""
        if os.path.exists(auth_file):
            with open(auth_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                session_data = data.get("session", data)
                refresh_token = session_data.get("refresh_token", "")

        if not refresh_token:
            print("Cảnh báo: Không tìm thấy refresh_token. Vui lòng đăng nhập lại.")
            return

        # 2. Dùng refresh_token gọi Supabase để lấy access_token mới
        access_token = _refresh_access_token(refresh_token)

        if not access_token:
            print("Cảnh báo: Không thể làm mới token. Vui lòng đăng nhập lại.")
            return

        # 3. Tạo file HTML tạm và gắn token mới vào
        temp_dir = tempfile.gettempdir()
        html_file = os.path.join(temp_dir, "gem_ai_chat.html")
        html_content = GEM_AI_HTML.replace("__ACCESS_TOKEN__", access_token)
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 4. Mở trình duyệt dưới dạng App Window
        file_url = f"file:///{html_file.replace(os.sep, '/')}"
        profile_dir = os.path.join(temp_dir, "gem_ai_profile")
        browser_args = [f"--app={file_url}", "--new-window", "--window-size=500,600",
                        "--window-position=200,50", "--disable-features=TranslateUI"]

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe")
        ]
        for p in chrome_paths:
            if p and os.path.exists(p):
                subprocess.Popen([p] + browser_args + [f"--user-data-dir={profile_dir}_chrome"])
                return

        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for p in edge_paths:
            if os.path.exists(p):
                subprocess.Popen([p] + browser_args + [f"--user-data-dir={profile_dir}_edge"])
                return

        webbrowser.open(file_url)
    except Exception as e:
        print(f"Lỗi khi mở GEM AI: {e}")


def _refresh_access_token(refresh_token: str) -> str:
    """
    Gọi Supabase Auth API để đổi refresh_token lấy access_token mới.
    Trả về access_token mới hoặc chuỗi rỗng nếu thất bại.
    """
    import urllib.request

    SUPABASE_URL = "https://hwqlvikkzeybssocyjjn.supabase.co"
    SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"  # <-- Điền anon key của bạn vào đây

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    payload = json.dumps({"refresh_token": refresh_token}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            new_access_token = result.get("access_token", "")
            new_refresh_token = result.get("refresh_token", "")

            # Lưu lại session mới vào file để dùng cho lần sau
            if new_access_token:
                _save_new_session(new_access_token, new_refresh_token, result)

            return new_access_token
    except Exception as e:
        print(f"Lỗi khi refresh token: {e}")
        return ""


def _save_new_session(access_token: str, refresh_token: str, full_response: dict) -> None:
    """Ghi session mới (access + refresh token) về lại file auth_session.json."""
    try:
        appdata_path = os.environ.get('APPDATA')
        auth_file = os.path.join(appdata_path, "GemxelProject", "auth_session.json")

        # Đọc file cũ để giữ các trường không liên quan (ví dụ: user info)
        existing = {}
        if os.path.exists(auth_file):
            with open(auth_file, "r", encoding="utf-8") as f:
                existing = json.load(f)

        session = existing.get("session", existing)
        session["access_token"] = access_token
        session["refresh_token"] = refresh_token
        # Supabase trả về expires_in (giây), lưu luôn nếu có
        if "expires_in" in full_response:
            session["expires_in"] = full_response["expires_in"]
        if "expires_at" in full_response:
            session["expires_at"] = full_response["expires_at"]

        if "session" in existing:
            existing["session"] = session
        else:
            existing = session

        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Lỗi khi lưu session mới: {e}")

def open_music_selection(game_state):
    game_state.set_temp_screen("music_selection")
