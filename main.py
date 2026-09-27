import pygame
import sys
import os
import json

pygame.init()

WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("風雲重製版 - 絕對座標與完美鏡像校正")
clock = pygame.time.Clock()

PLAYER_POS = (460, 360)
ENEMY_POS = (123, 184)

def safe_load(path, scale=1.0, is_alpha=True):
    if os.path.exists(path):
        img = pygame.image.load(path)
        img = img.convert_alpha() if is_alpha else img.convert()
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        return img
    return None

BG_IMAGE = safe_load(os.path.join("WarScene", "18-1.png"), scale=1.0, is_alpha=False)
if BG_IMAGE:
    BG_IMAGE = pygame.transform.scale(BG_IMAGE, (WIDTH, HEIGHT))

HEAD_NAMELESS = safe_load(os.path.join("WCHead", "7-1.png"), scale=0.5)

# ==========================================
# 核心升級：完美整合 .info 與 .json，並套用正確的鏡像數學公式
# ==========================================
def load_anim_with_info(folder, prefix, start, end, flip_x=False):
    frames = []
    # 讀取手動微調的 JSON
    json_filename = f"{folder}_{prefix}_offsets.json"
    json_offsets = {}
    if os.path.exists(json_filename):
        with open(json_filename, "r") as f:
            json_offsets = json.load(f)
            
    for i in range(start, end + 1):
        img_path = os.path.join(folder, f"{prefix}-{i}.png")
        info_path = f"{img_path}.info"
        img = safe_load(img_path)
        
        if img:
            ox, oy = 0, 0
            # 1. 優先讀取解包工具產生的 .info 原始座標
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if not line.startswith('//') and line.strip():
                                parts = line.strip().split(',')
                                if len(parts) >= 2:
                                    ox, oy = int(parts[0]), int(parts[1])
                                    break
                except Exception:
                    pass
            
            # 2. 如果你有用 offset_editor 存出 json，則覆蓋原始設定
            idx_str = str(i)
            if idx_str in json_offsets:
                ox, oy = json_offsets[idx_str]
            
            # 3. 完美的水平鏡像翻轉演算法
            if flip_x:
                img = pygame.transform.flip(img, True, False)
                # 翻轉後的 X 偏移量 = 原負值 - 圖片寬度 (保持錨點重心不變)
                ox = -ox - img.get_width()
                
            frames.append({"img": img, "ox": ox, "oy": oy})
    return frames

print("載入資源中，請稍候...")

# 1. 悲痛莫名 (步驚雲)
ANIM_BEITONG_ATK = load_anim_with_info("WCAttack", "27", 1, 62)
ANIM_BEITONG_SFX = load_anim_with_info("WarSfx", "21", 1, 44)

# 2. 萬劍歸宗 (斷帥基底 - 敵方素材轉我方，啟用 flip_x)
ANIM_WANJIAN_ATK = load_anim_with_info("WCAttack", "79", 1, 169, flip_x=True)
ANIM_WANJIAN_SFX = load_anim_with_info("WarSfx", "69", 1, 51, flip_x=True)
STAND_JIANCHEN = safe_load(os.path.join("WarStand", "58-1.png")) 

# 3. 名動一時 (劍晨)
ANIM_MINGDONG = load_anim_with_info("WCAttack", "193", 1, 49)

# 4. 莫名其妙 (劍晨)
ANIM_MOMING = load_anim_with_info("WCAttack", "195", 1, 59)

# 5. 雲萊仙境 (無名)
ANIM_YUNLAI_ATK = load_anim_with_info("WCAttack", "49", 1, 103)
ANIM_YUNLAI_SFX = load_anim_with_info("WarSfx", "43", 1, 119)

STAND_NAMELESS = safe_load(os.path.join("WarStand", "28-1.png"))
STAND_ENEMY = safe_load(os.path.join("WarStand", "28-1.png"))
print("載入完畢！")

