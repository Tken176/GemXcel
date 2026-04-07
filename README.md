# 🌟 GemXcel - Gamified AI Learning Platform

![GemXcel Logo](https://sf-static.upanhlaylink.com/img/image_2025081939b154f7796f5fd26683315cdd3dbb2a.jpg)

**Học tập không còn nhàm chán khi kiến thức biến thành những viên đá quý!** 💎

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg?style=for-the-badge)](https://github.com/Tken176/GemXcel-Project)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-Community-green?style=for-the-badge&logo=python)](https://www.pygame.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-red.svg?style=for-the-badge)](LICENSE)

*Dự án được phát triển bởi học sinh THPT Chuyên Bến Tre.*

[Trải nghiệm ngay](https://gemxcel.pages.dev/) • [Báo lỗi (Issues)](https://github.com/Tken176/GemXcel-Project/issues) • [Đóng góp](#-đóng-góp)

---

## 🚀 Giới thiệu (Introduction)

**GemXcel** là một ứng dụng học tập sáng tạo, kết hợp hoàn hảo giữa **Gamification (Game hóa)** và **Trí tuệ nhân tạo (AI)**. 

Được xây dựng trên nền tảng Python (Pygame) và quản lý dữ liệu với Supabase, GemXcel biến trải nghiệm học tập khô khan thành một hành trình phiêu lưu. Học sinh không chỉ được nạp kiến thức thông qua các bài học và quiz, mà còn được "săn" đá quý, tham gia vòng quay nhân phẩm (Gacha), tùy chỉnh avatar và đua top với bạn bè. 

**Mục tiêu cốt lõi:** Mang lại một môi trường học tập vui vẻ, chủ động, khơi dậy động lực từ bên trong thông qua hệ thống phần thưởng và thành tựu.

---

## ✨ Tính năng nổi bật (Key Features)

GemXcel mang đến một hệ sinh thái học tập toàn diện với các tính năng sau:

### 🧠 Trợ lý Học tập AI (AI-Powered Learning)
* **Tạo nội dung tự động:** AI tự động phân tích tài liệu của bạn để tạo ra bài học và bài tập (Quiz) sinh động.
* **Gia sư AI 24/7:** Tích hợp chatbot gia sư, sẵn sàng giải đáp mọi thắc mắc của bạn trong quá trình học.

### 🎮 Gamification & Hệ thống phần thưởng
* **Bộ sưu tập Đá quý (Gem Collection):** Học và làm bài kiểm tra để thu thập các loại đá quý độc đáo.
* **Cơ chế Gacha:** Sử dụng tài nguyên kiếm được để quay Gacha, săn tìm các viên đá quý hiếm hoặc vật phẩm giới hạn.
* **Cửa hàng (Shop):** Mua sắm vật phẩm, đổi Gem để nâng cấp trải nghiệm trong game.
* **Avatar & Hồ sơ cá nhân:** Tùy chỉnh ảnh đại diện (Avt) và thể hiện cá tính riêng.

### 🏆 Cộng đồng & Xếp hạng
* **Bảng xếp hạng trực tuyến (Leaderboard):** Đồng bộ dữ liệu real-time, đua top điểm số và bộ sưu tập với học sinh toàn trường/toàn cầu.
* **Hệ thống Tài khoản:** Đăng ký tài khoản dễ dàng qua nền tảng Web, quản lý tiến độ học tập an toàn.

### ⚙️ Trải nghiệm Tối ưu
* **Offline-First:** Hoạt động mượt mà ngay cả khi không có mạng. (Internet chỉ yêu cầu khi cần AI tạo nội dung hoặc chat với gia sư).
* **Âm nhạc & Không gian:** Tích hợp hệ thống nhạc nền (BGM) thư giãn, giúp tăng cường sự tập trung khi học.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

* **Ngôn ngữ chính:** Python (3.10+)
* **Giao diện & Game Engine:** Pygame
* **Backend & Cơ sở dữ liệu:** Supabase (Xác thực, Lưu trữ, Leaderboard)
* **AI Engine:** Tích hợp mô hình ngôn ngữ lớn (LLM) để xử lý văn bản và trò chuyện.
* **Web Framework:** (Dành cho trang web đăng ký/landing page)

---

## 🚀 Cài đặt & Hướng dẫn sử dụng (Quick Start)

Bạn có thể tải và trải nghiệm ứng dụng trực tiếp tại: **[gemxcel.pages.dev](https://gemxcel.pages.dev/)**

## 📂 Cấu trúc thư mục (Project Structure)

Dự án được tổ chức theo mô hình phân tách logic và giao diện (Separation of Concerns), giúp mã nguồn dễ đọc, dễ bảo trì và dễ mở rộng:

```
GemXcel/
├── LICENSE
├── README.md
└── src/                            # Thư mục chứa toàn bộ mã nguồn chính của ứng dụng
    ├── main.py                     # Điểm khởi chạy ứng dụng (Entry point)
    ├── config.py                   # Chứa các thông số cấu hình hệ thống (Kích thước, FPS, màu sắc...)
    ├── game_state.py               # Quản lý trạng thái trò chơi và dữ liệu tiến trình của người dùng
    ├── storage.py                  # Xử lý logic lưu trữ dữ liệu (Local & Cloud)
    ├── ui_elements.py              # Các thành phần giao diện dùng chung (Button, Textbox, Panel...)
    ├── build.py & dowload.iss      # Các script hỗ trợ đóng gói ứng dụng (Build/Installer)
    │
    ├── screens/                    # [Mô-đun Giao Diện] Quản lý logic và UI của từng màn hình riêng biệt
    │   ├── login_screen.py         # Màn hình đăng nhập & xác thực tài khoản
    │   ├── home_screen.py          # Màn hình chính (Lobby/Dashboard)
    │   ├── lesson_screen.py        # Màn hình hiển thị nội dung bài học
    │   ├── exercise_screen.py      # Màn hình làm bài tập
    │   ├── quiz_screen.py          # Màn hình kiểm tra (Quiz) kiếm Gem
    │   ├── shop_screen.py          # Màn hình cửa hàng ảo và hệ thống Gacha
    │   ├── collection_screen.py    # Màn hình trưng bày Bộ sưu tập Đá quý (Gems)
    │   ├── account_screen.py       # Màn hình thông tin hồ sơ/Avatar người dùng
    │   ├── content_processor.py    # Xử lý logic đọc file và tạo nội dung học tập
    │   └── setting_screen.py       # Màn hình tùy chỉnh cài đặt ứng dụng
    │
    └── assets/                     # [Tài Nguyên] Chứa toàn bộ file đa phương tiện của Game
        ├── audio/                  # Nhạc nền (BGM) và Hiệu ứng âm thanh (SFX như click, success)
        ├── font/                   # Các phông chữ tùy chỉnh (Minecraft, Dogicapixel, SVN...)
        ├── setting/                # Sprite và Hình ảnh UI (Avatar, Background, Icon vật phẩm, Gem 1-9...)
        └── tai_nguyen/             # Cơ sở dữ liệu cục bộ (game_data.json) và các icon hệ thống
```

### 📖 Cách thức hoạt động

1.  **Đăng ký/Đăng nhập:** Tạo tài khoản qua Web để lưu trữ tiến trình lên Cloud.
2.  **Khởi tạo nội dung:** Nhấn `Nạp FILE` và tải lên tài liệu học tập của bạn. AI sẽ làm phần việc còn lại.
3.  **Học & Tương tác:** Đọc bài học, nếu không hiểu có thể hỏi ngay Gia sư AI.
4.  **Kiểm tra & Nhận thưởng:** Làm Quiz để nhận tiền tệ và Gem cơ bản.
5.  **Giải trí:** Vào Shop mua sắm hoặc thử vận may với vòng quay Gacha. Nhớ bật nhạc nền lên để thư giãn nhé!

> 💡 **Pro Tip:** Hãy chuẩn bị các file tài liệu có tiêu đề và bố cục rõ ràng, AI của GemXcel sẽ tạo ra các bộ câu hỏi chất lượng và bám sát trọng tâm hơn!

---
## 📩 Hỗ trợ & Liên hệ

### 🎯 Kênh hỗ trợ chính thức

- 📧 **Email hỗ trợ**: [dinhminhtoan17062009@gmail.com](https://mail.google.com/mail/u/0/#inbox?compose=GTvVlcSKkwsmPGpHDNvVJTqcJdVvLwPPtzFSmpDHQLgHNTHVzfhtsTlQNdRvdZwMjJwFxvkCXbCxD)
- 🌐 **GitHub**: [https://github.com/Tken176](https://github.com/Tken176)
- 💬 **Issues**: [GitHub Issues](https://github.com/Tken176/GemXcel-Project/issues)

### 📱 Mạng xã hội
- 🔗 **Facebook**: [Đinh Minh Toàn](https://www.facebook.com/minh.toan.708322/?locale=vi_VN)


---
## 📄 Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

## 🙏 Lời cảm ơn

Xin chân thành cảm ơn:
- Các thầy cô giáo đã hướng dẫn và hỗ trợ
- Cộng đồng open source đã đóng góp các thư viện và công cụ
- Tất cả người dùng đã tin tưởng và sử dụng sản phẩm
