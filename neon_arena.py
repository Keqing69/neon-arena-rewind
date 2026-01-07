import pygame
import random
import math

# ==========================================================
# FRONTEND / ASSET CONFIG AREA
# ==========================================================
# Hier kannst du alles visuelle & Audio anpassen:
# - Farben
# - Radii
# - Sprite-Pfade (PNG, etc.)
# - Sound-Pfade (WAV/OGG)
# Wenn du keine Dateien nutzen willst -> einfach None lassen.

PLAYER_CONFIG = {
    "color": (80, 200, 255),
    "radius": 18,
    "sprite_path": "Frontend_Nico/Ufo_Player.png",
}

ENEMY_CONFIG = {
    "color": (255, 80, 120),
    "radius": 16,
    "sprite_path": "Frontend_Nico/Ufo_Enemy.png",          # z.B. "assets/enemy.png"
}

POWERUP_CONFIG = {
    "color": (180, 255, 180),
    "radius": 10,
    "sprite_path": None,          # z.B. "assets/powerup_time.png"
}

BACKGROUND_COLOR = (15, 15, 25)
BULLET_COLOR = (255, 230, 120)

SOUND_CONFIG = {
    "shoot": "Frontend_Nico/laser.mp3",         # z.B. "assets/shoot.wav"
    "powerup": None,       # z.B. "assets/powerup.wav"
    "enemy_kill": None,    # z.B. "assets/enemy_kill.wav"
    "rewind_start": "Frontend_Nico/zeitanker.mp3",  # z.B. "assets/rewind_start.wav"
}

# Glow-Effekt um den Player während der Rewind-Animation
ENABLE_REWIND_GLOW = True

# ==========================================================
# AB HIER: GAME LOGIC (nur anfassen, wenn du Bock auf Schmerz hast)
# ==========================================================

# Bildschirmkonstanten
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Spieler
PLAYER_SPEED = 5
PLAYER_RADIUS = PLAYER_CONFIG["radius"]
PLAYER_MAX_HP = 5

# Projektile
BULLET_SPEED = 10
BULLET_RADIUS = 5
BULLET_COOLDOWN = 200  # ms

# Gegner
ENEMY_SPEED_MIN = 1.5
ENEMY_SPEED_MAX = 3.0
ENEMY_RADIUS = ENEMY_CONFIG["radius"]
ENEMY_SPAWN_INTERVAL = 1200  # ms

# Powerups (Zeit-Rückkehr)
POWERUP_RADIUS = POWERUP_CONFIG["radius"]
POWERUP_SPAWN_INTERVAL = 12000  # alle ~12 Sekunden möglich

REWIND_DURATION_MS = 5000        # 5 Sekunden in die Vergangenheit
REWIND_ANIM_DURATION_MS = 2000   # 2 Sekunden Animation
ABILITY_CHARGE_TIME_MS = 5000    # 5 Sekunden nach Pickup, bevor E nutzbar ist


class AssetBundle:
    def __init__(self):
        self.player_sprite = None
        self.enemy_sprite = None
        self.powerup_sprite = None
        self.sounds = {}
        self.sound_enabled = False


def load_image(path, scale_radius=None):
    if not path:
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale_radius is not None:
            diameter = scale_radius * 2
            img = pygame.transform.smoothscale(img, (diameter, diameter))
        return img
    except Exception as e:
        print(f"Bild konnte nicht geladen werden ('{path}'): {e}")
        return None


def load_sound(path):
    if not path:
        return None
    try:
        snd = pygame.mixer.Sound(path)
        return snd
    except Exception as e:
        print(f"Sound konnte nicht geladen werden ('{path}'): {e}")
        return None


def init_assets():
    assets = AssetBundle()

    # Mixer initialisieren (für Sounds)
    try:
        pygame.mixer.init()
        assets.sound_enabled = True
    except Exception as e:
        print("Konnte Audio nicht initialisieren, Sounds werden deaktiviert:", e)
        assets.sound_enabled = False

    # Sprites laden
    assets.player_sprite = load_image(PLAYER_CONFIG["sprite_path"], PLAYER_RADIUS)
    assets.enemy_sprite = load_image(ENEMY_CONFIG["sprite_path"], ENEMY_RADIUS)
    assets.powerup_sprite = load_image(POWERUP_CONFIG["sprite_path"], POWERUP_RADIUS)

    # Sounds laden
    if assets.sound_enabled:
        for key, path in SOUND_CONFIG.items():
            assets.sounds[key] = load_sound(path)
    return assets