# ==========================================
# 渲染圖層：徹底放棄 get_rect 對齊，改用絕對坐標
# ==========================================
class SkillLayer:
    def __init__(self, frames, speed, anchor_pos, is_additive=False, delay_frames=0):
        self.frames = frames
        self.frame_index = 0.0
        self.speed = speed
        self.anchor_pos = anchor_pos
        self.is_additive = is_additive
        self.delay = delay_frames
        self.alive = len(frames) > 0
        self.started = False

    def update(self):
        if not self.alive: return
        
        if self.delay > 0:
            self.delay -= 1
            return
        else:
            self.started = True

        self.frame_index += self.speed
        if self.frame_index >= len(self.frames):
            self.alive = False

    def draw(self, surface):
        if self.alive and self.started and int(self.frame_index) < len(self.frames):
            frame_data = self.frames[int(self.frame_index)]
            img = frame_data["img"]
            
            # 核心修正：人物基準點 + 圖片真實偏移量 (這就是你 offset_editor.py 的畫法)
            draw_x = self.anchor_pos[0] + frame_data["ox"]
            draw_y = self.anchor_pos[1] + frame_data["oy"]
            
            if self.is_additive:
                surface.blit(img, (draw_x, draw_y), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                surface.blit(img, (draw_x, draw_y))

class CompositeSkillPlayer:
    def __init__(self):
        self.layers = []
        self.alive = True

    def add_layer(self, layer):
        if layer.alive:
            self.layers.append(layer)

    def update(self):
        self.alive = False
        for layer in self.layers:
            layer.update()
            if layer.alive:
                self.alive = True

    def draw(self, surface):
        for layer in self.layers:
            layer.draw(surface)

class Character:
    def __init__(self, x, y, stand_img):
        self.x = x
        self.y = y
        self.base_stand_img = stand_img
        self.override_stand_img = None
        self.is_casting = False

    def draw(self, surface):
        img_to_draw = self.override_stand_img if self.override_stand_img else self.base_stand_img
        if img_to_draw and not self.is_casting:
            rect = img_to_draw.get_rect(midbottom=(self.x, self.y))
            surface.blit(img_to_draw, rect)

player = Character(PLAYER_POS[0], PLAYER_POS[1], STAND_NAMELESS)
enemy = Character(ENEMY_POS[0], ENEMY_POS[1], STAND_ENEMY) 

active_skill = None
font = pygame.font.SysFont("simhei", 20)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN and not active_skill:
            skill_triggered = False
            active_skill = CompositeSkillPlayer()
            player.is_casting = True 
            player.override_stand_img = None
            
            # [1] 悲痛莫名 (步驚雲)
            if event.key == pygame.K_1:
                active_skill.add_layer(SkillLayer(ANIM_BEITONG_ATK, 0.25, (player.x, player.y)))
                active_skill.add_layer(SkillLayer(ANIM_BEITONG_SFX, 0.25, (enemy.x, enemy.y), is_additive=True, delay_frames=20))
                skill_triggered = True
                
            # [2] 萬劍歸宗 (斷帥基底：人物翻轉，特效精準打在敵人身上)
            elif event.key == pygame.K_2:
                player.is_casting = False # 萬劍歸宗需要保留人物站姿
                player.override_stand_img = STAND_JIANCHEN
                active_skill.add_layer(SkillLayer(ANIM_WANJIAN_ATK, 0.25, (player.x, player.y)))
                # 修正：將 SFX 的中心點設定在敵人 (enemy.x, enemy.y)
                active_skill.add_layer(SkillLayer(ANIM_WANJIAN_SFX, 0.25, (enemy.x, enemy.y), is_additive=True, delay_frames=30))
                skill_triggered = True
                
            # [3] 名動一時
            elif event.key == pygame.K_3:
                active_skill.add_layer(SkillLayer(ANIM_MINGDONG, 0.25, (player.x, player.y)))
                skill_triggered = True
                
            # [4] 莫名其妙
            elif event.key == pygame.K_4:
                active_skill.add_layer(SkillLayer(ANIM_MOMING, 0.25, (player.x, player.y)))
                skill_triggered = True
                
            # [5] 雲萊仙境
            elif event.key == pygame.K_5:
                active_skill.add_layer(SkillLayer(ANIM_YUNLAI_ATK, 0.25, (player.x, player.y)))
                active_skill.add_layer(SkillLayer(ANIM_YUNLAI_SFX, 0.25, (enemy.x, enemy.y), is_additive=True, delay_frames=20))
                skill_triggered = True

            if not skill_triggered:
                player.is_casting = False
                active_skill = None

    if active_skill:
        active_skill.update()
        if not active_skill.alive:
            active_skill = None
            player.is_casting = False
            player.override_stand_img = None

    screen.fill((0, 0, 0))
    if BG_IMAGE:
        screen.blit(BG_IMAGE, BG_IMAGE.get_rect(center=(WIDTH//2, HEIGHT//2)))
    
    enemy.draw(screen)
    player.draw(screen)
    
    if active_skill:
        active_skill.draw(screen)

    instructions = [
        "請按數字鍵測試無名劍法 (已校正鏡像與打擊點)：",
        "1: 悲痛莫名 (步驚雲)",
        "2: 萬劍歸宗 (斷帥已正確翻轉，打擊敵人)",
        "3: 名動一時 (劍晨)",
        "4: 莫名其妙 (劍晨)",
        "5: 雲萊仙境"
    ]
    for i, text in enumerate(instructions):
        render_text = font.render(text, True, (255, 255, 255))
        screen.blit(render_text, (10, 10 + i * 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()