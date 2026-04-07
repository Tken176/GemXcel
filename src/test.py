import os

def count_code_lines(root_folder):
    total_lines = 0
    
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        line_count = sum(1 for line in lines if line.strip())
                        total_lines += line_count
                        
                        print(f"{file_path} → {line_count} dòng (không tính dòng trống)")
                
                except Exception as e:
                    print(f"Lỗi khi đọc {file_path}: {e}")
    
    print("\n======================")
    print(f"TỔNG SỐ DÒNG CODE: {total_lines}")

project_folder = "."

count_code_lines(project_folder)