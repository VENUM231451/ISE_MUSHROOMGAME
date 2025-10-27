import pygame, sys, random, os, math
from functools import lru_cache

# Game Settings
WIDTH, HEIGHT = 1920, 1076
FPS = 60
ASSET_DIR = "assets"
HIGH_SCORE_FILE = "highscore.txt"

# Game Balance (Made Easier)
LEVEL1_GOAL = 5        # Testing: lowered from 25
LEVEL2_COINS = 4       # Reduced from 6
GROUND_Y = HEIGHT - 140
GRAVITY = 0.5        # Reduced from 0.5
PLAYER_RUN_SPEED = 6   # Increased from 5
PLAYER_JUMP_SPEED = -12  # Stronger jump
DASH_SPEED = 15        # Faster dash
DASH_COOLDOWN_FRAMES = 15 * FPS  # 15-second cooldown
SHIELD_DURATION_FRAMES = 600  # Increased from 420
SHIELD_HIT_COST_FRAMES = int(SHIELD_DURATION_FRAMES * 0.25)  # Shield reduces by ~25% per hit

# Screen FX tuning
COLLECT_FLASH_DURATION = 8
HIT_FLASH_DURATION = 16

UI_COLORS = {
    "panel": (34, 52, 96),
    "panel_alt": (60, 36, 72),
    "accent": (130, 190, 255),
    "accent_alt": (255, 180, 120),
    "danger": (255, 120, 150),
    "success": (130, 220, 190),
    "bg_top": (14, 20, 34),
    "bg_bottom": (4, 8, 18),
}

LIVES_START = 3        # Much more forgiving
MUSHROOM_FALL_SPEED = 3.5  # Faster base falling speed
LEVEL1_MAX_CONCURRENT = 2  # Max mushrooms falling at once
LEVEL1_SPAWN_DELAY_MIN = 20
LEVEL1_SPAWN_DELAY_MAX = 50
LEVEL1_MIN_X_GAP = 220  # Minimum horizontal separation between active mushrooms
# Endless Runner Settings
RUNNER_SPEED = 4      # Base scrolling speed
RUNNER_ACCELERATION = 0.01  # Speed increase over time
MAX_RUNNER_SPEED = 12  # Maximum speed cap
MONSTER_SPAWN_DISTANCE = 800  # Distance between monster spawns
MONSTER_MAX_CONCURRENT = 3    # Cap active monsters for fairness
POWERUP_SPAWN_DISTANCE = 2400  # Increased from 1200 to reduce overall powerup frequency
DISTANCE_SCORE_UNIT = 100  # Distance units per 1 score point

# Helper Functions
def resource_path(folder, name):
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(folder, name + ext)
        if os.path.exists(path):
            return path
    return None

def load_image(name, size):
    path = resource_path(ASSET_DIR, name)
    if path and os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
        except:
            return None
    return None

def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(ASSET_DIR, "sounds", "new_sfx", name + ".wav"))
    except:
        return None

def adjust_color(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def draw_vertical_gradient(surface, top_color, bottom_color):
    width, height = surface.get_size()
    if height <= 0:
        return
    top = (*top_color, 255) if len(top_color) == 3 else top_color
    bottom = (*bottom_color, 255) if len(bottom_color) == 3 else bottom_color
    channels = len(top)
    for y in range(height):
        ratio = y / (height - 1) if height > 1 else 0
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(channels))
        pygame.draw.line(surface, color, (0, y), (width, y))


@lru_cache(maxsize=64)
def get_font(size, bold=True):
    return pygame.font.SysFont("arial", size, bold=bold)


def draw_glass_panel(surface, rect, base_color=(34, 52, 96), border_color=None, radius=20, alpha=200, shadow=True):
    rect = pygame.Rect(rect)
    if shadow:
        shadow_rect = rect.move(0, 6)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 110), shadow_surface.get_rect(), border_radius=radius)
        surface.blit(shadow_surface, shadow_rect.topleft)

    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    top = (*adjust_color(base_color, 45), alpha)
    bottom = (*adjust_color(base_color, -30), alpha)
    draw_vertical_gradient(panel, top, bottom)

    if rect.width > 24 and rect.height > 24:
        highlight = pygame.Surface((rect.width - 24, 10), pygame.SRCALPHA)
        draw_vertical_gradient(highlight, (255, 255, 255, 90), (255, 255, 255, 0))
        panel.blit(highlight, (12, 12))
        lowlight = pygame.Surface((rect.width - 24, 12), pygame.SRCALPHA)
        draw_vertical_gradient(lowlight, (0, 0, 0, 0), (0, 0, 0, 90))
        panel.blit(lowlight, (12, rect.height - 18))

    border = border_color if border_color else adjust_color(base_color, 80)
    pygame.draw.rect(panel, (*border, 210), panel.get_rect(), width=2, border_radius=radius)

    inner_rect = panel.get_rect().inflate(-12, -12)
    if inner_rect.width > 0 and inner_rect.height > 0:
        pygame.draw.rect(panel, (255, 255, 255, 40), inner_rect, width=1, border_radius=max(4, radius - 6))

    surface.blit(panel, rect.topleft)


def draw_text(surf, text, size, x, y, color=(255,255,255)):
    font = get_font(size, bold=True)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(x, y))
    surf.blit(txt, rect)
    return rect

