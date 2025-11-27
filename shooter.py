# mind_blinding_shooter_sketchy.py
# Modified to give a hand-drawn / sketchy look so it doesn't feel "AI-generated"
import pygame
import math
import random
import os
from pygame import mixer
import time

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH = 1200
HEIGHT = 800

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mind-Blowing Shooter (Sketchy Edition)")

# Create directory for assets if it doesn't exist
if not os.path.exists('assets'):
    os.makedirs('assets')

# Colors
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Sound effects
mixer.init()
mixer.music.set_volume(0.7)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# -----------------------
# Helper: sketchy draw functions (hand-drawn feel)
# -----------------------
def jitter(seed, magnitude=2.0, freq=1.0):
    """
    Deterministic low-flicker jitter using sin + seed to avoid pure random flicker.
    seed: float (could be time or object id)
    """
    t = time.time() * 0.6 * freq + seed
    return math.sin(t) * magnitude, math.cos(t * 0.9) * (magnitude * 0.6)

def sketch_line(surface, color, start, end, width=2, strokes=3, seed=0):
    """Draw multiple slightly offset lines to emulate hand-drawn stroke"""
    x1, y1 = start
    x2, y2 = end
    for i in range(strokes):
        ox1, oy1 = jitter(seed + i * 13, magnitude=1.2)
        ox2, oy2 = jitter(seed + i * 31, magnitude=1.2)
        pygame.draw.line(surface, color,
                         (int(x1 + ox1), int(y1 + oy1)),
                         (int(x2 + ox2), int(y2 + oy2)),
                         max(1, int(width + random.choice([-1, 0, 1]))))

