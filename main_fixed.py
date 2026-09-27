import pygame
import sys
import os
import json
import math

pygame.init()

# ============================================================
# 風雲重製版 - 無名動畫校正版
#
# 核心原則：
# 1. 人物永遠使用「腳底中心」作為 Anchor。
# 2. 攻擊動畫、命中特效不再直接把 enemy.x/y 當圖片左上角。
# 3. 每一招可以獨立設定 attack_anchor / hit_anchor / delay / scale。
# 4. 保留 .info + *_offsets.json。
# 5. 無名沒有原始完整動畫時，可用既有素材 + 程式特效組合。
# ============================================================

WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("風雲重製版 - 無名動畫校正版")
clock = pygame.time.Clock()

FPS = 60

# ------------------------------------------------------------
# 戰場基準座標
# ------------------------------------------------------------
PLAYER_POS = (460, 360)       # 無名「腳底中心」
ENEMY_POS = (123, 184)        # 敵人「腳底中心」

# 命中位置不要直接使用敵人的腳底。
# 這裡是「相對於敵人腳底」的位置。
ENEMY_HIT_OFFSET = (0, -58)

# 無名攻擊動畫如果需要微調，只改這裡。
# 不要再到處改 draw_x / draw_y。
PLAYER_ATTACK_OFFSET = (0, 0)

# ------------------------------------------------------------
# 素材載入
# ------------------------------------------------------------
def safe_load(path, scale=1.0, is_alpha=True):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path)
            img = img.convert_alpha() if is_alpha else img.convert()
            if scale != 1.0:
                img = pygame.transform.smoothscale(
                    img,
                    (
                        max(1, int(img.get_width() * scale)),
                        max(1, int(img.get_height() * scale))
                    )
                )
            return img
        except Exception as e:
            print("素材讀取失敗:", path, e)
    return None


BG_IMAGE = safe_load(
    os.path.join("WarScene", "18-1.png"),
    scale=1.0,
    is_alpha=False
)

if BG_IMAGE:
    BG_IMAGE = pygame.transform.scale(BG_IMAGE, (WIDTH, HEIGHT))


HEAD_NAMELESS = safe_load(
    os.path.join("WCHead", "7-1.png"),
    scale=0.5
)