def play_sound(assets, key):
    if not assets.sound_enabled:
        return
    snd = assets.sounds.get(key)
    if snd is not None:
        snd.play()


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.hp = PLAYER_MAX_HP

    def move(self, keys):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # Richtung normalisieren
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.x += dx * self.speed
            self.y += dy * self.speed

        # Bildschirmgrenzen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))


def draw_player(surf, player, assets, alpha_glow=False):
    if alpha_glow and ENABLE_REWIND_GLOW:
        # Aura-Ringe
        for r in range(player.radius + 8, player.radius, -3):
            color = (
                PLAYER_CONFIG["color"][0],
                PLAYER_CONFIG["color"][1],
                min(255, PLAYER_CONFIG["color"][2] + 40),
            )
            pygame.draw.circle(surf, color, (int(player.x), int(player.y)), r, 1)

    if assets.player_sprite:
        rect = assets.player_sprite.get_rect(center=(int(player.x), int(player.y)))
        surf.blit(assets.player_sprite, rect)
    else:
        pygame.draw.circle(
            surf, PLAYER_CONFIG["color"], (int(player.x), int(player.y)), player.radius
        )


class Bullet:
    def __init__(self, x, y, dir_x, dir_y):
        self.x = x
        self.y = y
        self.radius = BULLET_RADIUS
        length = math.hypot(dir_x, dir_y)
        if length == 0:
            length = 1
        self.vx = dir_x / length * BULLET_SPEED
        self.vy = dir_y / length * BULLET_SPEED

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def off_screen(self):
        return (
            self.x < -self.radius
            or self.x > SCREEN_WIDTH + self.radius
            or self.y < -self.radius
            or self.y > SCREEN_HEIGHT + self.radius
        )

    def draw(self, surf):
        pygame.draw.circle(
            surf, BULLET_COLOR, (int(self.x), int(self.y)), self.radius
        )