def draw_health_bar(surf, x, y, w, h, value, max_value, color=(255,60,60)):
    pygame.draw.rect(surf, (20, 28, 44), (x, y, w, h), border_radius=6)
    fill_ratio = (value / max_value) if max_value > 0 else 0
    fill_w = int(max(0.0, min(1.0, fill_ratio)) * w)
    if fill_w > 0:
        fill = pygame.Surface((fill_w, h), pygame.SRCALPHA)
        draw_vertical_gradient(fill, (255, 150, 170, 230), (200, 70, 110, 230))
        surf.blit(fill, (x, y))
        highlight_h = max(2, h // 2)
        if fill_w > 4:
            pygame.draw.rect(surf, (255, 255, 255, 40), (x + 2, y + 2, fill_w - 4, highlight_h), border_radius=4)
    pygame.draw.rect(surf, (255, 200, 220), (x, y, w, h), 2, border_radius=6)


def draw_shield_bar(surf, x, y, w, h, value, max_value):
    pygame.draw.rect(surf, (18, 26, 40), (x, y, w, h), border_radius=6)
    fill_ratio = (value / max_value) if max_value > 0 else 0
    fill_w = int(max(0.0, min(1.0, fill_ratio)) * w)
    if fill_w > 0:
        fill = pygame.Surface((fill_w, h), pygame.SRCALPHA)
        draw_vertical_gradient(fill, (140, 210, 255, 230), (60, 140, 230, 230))
        surf.blit(fill, (x, y))
        highlight_h = max(2, h // 2)
        if fill_w > 4:
            pygame.draw.rect(surf, (255, 255, 255, 40), (x + 2, y + 2, fill_w - 4, highlight_h), border_radius=4)
    pygame.draw.rect(surf, (150, 210, 255), (x, y, w, h), 2, border_radius=6)


def draw_dash_bar(surf, x, y, w, h, value, max_value):
    pygame.draw.rect(surf, (18, 26, 40), (x, y, w, h), border_radius=6)
    if max_value > 0:
        fill_ratio = max(0.0, min(1.0, value / max_value))
    else:
        fill_ratio = 0.0
    fill_w = int(fill_ratio * w)
    if value > 0 and fill_w > 0:
        base = pygame.Surface((fill_w, h), pygame.SRCALPHA)
        draw_vertical_gradient(base, (120, 160, 255, 220), (40, 80, 210, 220))
        surf.blit(base, (x, y))
        highlight_h = max(2, h // 2)
        if fill_w > 4:
            pygame.draw.rect(surf, (255, 255, 255, 40), (x + 2, y + 2, fill_w - 4, highlight_h), border_radius=4)
    elif value <= 0:
        ready_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        draw_vertical_gradient(ready_surface, (110, 220, 160, 220), (70, 180, 130, 220))
        surf.blit(ready_surface, (x, y))
        highlight_h = max(2, h // 2)
        pygame.draw.rect(surf, (255, 255, 255, 40), (x + 2, y + 2, w - 4, highlight_h), border_radius=4)
    pygame.draw.rect(surf, (170, 200, 255), (x, y, w, h), 2, border_radius=6)
    if value <= 0:
        font = get_font(16)
        txt = font.render("READY", True, (230, 255, 240))
        surf.blit(txt, txt.get_rect(center=(x + w//2, y + h//2)))


@lru_cache(maxsize=12)
def build_runner_floor_segment(tile_width, floor_height):
    tile_width = max(120, int(tile_width))
    floor_height = max(24, int(floor_height))
    segment = pygame.Surface((tile_width, floor_height), pygame.SRCALPHA)

    draw_vertical_gradient(segment, (78, 92, 140, 255), (26, 30, 58, 255))

    bevel = pygame.Surface((tile_width, 12), pygame.SRCALPHA)
    draw_vertical_gradient(bevel, (210, 230, 255, 120), (90, 120, 180, 0))
    segment.blit(bevel, (0, 0))

    base_panel = pygame.Surface((tile_width, floor_height), pygame.SRCALPHA)
    draw_vertical_gradient(base_panel, (22, 26, 46, 180), (14, 16, 32, 220))
    segment.blit(base_panel, (0, 0))

    panel_width = tile_width // 2
    inset = max(16, tile_width // 12)
    inner_margin = max(18, floor_height // 6)
    for i in range(2):
        panel_rect = pygame.Rect(
            i * panel_width + inset,
            14,
            panel_width - inset * 2,
            floor_height - 28,
        )
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel_surface, (96, 112, 162, 255), (44, 50, 88, 255))
        segment.blit(panel_surface, panel_rect.topleft)

        seam_y = panel_rect.y + panel_rect.height // 2
        pygame.draw.line(segment, (32, 36, 58), (panel_rect.x + 10, seam_y + 1), (panel_rect.right - 10, seam_y + 1), 2)
        pygame.draw.line(segment, (150, 180, 230), (panel_rect.x + 10, seam_y - 1), (panel_rect.right - 10, seam_y - 1), 1)

        bolt_offsets = [
            (panel_rect.x + 20, panel_rect.y + inner_margin),
            (panel_rect.right - 20, panel_rect.y + inner_margin),
            (panel_rect.x + 20, panel_rect.bottom - inner_margin),
            (panel_rect.right - 20, panel_rect.bottom - inner_margin),
        ]
        for bx, by in bolt_offsets:
            pygame.draw.circle(segment, (16, 18, 32), (int(bx), int(by)), 5)
            pygame.draw.circle(segment, (170, 190, 240), (int(bx), int(by)), 2)

        glow_y = panel_rect.y + 18
        for j in range(3):
            light_x = panel_rect.x + int((j + 1) * panel_rect.width / 4)
            pygame.draw.circle(segment, (210, 235, 255, 140), (light_x, glow_y), 6)
            pygame.draw.circle(segment, (40, 60, 90, 240), (light_x, glow_y), 3)

    divider_x = tile_width // 2
    pygame.draw.line(segment, (18, 20, 38, 220), (divider_x, 18), (divider_x, floor_height - 12), 6)
    pygame.draw.line(segment, (92, 110, 160, 160), (divider_x, 18), (divider_x, floor_height - 12), 2)

    lower_shadow = pygame.Surface((tile_width, 34), pygame.SRCALPHA)
    draw_vertical_gradient(lower_shadow, (0, 0, 0, 160), (0, 0, 0, 0))
    segment.blit(lower_shadow, (0, floor_height - 34))

    lip = pygame.Surface((tile_width, 10), pygame.SRCALPHA)
    draw_vertical_gradient(lip, (120, 150, 210, 140), (30, 40, 80, 220))
    segment.blit(lip, (0, max(0, floor_height - 20)))

    return segment


@lru_cache(maxsize=4)
def get_runner_horizon_glow(width, ground_y):
    height = max(60, min(ground_y, 260))
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    draw_vertical_gradient(glow, (90, 150, 220, 90), (20, 40, 80, 0))
    return glow


@lru_cache(maxsize=6)
def get_runner_glow_band(width, height):
    band = pygame.Surface((width, height), pygame.SRCALPHA)
    draw_vertical_gradient(band, (120, 180, 240, 110), (40, 80, 140, 0))
    return band


def draw_runner_floor(surf, width, ground_y, scroll_value):
    floor_height = max(20, surf.get_height() - ground_y)
    if floor_height <= 0:
        return

    tile_width = max(360, min(560, ((width // 3) // 2) * 2 or 360))
    segment = build_runner_floor_segment(tile_width, floor_height)
    tile_w = segment.get_width()
    if tile_w <= 0:
        return

    offset = int((-scroll_value * 1.4) % tile_w)
    start_x = -tile_w + offset
    while start_x < width + tile_w:
        surf.blit(segment, (start_x, ground_y))
        start_x += tile_w

    guard_height = 16
    rail = pygame.Surface((width, guard_height), pygame.SRCALPHA)
    draw_vertical_gradient(rail, (200, 220, 255, 120), (60, 80, 130, 220))
    surf.blit(rail, (0, ground_y - guard_height + 4))

    guard_shadow = pygame.Surface((width, 22), pygame.SRCALPHA)
    draw_vertical_gradient(guard_shadow, (0, 0, 0, 140), (0, 0, 0, 0))
    surf.blit(guard_shadow, (0, ground_y - 4))

    horizon_glow = get_runner_horizon_glow(width, ground_y)
    glow_y = max(0, ground_y - horizon_glow.get_height() - 40)
    surf.blit(horizon_glow, (0, glow_y))


def draw_status_panel(surf, x, y, lives, lives_max, shield_timer, shield_max, dash_cd, dash_max, heart_icon):
    w, h = 380, 190
    panel_rect = pygame.Rect(x, y, w, h)
    draw_glass_panel(surf, panel_rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=26)

    label_font = get_font(16)
    value_font = get_font(20)
    icon_x = panel_rect.x + 24
    label_x = panel_rect.x + 66
    bar_x = panel_rect.x + 66
    bar_w = panel_rect.width - 110
    row_y = panel_rect.y + 32

    if heart_icon:
        icon_surface = heart_icon if heart_icon.get_size() == (26, 26) else pygame.transform.smoothscale(heart_icon, (26, 26))
        surf.blit(icon_surface, (icon_x, row_y - 10))
    surf.blit(label_font.render("HEALTH", True, (255, 210, 220)), (label_x, row_y - 10))
    value_text = value_font.render(f"{lives}/{lives_max}", True, (255, 245, 250))
    surf.blit(value_text, (panel_rect.right - value_text.get_width() - 24, row_y - 10))
    draw_health_bar(surf, bar_x, row_y + 12, bar_w, 16, lives, lives_max)

    row_y += 60
    shield_center = (icon_x + 12, row_y)
    pygame.draw.circle(surf, (140, 200, 255), shield_center, 12, 2)
    surf.blit(label_font.render("SHIELD", True, (210, 230, 255)), (label_x, row_y - 10))
    shield_seconds = max(0, shield_timer // FPS)
    shield_text = value_font.render(f"{shield_seconds}s", True, (210, 235, 255))
    surf.blit(shield_text, (panel_rect.right - shield_text.get_width() - 24, row_y - 10))
    draw_shield_bar(surf, bar_x, row_y + 12, bar_w, 16, shield_timer, shield_max)

    row_y += 60
    lightning = pygame.Surface((26, 26), pygame.SRCALPHA)
    pygame.draw.polygon(
        lightning,
        (255, 210, 150),
        [(12, 0), (20, 0), (14, 12), (24, 12), (8, 26), (14, 14)],
    )
    surf.blit(lightning, (icon_x, row_y - 12))
    dash_label = "DASH READY" if dash_cd <= 0 else "DASH"
    dash_color = (200, 240, 200) if dash_cd <= 0 else (255, 235, 200)
    surf.blit(label_font.render(dash_label, True, dash_color), (label_x, row_y - 10))
    dash_value = "Ready" if dash_cd <= 0 else f"{max(0, dash_cd // FPS)}s"
    dash_text = value_font.render(dash_value, True, (235, 245, 255))
    surf.blit(dash_text, (panel_rect.right - dash_text.get_width() - 24, row_y - 10))
    draw_dash_bar(surf, bar_x, row_y + 12, bar_w, 16, dash_cd, dash_max)


def draw_metrics_strip(surf, distance, score, speed, x=30, y=24):
    available = max(360, surf.get_width() - x - 30)
    w, h = min(520, available), 66
    rect = pygame.Rect(x, y, w, h)
    draw_glass_panel(surf, rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=28)
    label_font = get_font(16)
    info_font = get_font(22)
    label = label_font.render("ENDLESS RUN • STATUS", True, (190, 210, 250))
    surf.blit(label, (rect.x + 22, rect.y + 10))
    text = f"Distance {int(distance):,}    •    Score {score}    •    Speed {speed:.1f}"
    info = info_font.render(text, True, (240, 245, 255))
    surf.blit(info, (rect.x + 22, rect.y + 32))


def draw_controls_pill(surf, text, x, y, w):
    rect = pygame.Rect(x, y, w, 52)
    draw_glass_panel(surf, rect, base_color=(26, 36, 64), border_color=UI_COLORS["accent"], radius=26)
    font = get_font(20)
    txt = font.render(text, True, (225, 232, 242))
    surf.blit(txt, txt.get_rect(center=rect.center))


def draw_score_pill(surf, score, x=30, y=24):
    rect = pygame.Rect(x, y, 220, 74)
    draw_glass_panel(surf, rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=22)
    label = get_font(16).render("SCORE", True, (190, 208, 250))
    value = get_font(34).render(f"{score}", True, (255, 255, 255))
    surf.blit(label, (rect.x + 20, rect.y + 16))
    pygame.draw.line(surf, (180, 200, 255), (rect.x + 20, rect.y + 30), (rect.x + rect.width - 20, rect.y + 30), 1)
    surf.blit(value, (rect.x + 20, rect.y + 34))


def draw_goal_progress_pill(surf, x, y, w, h, collected, goal):
    rect = pygame.Rect(x, y, w, h)
    draw_glass_panel(surf, rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=24)
    header_font = get_font(16)
    desc_font = get_font(18)
    value_font = get_font(32)
    ratio = 0 if goal <= 0 else max(0.0, min(1.0, collected / goal))

    header = header_font.render("LEVEL 1 GOAL", True, (200, 220, 255))
    surf.blit(header, (rect.x + 20, rect.y + 16))
    description = desc_font.render("Catch glowing mushrooms to unlock the run", True, (225, 235, 255))
    surf.blit(description, (rect.x + 20, rect.y + 46))
    value_text = value_font.render(f"{collected}/{goal}", True, (255, 255, 255))
    surf.blit(value_text, (rect.right - value_text.get_width() - 20, rect.y + 18))

    bar_rect = pygame.Rect(rect.x + 20, rect.bottom - 32, rect.width - 40, 16)
    pygame.draw.rect(surf, (18, 26, 44), bar_rect, border_radius=8)
    fill_w = int(bar_rect.width * ratio)
    if fill_w > 0:
        fill = pygame.Surface((fill_w, bar_rect.height), pygame.SRCALPHA)
        draw_vertical_gradient(fill, (130, 230, 200, 230), (70, 200, 160, 230))
        surf.blit(fill, (bar_rect.x, bar_rect.y))
        highlight_h = max(2, bar_rect.height // 2)
        if fill_w > 4:
            pygame.draw.rect(
                surf,
                (255, 255, 255, 50),
                (bar_rect.x + 2, bar_rect.y + 2, fill_w - 4, highlight_h),
                border_radius=6,
            )
    pygame.draw.rect(surf, (150, 230, 200), bar_rect, 2, border_radius=8)


def draw_lives_panel(surf, lives, heart_icon, x, y):
    rect = pygame.Rect(x, y, 280, 96)
    draw_glass_panel(surf, rect, base_color=UI_COLORS["panel_alt"], border_color=UI_COLORS["danger"], radius=24)
    label = get_font(16).render("LIVES", True, (255, 205, 220))
    value = get_font(32).render(str(lives), True, (255, 240, 245))
    surf.blit(label, (rect.x + 20, rect.y + 16))
    surf.blit(value, (rect.right - value.get_width() - 24, rect.y + 18))

    icon_size = 24
    icons_to_show = min(lives, 6)
    base_y = rect.y + rect.height - icon_size - 18
    for i in range(icons_to_show):
        ix = rect.x + 20 + i * (icon_size + 12)
        glow = pygame.Surface((icon_size + 12, icon_size + 12), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (255, 120, 160, 80),
            (glow.get_width() // 2, glow.get_height() // 2),
            glow.get_width() // 2,
        )
        surf.blit(glow, (ix - 6, base_y - 6))
        if heart_icon:
            if heart_icon.get_size() != (icon_size, icon_size):
                icon_surface = pygame.transform.smoothscale(heart_icon, (icon_size, icon_size))
            else:
                icon_surface = heart_icon
            surf.blit(icon_surface, (ix, base_y))
        else:
            pygame.draw.circle(
                surf,
                UI_COLORS["danger"],
                (ix + icon_size // 2, base_y + icon_size // 2),
                icon_size // 2,
            )

def draw_text_shadow(surf, text, size, x, y, color=(255,255,255), shadow_offset=(2,2), shadow_color=(0,0,0)):
    font = get_font(size, bold=True)
    txt_shadow = font.render(text, True, shadow_color)
    rect_shadow = txt_shadow.get_rect(center=(x + shadow_offset[0], y + shadow_offset[1]))
    surf.blit(txt_shadow, rect_shadow)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(x, y))
    surf.blit(txt, rect)
    return rect

def draw_button(surf, rect, label, hovered=False):
    rect = pygame.Rect(rect)
    base = (70, 130, 220)
    hover = (90, 170, 255)
    color = hover if hovered else base
    draw_glass_panel(
        surf,
        rect,
        base_color=color,
        border_color=adjust_color(color, 60),
        radius=rect.height // 2,
        alpha=220,
    )
    draw_text_shadow(surf, label, 30, rect.centerx, rect.centery, (255, 255, 255))

def draw_lives_hearts(surf, lives, x, y):
    spacing = 34
    max_icons = min(lives, 8)
    for i in range(max_icons):
        px = x + i * spacing
        py = y
        icon_rect = pygame.Rect(px, py, 28, 28)
        if heart_img:
            surf.blit(heart_img, icon_rect)
        else:
            pygame.draw.circle(surf, (255,100,150), (px+14, py+14), 14)
    draw_text_shadow(surf, f"x{lives}", 20, x + max_icons * spacing + 20, y + 14, (255,255,255))


def get_menu_layout(width, height):
    hero_w = max(360, min(760, width - 160))
    hero_h = 260
    hero_x = max(40, width // 2 - hero_w // 2)
    ideal_y = height // 2 - hero_h // 2 - 20
    hero_y = max(40, min(height - hero_h - 140, ideal_y))
    hero_rect = pygame.Rect(hero_x, hero_y, hero_w, hero_h)
    start_rect = pygame.Rect(hero_rect.centerx - 180, hero_rect.bottom - 92, 360, 70)
    return hero_rect, start_rect


def load_highscore():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_highscore(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass

# Initialize Pygame
pygame.init()
# Detect current display size and set a safe window size
info = pygame.display.Info()
WIDTH = min(WIDTH, max(800, info.current_w - 40))
HEIGHT = min(HEIGHT, max(450, info.current_h - 80))
GROUND_Y = HEIGHT - 140
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
fullscreen = False
clock = pygame.time.Clock()
pygame.display.set_caption("Shroom Hunter")

try:
    pygame.mixer.init()
except:
    pass

# Load Assets
menu_bg = load_image("menu_bg", (WIDTH, HEIGHT))
level1_bg = load_image("level1_bg", (WIDTH, HEIGHT))
level2_bg = load_image("level2_bg", (WIDTH, HEIGHT))
basket_img = load_image("basket", (298,168))
mushroom_img = load_image("mushroom", (300,300))
mushroom_player_img = load_image("mushroom_legs", (64,64))
monster_img = load_image("monster", (56,56))
heart_img = load_image("heart", (28,28))
heart_icon_small = pygame.transform.smoothscale(heart_img, (24, 24)) if heart_img else None
heart_icon_status = pygame.transform.smoothscale(heart_img, (26, 26)) if heart_img else None

# Load Sounds
collect_snd = load_sound("collect")
miss_snd = load_sound("miss")
hit_snd = load_sound("hit")
jump_snd = load_sound("wing")
dash_snd = load_sound("swoosh")

# Set volumes
for snd in [collect_snd, miss_snd, hit_snd, jump_snd, dash_snd]:
    if snd:
        snd.set_volume(0.7)

# Game Variables
MENU, LEVEL1, LEVEL2, LEVEL2_READY, GAMEOVER, WIN = "menu","level1","level2","level2_ready","gameover","win"
state = MENU
score = 0
highscore = load_highscore()
lives = LIVES_START
combo = 0
paused = False
level2_ready_timer = 0  # Timer for the ready prompt
gameover_timer = 0  # Auto-return timer for GAME OVER

# Endless Runner Variables
runner_distance = 0    # Total distance traveled
runner_speed = RUNNER_SPEED  # Current scrolling speed
bg_scroll_x = 0       # Background scroll position
next_monster_spawn = MONSTER_SPAWN_DISTANCE
next_powerup_spawn = POWERUP_SPAWN_DISTANCE
particles = []        # Particle effects list
distance_score_carry = 0.0  # Accumulates distance towards score points
ambient_spore_timer = 0
trail_emit_timer = 0
collect_flash_timer = 0
hit_flash_timer = 0

# Level 1 Variables
basket = basket_img.get_rect(midbottom=(WIDTH//2, HEIGHT-10))
mushrooms = []
next_mushroom_spawn_timer = 0

# Level 2 Variables
player = mushroom_player_img.get_rect(center=(WIDTH//2, HEIGHT//2))
player_vx, player_vy = 0, 0
on_ground = False
dash_cd = 0
shield_timer = 0
coins, monsters, spikes, hearts, shields = [], [], [], [], []

def spawn_mushroom():
    # Choose an X that maintains a fair horizontal gap from existing mushrooms
    def choose_x():
        for _ in range(24):
            x = random.randint(50, WIDTH-350)
            too_close = any(abs(x - m["rect"].x) < LEVEL1_MIN_X_GAP for m in mushrooms)
            if not too_close:
                return x
        # Fallback: bias away from basket center to increase challenge unpredictably
        return 50 if basket.centerx > WIDTH//2 else WIDTH - 350
    x = choose_x()
    kind = random.choices(["normal", "gold"], weights=[85, 15])[0]
    # Ensure we always have a valid image; if gold asset is missing, use the normal mushroom image
    gold_img = load_image("mushroom_gold", (300,300)) if kind == "gold" else None
    img = mushroom_img if gold_img is None else gold_img
    return {"rect": pygame.Rect(x, -300, 300, 300), "kind": kind, "img": img}

def spawn_level2():
    # For endless runner, we don't need static coins anymore
    coins = []
    # Start with no monsters - they'll spawn dynamically
    monsters = []
    spikes = []
    # Start with some powerups
    hearts = [pygame.Rect(600, GROUND_Y-60, 28, 28)]
    shields = [pygame.Rect(1000, GROUND_Y-50, 24, 24)]
    return coins, monsters, spikes, hearts, shields

def spawn_monster(distance):
    """Spawn a monster at the given distance from the right edge"""
    monster_types = [
        {"vx": -runner_speed - 2, "size": (56, 56)},  # Fast monster
        {"vx": -runner_speed - 1, "size": (40, 40)},  # Medium monster
        {"vx": -runner_speed - 3, "size": (72, 72)},  # Big slow monster
    ]
    monster_type = random.choice(monster_types)
    return {
        "rect": pygame.Rect(WIDTH + distance, GROUND_Y - monster_type["size"][1], *monster_type["size"]),
        "vx": monster_type["vx"],
        "type": "monster"
    }

def spawn_powerup(distance, powerup_type):
    """Spawn a powerup at the given distance from the right edge"""
    if powerup_type == "heart":
        return pygame.Rect(WIDTH + distance, GROUND_Y-60, 28, 28)
    elif powerup_type == "shield":
        return pygame.Rect(WIDTH + distance, GROUND_Y-50, 24, 24)

def create_particle(
    x,
    y,
    color,
    velocity=(0, 0),
    life=30,
    size_range=(2, 6),
    gravity=0.2,
    fade=True,
    shrink=True,
    friction=0.96,
    kind="spark",
    color_end=None,
):
    """Create a particle effect with configurable behaviour."""
    size_min, size_max = size_range if isinstance(size_range, (tuple, list)) else (size_range, size_range)
    size = random.randint(int(size_min), int(size_max))
    vx, vy = velocity
    return {
        "x": x,
        "y": y,
        "vx": vx + random.uniform(-1.5, 1.5),
        "vy": vy + random.uniform(-1.2, 1.2),
        "color": color,
        "color_end": color_end,
        "life": life,
        "max_life": life,
        "size": size,
        "gravity": gravity,
        "fade": fade,
        "shrink": shrink,
        "friction": friction,
        "kind": kind,
    }

def update_particles():
    """Update all particle effects"""
    global particles
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vx"] *= particle.get("friction", 1.0)
        particle["vy"] += particle.get("gravity", 0)

        if particle["kind"] == "spore":
            particle["vx"] += math.sin(particle["life"] * 0.08) * 0.05
            particle["vy"] += math.cos(particle["life"] * 0.05) * 0.02
        elif particle["kind"] == "ember":
            particle["vx"] += random.uniform(-0.05, 0.05)
            particle["vy"] -= 0.02
        elif particle["kind"] == "dust":
            particle["vx"] *= 0.94

        particle["life"] -= 1
        if particle["life"] <= 0:
            particles.remove(particle)

def draw_particles(screen):
    """Draw all particle effects"""
    for particle in particles:
        life_ratio = particle["life"] / particle["max_life"] if particle["max_life"] else 0
        base_color = particle["color"]
        if particle.get("color_end"):
            end_color = particle["color_end"]
            blend = 1 - life_ratio
            color = tuple(
                int(base_color[i] + (end_color[i] - base_color[i]) * blend) for i in range(3)
            )
        else:
            color = base_color

        alpha = int(255 * life_ratio) if particle.get("fade", True) else 255
        size = particle["size"]
        if particle.get("shrink", True):
            size = max(1, int(size * life_ratio))

        if size <= 0 or alpha <= 0:
            continue

        if particle["kind"] in ("dust", "dash"):
            surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            rect = surf.get_rect()
            pygame.draw.ellipse(
                surf,
                (*color, alpha),
                (rect.width // 6, rect.height // 4, rect.width * 2 // 3, rect.height // 2),
            )
            screen.blit(surf, (particle["x"] - rect.width // 2, particle["y"] - rect.height // 2))
        else:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (size, size), size)
            if particle["kind"] == "spore":
                glow = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*color, max(10, alpha // 4)), (glow.get_width() // 2, glow.get_height() // 2), glow.get_width() // 2)
                screen.blit(glow, (particle["x"] - glow.get_width() // 2, particle["y"] - glow.get_height() // 2))
            screen.blit(surf, (particle["x"] - size, particle["y"] - size))

# Initialize Level 1
mushrooms.append(spawn_mushroom())

# Variable spawn delay helper to produce micro/normal/long gaps
def next_spawn_delay_level1():
    r = random.random()
    if r < 0.40:  # micro gaps: bursts
        return random.randint(8, 18)
    elif r < 0.85:  # normal gaps
        return random.randint(20, 45)
    else:  # long gaps: breathing room
        return random.randint(60, 100)

# Randomized monster gap helper for Level 2
def next_monster_gap():
    # Choose varied distances; scale slightly with speed to keep reaction time fair
    r = random.random()
    if r < 0.40:          # micro gaps for brief pressure
        base = random.randint(300, 500)
    elif r < 0.85:        # normal gaps most of the time
        base = random.randint(700, 1100)
    else:                 # long gaps for breathing room
        base = random.randint(1200, 1800)
    return base

# Varied, longer gaps for powerups to reduce frequency significantly
def next_powerup_gap():
    r = random.random()
    if r < 0.20:          # rare micro gap
        return random.randint(3500, 4500)
    elif r < 0.85:        # normal long gaps most of the time
        return random.randint(6000, 8500)
    else:                 # very long gaps occasionally
        return random.randint(10000, 15000)

# Add helper to start Level 1 consistently from keyboard or mouse
def start_level1():
    global score, lives, mushrooms, next_mushroom_spawn_timer, basket, state, particles, paused
    global distance_score_carry, ambient_spore_timer, trail_emit_timer, collect_flash_timer, hit_flash_timer
    score = 0
    lives = LIVES_START
    mushrooms = []
    next_mushroom_spawn_timer = 0
    basket = basket_img.get_rect(midbottom=(WIDTH//2, HEIGHT-10))
    mushrooms.append(spawn_mushroom())
    particles = []
    distance_score_carry = 0.0
    ambient_spore_timer = 0
    trail_emit_timer = 0
    collect_flash_timer = 0
    hit_flash_timer = 0
    paused = False
    state = LEVEL1

# Main Game Loop
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_p:
                paused = not paused
            # Toggle fullscreen on F11
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
            if state == MENU and event.key == pygame.K_RETURN:
                # Start Level 1
                start_level1()
            elif state in (GAMEOVER, WIN) and event.key == pygame.K_RETURN:
                # Return to menu
                state = MENU
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            GROUND_Y = HEIGHT - 140
            flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
            screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
            # Re-anchor UI elements
            basket.midbottom = (max(0, min(WIDTH, basket.midbottom[0])), HEIGHT - 10)
            player.bottom = GROUND_Y
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Enable mouse click on Start button in the menu
            if state == MENU and event.button == 1:
                _, start_rect = get_menu_layout(WIDTH, HEIGHT)
                if start_rect.collidepoint(event.pos):
                    start_level1()

    if paused and state not in (GAMEOVER, WIN):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (12, 18, 30, 210), (6, 10, 20, 230))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(WIDTH//2 - 240, HEIGHT//2 - 140, 480, 220)
        draw_glass_panel(screen, panel_rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=28)
        draw_text_shadow(screen, "Paused", 72, panel_rect.centerx, panel_rect.y + 90, (255, 255, 255))
        draw_text_shadow(screen, "Press P to resume", 26, panel_rect.centerx, panel_rect.y + 150, (220, 230, 255))
        draw_text_shadow(screen, "Press ESC to quit", 20, panel_rect.centerx, panel_rect.y + 190, (200, 210, 230))
        pygame.display.flip()
        continue

    keys = pygame.key.get_pressed()

    if state == MENU:
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
        else:
            draw_vertical_gradient(screen, UI_COLORS["bg_top"], UI_COLORS["bg_bottom"])
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (10, 14, 24, 180), (4, 6, 16, 220))
        screen.blit(overlay, (0, 0))

        hero_rect, start_rect = get_menu_layout(WIDTH, HEIGHT)
        draw_glass_panel(screen, hero_rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=28)
        draw_text_shadow(screen, "Shroom Hunter", 76, hero_rect.centerx, hero_rect.y + 92, (255, 255, 255))
        draw_text_shadow(
            screen,
            "Chase the spores. Outrun the dusk.",
            28,
            hero_rect.centerx,
            hero_rect.y + 150,
            (215, 230, 255),
        )

        hovered = start_rect.collidepoint(pygame.mouse.get_pos())
        draw_button(screen, start_rect, "Start Adventure", hovered)

        score_w = min(hero_rect.width, 480)
        score_rect = pygame.Rect(WIDTH//2 - score_w//2, hero_rect.bottom + 24, score_w, 74)
        draw_glass_panel(screen, score_rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["accent"], radius=24)
        high_label = get_font(16).render("HIGH SCORE", True, (200, 220, 255))
        high_value = get_font(32).render(f"{highscore}", True, (255, 255, 255))
        screen.blit(high_label, (score_rect.x + 24, score_rect.y + 18))
        screen.blit(high_value, (score_rect.x + 24, score_rect.y + 38))
        pygame.draw.line(
            screen,
            (170, 200, 255),
            (score_rect.x + 24, score_rect.y + 32),
            (score_rect.right - 24, score_rect.y + 32),
            1,
        )

        info_bottom = score_rect.bottom
        info_space = HEIGHT - info_bottom - 160
        if info_space > 0:
            info_h = 116
            info_rect = pygame.Rect(WIDTH//2 - hero_rect.width//2, score_rect.bottom + 16, hero_rect.width, info_h)
            draw_glass_panel(
                screen,
                info_rect,
                base_color=UI_COLORS["panel_alt"],
                border_color=UI_COLORS["accent_alt"],
                radius=26,
            )
            bullet_font = get_font(18)
            info_lines = [
                f"Level 1 • Catch {LEVEL1_GOAL} glowing mushrooms",
                "Level 2 • Dash through the endless grove",
            ]
            for i, line in enumerate(info_lines):
                text = bullet_font.render(line, True, (245, 230, 255))
                line_y = info_rect.y + 26 + i * 36
                screen.blit(text, (info_rect.x + 46, line_y))
                pygame.draw.circle(screen, UI_COLORS["accent_alt"], (info_rect.x + 24, line_y + 6), 6)

        pill_w = int(min(WIDTH - 120, 860))
        pill_y = HEIGHT - 78
        draw_controls_pill(
            screen,
            "[ENTER] Start   [F11] Fullscreen   [ESC] Quit",
            WIDTH//2 - pill_w//2,
            pill_y,
            pill_w,
        )
        ambient_spore_timer -= 1
        if ambient_spore_timer <= 0:
            spawn_x = random.uniform(60, WIDTH - 60)
            spawn_y = random.uniform(HEIGHT * 0.2, HEIGHT * 0.75)
            particles.append(
                create_particle(
                    spawn_x,
                    spawn_y,
                    (190, 220, 255),
                    velocity=(random.uniform(-0.25, 0.25), random.uniform(-0.1, 0.1)),
                    life=random.randint(110, 160),
                    size_range=(3, 6),
                    gravity=-0.004,
                    fade=True,
                    shrink=False,
                    friction=0.99,
                    kind="spore",
                    color_end=(140, 180, 255),
                )
            )
            ambient_spore_timer = random.randint(10, 24)
        update_particles()
        draw_particles(screen)

    elif state == LEVEL1:
        ambient_spore_timer -= 1
        if ambient_spore_timer <= 0:
            spawn_x = random.uniform(40, WIDTH - 40)
            spawn_y = random.uniform(HEIGHT * 0.12, HEIGHT * 0.55)
            particles.append(
                create_particle(
                    spawn_x,
                    spawn_y,
                    (200, 240, 255),
                    velocity=(random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.2)),
                    life=random.randint(90, 140),
                    size_range=(3, 6),
                    gravity=-0.006,
                    fade=True,
                    shrink=False,
                    friction=0.985,
                    kind="spore",
                    color_end=(160, 200, 255),
                )
            )
            ambient_spore_timer = random.randint(6, 16)

        # Update basket movement
        if keys[pygame.K_LEFT]:
            basket.x -= 10
        if keys[pygame.K_RIGHT]:
            basket.x += 10
        basket.x = max(0, min(WIDTH - basket.width, basket.x))

        # Spawn mushrooms with cap and random delay
        if len(mushrooms) < LEVEL1_MAX_CONCURRENT:
            if next_mushroom_spawn_timer <= 0:
                mushrooms.append(spawn_mushroom())
                next_mushroom_spawn_timer = next_spawn_delay_level1()
            else:
                next_mushroom_spawn_timer -= 1

        # Update mushrooms fall and collisions
        for m in mushrooms[:]:
            fall_speed = MUSHROOM_FALL_SPEED + min(score * 0.12, 10)
            m["rect"].y += fall_speed
            # Reduced hitboxes for fairer collisions
            m_hit = m["rect"].inflate(-int(m["rect"].width * 0.4), -int(m["rect"].height * 0.4))
            basket_hit = basket.inflate(-int(basket.width * 0.3), -int(basket.height * 0.3))
            if m_hit.colliderect(basket_hit):
                score += 1
                if collect_snd: collect_snd.play()
                collect_flash_timer = COLLECT_FLASH_DURATION
                burst_center = (m["rect"].centerx, m["rect"].centery)
                for _ in range(18):
                    particles.append(
                        create_particle(
                            burst_center[0],
                            burst_center[1],
                            (255, 220, 120),
                            velocity=(random.uniform(-1.5, 1.5), random.uniform(-3.5, 0.5)),
                            life=random.randint(28, 40),
                            size_range=(3, 6),
                            gravity=0.18,
                            kind="spark",
                            color_end=(255, 160, 40),
                        )
                    )
                for angle in range(0, 360, 45):
                    radians = math.radians(angle)
                    particles.append(
                        create_particle(
                            burst_center[0] + math.cos(radians) * 30,
                            burst_center[1] + math.sin(radians) * 30,
                            (255, 240, 180),
                            velocity=(math.cos(radians) * 1.5, math.sin(radians) * 1.5),
                            life=36,
                            size_range=(2, 4),
                            gravity=-0.05,
                            fade=True,
                            shrink=False,
                            friction=0.92,
                            kind="spore",
                            color_end=(180, 220, 255),
                        )
                    )
                mushrooms.remove(m)
            elif m["rect"].top > HEIGHT:
                lives -= 1
                if miss_snd: miss_snd.play()
                hit_flash_timer = HIT_FLASH_DURATION
                miss_x = basket.centerx + random.uniform(-80, 80)
                for _ in range(12):
                    particles.append(
                        create_particle(
                            miss_x,
                            GROUND_Y,
                            (255, 120, 120),
                            velocity=(random.uniform(-1.2, 1.2), random.uniform(-2.5, -0.5)),
                            life=30,
                            size_range=(3, 5),
                            gravity=0.25,
                            kind="dust",
                            color_end=(200, 60, 60),
                        )
                    )
                mushrooms.remove(m)

        # Game Over check for Level 1
        if lives <= 0:
            state = GAMEOVER
            if score > highscore:
                save_highscore(score)
                highscore = score
            gameover_timer = FPS * 3

        # Transition to Level 2 when goal reached
        if score >= LEVEL1_GOAL:
            coins, monsters, spikes, hearts, shields = spawn_level2()
            runner_distance = 0
            runner_speed = RUNNER_SPEED
            bg_scroll_x = 0
            player = mushroom_player_img.get_rect(center=(WIDTH//2, HEIGHT//2))
            player_vx, player_vy = 0, 0
            on_ground = False
            dash_cd = 0
            shield_timer = 0
            particles = []
            distance_score_carry = 0.0
            ambient_spore_timer = 0
            trail_emit_timer = 0
            collect_flash_timer = 0
            hit_flash_timer = 0
            state = LEVEL2

        # Draw Level 1
        if level1_bg:
            screen.blit(level1_bg, (0, 0))
        else:
            draw_vertical_gradient(screen, (42, 64, 108), (16, 24, 48))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (8, 16, 32, 120), (2, 4, 12, 180))
        screen.blit(overlay, (0, 0))
        for m in mushrooms:
            screen.blit(m["img"], m["rect"]) if m["img"] else pygame.draw.rect(screen, (220, 180, 100), m["rect"])
        screen.blit(basket_img, basket)
        update_particles()
        draw_particles(screen)

        # HUD
        draw_score_pill(screen, score, 30, 28)
        pill_margin = 24
        goal_w = max(320, min(420, int(WIDTH * 0.24)))
        goal_h = 116
        goal_x = WIDTH - goal_w - pill_margin
        goal_y = pill_margin
        draw_goal_progress_pill(screen, goal_x, goal_y, goal_w, goal_h, score, LEVEL1_GOAL)
        draw_lives_panel(screen, lives, heart_icon_small, 30, 120)
        pill_w = int(min(WIDTH - 120, 780))
        pill_y = HEIGHT - 78
        draw_controls_pill(
            screen,
            "[LEFT/RIGHT] Move   [ESC] Quit   Catch every glow!",
            WIDTH//2 - pill_w//2,
            pill_y,
            pill_w,
        )

    elif state == LEVEL2:
        ambient_spore_timer -= 1
        if ambient_spore_timer <= 0:
            spawn_x = random.uniform(0, WIDTH)
            spawn_y = random.uniform(HEIGHT * 0.05, HEIGHT * 0.45)
            particles.append(
                create_particle(
                    spawn_x,
                    spawn_y,
                    (150, 210, 255),
                    velocity=(random.uniform(-0.6, 0.6) - runner_speed * 0.03, random.uniform(-0.15, 0.15)),
                    life=random.randint(110, 160),
                    size_range=(3, 6),
                    gravity=-0.004,
                    fade=True,
                    shrink=False,
                    friction=0.988,
                    kind="spore",
                    color_end=(120, 180, 255),
                )
            )
            ambient_spore_timer = random.randint(5, 12)

        # Scrolling background
        bg_scroll_x -= runner_speed
        runner_speed = min(MAX_RUNNER_SPEED, runner_speed + RUNNER_ACCELERATION)
        runner_distance += runner_speed
        distance_score_carry += runner_speed
        while distance_score_carry >= DISTANCE_SCORE_UNIT:
            score += 1
            distance_score_carry -= DISTANCE_SCORE_UNIT

        # Player jump
        was_on_ground = on_ground
        if keys[pygame.K_SPACE] and on_ground:
            player_vy = PLAYER_JUMP_SPEED
            on_ground = False
            if jump_snd: jump_snd.play()
        # Super jump / dash on Shift with cooldown
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and dash_cd == 0:
            player_vy = PLAYER_JUMP_SPEED * 1.5
            dash_cd = DASH_COOLDOWN_FRAMES
            if dash_snd: dash_snd.play()
            for _ in range(24):
                particles.append(
                    create_particle(
                        player.centerx,
                        player.centery + 10,
                        (140, 220, 255),
                        velocity=(random.uniform(-3, 3), random.uniform(-4, -1)),
                        life=random.randint(24, 36),
                        size_range=(3, 6),
                        gravity=0.22,
                        fade=True,
                        shrink=False,
                        friction=0.9,
                        kind="dash",
                        color_end=(30, 140, 255),
                    )
                )

        # Gravity & ground collision
        player_vy += GRAVITY
        player.y += int(player_vy)
        if player.bottom >= GROUND_Y:
            player.bottom = GROUND_Y
            player_vy = 0
            on_ground = True
        else:
            on_ground = False

        if not was_on_ground and on_ground:
            for offset in (-18, 18):
                particles.append(
                    create_particle(
                        player.centerx + offset,
                        GROUND_Y,
                        (220, 210, 180),
                        velocity=(offset * 0.08 - runner_speed * 0.35, random.uniform(-3.2, -1.2)),
                        life=34,
                        size_range=(4, 7),
                        gravity=0.36,
                        fade=True,
                        shrink=True,
                        friction=0.92,
                        kind="dust",
                        color_end=(150, 120, 90),
                    )
                )

        if on_ground:
            trail_emit_timer = max(0, trail_emit_timer - 1)
            if trail_emit_timer <= 0 and runner_speed > RUNNER_SPEED + 0.5:
                particles.append(
                    create_particle(
                        player.centerx - player.width // 3,
                        GROUND_Y - 4,
                        (210, 200, 160),
                        velocity=(-runner_speed * 0.45 - 0.5, random.uniform(-2.0, -0.8)),
                        life=26,
                        size_range=(3, 5),
                        gravity=0.3,
                        fade=True,
                        shrink=True,
                        friction=0.9,
                        kind="dust",
                        color_end=(140, 120, 90),
                    )
                )
                trail_emit_timer = max(4, int(14 - runner_speed))
        else:
            trail_emit_timer = 0

        # Dash cooldown tick
        if dash_cd > 0:
            dash_cd -= 1

        if shield_timer > 0 and random.random() < 0.3:
            angle = random.uniform(0, math.tau)
            radius = random.uniform(20, 34)
            px = player.centerx + math.cos(angle) * radius
            py = player.centery + math.sin(angle) * radius
            particles.append(
                create_particle(
                    px,
                    py,
                    (130, 200, 255),
                    velocity=(math.cos(angle) * 0.6, math.sin(angle) * 0.6),
                    life=28,
                    size_range=(2, 4),
                    gravity=0,
                    fade=True,
                    shrink=False,
                    friction=0.92,
                    kind="spore",
                    color_end=(60, 160, 255),
                )
            )

        # Spawn monsters
        next_monster_spawn -= runner_speed
        if next_monster_spawn <= 0 and len(monsters) < MONSTER_MAX_CONCURRENT:
            monsters.append(spawn_monster(0))
            next_monster_spawn = next_monster_gap()

        # Update monsters
        for monster in monsters[:]:
            monster["rect"].x += monster["vx"]
            if monster["rect"].right < 0:
                monsters.remove(monster)
            elif monster["rect"].colliderect(player):
                if shield_timer > 0:
                    # Shield absorbs the hit but loses part of its duration
                    shield_timer = max(0, shield_timer - SHIELD_HIT_COST_FRAMES)
                    for _ in range(10):
                        particles.append(
                            create_particle(
                                player.centerx,
                                player.centery,
                                (160, 220, 255),
                                velocity=(random.uniform(-2.0, 2.0), random.uniform(-2.5, 0.5)),
                                life=26,
                                size_range=(2, 4),
                                gravity=0.1,
                                fade=True,
                                shrink=False,
                                friction=0.9,
                                kind="spore",
                                color_end=(80, 160, 255),
                            )
                        )
                    monsters.remove(monster)
                else:
                    lives -= 1
                    if hit_snd: hit_snd.play()
                    hit_flash_timer = HIT_FLASH_DURATION
                    for _ in range(16):
                        particles.append(
                            create_particle(
                                player.centerx,
                                player.centery,
                                (255, 120, 120),
                                velocity=(random.uniform(-2.5, 2.5), random.uniform(-3.5, 1.0)),
                                life=32,
                                size_range=(3, 5),
                                gravity=0.25,
                                fade=True,
                                shrink=True,
                                friction=0.9,
                                kind="spark",
                                color_end=(255, 60, 60),
                            )
                        )
                    monsters.remove(monster)

        # Spawn powerups
        next_powerup_spawn -= runner_speed
        if next_powerup_spawn <= 0:
            r = random.random()
            if lives < LIVES_START and r < 0.70:
                hearts.append(spawn_powerup(0, "heart"))
            elif r < 0.85:
                shields.append(spawn_powerup(0, "shield"))
            # else: skip spawning to keep powerups rare
            next_powerup_spawn = next_powerup_gap()

        # Move powerups with scroll & collect
        for heart in hearts[:]:
            heart.x -= int(runner_speed)
            if heart.right < 0:
                hearts.remove(heart)
            elif heart.colliderect(player):
                lives = min(lives + 1, LIVES_START)
                if collect_snd: collect_snd.play()
                collect_flash_timer = COLLECT_FLASH_DURATION
                for _ in range(14):
                    particles.append(
                        create_particle(
                            heart.centerx,
                            heart.centery,
                            (255, 150, 180),
                            velocity=(random.uniform(-2.0, 2.0), random.uniform(-2.5, 0.5)),
                            life=30,
                            size_range=(3, 6),
                            gravity=0.15,
                            fade=True,
                            shrink=False,
                            friction=0.9,
                            kind="spark",
                            color_end=(255, 200, 200),
                        )
                    )
                hearts.remove(heart)
        for shield in shields[:]:
            shield.x -= int(runner_speed)
            if shield.right < 0:
                shields.remove(shield)
            elif shield.colliderect(player):
                shield_timer = SHIELD_DURATION_FRAMES
                collect_flash_timer = COLLECT_FLASH_DURATION
                for _ in range(16):
                    particles.append(
                        create_particle(
                            shield.centerx,
                            shield.centery,
                            (120, 200, 255),
                            velocity=(random.uniform(-1.5, 1.5), random.uniform(-2.0, 1.0)),
                            life=32,
                            size_range=(3, 5),
                            gravity=0.1,
                            fade=True,
                            shrink=False,
                            friction=0.92,
                            kind="spore",
                            color_end=(60, 150, 255),
                        )
                    )
                shields.remove(shield)

        if shield_timer > 0:
            shield_timer -= 1

        update_particles()

        # Game Over
        if lives <= 0:
            state = GAMEOVER
            if miss_snd: miss_snd.play()
            if score > highscore:
                save_highscore(score)
                highscore = score

        # Draw Level 2 scene
        if level2_bg:
            bg_offset = int(bg_scroll_x % WIDTH)
            screen.blit(level2_bg, (bg_offset - WIDTH, 0))
            screen.blit(level2_bg, (bg_offset, 0))
        else:
            draw_vertical_gradient(screen, (24, 44, 78), (8, 12, 28))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (22, 40, 70, 120), (6, 10, 24, 200))
        screen.blit(overlay, (0, 0))

        glow_band = get_runner_glow_band(WIDTH, 220)
        band_y = max(0, int(GROUND_Y * 0.55))
        screen.blit(glow_band, (0, band_y))

        draw_runner_floor(screen, WIDTH, GROUND_Y, bg_scroll_x)

        # Player
        screen.blit(mushroom_player_img, player)
        if shield_timer > 0:
            pulse = 1 + 0.3 * abs(pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * 0.5).x)
            radius = int(40 * pulse)
            pygame.draw.circle(screen, (120, 180, 255), player.center, radius, 3)
            pygame.draw.circle(screen, (200, 220, 255), player.center, radius - 10, 1)

        # Powerups
        for heart in hearts:
            glow_surf = pygame.Surface((56, 56), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 100, 150, 30), (28, 28), 28)
            screen.blit(glow_surf, (heart.x - 14, heart.y - 14))
            screen.blit(heart_img, heart) if heart_img else pygame.draw.circle(screen, (255, 100, 150), heart.center, 14)
        for shield in shields:
            glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (90, 160, 255, 40), (24, 24), 24)
            screen.blit(glow_surf, (shield.x - 12, shield.y - 12))
            pygame.draw.circle(screen, (90, 160, 255), shield.center, 12)

        # Monsters
        for monster in monsters:
            shadow_rect = monster["rect"].copy()
            shadow_rect.y = GROUND_Y - 10
            pygame.draw.ellipse(screen, (0, 0, 0, 100), shadow_rect)
            screen.blit(monster_img, monster["rect"]) if monster_img else pygame.draw.rect(screen, (200, 50, 50), monster["rect"])

        draw_particles(screen)

        # HUD panels
        status_w, status_h = 380, 190
        status_x, status_y = WIDTH - status_w - 30, 24
        draw_status_panel(
            screen,
            status_x,
            status_y,
            lives,
            LIVES_START,
            shield_timer,
            SHIELD_DURATION_FRAMES,
            dash_cd,
            DASH_COOLDOWN_FRAMES,
            heart_icon_status,
        )
        draw_metrics_strip(screen, runner_distance, score, runner_speed, x=30, y=24)
        pill_w = int(min(WIDTH - 120, 820))
        draw_controls_pill(
            screen,
            "[SPACE] Jump   [SHIFT] Air Dash   [P] Pause   [ESC] Quit",
            WIDTH//2 - pill_w//2,
            HEIGHT - 78,
            pill_w,
        )

    elif state == GAMEOVER:
        # Auto-return to menu after short delay
        if gameover_timer > 0:
            gameover_timer -= 1
            if gameover_timer <= 0:
                state = MENU
        draw_vertical_gradient(screen, (60, 20, 30), (20, 6, 12))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (0, 0, 0, 90), (0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(WIDTH//2 - 320, HEIGHT//2 - 170, 640, 260)
        draw_glass_panel(screen, panel_rect, base_color=UI_COLORS["panel_alt"], border_color=UI_COLORS["danger"], radius=30)
        draw_text_shadow(screen, "Game Over", 78, panel_rect.centerx, panel_rect.y + 100, (255, 225, 235))
        draw_text_shadow(screen, f"Score {score}", 34, panel_rect.centerx, panel_rect.y + 152, (255, 240, 245))
        draw_text_shadow(screen, f"High Score {highscore}", 26, panel_rect.centerx, panel_rect.y + 196, (255, 220, 230))

        pill_w = int(min(WIDTH - 160, 520))
        pill_y = panel_rect.bottom + 24
        if pill_y + 60 < HEIGHT:
            draw_controls_pill(screen, "[ENTER] Back to menu   [ESC] Quit", WIDTH//2 - pill_w//2, pill_y, pill_w)
        else:
            draw_text_shadow(screen, "[ENTER] Back to menu   [ESC] Quit", 24, WIDTH//2, panel_rect.bottom + 80, (240, 240, 240))

    elif state == WIN:
        draw_vertical_gradient(screen, (32, 72, 58), (12, 28, 20))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(overlay, (0, 0, 0, 60), (0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(WIDTH//2 - 320, HEIGHT//2 - 170, 640, 260)
        draw_glass_panel(screen, panel_rect, base_color=UI_COLORS["panel"], border_color=UI_COLORS["success"], radius=30)
        draw_text_shadow(screen, "Victory!", 78, panel_rect.centerx, panel_rect.y + 100, (240, 255, 245))
        draw_text_shadow(screen, f"Score {score}", 34, panel_rect.centerx, panel_rect.y + 152, (255, 255, 240))
        draw_text_shadow(screen, f"High Score {highscore}", 26, panel_rect.centerx, panel_rect.y + 196, (220, 255, 235))

        pill_w = int(min(WIDTH - 160, 520))
        pill_y = panel_rect.bottom + 24
        if pill_y + 60 < HEIGHT:
            draw_controls_pill(screen, "[ENTER] Back to menu   [ESC] Quit", WIDTH//2 - pill_w//2, pill_y, pill_w)
        else:
            draw_text_shadow(screen, "[ENTER] Back to menu   [ESC] Quit", 24, WIDTH//2, panel_rect.bottom + 80, (240, 255, 240))

    if collect_flash_timer > 0:
        ratio = collect_flash_timer / COLLECT_FLASH_DURATION if COLLECT_FLASH_DURATION else 0
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 220, 120, int(90 * ratio)))
        screen.blit(overlay, (0, 0))
        collect_flash_timer = max(0, collect_flash_timer - 1)

    if hit_flash_timer > 0:
        ratio = hit_flash_timer / HIT_FLASH_DURATION if HIT_FLASH_DURATION else 0
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 60, 60, int(140 * ratio)))
        screen.blit(overlay, (0, 0))
        hit_flash_timer = max(0, hit_flash_timer - 1)

    pygame.display.flip()

pygame.quit()
sys.exit()