# ============================================================
# offset / animation
# ============================================================
def read_frame_offset(img_path, frame_number, folder, prefix):
    """
    優先順序：
      JSON > .info > (0,0)

    JSON:
      WCAttack_27_offsets.json
      {
          "1": [x, y],
          "2": [x, y]
      }
    """
    ox, oy = 0, 0

    json_filename = f"{folder}_{prefix}_offsets.json"

    if os.path.exists(json_filename):
        try:
            with open(json_filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            key = str(frame_number)
            if key in data and len(data[key]) >= 2:
                ox = int(data[key][0])
                oy = int(data[key][1])
                return ox, oy
        except Exception:
            pass

    info_path = f"{img_path}.info"

    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith("//"):
                        continue

                    parts = line.split(",")

                    if len(parts) >= 2:
                        ox = int(parts[0])
                        oy = int(parts[1])
                        break
        except Exception:
            pass

    return ox, oy


def load_anim_with_info(
    folder,
    prefix,
    start,
    end,
    flip_x=False,
    scale=1.0
):
    frames = []

    for i in range(start, end + 1):
        img_path = os.path.join(folder, f"{prefix}-{i}.png")
        img = safe_load(img_path, scale=scale)

        if not img:
            continue

        ox, oy = read_frame_offset(
            img_path,
            i,
            folder,
            prefix
        )

        # 如果圖片縮放，offset 也必須一起縮放。
        if scale != 1.0:
            ox = int(ox * scale)
            oy = int(oy * scale)

        if flip_x:
            # 正確的水平鏡像：
            # 原 anchor = ox
            # 翻轉後左界會改變，因此：
            # new_ox = -ox - image_width
            img = pygame.transform.flip(img, True, False)
            ox = -ox - img.get_width()

        frames.append({
            "img": img,
            "ox": ox,
            "oy": oy
        })

    return frames


# ============================================================
# 角色基準點
# ============================================================
class Character:
    def __init__(self, x, y, stand_img):
        self.x = x
        self.y = y

        # 永遠以腳底中心定位
        self.base_stand_img = stand_img

        self.override_stand_img = None
        self.is_casting = False

        # 可以個別微調站姿，不需要改整個程式
        self.stand_offset = (0, 0)

    @property
    def anchor(self):
        return (
            self.x,
            self.y
        )

    @property
    def hit_anchor(self):
        return (
            self.x + ENEMY_HIT_OFFSET[0],
            self.y + ENEMY_HIT_OFFSET[1]
        )

    def draw(self, surface):
        img = (
            self.override_stand_img
            if self.override_stand_img
            else self.base_stand_img
        )

        if not img:
            return

        # 注意：
        # 這裡不是把圖片左上角放在 x/y。
        # 而是把圖片「腳底中心」對準角色 anchor。
        rect = img.get_rect(
            midbottom=(
                self.x + self.stand_offset[0],
                self.y + self.stand_offset[1]
            )
        )

        surface.blit(img, rect)


# ============================================================
# Skill Layer
# ============================================================
class SkillLayer:
    def __init__(
        self,
        frames,
        speed,
        anchor_pos,
        local_offset=(0, 0),
        is_additive=False,
        delay_frames=0,
        loop=False
    ):
        self.frames = frames
        self.frame_index = 0.0
        self.speed = speed

        # 固定 anchor
        self.anchor_pos = anchor_pos

        # 這是整組動畫的微調，不改 frame 本身
        self.local_offset = local_offset

        self.is_additive = is_additive
        self.delay = delay_frames
        self.loop = loop

        self.alive = len(frames) > 0
        self.started = False

    def update(self):
        if not self.alive:
            return

        if self.delay > 0:
            self.delay -= 1
            return

        self.started = True
        self.frame_index += self.speed

        if self.loop:
            if len(self.frames) > 0:
                self.frame_index %= len(self.frames)
        else:
            if self.frame_index >= len(self.frames):
                self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        if not self.started:
            return

        index = int(self.frame_index)

        if index < 0 or index >= len(self.frames):
            return

        frame = self.frames[index]

        img = frame["img"]

        draw_x = (
            self.anchor_pos[0]
            + frame["ox"]
            + self.local_offset[0]
        )

        draw_y = (
            self.anchor_pos[1]
            + frame["oy"]
            + self.local_offset[1]
        )

        if self.is_additive:
            surface.blit(
                img,
                (draw_x, draw_y),
                special_flags=pygame.BLEND_RGBA_ADD
            )
        else:
            surface.blit(img, (draw_x, draw_y))


# ============================================================
# 程式生成的無名劍氣
# ============================================================
class ProceduralSwordAura:
    """
    無名專用：
    不需要原始 PNG，也能產生劍氣。
    """

    def __init__(
        self,
        anchor_pos,
        duration=90,
        start_delay=0
    ):
        self.anchor_pos = anchor_pos
        self.duration = duration
        self.age = -start_delay
        self.alive = True

    def update(self):
        if not self.alive:
            return

        self.age += 1

        if self.age >= self.duration:
            self.alive = False

    def draw(self, surface):
        if not self.alive or self.age < 0:
            return

        t = self.age / max(1, self.duration)

        # 前段蓄力、後段爆發
        power = min(1.0, t * 2.0)

        cx, cy = self.anchor_pos

        # 劍氣半徑
        radius = int(18 + power * 95)

        # 多層圓弧 / 劍意
        for n in range(4):
            r = max(4, radius - n * 9)

            rect = pygame.Rect(
                cx - r,
                cy - r,
                r * 2,
                r * 2
            )

            start_angle = -2.7 + t * 2.0
            end_angle = -0.4 + t * 2.0

            # 用弧線模擬劍氣
            try:
                pygame.draw.arc(
                    surface,
                    (210, 230, 255),
                    rect,
                    start_angle,
                    end_angle,
                    max(1, 4 - n)
                )
            except Exception:
                pass


class SwordBurst:
    """
    劍二十三式的最後爆發。
    """
    def __init__(self, anchor_pos, start_delay=0, duration=24):
        self.anchor_pos = anchor_pos
        self.age = -start_delay
        self.duration = duration
        self.alive = True

    def update(self):
        if not self.alive:
            return

        self.age += 1

        if self.age >= self.duration:
            self.alive = False

    def draw(self, surface):
        if not self.alive or self.age < 0:
            return

        t = self.age / max(1, self.duration)

        cx, cy = self.anchor_pos

        max_len = 170
        length = int(max_len * (1.0 - abs(t - 0.35) * 1.8))
        length = max(10, length)

        # 放射狀劍芒
        for i in range(16):
            angle = (math.pi * 2.0 * i / 16.0)

            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length

            pygame.draw.line(
                surface,
                (220, 235, 255),
                (cx, cy),
                (x2, y2),
                max(1, 5 - int(t * 4))
            )


# ============================================================
# Composite Skill
# ============================================================
class CompositeSkillPlayer:
    def __init__(self):
        self.layers = []
        self.alive = True

    def add_layer(self, layer):
        if layer and getattr(layer, "alive", False):
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


# ============================================================
# 載入原有素材
# ============================================================

print("載入資源中，請稍候...")

# 1. 悲痛莫名
ANIM_BEITONG_ATK = load_anim_with_info(
    "WCAttack", "27", 1, 62
)

ANIM_BEITONG_SFX = load_anim_with_info(
    "WarSfx", "21", 1, 44
)


# 2. 萬劍歸宗
ANIM_WANJIAN_ATK = load_anim_with_info(
    "WCAttack", "79", 1, 169,
    flip_x=True
)

ANIM_WANJIAN_SFX = load_anim_with_info(
    "WarSfx", "69", 1, 51,
    flip_x=True
)

STAND_JIANCHEN = safe_load(
    os.path.join("WarStand", "58-1.png")
)


# 3. 名動一時
ANIM_MINGDONG = load_anim_with_info(
    "WCAttack", "193", 1, 49
)


# 4. 莫名其妙
ANIM_MOMING = load_anim_with_info(
    "WCAttack", "195", 1, 59
)


# 5. 雲萊仙境
ANIM_YUNLAI_ATK = load_anim_with_info(
    "WCAttack", "49", 1, 103
)

ANIM_YUNLAI_SFX = load_anim_with_info(
    "WarSfx", "43", 1, 119
)


# 無名站姿
STAND_NAMELESS = safe_load(
    os.path.join("WarStand", "28-1.png")
)

STAND_ENEMY = safe_load(
    os.path.join("WarStand", "28-1.png")
)

print("載入完畢！")


# ============================================================
# 角色
# ============================================================
player = Character(
    PLAYER_POS[0],
    PLAYER_POS[1],
    STAND_NAMELESS
)

enemy = Character(
    ENEMY_POS[0],
    ENEMY_POS[1],
    STAND_ENEMY
)


# ============================================================
# 招式設定
#
# 之後只需要改這裡。
# 不要再去 SkillLayer 裡面亂改座標。
# ============================================================
SKILL_CONFIG = {

    # 原素材招式
    "beitong": {
        "attack_offset": (0, 0),
        "hit_offset": ENEMY_HIT_OFFSET,
        "sfx_delay": 20
    },

    "wanjian": {
        "attack_offset": (0, 0),
        "hit_offset": ENEMY_HIT_OFFSET,
        "sfx_delay": 30
    },

    "mingdong": {
        "attack_offset": (0, 0)
    },

    "momingt": {
        "attack_offset": (0, 0)
    },

    "yunlai": {
        "attack_offset": (0, 0),
        "hit_offset": ENEMY_HIT_OFFSET,
        "sfx_delay": 20
    },

    # 全新無名劍二十三
    "jian23": {
        "aura_offset": (0, -60),
        "burst_offset": ENEMY_HIT_OFFSET,
        "burst_delay": 52
    }
}


# ============================================================
# 建立無名「劍二十三」
# ============================================================
def build_jian23():
    skill = CompositeSkillPlayer()

    # 第一層：
    # 無名自己身上的劍意
    aura_anchor = (
        player.x + SKILL_CONFIG["jian23"]["aura_offset"][0],
        player.y + SKILL_CONFIG["jian23"]["aura_offset"][1]
    )

    skill.add_layer(
        ProceduralSwordAura(
            aura_anchor,
            duration=82,
            start_delay=0
        )
    )

    # 第二層：
    # 敵人命中點爆發
    burst_anchor = (
        enemy.hit_anchor[0]
        + SKILL_CONFIG["jian23"]["burst_offset"][0],
        enemy.hit_anchor[1]
        + SKILL_CONFIG["jian23"]["burst_offset"][1]
    )

    skill.add_layer(
        SwordBurst(
            burst_anchor,
            start_delay=SKILL_CONFIG["jian23"]["burst_delay"],
            duration=24
        )
    )

    return skill


# ============================================================
# 操作
# ============================================================
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

            # 預設：
            # 攻擊期間不要把站姿清掉。
            # 這樣沒有完整無名 attack sprite 時，
            # 角色也不會突然消失。
            player.is_casting = False
            player.override_stand_img = None

            # ------------------------------------------------
            # 1 悲痛莫名
            # ------------------------------------------------
            if event.key == pygame.K_1:

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_BEITONG_ATK,
                        0.25,
                        player.anchor,
                        local_offset=(
                            SKILL_CONFIG["beitong"]["attack_offset"]
                        )
                    )
                )

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_BEITONG_SFX,
                        0.25,
                        enemy.hit_anchor,
                        is_additive=True,
                        delay_frames=SKILL_CONFIG["beitong"]["sfx_delay"]
                    )
                )

                skill_triggered = True

            # ------------------------------------------------
            # 2 萬劍歸宗
            # ------------------------------------------------
            elif event.key == pygame.K_2:

                # 仍然可以保留劍晨站姿測試，
                # 但它不再決定攻擊座標。
                player.override_stand_img = STAND_JIANCHEN

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_WANJIAN_ATK,
                        0.25,
                        player.anchor,
                        local_offset=(
                            SKILL_CONFIG["wanjian"]["attack_offset"]
                        )
                    )
                )

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_WANJIAN_SFX,
                        0.25,
                        enemy.hit_anchor,
                        is_additive=True,
                        delay_frames=SKILL_CONFIG["wanjian"]["sfx_delay"]
                    )
                )

                skill_triggered = True

            # ------------------------------------------------
            # 3 名動一時
            # ------------------------------------------------
            elif event.key == pygame.K_3:

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_MINGDONG,
                        0.25,
                        player.anchor,
                        local_offset=(
                            SKILL_CONFIG["mingdong"]["attack_offset"]
                        )
                    )
                )

                skill_triggered = True

            # ------------------------------------------------
            # 4 劍二十三
            # ------------------------------------------------
            elif event.key == pygame.K_4:

                active_skill = build_jian23()

                skill_triggered = True

            # ------------------------------------------------
            # 5 雲萊仙境
            # ------------------------------------------------
            elif event.key == pygame.K_5:

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_YUNLAI_ATK,
                        0.25,
                        player.anchor,
                        local_offset=(
                            SKILL_CONFIG["yunlai"]["attack_offset"]
                        )
                    )
                )

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_YUNLAI_SFX,
                        0.25,
                        enemy.hit_anchor,
                        is_additive=True,
                        delay_frames=SKILL_CONFIG["yunlai"]["sfx_delay"]
                    )
                )

                skill_triggered = True

            # ------------------------------------------------
            # 6 莫名其妙
            # ------------------------------------------------
            elif event.key == pygame.K_6:

                active_skill.add_layer(
                    SkillLayer(
                        ANIM_MOMING,
                        0.25,
                        player.anchor,
                        local_offset=(
                            SKILL_CONFIG["momingt"]["attack_offset"]
                        )
                    )
                )

                skill_triggered = True

            if not skill_triggered:
                active_skill = None


    # ========================================================
    # Update
    # ========================================================
    if active_skill:

        active_skill.update()

        if not active_skill.alive:
            active_skill = None
            player.is_casting = False
            player.override_stand_img = None


    # ========================================================
    # Render
    # ========================================================
    screen.fill((0, 0, 0))

    if BG_IMAGE:
        screen.blit(
            BG_IMAGE,
            BG_IMAGE.get_rect(
                center=(WIDTH // 2, HEIGHT // 2)
            )
        )

    # 敵人在後
    enemy.draw(screen)

    # 無名
    player.draw(screen)

    # 招式特效在最上層
    if active_skill:
        active_skill.draw(screen)


    # ========================================================
    # Debug / 操作說明
    # ========================================================
    instructions = [
        "無名動畫校正版",
        "1: 悲痛莫名",
        "2: 萬劍歸宗",
        "3: 名動一時",
        "4: 劍二十三（新設計）",
        "5: 雲萊仙境",
        "6: 莫名其妙",
        "",
        "座標基準：角色腳底 Anchor / 敵人命中點 Anchor"
    ]

    for i, text in enumerate(instructions):

        render_text = font.render(
            text,
            True,
            (255, 255, 255)
        )

        screen.blit(
            render_text,
            (10, 10 + i * 23)
        )


    pygame.display.flip()
    clock.tick(FPS)


pygame.quit()
sys.exit()