def sketch_circle(surface, color, center, radius, strokes=4, seed=0, filled=True):
    """Hand-sketched circle: multiple slightly offset circles/ellipses"""
    cx, cy = center
    for i in range(strokes):
        ox, oy = jitter(seed + i * 7, magnitude=1.5 + i * 0.2)
        r_off = radius + (i - strokes / 2) * 0.8
        if filled:
            # draw many concentric slightly offset circles with alpha effect using surface
            s = pygame.Surface((int(r_off*2)+6, int(r_off*2)+6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 180 - i*20), (s.get_width()//2, s.get_height()//2), max(1, int(r_off)))
            surface.blit(s, (int(cx - s.get_width()//2 + ox), int(cy - s.get_height()//2 + oy)))
        else:
            pygame.draw.circle(surface, color, (int(cx + ox), int(cy + oy)), max(1, int(r_off)), max(1, int(2 - i/2)))

def sketch_polygon(surface, color, points, strokes=3, seed=0, filled=True):
    """Draw polygon with jitter on vertices to look hand-made"""
    for i in range(strokes):
        pts = []
        for j, (x, y) in enumerate(points):
            ox, oy = jitter(seed + i*11 + j*3, magnitude=1.6)
            pts.append((int(x + ox), int(y + oy)))
        if filled:
            # use semi-transparent layer for 'fill'
            s_rect = pygame.Rect(min(p[0] for p in pts)-2, min(p[1] for p in pts)-2,
                                 max(p[0] for p in pts)-min(p[0] for p in pts)+4,
                                 max(p[1] for p in pts)-min(p[1] for p in pts)+4)
            s = pygame.Surface((s_rect.w, s_rect.h), pygame.SRCALPHA)
            adj_pts = [(p[0]-s_rect.x, p[1]-s_rect.y) for p in pts]
            alpha = 160 - i*30
            pygame.draw.polygon(s, (*color, max(30, alpha)), adj_pts)
            surface.blit(s, (s_rect.x, s_rect.y))
        else:
            pygame.draw.polygon(surface, color, pts, max(1, strokes - i))

# subtle grain overlay (cheap)
def draw_grain(surface, intensity=30, density=400):
    """Draw random tiny translucent dots to create a paper-like grain."""
    for _ in range(int(density * (intensity/50.0))):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        a = random.randint(8, 40)
        surface.set_at((x, y), (a, a, a, a))

# -----------------------
# Power-up class
# -----------------------
class PowerUp:
    def __init__(self, x=None, y=None):
        # If no position specified, spawn at random location
        if x is None:
            self.x = random.randint(100, WIDTH - 100)
        else:
            self.x = x

        if y is None:
            self.y = random.randint(100, HEIGHT - 100)
        else:
            self.y = y

        self.size = 30
        self.type = random.choice(['health', 'speed', 'rapidfire', 'damage'])
        self.lifetime = 600  # 10 seconds at 60 FPS
        self.pulse_size = self.size
        self.pulse_dir = 1
        self.angle = random.uniform(0, 2*math.pi)  # For rotation effect
        self.seed = random.random() * 1000

        # Set color based on type
        if self.type == 'health':
            self.color = (90, 220, 120)  # slightly muted green
        elif self.type == 'speed':
            self.color = (100, 220, 220)  # cyanish
        elif self.type == 'rapidfire':
            self.color = (255, 230, 80)  # yellow
        elif self.type == 'damage':
            self.color = (255, 90, 90)  # red

    def update(self):
        # Pulsing effect (use sin-based jitter so it's smooth)
        self.pulse_size = self.size + math.sin(time.time()*3 + self.seed) * 4
        # Rotation effect
        self.angle += 0.04
        if self.angle > 2 * math.pi:
            self.angle = 0

        # Reduce lifetime
        self.lifetime -= 1
        return self.lifetime <= 0

    def draw(self):
        # Glow: slightly hand-sketched circular glow
        glow_surf = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
        sketch_circle(glow_surf, self.color, (self.size*2, self.size*2), int(self.pulse_size*1.5), strokes=3, seed=self.seed, filled=True)
        glow_surf.set_alpha(80)
        screen.blit(glow_surf, (self.x - self.size * 2, self.y - self.size * 2))

        # Draw main power-up shape (different shapes for different types) with sketchy rendering
        if self.type == 'health':
            # cross: made from two rectangles approximated as polygons
            w = self.size // 2
            points_h = [(self.x - w//2, self.y - self.size//2), (self.x + w//2, self.y - self.size//2),
                        (self.x + w//2, self.y + self.size//2), (self.x - w//2, self.y + self.size//2)]
            points_v = [(self.x - self.size//2, self.y - w//2), (self.x + self.size//2, self.y - w//2),
                        (self.x + self.size//2, self.y + w//2), (self.x - self.size//2, self.y + w//2)]
            sketch_polygon(screen, self.color, points_h, strokes=3, seed=self.seed)
            sketch_polygon(screen, self.color, points_v, strokes=3, seed=self.seed+5)
        elif self.type == 'speed':
            # triangle rotating
            pts = []
            for k in range(3):
                ang = self.angle + k * (2 * math.pi / 3)
                pts.append((self.x + math.cos(ang) * self.size, self.y + math.sin(ang) * self.size))
            sketch_polygon(screen, self.color, pts, strokes=3, seed=self.seed)
        elif self.type == 'rapidfire':
            # star-like shape
            star_pts = []
            for i in range(5):
                angle = self.angle + i * (2 * math.pi / 5)
                outer = (self.x + math.cos(angle) * self.size, self.y + math.sin(angle) * self.size)
                inner_angle = angle + math.pi / 5
                inner = (self.x + math.cos(inner_angle) * (self.size // 2), self.y + math.sin(inner_angle) * (self.size // 2))
                star_pts.append(outer)
                star_pts.append(inner)
            sketch_polygon(screen, self.color, star_pts, strokes=3, seed=self.seed)
        elif self.type == 'damage':
            # diamond
            pts = [(self.x, self.y - self.size), (self.x + self.size, self.y), (self.x, self.y + self.size), (self.x - self.size, self.y)]
            sketch_polygon(screen, self.color, pts, strokes=3, seed=self.seed)

    def apply(self, player):
        if self.type == 'health':
            player.health = min(player.max_health, player.health + 50)
            return "Health restored!"
        elif self.type == 'speed':
            player.speed = 8  # Increased speed
            return "Speed boosted!"
        elif self.type == 'rapidfire':
            player.gun_cooldown_max = 5  # Faster shooting
            return "Rapid fire activated!"
        elif self.type == 'damage':
            player.bullet_damage = 50  # Double damage
            return "Damage increased!"

# -----------------------
# Player class
# -----------------------
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 5
        self.angle = 0
        self.size = 50
        self.health = 100
        self.max_health = 100
        self.gun_cooldown = 0
        self.gun_cooldown_max = 10
        self.score = 0
        self.power_up_time = 0  # Time left for current power-up
        self.power_up_type = None  # Current active power-up
        self.bullet_damage = 25  # Default bullet damage
        self.seed = random.random() * 1000

    def update(self, keys):
        # Movement
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed

        # Keep player on screen
        self.x = max(self.size // 2, min(WIDTH - self.size // 2, self.x))
        self.y = max(self.size // 2, min(HEIGHT - self.size // 2, self.y))

        # Calculate angle to mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.angle = math.atan2(mouse_y - self.y, mouse_x - self.x)

        # Gun cooldown
        if self.gun_cooldown > 0:
            self.gun_cooldown -= 1

        # Update power-up time
        if self.power_up_time > 0:
            self.power_up_time -= 1
            # Power-up expired
            if self.power_up_time <= 0:
                # Reset effects
                self.speed = 5
                self.gun_cooldown_max = 10
                self.bullet_damage = 25
                self.power_up_type = None

    def draw(self):
        # Add small wobble to center so it doesn't look perfectly static
        ox, oy = jitter(self.seed, magnitude=0.8, freq=0.6)

        # Draw player body (sketchy circle)
        sketch_circle(screen, BLUE, (int(self.x + ox), int(self.y + oy)), int(self.size // 2), strokes=4, seed=self.seed, filled=True)

        # Draw eyes (with small asymmetric offsets)
        eye_offset = self.size // 6
        eye_size = self.size // 8
        eye_dir_x = math.cos(self.angle) * (eye_offset//2)
        eye_dir_y = math.sin(self.angle) * (eye_offset//2)

        # Left eye (sketch)
        lx = int(self.x - eye_offset + eye_dir_x + ox)
        ly = int(self.y - eye_offset + eye_dir_y + oy)
        sketch_circle(screen, WHITE, (lx, ly), int(eye_size), strokes=3, seed=self.seed+10)
        sketch_circle(screen, BLACK, (lx+int(eye_dir_x*0.6), ly+int(eye_dir_y*0.6)), int(eye_size//2), strokes=2, seed=self.seed+11)

        # Right eye (sketch)
        rx = int(self.x + eye_offset + eye_dir_x + ox)
        ry = int(self.y - eye_offset + eye_dir_y + oy)
        sketch_circle(screen, WHITE, (rx, ry), int(eye_size), strokes=3, seed=self.seed+20)
        sketch_circle(screen, BLACK, (rx+int(eye_dir_x*0.6), ry+int(eye_dir_y*0.6)), int(eye_size//2), strokes=2, seed=self.seed+21)

        # Draw mouth: change shape based on health but sketchy
        mouth_size = self.size // 4
        health_percent = self.health / self.max_health
        if health_percent > 0.7:
            # happy arc -> approximate with multiple short lines
            start = (self.x - mouth_size, self.y + mouth_size//2 + oy)
            end = (self.x + mouth_size, self.y + mouth_size//2 + oy)
            for i in range(5):
                # slightly curved by offsetting middle
                mx = start[0] + (end[0]-start[0]) * (i/4)
                my = start[1] - abs(math.sin((i/4)*math.pi)) * mouth_size * 0.6
                sketch_line(screen, BLACK, (mx-6, my), (mx+6, my+1), width=2, strokes=2, seed=self.seed+i*3)
        elif health_percent > 0.3:
            # neutral line
            sketch_line(screen, BLACK, (self.x - mouth_size, self.y + mouth_size//2 + oy), (self.x + mouth_size, self.y + mouth_size//2 + oy), width=3, strokes=3, seed=self.seed+50)
        else:
            # sad arc (inverse)
            start = (self.x - mouth_size, self.y + mouth_size + oy)
            end = (self.x + mouth_size, self.y + mouth_size + oy)
            for i in range(5):
                mx = start[0] + (end[0]-start[0]) * (i/4)
                my = start[1] + abs(math.sin((i/4)*math.pi)) * mouth_size * 0.4
                sketch_line(screen, BLACK, (mx-6, my), (mx+6, my-1), width=2, strokes=2, seed=self.seed+i*7)

        # Draw gun (sketchy lines)
        gun_length = self.size * 1.2
        end_x = self.x + math.cos(self.angle) * gun_length
        end_y = self.y + math.sin(self.angle) * self.size
        sketch_line(screen, BLACK, (self.x + ox, self.y + oy), (end_x, end_y), width=6, strokes=4, seed=self.seed+100)

        # barrel extension
        barrel_end_x = end_x + math.cos(self.angle) * (self.size // 2)
        barrel_end_y = end_y + math.sin(self.angle) * (self.size // 2)
        sketch_line(screen, (80, 80, 80), (end_x, end_y), (barrel_end_x, barrel_end_y), width=8, strokes=3, seed=self.seed+101)

        # handle - draw a short thick line with jitter
        handle_angle = self.angle + math.pi/2
        handle_length = self.size // 3
        handle_x = self.x + math.cos(self.angle) * (self.size // 2)
        handle_y = self.y + math.sin(self.angle) * (self.size // 2)
        handle_end_x = handle_x + math.cos(handle_angle) * handle_length
        handle_end_y = handle_y + math.sin(handle_angle) * handle_length
        sketch_line(screen, (139, 69, 19), (handle_x, handle_y), (handle_end_x, handle_end_y), width=6, strokes=3, seed=self.seed+111)

        # Health bar (sketchy rectangles using lines)
        health_width = int((self.health / self.max_health) * 100)
        # background box (drawn with sketch_line as border)
        sketch_line(screen, RED, (self.x - 50, self.y - 60), (self.x + 50, self.y - 60), width=8, strokes=3, seed=self.seed+200)
        sketch_line(screen, GREEN, (self.x - 50, self.y - 60), (self.x - 50 + health_width, self.y - 60), width=6, strokes=3, seed=self.seed+201)

    def shoot(self, bullets, particles):
        if self.gun_cooldown == 0:
            # Create bullet with current damage (possibly increased by power-up)
            bullet = Bullet(self.x, self.y, self.angle, self.bullet_damage)
            bullets.append(bullet)
            self.gun_cooldown = self.gun_cooldown_max

            # Add muzzle flash effect
            flash_x = self.x + math.cos(self.angle) * self.size * 1.5
            flash_y = self.y + math.sin(self.angle) * self.size * 1.5
            for _ in range(10):
                flash_angle = self.angle + random.uniform(-0.5, 0.5)
                flash_speed = random.uniform(2, 6)
                flash_color = (255, random.randint(100, 255), 0)  # Orange-yellow
                flash = Particle(flash_x, flash_y, flash_color)
                flash.angle = flash_angle
                flash.speed = flash_speed
                flash.lifetime = random.randint(5, 10)  # Short lifetime
                particles.append(flash)

            # Gun sound effect placeholder
            # mixer.Sound('assets/shoot.wav').play()

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Player is dead
        return False

# -----------------------
# Bullet class
# -----------------------
class Bullet:
    def __init__(self, x, y, angle, damage=25):
        self.x = x + math.cos(angle) * 50  # Start bullet from gun position
        self.y = y + math.sin(angle) * 50
        self.angle = angle
        self.speed = 15
        self.size = 8
        self.damage = damage  # Now takes damage parameter
        self.lifetime = 60  # Frames before bullet disappears
        self.seed = random.random() * 1000

    def update(self):
        # Move bullet
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1

        # Check if bullet is off screen or expired
        if (self.x < 0 or self.x > WIDTH or
            self.y < 0 or self.y > HEIGHT or
            self.lifetime <= 0):
            return True  # Bullet should be removed
        return False

    def draw(self):
        # Make bullet look sketchy and glowing
        sketch_circle(screen, ORANGE, (int(self.x), int(self.y)), self.size, strokes=3, seed=self.seed, filled=True)
        sketch_circle(screen, (255, 255, 200), (int(self.x), int(self.y)), self.size+3, strokes=2, seed=self.seed+3, filled=False)

# -----------------------
# Enemy class
# -----------------------
class Enemy:
    def __init__(self):
        # Spawn enemies from edges
        side = random.randint(0, 3)
        if side == 0:  # Top
            self.x = random.randint(0, WIDTH)
            self.y = -50
        elif side == 1:  # Right
            self.x = WIDTH + 50
            self.y = random.randint(0, HEIGHT)
        elif side == 2:  # Bottom
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + 50
        else:  # Left
            self.x = -50
            self.y = random.randint(0, HEIGHT)

        self.speed = random.uniform(1.0, 3.0)
        self.size = random.randint(30, 70)
        self.health = self.size
        self.color = (random.randint(80, 220), random.randint(20, 120), random.randint(20, 120))
        self.seed = random.random() * 1000

    def update(self, player_x, player_y):
        # Move towards player
        angle = math.atan2(player_y - self.y, player_x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed

    def draw(self):
        # Slight wobble so circles are not perfect
        sketch_circle(screen, self.color, (int(self.x), int(self.y)), int(self.size), strokes=4, seed=self.seed, filled=True)

        # Draw eyes (sketchy)
        eye_distance = self.size // 3
        eye_size = max(3, self.size // 6)
        sketch_circle(screen, WHITE, (int(self.x - eye_distance), int(self.y - eye_distance/2)), eye_size, strokes=2, seed=self.seed+10)
        sketch_circle(screen, WHITE, (int(self.x + eye_distance), int(self.y - eye_distance/2)), eye_size, strokes=2, seed=self.seed+20)

        # Angry mouth arc - sketch approximation
        mouth_control_x = int(self.x)
        mouth_control_y = int(self.y + self.size / 2)
        sketch_line(screen, WHITE, (mouth_control_x - eye_distance, mouth_control_y), (mouth_control_x + eye_distance, mouth_control_y), width=3, strokes=3, seed=self.seed+30)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            return True  # Enemy is dead
        # Make enemy shrink when damaged
        self.size = max(20, int(self.health))
        return False

# -----------------------
# Particle effect for explosions
# -----------------------
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.size = random.randint(3, 10)
        self.color = color
        self.lifetime = random.randint(20, 40)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(2.0, 6.0)
        self.seed = random.random() * 1000

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.speed *= 0.95  # Slow down
        self.lifetime -= 1
        self.size *= 0.95  # Shrink

        if self.lifetime <= 0:
            return True  # Particle should be removed
        return False

    def draw(self):
        sketch_circle(screen, self.color, (int(self.x), int(self.y)), max(1, int(self.size)), strokes=2, seed=self.seed, filled=True)

# -----------------------
# Background stars
# -----------------------
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.uniform(0.5, 3.0)
        self.brightness = random.randint(100, 255)
        self.speed = random.uniform(0.2, 1.0)
        self.twinkle_speed = random.uniform(0.02, 0.1)
        self.twinkle_direction = random.choice([-1, 1])
        self.original_brightness = self.brightness
        self.seed = random.random() * 1000

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

        # Twinkle effect
        self.brightness += self.twinkle_speed * self.twinkle_direction * 60/FPS
        if self.brightness > 255 or self.brightness < self.original_brightness - 50:
            self.twinkle_direction *= -1

    def draw(self):
        color = (min(255, int(self.brightness)),
                 min(255, int(self.brightness)),
                 min(255, int(self.brightness)))
        # small stars as sketch circles
        sketch_circle(screen, color, (int(self.x), int(self.y)), max(1, int(self.size)), strokes=2, seed=self.seed, filled=True)
        if self.size > 2:
            # glow stroke
            sketch_circle(screen, color, (int(self.x), int(self.y)), int(self.size*1.8), strokes=2, seed=self.seed+10, filled=False)

# -----------------------
# Nebula background effect
# -----------------------
class Nebula:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(100, 300)
        self.color = (random.randint(0, 100),
                     random.randint(0, 100),
                     random.randint(100, 255))  # Bluish
        self.alpha = random.randint(10, 30)
        self.seed = random.random() * 1000

    def draw(self):
        # Create a transparent surface for the nebula
        nebula_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        # Draw nebula as a gradient circle but sketchy
        for i in range(self.size, 0, -12):
            current_alpha = max(2, int(self.alpha * (i / self.size)))
            pygame.draw.circle(nebula_surface,
                               (*self.color, current_alpha),
                               (self.size // 2 + int(math.sin(time.time()*0.3 + self.seed)*6),
                                self.size // 2 + int(math.cos(time.time()*0.25 + self.seed)*6)),
                               i // 2)
        nebula_surface.set_alpha(self.alpha + 20)
        screen.blit(nebula_surface, (self.x - self.size // 2, self.y - self.size // 2))

# -----------------------
# Draw text function (keeps same)
# -----------------------
def draw_text(text, font_size, x, y, color=WHITE):
    font = pygame.font.SysFont("Arial", font_size)
    # Note: pygame font doesn't support per-character alpha in simple way, keep it simple
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

# -----------------------
# Game states
# -----------------------
MENU = 0
PLAYING = 1
GAME_OVER = 2

# -----------------------
# Main game function (logic mostly same)
# -----------------------
def main():
    game_state = MENU

    # Create player
    player = Player()

    # Game objects
    bullets = []
    enemies = []
    particles = []
    power_ups = []

    # Create stars for background
    stars = [Star() for _ in range(120)]

    # Create nebulas for background
    nebulas = [Nebula() for _ in range(5)]

    # Game variables
    enemy_spawn_timer = 0
    enemy_spawn_delay = 60  # Frames between enemy spawns
    power_up_spawn_timer = 0
    power_up_spawn_interval = 600  # Spawn power-up every 10 seconds
    score = 0
    message_text = ""
    message_time = 0

    # optional: small grain overlay surface (create once)
    grain_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # fill grain with few dots (cheap)
    for _ in range(350):
        gx = random.randint(0, WIDTH-1)
        gy = random.randint(0, HEIGHT-1)
        ga = random.randint(8, 24)
        try:
            grain_surface.set_at((gx, gy), (ga, ga, ga, ga))
        except:
            pass

    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game_state == MENU and event.key == pygame.K_SPACE:
                    game_state = PLAYING

                if game_state == GAME_OVER and event.key == pygame.K_SPACE:
                    # Reset game
                    game_state = PLAYING
                    player = Player()
                    bullets = []
                    enemies = []
                    particles = []
                    power_ups = []
                    score = 0

            if game_state == PLAYING and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    player.shoot(bullets, particles)

        # Fill screen with deep blue background
        screen.fill((8, 8, 36))

        # Draw nebulas
        for nebula in nebulas:
            nebula.draw()

        # Update and draw stars
        for star in stars:
            star.update()
            star.draw()

        # lightly overlay grain
        screen.blit(grain_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # Game state specific logic
        if game_state == MENU:
            # Draw menu (sketchy text not necessary, keep normal text)
            draw_text("MIND-BLOWING SHOOTER", 64, WIDTH//2, HEIGHT//3, (255, 0, 128))
            draw_text("Use WASD or Arrow Keys to move", 32, WIDTH//2, HEIGHT//2)
            draw_text("Left Mouse Button to shoot", 32, WIDTH//2, HEIGHT//2 + 50)
            draw_text("Press SPACE to start", 48, WIDTH//2, HEIGHT//2 + 150, (0, 255, 255))

        elif game_state == PLAYING:
            # Get keyboard state
            keys = pygame.key.get_pressed()

            # Update player
            player.update(keys)

            # Update bullets
            for bullet in bullets[:]:
                if bullet.update():
                    bullets.remove(bullet)
                else:
                    bullet.draw()

            # Spawn enemies
            enemy_spawn_timer += 1
            if enemy_spawn_timer >= enemy_spawn_delay:
                enemies.append(Enemy())
                enemy_spawn_timer = 0
                # Decrease spawn delay over time for difficulty increase
                enemy_spawn_delay = max(10, enemy_spawn_delay - 0.2)

            # Spawn power-ups
            power_up_spawn_timer += 1
            if power_up_spawn_timer >= power_up_spawn_interval:
                power_ups.append(PowerUp())
                power_up_spawn_timer = 0

            # Update power-ups
            for power_up in power_ups[:]:
                if power_up.update():
                    power_ups.remove(power_up)
                    continue

                # Check collision with player
                distance = math.hypot(power_up.x - player.x, power_up.y - player.y)
                if distance < power_up.size + player.size // 2:
                    # Apply power-up
                    message_text = power_up.apply(player)
                    message_time = 180  # Display message for 3 seconds

                    # Set power-up duration
                    player.power_up_time = 600  # 10 seconds
                    player.power_up_type = power_up.type

                    # Create collection effect
                    for _ in range(20):
                        particles.append(Particle(power_up.x, power_up.y, power_up.color))

                    power_ups.remove(power_up)
                    continue

                power_up.draw()

            # Update enemies
            for enemy in enemies[:]:
                enemy.update(player.x, player.y)

                # Check collision with player
                distance = math.hypot(enemy.x - player.x, enemy.y - player.y)
                if distance < enemy.size + player.size // 2:
                    # Player takes damage on collision
                    if player.take_damage(10):
                        game_state = GAME_OVER

                    # Create explosion particles
                    for _ in range(20):
                        particles.append(Particle(enemy.x, enemy.y, enemy.color))

                    enemies.remove(enemy)
                    continue

                # Check bullet collisions
                for bullet in bullets[:]:
                    distance = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                    if distance < enemy.size + bullet.size:
                        # Enemy takes damage
                        if enemy.take_damage(bullet.damage):
                            # Enemy killed
                            score += int(enemy.size)

                            # Create explosion particles
                            for _ in range(30):
                                particles.append(Particle(enemy.x, enemy.y, enemy.color))

                            enemies.remove(enemy)

                        # Remove bullet
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break

                # Draw enemy after all checks
                if enemy in enemies:
                    enemy.draw()

            # Update particles
            for particle in particles[:]:
                if particle.update():
                    particles.remove(particle)
                else:
                    particle.draw()

            # Draw player
            player.draw()

            # Draw score
            draw_text(f"Score: {score}", 36, 100, 40)

            # Draw active power-up indicator if one is active
            if player.power_up_type:
                if player.power_up_type == 'health':
                    indicator_color = (0, 255, 0)
                    indicator_text = "Health Boost"
                elif player.power_up_type == 'speed':
                    indicator_color = (0, 255, 255)
                    indicator_text = "Speed Boost"
                elif player.power_up_type == 'rapidfire':
                    indicator_color = (255, 255, 0)
                    indicator_text = "Rapid Fire"
                elif player.power_up_type == 'damage':
                    indicator_color = (255, 0, 0)
                    indicator_text = "Damage Boost"

                # Draw power-up name and time bar
                draw_text(indicator_text, 24, WIDTH - 150, 40, indicator_color)
                time_left = int((player.power_up_time / 600) * 100)
                pygame.draw.rect(screen, (100, 100, 100), (WIDTH - 200, 60, 100, 10))
                pygame.draw.rect(screen, indicator_color, (WIDTH - 200, 60, time_left, 10))

            # Draw message if active
            if message_time > 0:
                # Make message fade out
                alpha = min(255, message_time * 1.5)
                draw_text(message_text, 36, WIDTH // 2, HEIGHT // 4, (255, 255, 255))
                message_time -= 1

        elif game_state == GAME_OVER:
            # Draw game over screen
            draw_text("GAME OVER", 72, WIDTH//2, HEIGHT//3, RED)
            draw_text(f"Final Score: {score}", 48, WIDTH//2, HEIGHT//2)
            draw_text("Press SPACE to play again", 36, WIDTH//2, HEIGHT//2 + 100)

        # Update display
        pygame.display.flip()

        # Cap framerate
        clock.tick(FPS)

    # Quit pygame
    pygame.quit()

if __name__ == "__main__":
    main()