class Enemy:
    def __init__(self):
        self.radius = ENEMY_RADIUS
        self.x, self.y = self.random_spawn_pos()
        self.speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

    def random_spawn_pos(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            return random.randint(0, SCREEN_WIDTH), -self.radius * 2
        if side == "bottom":
            return random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + self.radius * 2
        if side == "left":
            return -self.radius * 2, random.randint(0, SCREEN_HEIGHT)
        return SCREEN_WIDTH + self.radius * 2, random.randint(0, SCREEN_HEIGHT)

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        length = math.hypot(dx, dy)
        if length == 0:
            return
        dx /= length
        dy /= length
        self.x += dx * self.speed
        self.y += dy * self.speed

    def collides_with_player(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius

    def collides_with_bullet(self, bullet):
        dist = math.hypot(self.x - bullet.x, self.y - bullet.y)
        return dist < self.radius + bullet.radius


def draw_enemy(surf, enemy, assets):
    if assets.enemy_sprite:
        rect = assets.enemy_sprite.get_rect(center=(int(enemy.x), int(enemy.y)))
        surf.blit(assets.enemy_sprite, rect)
    else:
        pygame.draw.circle(
            surf, ENEMY_CONFIG["color"], (int(enemy.x), int(enemy.y)), enemy.radius
        )


class Powerup:
    def __init__(self):
        self.radius = POWERUP_RADIUS
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = random.randint(self.radius, SCREEN_HEIGHT - self.radius)

    def collides_with_player(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius


def draw_powerup(surf, powerup, assets):
    if assets.powerup_sprite:
        rect = assets.powerup_sprite.get_rect(center=(int(powerup.x), int(powerup.y)))
        surf.blit(assets.powerup_sprite, rect)
    else:
        pygame.draw.circle(
            surf,
            POWERUP_CONFIG["color"],
            (int(powerup.x), int(powerup.y)),
            powerup.radius,
        )


def draw_text_centered(surf, text, font, color, y):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
    surf.blit(surface, rect)


def main():
    print("Starte Neon Arena mit Frontend-Config...")
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Neon Arena")
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("consolas", 22)
        big_font = pygame.font.SysFont("consolas", 40)
    except Exception:
        font = pygame.font.SysFont(None, 22)
        big_font = pygame.font.SysFont(None, 40)

    assets = init_assets()

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    bullets = []
    enemies = []
    powerups = []
    score = 0

    running = True
    game_over = False

    last_bullet_time = 0
    last_spawn_time = 0
    last_powerup_time = 0
    last_mouse_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    # Zeitrückkehr-Ability
    ability_ready = False
    ability_charging = False
    ability_charge_start = 0
    history = []

    rewind_active = False
    rewind_start_time = 0
    rewind_frames = []

    print("Neon Arena läuft. Fenster sollte jetzt sichtbar sein.")

    while running:
        dt = clock.tick(60)
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEMOTION:
                last_mouse_pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game_over and event.key == pygame.K_r:
                    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                    bullets = []
                    enemies = []
                    powerups = []
                    score = 0
                    player.hp = PLAYER_MAX_HP
                    game_over = False
                    ability_ready = False
                    ability_charging = False
                    history = []
                    rewind_active = False
                    rewind_frames = []
                    last_spawn_time = now_ms
                    last_powerup_time = now_ms

                # Rewind aktivieren
                if (
                    not game_over
                    and event.key == pygame.K_e
                    and ability_ready
                    and not rewind_active
                ):
                    target_time = now_ms - REWIND_DURATION_MS
                    window = [h for h in history if target_time <= h[0] <= now_ms]
                    if len(window) >= 2:
                        window.sort(key=lambda h: h[0])
                        rewind_frames = [(x, y, hp) for (_, x, y, hp) in window]
                        rewind_active = True
                        rewind_start_time = now_ms
                        ability_ready = False
                        play_sound(assets, "rewind_start")
                        print(f"Zeitrückkehr-Animation gestartet: {len(rewind_frames)} Frames")
                    else:
                        print("Zeitrückkehr: Noch nicht genug Historie, Ability bleibt bereit.")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_over and not rewind_active:
                    if now_ms - last_bullet_time >= BULLET_COOLDOWN:
                        dir_x = last_mouse_pos[0] - player.x
                        dir_y = last_mouse_pos[1] - player.y
                        bullets.append(Bullet(player.x, player.y, dir_x, dir_y))
                        last_bullet_time = now_ms
                        play_sound(assets, "shoot")

        keys = pygame.key.get_pressed()

        if not game_over:
            if not rewind_active:
                # Normaler Zustand

                # Ability-Aufladung
                if ability_charging and not ability_ready:
                    elapsed_charge = now_ms - ability_charge_start
                    if elapsed_charge >= ABILITY_CHARGE_TIME_MS:
                        ability_ready = True
                        ability_charging = False
                        print("Zeitrückkehr-Ability ist jetzt einsatzbereit.")

                # Space-Shooting
                if keys[pygame.K_SPACE]:
                    if now_ms - last_bullet_time >= BULLET_COOLDOWN:
                        dir_x = last_mouse_pos[0] - player.x
                        dir_y = last_mouse_pos[1] - player.y
                        bullets.append(Bullet(player.x, player.y, dir_x, dir_y))
                        last_bullet_time = now_ms
                        play_sound(assets, "shoot")

                # Gegner spawnen
                if now_ms - last_spawn_time >= ENEMY_SPAWN_INTERVAL:
                    enemies.append(Enemy())
                    last_spawn_time = now_ms

                # Powerup-Spawns nur, wenn keine Ability aktiv/ladend ist
                if (not ability_ready) and (not ability_charging) and len(powerups) == 0:
                    if now_ms - last_powerup_time >= POWERUP_SPAWN_INTERVAL:
                        if random.random() < 0.7:
                            powerups.append(Powerup())
                            last_powerup_time = now_ms
                        else:
                            last_powerup_time = now_ms

                # Player bewegen
                player.move(keys)

                # Bullets updaten
                for b in bullets:
                    b.update()
                bullets = [b for b in bullets if not b.off_screen()]

                # Gegner updaten
                for e in enemies:
                    e.update(player)

                # Bullet-Enemy-Kollision
                for e in enemies[:]:
                    for b in bullets[:]:
                        if e.collides_with_bullet(b):
                            enemies.remove(e)
                            bullets.remove(b)
                            score += 10
                            play_sound(assets, "enemy_kill")
                            break

                # Enemy-Player-Kollision
                for e in enemies[:]:
                    if e.collides_with_player(player):
                        enemies.remove(e)
                        player.hp -= 1
                        if player.hp <= 0:
                            game_over = True
                            break

                # Player-Powerup-Kollision
                for p in powerups[:]:
                    if p.collides_with_player(player):
                        powerups.remove(p)
                        ability_ready = False
                        ability_charging = True
                        ability_charge_start = now_ms
                        history = []
                        play_sound(assets, "powerup")
                        print("Zeitrückkehr-Powerup eingesammelt. Ability lädt jetzt.")

                # Historie für Rewind
                history.append((now_ms, player.x, player.y, player.hp))
                cutoff = now_ms - (REWIND_DURATION_MS + 2000)
                while history and history[0][0] < cutoff:
                    history.pop(0)

            else:
                # Rewind-Animation aktiv
                elapsed = now_ms - rewind_start_time
                t = min(1.0, elapsed / REWIND_ANIM_DURATION_MS)

                if rewind_frames:
                    n = len(rewind_frames)
                    idx = int((1.0 - t) * (n - 1))
                    idx = max(0, min(n - 1, idx))
                    x, y, hp = rewind_frames[idx]
                    player.x = x
                    player.y = y

                # Gegner/Bullets bewegen, aber Schaden egal (invuln)
                for b in bullets:
                    b.update()
                bullets = [b for b in bullets if not b.off_screen()]
                for e in enemies:
                    e.update(player)

                if elapsed >= REWIND_ANIM_DURATION_MS:
                    if rewind_frames:
                        x0, y0, hp0 = rewind_frames[0]
                        player.x = x0
                        player.y = y0
                        player.hp = hp0
                    rewind_active = False
                    rewind_frames = []
                    history = [(now_ms, player.x, player.y, player.hp)]
                    print("Zeitrückkehr abgeschlossen.")

        # ================== RENDERING ==================
        screen.fill(BACKGROUND_COLOR)

        for b in bullets:
            b.draw(screen)
        for e in enemies:
            draw_enemy(screen, e, assets)

        for p in powerups:
            draw_powerup(screen, p, assets)

        draw_player(screen, player, assets, alpha_glow=rewind_active)

        # HUD
        hp_text = font.render(f"HP: {player.hp}/{PLAYER_MAX_HP}", True, (120, 255, 120))
        score_text = font.render(f"Score: {score}", True, (230, 230, 230))
        info_text = font.render("WASD bewegen, Maus zielen, Linksklick/SPACE schießen", True, (230, 230, 230))

        screen.blit(hp_text, (10, 10))
        screen.blit(score_text, (10, 40))
        screen.blit(info_text, (10, SCREEN_HEIGHT - 30))

        # Ability-Status
        if ability_charging and not ability_ready and not rewind_active:
            elapsed_charge = now_ms - ability_charge_start
            remaining_ms = max(0, ABILITY_CHARGE_TIME_MS - elapsed_charge)
            remaining_sec = remaining_ms / 1000.0
            ability_text = font.render(
                f"Ability lädt: {remaining_sec:0.1f}s",
                True,
                (180, 200, 255),
            )
            screen.blit(ability_text, (10, 70))
        elif ability_ready and not rewind_active:
            ability_text = font.render(
                "Ability bereit: [E] Zeitrückkehr (5s zurück)",
                True,
                (180, 200, 255),
            )
            screen.blit(ability_text, (10, 70))
        elif rewind_active:
            rewind_text = font.render("ZEITRÜCKKEHR AKTIV", True, (200, 220, 255))
            screen.blit(rewind_text, (10, 70))

        if game_over:
            draw_text_centered(screen, "GAME OVER", big_font, (230, 230, 230), SCREEN_HEIGHT // 2 - 20)
            draw_text_centered(screen, f"Score: {score}", font, (230, 230, 230), SCREEN_HEIGHT // 2 + 20)
            draw_text_centered(
                screen,
                "Drück R zum Restart oder ESC zum Beenden",
                font,
                (230, 230, 230),
                SCREEN_HEIGHT // 2 + 50,
            )

        pygame.display.flip()

    pygame.quit()
    print("Neon Arena wurde beendet.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fehler im Spiel:", e)
        input("Enter drücken zum Schließen...")
