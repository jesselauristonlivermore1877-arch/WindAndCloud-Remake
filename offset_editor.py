import pygame
import sys
import os
import json

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("風雲絕招 - 視覺化定錨點編輯器")
clock = pygame.time.Clock()

# ==========================================
# 設定你要校正的招式資料夾與前綴
# ==========================================
TARGET_FOLDER = "WCAttack"  # 可以改成 "WarSfx"
TARGET_PREFIX = "119"       # 可以改成 "43"
START_FRAME = 1
END_FRAME = 115             # 根據該招式總幀數修改

def load_frames():
    frames = []
    for i in range(START_FRAME, END_FRAME + 1):
        path = os.path.join(TARGET_FOLDER, f"{TARGET_PREFIX}-{i}.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            frames.append({"img": img, "offset": [0, 0], "index": i})
    return frames

frames = load_frames()
if not frames:
    print(f"找不到任何圖片，請確認 {TARGET_FOLDER}/{TARGET_PREFIX}-x.png 是否存在。")
    sys.exit()

current_idx = 0
crosshair_pos = (WIDTH // 2, HEIGHT // 2)

# 嘗試讀取已存在的 JSON 進度
json_filename = f"{TARGET_FOLDER}_{TARGET_PREFIX}_offsets.json"
if os.path.exists(json_filename):
    with open(json_filename, "r") as f:
        saved_data = json.load(f)
        for i, frame in enumerate(frames):
            idx_str = str(frame["index"])
            if idx_str in saved_data:
                frame["offset"] = saved_data[idx_str]

font = pygame.font.SysFont("simhei", 20)

running = True
while running:
    shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT
    move_speed = 10 if shift_pressed else 1  # 按住 Shift 可以一次移動 10 像素

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # 切換影格
            if event.key == pygame.K_SPACE or event.key == pygame.K_RIGHT:
                if current_idx < len(frames) - 1:
                    # 自動繼承上一幀的偏移量，減少調整時間
                    next_offset = frames[current_idx]["offset"].copy()
                    current_idx += 1
                    frames[current_idx]["offset"] = next_offset
            elif event.key == pygame.K_LEFT:
                if current_idx > 0:
                    current_idx -= 1
                    
            # 儲存 JSON
            elif event.key == pygame.K_s:
                export_data = {str(f["index"]): f["offset"] for f in frames}
                with open(json_filename, "w") as f:
                    json.dump(export_data, f, indent=4)
                print(f"進度已儲存至 {json_filename}！")
                
            # 調整當前圖片偏移量 (WASD 或 方向鍵)
            elif event.key == pygame.K_w or event.key == pygame.K_UP:
                frames[current_idx]["offset"][1] -= move_speed
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                frames[current_idx]["offset"][1] += move_speed
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                frames[current_idx]["offset"][0] -= move_speed
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                frames[current_idx]["offset"][0] += move_speed

    screen.fill((40, 40, 40))

    # 繪製十字輔助線 (代表人物腳底中心點)
    pygame.draw.line(screen, (0, 255, 0), (crosshair_pos[0], 0), (crosshair_pos[0], HEIGHT), 1)
    pygame.draw.line(screen, (0, 255, 0), (0, crosshair_pos[1]), (WIDTH, crosshair_pos[1]), 1)
    
    # 繪製殘影 (Onion Skin) - 顯示前一幀半透明狀態，方便對齊
    if current_idx > 0:
        prev_frame = frames[current_idx - 1]
        prev_img = prev_frame["img"].copy()
        prev_img.set_alpha(100)
        px = crosshair_pos[0] + prev_frame["offset"][0]
        py = crosshair_pos[1] + prev_frame["offset"][1]
        screen.blit(prev_img, (px, py))

    # 繪製當前影格
    curr_frame = frames[current_idx]
    cx = crosshair_pos[0] + curr_frame["offset"][0]
    cy = crosshair_pos[1] + curr_frame["offset"][1]
    screen.blit(curr_frame["img"], (cx, cy))

    # UI 資訊
    text_info = font.render(f"影格: {curr_frame['index']} / {END_FRAME} | 偏移量: X={curr_frame['offset'][0]}, Y={curr_frame['offset'][1]}", True, (255, 255, 255))
    text_help1 = font.render("操作: [方向鍵] 移動圖片 | [Shift+方向鍵] 快速移動", True, (200, 200, 200))
    text_help2 = font.render("[空白鍵] 下一幀 | [S] 儲存 JSON 檔案", True, (200, 200, 200))
    
    screen.blit(text_info, (10, 10))
    screen.blit(text_help1, (10, 40))
    screen.blit(text_help2, (10, 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()