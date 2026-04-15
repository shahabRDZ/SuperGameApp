"""
Water Sort Puzzle - Playable Demo
Part of SuperGameApp project
Built with Pygame for desktop testing
"""

import pygame
import sys
import random
import copy
import math

# ─────────────────────────── CONFIG ───────────────────────────

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60
LAYERS_PER_TUBE = 4

# Colors
BG_COLOR = (24, 24, 32)
BG_GRADIENT_TOP = (30, 30, 50)
BG_GRADIENT_BOTTOM = (15, 15, 25)
TUBE_COLOR = (60, 65, 80)
TUBE_OUTLINE = (90, 95, 110)
TUBE_SELECTED = (255, 220, 80)
TEXT_COLOR = (240, 240, 245)
TEXT_SECONDARY = (160, 165, 180)
BUTTON_COLOR = (55, 60, 80)
BUTTON_HOVER = (75, 80, 105)
BUTTON_TEXT = (240, 240, 245)
COIN_COLOR = (255, 215, 0)
STAR_COLOR = (255, 200, 50)
PANEL_BG = (35, 38, 55)
PANEL_BORDER = (70, 75, 95)
SUCCESS_COLOR = (80, 200, 120)
OVERLAY_COLOR = (0, 0, 0, 160)

LIQUID_COLORS = [
    (231, 76, 60),    # Red
    (52, 152, 219),   # Blue
    (46, 204, 113),   # Green
    (241, 196, 15),   # Yellow
    (230, 126, 34),   # Orange
    (155, 89, 182),   # Purple
    (26, 188, 156),   # Teal
    (233, 30, 99),    # Pink
    (121, 85, 72),    # Brown
    (149, 165, 166),  # Gray
]


# ─────────────────────────── LEVEL GENERATOR ───────────────────────────

def get_difficulty(level):
    if level <= 5:    return (3, 2, 30)
    if level <= 15:   return (4, 2, 50)
    if level <= 30:   return (5, 2, 70)
    if level <= 50:   return (6, 2, 90)
    if level <= 75:   return (7, 2, 110)
    if level <= 100:  return (8, 2, 130)
    return (9, 2, 160)


def generate_level(level_num):
    colors, empties, shuffles = get_difficulty(level_num)

    # Use level number as seed for reproducible levels
    rng = random.Random(level_num * 7919 + 42)

    # Start solved
    tubes = []
    for c in range(colors):
        tubes.append([c + 1] * LAYERS_PER_TUBE)
    for _ in range(empties):
        tubes.append([])

    # Shuffle by random valid moves
    for _ in range(shuffles):
        moves = get_valid_moves(tubes)
        if not moves:
            break
        fr, to = rng.choice(moves)
        perform_move(tubes, fr, to)

    # Verify it's actually shuffled (not still solved)
    solved_count = sum(1 for t in tubes if len(t) == LAYERS_PER_TUBE and len(set(t)) == 1)
    if solved_count == colors:
        # Still solved, force a harder shuffle
        for _ in range(shuffles * 3):
            moves = get_valid_moves(tubes)
            if not moves:
                break
            fr, to = rng.choice(moves)
            # Prefer moves that break completed tubes
            breaking = [(f, t) for f, t in moves
                        if len(tubes[f]) == LAYERS_PER_TUBE and len(set(tubes[f])) == 1]
            if breaking:
                fr, to = rng.choice(breaking)
            perform_move(tubes, fr, to)

    return tubes


def get_valid_moves(tubes):
    moves = []
    for fr in range(len(tubes)):
        if not tubes[fr]:
            continue
        top = tubes[fr][-1]
        for to in range(len(tubes)):
            if fr == to:
                continue
            if len(tubes[to]) >= LAYERS_PER_TUBE:
                continue
            if not tubes[to] or tubes[to][-1] == top:
                moves.append((fr, to))
    return moves


def perform_move(tubes, fr, to):
    if not tubes[fr]:
        return
    if len(tubes[to]) >= LAYERS_PER_TUBE:
        return
    top = tubes[fr][-1]
    while tubes[fr] and len(tubes[to]) < LAYERS_PER_TUBE and tubes[fr][-1] == top:
        tubes[to].append(tubes[fr].pop())


# ─────────────────────────── ANIMATION ───────────────────────────

