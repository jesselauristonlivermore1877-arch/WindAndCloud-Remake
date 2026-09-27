import os
import pygame

def run_diagnostics(folder, prefix, num_frames=10):
    print(f"\n[{folder} / {prefix} 系列特效] - 載入前 {num_frames} 幀數據")
    print("-" * 65)
    print(f"{'影格':<6} | {'圖片實際尺寸 (W x H)':<22} | {'.info 讀取偏移量 (X, Y)':<25}")
    print("-" * 65)
    
    for i in range(1, num_frames + 1):
        img_path = os.path.join(folder, f"{prefix}-{i}.png")
        info_path = f"{img_path}.info"
        
        # 讀取圖片尺寸
        img_w, img_h = 0, 0
        if os.path.exists(img_path):
            img = pygame.image.load(img_path)
            img_w, img_h = img.get_size()
        else:
            print(f"Frame {i:<2} | 找不到圖片檔案: {img_path}")
            continue
            
        # 讀取 info 偏移量
        info_ox, info_oy = "N/A", "N/A"
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.startswith('//') and line.strip():
                            parts = line.strip().split(',')
                            if len(parts) >= 2:
                                info_ox, info_oy = parts[0], parts[1]
                                break
            except Exception as e:
                info_ox, info_oy = "ERR", "ERR"
                
        print(f"Frame {i:<2} | W:{img_w:<4} x H:{img_h:<4}           | X: {info_ox:<5}, Y: {info_oy:<5}")

if __name__ == "__main__":
    pygame.display.set_mode((100, 100)) # 初始化 Pygame 環境以讀取圖片尺寸
    print("啟動座標與畫布解析器...")
    
    # 檢查劍聖 (119系列)
    run_diagnostics("WCAttack", "119", 10)
    
    # 檢查無名/步驚雲 (43系列)
    run_diagnostics("WarSfx", "43", 10)
    
    print("\n除錯完畢，請將以上終端機輸出的表格貼回給我。")