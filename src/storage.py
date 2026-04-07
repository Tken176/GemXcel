# storage.py
import json
import shutil
import os
import config


def ensure_file_exists(bundled_path, save_path):
    """Nếu chưa có file save, copy từ bản bundled."""
    import os, shutil, json
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if not os.path.exists(save_path):
        if os.path.exists(bundled_path):
            shutil.copy(bundled_path, save_path)
        else:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

def load_data():
    ensure_save_exists()
    try:
        with open(config.DATA_SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # if corrupted, return empty and overwrite on next save
        return {}

def save_data(data):
    try:
        with open(config.DATA_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False