class PourAnimation:
    def __init__(self):
        self.active = False
        self.phase = 0
        self.progress = 0.0
        self.source_idx = -1
        self.target_idx = -1
        self.moved_layers = []
        self.source_original_pos = (0, 0)
        self.source_current_pos = (0, 0)
        self.speed = 4.0

    def start(self, source_idx, target_idx, moved_layers, source_pos):
        self.active = True
        self.phase = 0
        self.progress = 0.0
        self.source_idx = source_idx
        self.target_idx = target_idx
        self.moved_layers = moved_layers
        self.source_original_pos = source_pos
        self.source_current_pos = source_pos

    def update(self, dt, tube_positions):
        if not self.active:
            return False

        self.progress += dt * self.speed

        if self.phase == 0:  # Lift
            if self.progress >= 1.0:
                self.phase = 1
                self.progress = 0.0
        elif self.phase == 1:  # Move to target
            if self.progress >= 1.0:
                self.phase = 2
                self.progress = 0.0
        elif self.phase == 2:  # Pour
            if self.progress >= 1.0:
                self.phase = 3
                self.progress = 0.0
        elif self.phase == 3:  # Return
            if self.progress >= 1.0:
                self.active = False
                return True  # Done

        return False

    def get_source_offset(self, tube_positions):
        if not self.active:
            return (0, 0)

        target_pos = tube_positions[self.target_idx]
        source_pos = self.source_original_pos

        t = min(self.progress, 1.0)
        t = t * t * (3 - 2 * t)  # Smoothstep

        if self.phase == 0:
            return (0, -50 * t)
        elif self.phase == 1:
            dx = (target_pos[0] - source_pos[0]) * t
            return (dx, -50)
        elif self.phase == 2:
            dx = target_pos[0] - source_pos[0]
            return (dx, -50)
        elif self.phase == 3:
            dx = (target_pos[0] - source_pos[0]) * (1 - t)
            dy = -50 * (1 - t)
            return (dx, dy)
        return (0, 0)


# ─────────────────────────── BUTTON ───────────────────────────

class Button:
    def __init__(self, x, y, w, h, text, font, color=BUTTON_COLOR, hover_color=BUTTON_HOVER, icon=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.icon = icon
        self.hovered = False

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, TUBE_OUTLINE, self.rect, 1, border_radius=10)

        text_surface = self.font.render(self.text, True, BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# ─────────────────────────── PARTICLE ───────────────────────────

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -1)
        self.life = 1.0
        self.size = random.randint(3, 7)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 5 * dt
        self.life -= dt * 1.5
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(self.life * 255)))
        color = (*self.color[:3], alpha)
        s = max(1, int(self.size * self.life))
        temp = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, color, (s, s), s)
        surface.blit(temp, (int(self.x) - s, int(self.y) - s))


# ─────────────────────────── GAME ───────────────────────────

class WaterSortGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Super Game App - Water Sort Puzzle")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.font_tiny = pygame.font.SysFont("Arial", 14)

        self.level = 1
        self.coins = 100
        self.moves = 0
        self.selected = -1
        self.tubes = []
        self.undo_stack = []
        self.tube_positions = []
        self.particles = []
        self.pour_anim = PourAnimation()
        self.state = "playing"  # playing, complete, menu

        self.tube_width = 50
        self.tube_height = 160
        self.layer_height = 35
        self.tube_inner_margin = 5

        self.buttons = {}
        self.level_complete_time = 0

        self.load_level(self.level)

    def load_level(self, level_num):
        self.level = level_num
        self.tubes = generate_level(level_num)
        self.moves = 0
        self.selected = -1
        self.undo_stack = []
        self.particles = []
        self.state = "playing"
        self.pour_anim.active = False
        self.calculate_positions()
        self.create_buttons()

    def calculate_positions(self):
        self.tube_positions = []
        n = len(self.tubes)
        max_per_row = min(n, 6)
        rows = math.ceil(n / max_per_row)

        for i in range(n):
            row = i // max_per_row
            col = i % max_per_row
            tubes_in_row = min(max_per_row, n - row * max_per_row)

            total_w = tubes_in_row * (self.tube_width + 30) - 30
            start_x = (SCREEN_WIDTH - total_w) // 2

            x = start_x + col * (self.tube_width + 30)
            y = 180 + row * (self.tube_height + 50)
            self.tube_positions.append((x, y))

    def create_buttons(self):
        btn_y = SCREEN_HEIGHT - 70
        btn_w = 110
        btn_h = 42
        gap = 20
        total = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total) // 2

        self.buttons = {
            "undo": Button(start_x, btn_y, btn_w, btn_h, "Undo", self.font_small),
            "restart": Button(start_x + btn_w + gap, btn_y, btn_w, btn_h, "Restart", self.font_small),
            "menu": Button(start_x + (btn_w + gap) * 2, btn_y, btn_w, btn_h, "Menu", self.font_small),
        }

    def draw_gradient_bg(self):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_GRADIENT_TOP[0] * (1 - t) + BG_GRADIENT_BOTTOM[0] * t)
            g = int(BG_GRADIENT_TOP[1] * (1 - t) + BG_GRADIENT_BOTTOM[1] * t)
            b = int(BG_GRADIENT_TOP[2] * (1 - t) + BG_GRADIENT_BOTTOM[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def draw_top_bar(self):
        # Background
        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 70)
        pygame.draw.rect(self.screen, PANEL_BG, bar_rect)
        pygame.draw.line(self.screen, PANEL_BORDER, (0, 70), (SCREEN_WIDTH, 70), 1)

        # Level
        level_text = self.font_medium.render(f"Level {self.level}", True, TEXT_COLOR)
        self.screen.blit(level_text, (30, 22))

        # Moves
        moves_text = self.font_small.render(f"Moves: {self.moves}", True, TEXT_SECONDARY)
        self.screen.blit(moves_text, (SCREEN_WIDTH // 2 - moves_text.get_width() // 2, 26))

        # Coins
        pygame.draw.circle(self.screen, COIN_COLOR, (SCREEN_WIDTH - 120, 35), 12)
        pygame.draw.circle(self.screen, (200, 170, 0), (SCREEN_WIDTH - 120, 35), 12, 2)
        coin_text = self.font_medium.render(str(self.coins), True, COIN_COLOR)
        self.screen.blit(coin_text, (SCREEN_WIDTH - 100, 20))

    def draw_tube(self, idx, tube, pos):
        x, y = pos

        # Apply animation offset
        offset_x, offset_y = 0, 0
        if self.pour_anim.active and self.pour_anim.source_idx == idx:
            offset_x, offset_y = self.pour_anim.get_source_offset(self.tube_positions)

        draw_x = x + offset_x
        draw_y = y + offset_y

        # Selection highlight
        if idx == self.selected and not self.pour_anim.active:
            draw_y -= 20
            glow_rect = pygame.Rect(draw_x - 5, draw_y - 5, self.tube_width + 10, self.tube_height + 25)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*TUBE_SELECTED, 40), glow_surf.get_rect(), border_radius=14)
            self.screen.blit(glow_surf, glow_rect.topleft)

        # Tube body (rounded rectangle with open top)
        tube_rect = pygame.Rect(draw_x, draw_y + 15, self.tube_width, self.tube_height)

        # Tube background
        pygame.draw.rect(self.screen, TUBE_COLOR, tube_rect, border_radius=8)

        # Draw liquid layers
        visible_tube = tube
        # During animation, hide moved layers from source
        if self.pour_anim.active and self.pour_anim.source_idx == idx and self.pour_anim.phase >= 2:
            visible_tube = tube  # Already removed from data

        for li, color_idx in enumerate(visible_tube):
            if color_idx == 0:
                continue
            color = LIQUID_COLORS[color_idx - 1]
            layer_y = draw_y + self.tube_height + 15 - (li + 1) * self.layer_height
            layer_rect = pygame.Rect(
                draw_x + self.tube_inner_margin,
                layer_y,
                self.tube_width - self.tube_inner_margin * 2,
                self.layer_height - 2
            )

            # Rounded bottom for first layer
            radius = 6 if li == 0 else 3
            pygame.draw.rect(self.screen, color, layer_rect, border_radius=radius)

            # Subtle shine
            shine_rect = pygame.Rect(layer_rect.x + 3, layer_rect.y + 2,
                                     layer_rect.width // 3, layer_rect.height - 4)
            shine_surf = pygame.Surface((shine_rect.width, shine_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shine_surf, (255, 255, 255, 30), shine_surf.get_rect(), border_radius=2)
            self.screen.blit(shine_surf, shine_rect.topleft)

        # Tube outline
        outline_color = TUBE_SELECTED if idx == self.selected and not self.pour_anim.active else TUBE_OUTLINE
        pygame.draw.rect(self.screen, outline_color, tube_rect, 2, border_radius=8)

        # Complete indicator
        if self.is_tube_complete(tube):
            check_x = draw_x + self.tube_width // 2
            check_y = draw_y + 5
            pygame.draw.circle(self.screen, SUCCESS_COLOR, (check_x, check_y), 8)
            check_surf = self.font_tiny.render("✓", True, (255, 255, 255))
            self.screen.blit(check_surf, (check_x - check_surf.get_width() // 2, check_y - check_surf.get_height() // 2))

    def is_tube_complete(self, tube):
        if len(tube) != LAYERS_PER_TUBE:
            return False
        return len(set(tube)) == 1

    def draw_level_complete(self):
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Panel
        panel_w, panel_h = 380, 320
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel_rect, 2, border_radius=16)

        # Title
        title = self.font_large.render("Level Complete!", True, SUCCESS_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, panel_y + 25))

        # Stars
        stars = self.calculate_stars()
        star_y = panel_y + 85
        for i in range(3):
            star_x = SCREEN_WIDTH // 2 - 60 + i * 45
            color = STAR_COLOR if i < stars else (60, 60, 70)
            self.draw_star(star_x, star_y, 18, color)

        # Stats
        moves_text = self.font_medium.render(f"Moves: {self.moves}", True, TEXT_COLOR)
        self.screen.blit(moves_text, (SCREEN_WIDTH // 2 - moves_text.get_width() // 2, panel_y + 130))

        reward = stars * 10
        reward_text = self.font_medium.render(f"+{reward} coins", True, COIN_COLOR)
        self.screen.blit(reward_text, (SCREEN_WIDTH // 2 - reward_text.get_width() // 2, panel_y + 165))

        # Buttons
        btn_w, btn_h = 140, 45
        gap = 20

        next_btn = pygame.Rect(SCREEN_WIDTH // 2 - btn_w - gap // 2, panel_y + 230, btn_w, btn_h)
        replay_btn = pygame.Rect(SCREEN_WIDTH // 2 + gap // 2, panel_y + 230, btn_w, btn_h)

        mouse = pygame.mouse.get_pos()

        for btn, text, color in [(next_btn, "Next Level", SUCCESS_COLOR), (replay_btn, "Replay", BUTTON_COLOR)]:
            c = tuple(min(255, x + 20) for x in color) if btn.collidepoint(mouse) else color
            pygame.draw.rect(self.screen, c, btn, border_radius=10)
            txt = self.font_small.render(text, True, (255, 255, 255))
            self.screen.blit(txt, (btn.centerx - txt.get_width() // 2, btn.centery - txt.get_height() // 2))

        return next_btn, replay_btn

    def draw_star(self, cx, cy, size, color):
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = size if i % 2 == 0 else size * 0.4
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(self.screen, color, points)

    def calculate_stars(self):
        colors, _, _ = get_difficulty(self.level)
        optimal = colors * 3
        if self.moves <= optimal:
            return 3
        if self.moves <= optimal * 1.5:
            return 2
        return 1

    def try_pour(self, source_idx, target_idx):
        source = self.tubes[source_idx]
        target = self.tubes[target_idx]

        if not source:
            return False

        top_color = source[-1]
        if target and target[-1] != top_color:
            return False
        if len(target) >= LAYERS_PER_TUBE:
            return False

        # Save state for undo
        self.undo_stack.append(copy.deepcopy(self.tubes))

        # Count matching top layers
        count = 0
        for i in range(len(source) - 1, -1, -1):
            if source[i] == top_color:
                count += 1
            else:
                break

        space = LAYERS_PER_TUBE - len(target)
        to_move = min(count, space)

        moved = []
        for _ in range(to_move):
            moved.append(source.pop())
            target.append(moved[-1])

        self.moves += 1

        # Start animation
        self.pour_anim.start(source_idx, target_idx, moved, self.tube_positions[source_idx])

        return True

    def undo(self):
        if not self.undo_stack:
            return
        self.tubes = self.undo_stack.pop()
        self.moves = max(0, self.moves - 1)
        self.selected = -1

    def check_win(self):
        for tube in self.tubes:
            if tube and not self.is_tube_complete(tube):
                return False
        return True

    def spawn_celebration(self):
        for _ in range(50):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(200, SCREEN_HEIGHT - 200)
            color = random.choice(LIQUID_COLORS)
            self.particles.append(Particle(x, y, color))

    def get_tube_at_pos(self, mx, my):
        for i, (x, y) in enumerate(self.tube_positions):
            rect = pygame.Rect(x - 5, y, self.tube_width + 10, self.tube_height + 20)
            if rect.collidepoint(mx, my):
                return i
        return -1

    def draw_menu(self):
        self.draw_gradient_bg()

        # Title
        title = self.font_large.render("Water Sort Puzzle", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        subtitle = self.font_small.render("Super Game App", True, TEXT_SECONDARY)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 200))

        # Decorative tubes
        for i in range(5):
            x = 150 + i * 100
            y = 280
            color = LIQUID_COLORS[i]
            rect = pygame.Rect(x, y, 40, 120)
            pygame.draw.rect(self.screen, TUBE_COLOR, rect, border_radius=6)
            for j in range(LAYERS_PER_TUBE):
                layer_rect = pygame.Rect(x + 4, y + 120 - (j + 1) * 27, 32, 25)
                pygame.draw.rect(self.screen, color, layer_rect, border_radius=4)
            pygame.draw.rect(self.screen, TUBE_OUTLINE, rect, 2, border_radius=6)

        # Play button
        play_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 460, 200, 55)
        mouse = pygame.mouse.get_pos()
        color = (100, 210, 140) if play_btn.collidepoint(mouse) else SUCCESS_COLOR
        pygame.draw.rect(self.screen, color, play_btn, border_radius=12)
        play_text = self.font_medium.render("Play", True, (255, 255, 255))
        self.screen.blit(play_text, (play_btn.centerx - play_text.get_width() // 2,
                                     play_btn.centery - play_text.get_height() // 2))

        # Level select hint
        hint = self.font_small.render(f"Starting Level: {self.level}", True, TEXT_SECONDARY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 540))

        # Credits
        credit = self.font_tiny.render("SuperGameApp - Built with Python + Pygame", True, (80, 80, 100))
        self.screen.blit(credit, (SCREEN_WIDTH // 2 - credit.get_width() // 2, SCREEN_HEIGHT - 40))

        return play_btn

    def run(self):
        running = True
        next_btn = None
        replay_btn = None
        play_btn = None

        while running:
            dt = self.clock.tick(FPS) / 1000.0
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "playing":
                            self.state = "menu"
                        elif self.state == "menu":
                            running = False
                    if event.key == pygame.K_u and self.state == "playing":
                        self.undo()
                    if event.key == pygame.K_r and self.state == "playing":
                        self.load_level(self.level)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "menu":
                        if play_btn and play_btn.collidepoint(mouse):
                            self.load_level(self.level)
                            self.state = "playing"

                    elif self.state == "playing" and not self.pour_anim.active:
                        # Check buttons
                        if self.buttons["undo"].clicked(mouse):
                            self.undo()
                        elif self.buttons["restart"].clicked(mouse):
                            self.load_level(self.level)
                        elif self.buttons["menu"].clicked(mouse):
                            self.state = "menu"
                        else:
                            # Check tubes
                            clicked = self.get_tube_at_pos(*mouse)
                            if clicked >= 0:
                                if self.selected == -1:
                                    if self.tubes[clicked]:
                                        self.selected = clicked
                                elif self.selected == clicked:
                                    self.selected = -1
                                else:
                                    if self.try_pour(self.selected, clicked):
                                        self.selected = -1
                                    else:
                                        # Can't pour, select new tube
                                        if self.tubes[clicked]:
                                            self.selected = clicked
                                        else:
                                            self.selected = -1

                    elif self.state == "complete":
                        if next_btn and next_btn.collidepoint(mouse):
                            self.coins += self.calculate_stars() * 10
                            self.load_level(self.level + 1)
                        elif replay_btn and replay_btn.collidepoint(mouse):
                            self.load_level(self.level)

            # Update animation
            if self.pour_anim.active:
                done = self.pour_anim.update(dt, self.tube_positions)
                if done:
                    if self.check_win():
                        self.state = "complete"
                        self.coins += self.calculate_stars() * 10
                        self.spawn_celebration()

            # Update particles
            self.particles = [p for p in self.particles if p.update(dt)]

            # Update button hover
            for btn in self.buttons.values():
                btn.update(mouse)

            # ─── DRAW ───
            if self.state == "menu":
                play_btn = self.draw_menu()

            elif self.state in ("playing", "complete"):
                self.draw_gradient_bg()
                self.draw_top_bar()

                # Difficulty label
                colors, _, _ = get_difficulty(self.level)
                diff_names = {3: "Easy", 4: "Normal", 5: "Medium", 6: "Hard", 7: "Expert", 8: "Master", 9: "Insane"}
                diff = diff_names.get(colors, "???")
                diff_text = self.font_tiny.render(diff, True, TEXT_SECONDARY)
                self.screen.blit(diff_text, (SCREEN_WIDTH // 2 - diff_text.get_width() // 2, 82))

                # Draw tubes
                for i, tube in enumerate(self.tubes):
                    self.draw_tube(i, tube, self.tube_positions[i])

                # Draw buttons
                for btn in self.buttons.values():
                    btn.draw(self.screen)

                # Keyboard hints
                hint = self.font_tiny.render("U = Undo  |  R = Restart  |  ESC = Menu", True, (60, 60, 80))
                self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 25))

                # Particles
                for p in self.particles:
                    p.draw(self.screen)

                # Level complete overlay
                if self.state == "complete":
                    next_btn, replay_btn = self.draw_level_complete()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ─────────────────────────── MAIN ───────────────────────────

if __name__ == "__main__":
    game = WaterSortGame()
    game.run()
