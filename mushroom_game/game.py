import pygame, sys, random, os

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

def draw_text(surf, text, size, x, y, color=(255,255,255)):
    font = pygame.font.SysFont("arial", size, bold=True)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(x, y))
    surf.blit(txt, rect)
    return rect

def draw_health_bar(surf, x, y, w, h, value, max_value, color=(255,60,60)):
    # Background
    pygame.draw.rect(surf, (60,60,60), (x, y, w, h))
    # Fill
    fill_w = int((value / max_value) * w) if max_value > 0 else 0
    pygame.draw.rect(surf, color, (x, y, fill_w, h))
    # Border
    pygame.draw.rect(surf, (200,200,200), (x, y, w, h), 2)

def draw_shield_bar(surf, x, y, w, h, value, max_value):
    # Background
    pygame.draw.rect(surf, (60,60,60), (x, y, w, h))
    # Fill
    fill_w = int((value / max_value) * w) if max_value > 0 else 0
    pygame.draw.rect(surf, (60,120,255), (x, y, fill_w, h))
    # Border
    pygame.draw.rect(surf, (200,200,200), (x, y, w, h), 2)

# Dash cooldown bar helper
# Shows remaining cooldown as a draining bar; when ready, turns green.
def draw_dash_bar(surf, x, y, w, h, value, max_value):
    # Background
    pygame.draw.rect(surf, (60,60,60), (x, y, w, h))
    # Fill is proportional to remaining cooldown
    if max_value > 0:
        fill_ratio = max(0.0, min(1.0, value / max_value))
    else:
        fill_ratio = 0.0
    fill_w = int(fill_ratio * w)
    color = (0, 200, 200) if value > 0 else (80, 220, 120)
    pygame.draw.rect(surf, color, (x, y, fill_w, h))
    # Border
    pygame.draw.rect(surf, (200,200,200), (x, y, w, h), 2)
    # Optional READY hint when off cooldown
    if value <= 0:
        font = pygame.font.SysFont("arial", 16, bold=True)
        txt = font.render("READY", True, (240,255,240))
        surf.blit(txt, txt.get_rect(center=(x + w//2, y + h//2)))

# Modern UI helpers for Level 2 HUD
def draw_status_panel(surf, x, y, lives, lives_max, shield_timer, shield_max, dash_cd, dash_max, heart_img):
    w, h = 360, 160
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (20, 20, 30, 180), (0, 0, w, h), border_radius=12)
    pygame.draw.rect(panel, (100, 100, 140, 200), (0, 0, w, h), width=2, border_radius=12)

    # Spacing and sizes
    icon_size = 20
    font_size = 16
    left_margin = 16
    label_center_x = 180

    # Health row
    if heart_img:
        try:
            heart_small = pygame.transform.smoothscale(heart_img, (icon_size, icon_size))
        except Exception:
            heart_small = None
        if heart_small:
            panel.blit(heart_small, (left_margin, 10))
    draw_text_shadow(panel, f"Health {lives}/{lives_max}", font_size, label_center_x, 20, (255,255,255))
    draw_health_bar(panel, left_margin, 36, w - 2*left_margin, 12, lives, lives_max)

    # Shield row (simple icon)
    pygame.draw.circle(panel, (90,160,255), (left_margin + 11, 70), 10, 2)
    shield_seconds = max(0, shield_timer // FPS)
    draw_text_shadow(panel, f"Shield {shield_seconds}s", font_size, label_center_x, 70, (220,240,255))
    draw_shield_bar(panel, left_margin, 86, w - 2*left_margin, 12, shield_timer, shield_max)

    # Dash row (simple lightning icon)
    bolt_points = [(left_margin + 8, 112), (left_margin + 18, 96), (left_margin + 12, 96), (left_margin + 22, 82), (left_margin + 16, 100), (left_margin + 22, 100)]
    pygame.draw.polygon(panel, (255, 230, 120), bolt_points)
    dash_label = "Dash READY" if dash_cd <= 0 else f"Dash {max(0, dash_cd // FPS)}s"
    draw_text_shadow(panel, dash_label, font_size, label_center_x, 112, (255,230,180))
    draw_dash_bar(panel, left_margin, 128, w - 2*left_margin, 12, dash_cd, dash_max)

    surf.blit(panel, (x, y))


def draw_metrics_strip(surf, distance, score, speed, x=30, y=24):
    w, h = 480, 36
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, w, h), border_radius=18)
    surf.blit(shadow, (x + 2, y + 3))
    pill = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(pill, (24, 28, 48, 200), (0, 0, w, h), border_radius=18)
    pygame.draw.rect(pill, (110, 130, 200, 220), (0, 0, w, h), width=2, border_radius=18)
    # Removed left accent stripe for a cleaner look
    font = pygame.font.SysFont("arial", 20, bold=True)
    text = f"Distance {int(distance)}    Score {score}    Speed {speed:.1f}"
    txt = font.render(text, True, (240, 245, 255))
    pill.blit(txt, (18, h // 2 - txt.get_height() // 2))
    surf.blit(pill, (x, y))


def draw_controls_pill(surf, text, x, y, w):
    h = 42
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 70), (0, 0, w, h), border_radius=21)
    surf.blit(shadow, (x + 2, y + 3))
    pill = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(pill, (22, 22, 32, 180), (0, 0, w, h), border_radius=21)
    pygame.draw.rect(pill, (120, 120, 160, 220), (0, 0, w, h), width=2, border_radius=21)
    # Removed top accent stripe
    font = pygame.font.SysFont("arial", 20, bold=True)
    txt = font.render(text, True, (220, 225, 235))
    pill.blit(txt, (w // 2 - txt.get_width() // 2, h // 2 - txt.get_height() // 2))
    surf.blit(pill, (x, y))

def draw_score_pill(surf, score, x=30, y=24):
    w, h = 220, 36
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, w, h), border_radius=18)
    surf.blit(shadow, (x + 2, y + 3))
    pill = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(pill, (24, 28, 48, 200), (0, 0, w, h), border_radius=18)
    pygame.draw.rect(pill, (110, 130, 200, 220), (0, 0, w, h), width=2, border_radius=18)
    # Removed left accent stripe for a cleaner look
    font = pygame.font.SysFont("arial", 20, bold=True)
    txt = font.render(f"Score {score}", True, (240, 245, 255))
    pill.blit(txt, (18, h // 2 - txt.get_height() // 2))
    surf.blit(pill, (x, y))


def draw_goal_progress_pill(surf, x, y, w, h, collected, goal):
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, w, h), border_radius=20)
    surf.blit(shadow, (x + 2, y + 3))
    pill = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(pill, (22, 26, 40, 200), (0, 0, w, h), border_radius=20)
    pygame.draw.rect(pill, (120, 120, 160, 220), (0, 0, w, h), width=2, border_radius=20)
    
    # Text layout with proper vertical spacing
    font = pygame.font.SysFont("arial", 16, bold=True)
    label = f"Catch {goal} mushrooms to reach Level 2"
    txt = font.render(label, True, (240, 250, 240))
    pill.blit(txt, (12, 10))  # Top text with margin
    
    # Progress value text positioned on the right side at same height
    val_txt = font.render(f"{collected}/{goal}", True, (220, 255, 220))
    pill.blit(val_txt, (w - val_txt.get_width() - 12, 10))  # Right-aligned with margin
    
    # Progress bar positioned in the middle with adequate spacing from text
    bar_margin = 12
    bar_y = h // 2 + 8  # Positioned in lower half with spacing
    bar_w = w - 2 * bar_margin
    bar_h = 10  # Slightly thicker bar
    ratio = 0 if goal <= 0 else max(0.0, min(1.0, collected / goal))
    
    # Background bar
    pygame.draw.rect(pill, (60, 60, 70), (bar_margin, bar_y, bar_w, bar_h), border_radius=5)
    # Progress fill
    fill_w = int(bar_w * ratio)
    if fill_w > 0:
        pygame.draw.rect(pill, (80, 220, 120), (bar_margin, bar_y, fill_w, bar_h), border_radius=5)
    
    surf.blit(pill, (x, y))


def draw_lives_panel(surf, lives, heart_img, x, y):
    w, h = 280, 64
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, w, h), border_radius=16)
    surf.blit(shadow, (x + 2, y + 3))
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (30, 18, 24, 200), (0, 0, w, h), border_radius=16)
    pygame.draw.rect(panel, (200, 100, 140, 220), (0, 0, w, h), width=2, border_radius=16)
    # Removed left accent stripe
    font = pygame.font.SysFont("arial", 18, bold=True)
    txt = font.render(f"Lives", True, (255, 235, 240))
    panel.blit(txt, (14, 10))
    count_txt = font.render(f"x{lives}", True, (255, 200, 220))
    panel.blit(count_txt, (w - count_txt.get_width() - 12, 10))
    # icons row
    icon_size = 22
    max_icons = min(lives, 8)
    if heart_img:
        try:
            heart_small = pygame.transform.smoothscale(heart_img, (icon_size, icon_size))
        except Exception:
            heart_small = None
        if heart_small:
            for i in range(max_icons):
                ix = 14 + i * (icon_size + 6)
                iy = 32
                glow = pygame.Surface((icon_size + 10, icon_size + 10), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 100, 150, 30), ((icon_size + 10) // 2, (icon_size + 10) // 2), (icon_size + 10) // 2)
                panel.blit(glow, (ix - 5, iy - 5))
                panel.blit(heart_small, (ix, iy))
    else:
        for i in range(max_icons):
            ix = 14 + i * (icon_size + 6)
            iy = 32
            pygame.draw.circle(panel, (255, 100, 150), (ix + icon_size // 2, iy + icon_size // 2), icon_size // 2)
    surf.blit(panel, (x, y))

def draw_text_shadow(surf, text, size, x, y, color=(255,255,255), shadow_offset=(2,2), shadow_color=(0,0,0)):
    font = pygame.font.SysFont("arial", size, bold=True)
    txt_shadow = font.render(text, True, shadow_color)
    rect_shadow = txt_shadow.get_rect(center=(x + shadow_offset[0], y + shadow_offset[1]))
    surf.blit(txt_shadow, rect_shadow)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(x, y))
    surf.blit(txt, rect)
    return rect

def draw_button(surf, rect, label, hovered=False):
    base = (70, 110, 80)
    hover = (90, 140, 100)
    color = hover if hovered else base
    pygame.draw.rect(surf, color, rect, border_radius=10)
    pygame.draw.rect(surf, (220,220,220), rect, 2, border_radius=10)
    draw_text_shadow(surf, label, 30, rect.centerx, rect.centery, (255,255,255))

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

def create_particle(x, y, color, velocity=(0, 0), life=30):
    """Create a particle effect"""
    return {
        "x": x, "y": y, "vx": velocity[0] + random.uniform(-2, 2),
        "vy": velocity[1] + random.uniform(-3, -1), "color": color,
        "life": life, "max_life": life, "size": random.randint(2, 6)
    }

def update_particles():
    """Update all particle effects"""
    global particles
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vy"] += 0.2  # Gravity
        particle["life"] -= 1
        if particle["life"] <= 0:
            particles.remove(particle)

def draw_particles(screen):
    """Draw all particle effects"""
    for particle in particles:
        alpha = int(255 * (particle["life"] / particle["max_life"]))
        size = int(particle["size"] * (particle["life"] / particle["max_life"]))
        if size > 0:
            color = (*particle["color"], alpha)
            pygame.draw.circle(screen, particle["color"], (int(particle["x"]), int(particle["y"])), size)

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
    global score, lives, mushrooms, next_mushroom_spawn_timer, basket, state, particles, paused, distance_score_carry
    score = 0
    lives = LIVES_START
    mushrooms = []
    next_mushroom_spawn_timer = 0
    basket = basket_img.get_rect(midbottom=(WIDTH//2, HEIGHT-10))
    mushrooms.append(spawn_mushroom())
    particles = []
    distance_score_carry = 0.0
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
                start_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 70)
                if start_rect.collidepoint(event.pos):
                    start_level1()

    if paused and state not in (GAMEOVER, WIN):
        # Draw paused overlay and skip updates
        screen.fill((20, 20, 20))
        draw_text_shadow(screen, "PAUSED", 92, WIDTH//2, HEIGHT//2, (255,255,255))
        draw_text_shadow(screen, "Press P to Resume", 28, WIDTH//2, HEIGHT//2+80, (220,220,220))
        pygame.display.flip()
        continue

    keys = pygame.key.get_pressed()

    if state == MENU:
        screen.blit(menu_bg, (0, 0)) if menu_bg else screen.fill((30, 40, 60))
        draw_text_shadow(screen, "Shroom Hunter", 72, WIDTH//2, HEIGHT//2 - 140)
        draw_text(screen, f"High Score: {highscore}", 26, WIDTH//2, HEIGHT//2 - 70, (200,255,200))
        # Start button UI (original style)
        start_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 70)
        hovered = start_rect.collidepoint(pygame.mouse.get_pos())
        draw_button(screen, start_rect, "Start", hovered)
        draw_controls_pill(screen, "[ENTER] or click START   [ESC] Quit", WIDTH//2 - 380, HEIGHT - 60, 760)

    elif state == LEVEL1:
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
                for _ in range(12):
                    particles.append(create_particle(m["rect"].centerx, m["rect"].centery, (255, 220, 120)))
                mushrooms.remove(m)
            elif m["rect"].top > HEIGHT:
                lives -= 1
                if miss_snd: miss_snd.play()
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
            state = LEVEL2

        # Draw Level 1
        screen.blit(level1_bg, (0, 0)) if level1_bg else screen.fill((120, 160, 200))
        for m in mushrooms:
            screen.blit(m["img"], m["rect"]) if m["img"] else pygame.draw.rect(screen, (220, 180, 100), m["rect"])
        screen.blit(basket_img, basket)
        update_particles()
        draw_particles(screen)

        # HUD
        draw_score_pill(screen, score, 30, 24)
        # Top-right goal progress pill with responsive width and margin
        pill_margin = 24
        goal_w = max(280, min(400, int(WIDTH * 0.22)))  # Increased width
        goal_h = 60  # Increased height significantly for proper spacing
        goal_x = WIDTH - goal_w - pill_margin
        goal_y = pill_margin
        draw_goal_progress_pill(screen, goal_x, goal_y, goal_w, goal_h, score, LEVEL1_GOAL)
        draw_lives_panel(screen, lives, heart_img, 30, 80)
        pill_w = int(min(WIDTH - 120, 720))
        pill_x = WIDTH//2 - pill_w//2
        pill_y = HEIGHT - 60
        draw_controls_pill(screen, "[LEFT/RIGHT] Move   [ESC] Quit", WIDTH//2 - 360, HEIGHT - 60, 720)

    elif state == LEVEL2:
        # Scrolling background
        bg_scroll_x -= runner_speed
        if bg_scroll_x <= -WIDTH:
            bg_scroll_x += WIDTH
        runner_speed = min(MAX_RUNNER_SPEED, runner_speed + RUNNER_ACCELERATION)
        runner_distance += runner_speed
        distance_score_carry += runner_speed
        while distance_score_carry >= DISTANCE_SCORE_UNIT:
            score += 1
            distance_score_carry -= DISTANCE_SCORE_UNIT

        # Player jump
        if keys[pygame.K_SPACE] and on_ground:
            player_vy = PLAYER_JUMP_SPEED
            on_ground = False
            if jump_snd: jump_snd.play()
        # Super jump / dash on Shift with cooldown
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and dash_cd == 0:
            player_vy = PLAYER_JUMP_SPEED * 1.5
            dash_cd = DASH_COOLDOWN_FRAMES
            if dash_snd: dash_snd.play()

        # Gravity & ground collision
        player_vy += GRAVITY
        player.y += int(player_vy)
        if player.bottom >= GROUND_Y:
            player.bottom = GROUND_Y
            player_vy = 0
            on_ground = True

        # Dash cooldown tick
        if dash_cd > 0:
            dash_cd -= 1

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
                    monsters.remove(monster)
                else:
                    lives -= 1
                    if hit_snd: hit_snd.play()
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
                hearts.remove(heart)
        for shield in shields[:]:
            shield.x -= int(runner_speed)
            if shield.right < 0:
                shields.remove(shield)
            elif shield.colliderect(player):
                shield_timer = SHIELD_DURATION_FRAMES
                shields.remove(shield)

        if shield_timer > 0:
            shield_timer -= 1

        # Game Over
        if lives <= 0:
            state = GAMEOVER
            if miss_snd: miss_snd.play()
            if score > highscore:
                save_highscore(score)
                highscore = score

        # Draw Level 2 scene
        screen.blit(level2_bg, (bg_scroll_x, 0)) if level2_bg else screen.fill((100, 180, 240))
        if level2_bg:
            screen.blit(level2_bg, (bg_scroll_x + WIDTH, 0))

        ground_color = (80, 160, 80)
        pygame.draw.rect(screen, ground_color, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for i in range(-1, WIDTH // 50 + 2):
            x = (i * 50 + bg_scroll_x) % WIDTH
            pygame.draw.line(screen, (60, 140, 60), (x, GROUND_Y), (x, HEIGHT), 2)

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

        # draw_particles(screen)

        # HUD panels
        status_w, status_h = 360, 160
        status_x, status_y = WIDTH - status_w - 30, 24
        draw_status_panel(screen, status_x, status_y, lives, LIVES_START, shield_timer, SHIELD_DURATION_FRAMES, dash_cd, DASH_COOLDOWN_FRAMES, heart_img)
        draw_metrics_strip(screen, runner_distance, score, runner_speed, x=30, y=24)
        pill_w = int(min(WIDTH - 120, 720))
        draw_controls_pill(screen, "[SPACE] Jump   [P] Pause   [ESC] Quit", WIDTH//2 - pill_w//2, HEIGHT - 60, pill_w)

    elif state == GAMEOVER:
        # Auto-return to menu after short delay
        if gameover_timer > 0:
            gameover_timer -= 1
            if gameover_timer <= 0:
                state = MENU
        screen.fill((200, 100, 100))
        draw_text(screen, "GAME OVER", 80, WIDTH//2, HEIGHT//2 - 100, (255,255,255))
        draw_text(screen, f"Score: {score}", 40, WIDTH//2, HEIGHT//2 - 20, (255,255,200))
        draw_text(screen, f"High Score: {highscore}", 30, WIDTH//2, HEIGHT//2 + 20, (200,255,200))
        draw_text(screen, "Press ENTER to return to menu", 25, WIDTH//2, HEIGHT//2 + 80, (255,255,255))

    elif state == WIN:
        screen.fill((100, 200, 150))
        draw_text(screen, "YOU WIN!", 80, WIDTH//2, HEIGHT//2 - 100, (255,255,255))
        draw_text(screen, f"Score: {score}", 40, WIDTH//2, HEIGHT//2 - 20, (255,255,200))
        draw_text(screen, f"High Score: {highscore}", 30, WIDTH//2, HEIGHT//2 + 20, (200,255,200))
        draw_text(screen, "Press ENTER to return to menu", 25, WIDTH//2, HEIGHT//2 + 80, (255,255,255))

    pygame.display.flip()

pygame.quit()
sys.exit()
