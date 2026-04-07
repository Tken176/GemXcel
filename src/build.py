#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AUTO BUILD SCRIPT — PyInstaller
Đóng gói project Python thành file thực thi
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"


# =============================
# CÀI PACKAGE NẾU THIẾU
# =============================
def install_package(package, import_name=None):
    if import_name is None:
        import_name = package

    try:
        __import__(import_name)
        print(f"✅ {package} đã cài")
        return True
    except ImportError:
        print(f"📦 Đang cài {package}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package]
            )
            print(f"✅ Cài {package} thành công")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Không thể cài {package}")
            return False


# =============================
# KIỂM TRA FILE CẦN THIẾT
# =============================
def check_files():
    if not Path("main.py").exists():
        print("❌ Không tìm thấy main.py")
        return False, None

    icon = Path("icon.ico")
    if icon.exists():
        print("🖼️ Tìm thấy icon.ico")
        return True, str(icon)
    else:
        print("⚠️ Không có icon.ico")
        return True, None


# =============================
# CÀI DEPENDENCIES
# =============================
def install_requirements():
    packages = [
        ("pyinstaller", "PyInstaller"),
        ("pillow", "PIL"),
        ("pygame", "pygame"),
        ("customtkinter", "customtkinter"),
        ("g4f", "g4f"),
        ("python-docx", "docx"),
        ("PyPDF2", "PyPDF2"),
        ("chardet", "chardet"),
        ("requests", "requests"),
    ]

    for pkg, name in packages:
        if not install_package(pkg, name):
            return False
    return True


# =============================
# THU THẬP FILE DATA
# =============================
def collect_data():
    print("📁 Đang quét file...")

    exclude_dirs = {
        "__pycache__", ".git", ".idea", ".vscode",
        "build", "dist", "venv", "env", ".env"
    }

    exclude_ext = {".pyc", ".pyo", ".pyd"}

    data_args = []
    sep = ";" if platform.system() == "Windows" else ":"

    for file in Path(".").rglob("*"):
        if any(x in file.parts for x in exclude_dirs):
            continue
        if file.suffix in exclude_ext:
            continue
        if file.name in ("main.py", "build.py"):
            continue

        if file.is_file():
            rel = file.relative_to(".")
            parent = rel.parent if rel.parent != Path(".") else Path(".")
            data_args.append(
                f"--add-data={rel}{sep}{parent}"
            )

    print(f"📊 Tổng file data: {len(data_args)}")
    return data_args


# =============================
# BUILD EXECUTABLE
# =============================
def build(icon_path):
    print("\n🔨 Bắt đầu build...")

    data = collect_data()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=GemXcel",
        "--clean",

        # 🔥 FIX lỗi pkg_resources
        "--hidden-import=pkg_resources",
    ]

    if icon_path:
        cmd.append(f"--icon={icon_path}")

    cmd += data
    cmd.append("main.py")

    print("⚙️ Running PyInstaller...")
    print(" ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ BUILD THÀNH CÔNG")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ BUILD THẤT BẠI")
        return False



# =============================
# DỌN DẸP
# =============================
def cleanup():
    print("\n🧹 Dọn dẹp...")

    if Path("build").exists():
        shutil.rmtree("build", ignore_errors=True)

    for spec in Path(".").glob("*.spec"):
        spec.unlink(missing_ok=True)

    print("✅ Done cleanup")


# =============================
# MAIN
# =============================
def main():
    print("=" * 50)
    print("🚀 PYINSTALLER AUTO BUILDER")
    print("=" * 50)

    print(f"OS: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}\n")

    ok, icon = check_files()
    if not ok:
        return

    if not install_requirements():
        return

    if build(icon):
        exe_name = "GemXcel.exe" if platform.system() == "Windows" else "GemXcel"
        exe_path = Path("dist") / exe_name

        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 File: {exe_path}")
            print(f"📏 Size: {size:.1f} MB")

        cleanup()
        print("\n🎉 HOÀN THÀNH!")
    else:
        print("\n💡 Kiểm tra lỗi phía trên")


if __name__ == "__main__":
    main()
