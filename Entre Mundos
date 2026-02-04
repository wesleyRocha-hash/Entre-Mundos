import pygame
import random
import os
import math
import asyncio
from datetime import datetime

# =====================================================================
# CONFIGURAÇÕES E CONSTANTES
# =====================================================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720 
FPS = 60
TITLE = "Entre Mundos: RPG Combat Edition"

# Cores
BLACK = (10, 10, 15); WHITE = (240, 240, 240); RED = (255, 60, 60)
GREEN = (60, 255, 60); BLUE = (60, 160, 255); YELLOW = (255, 230, 0)
SKY_COLOR = (15, 15, 30); DARK_GRAY = (40, 40, 50)

# Atributos de Classes RPG
CLASSES = {
    'Guerreiro': {
        'hp': 200, 'speed': 4.2, 'jump': -16, 'color': RED, 
        'shoot_cooldown': 600, 'damage': 50,
        'desc': "Especial: Salto pesado e muita resistência."
    },
    'Explorador': {
        'hp': 120, 'speed': 6.8, 'jump': -18, 'color': GREEN, 
        'shoot_cooldown': 500, 'damage': 30,
        'desc': "Especial: Velocidade e agilidade extrema."
    },
    'Mago': {
        'hp': 90, 'speed': 4.8, 'jump': -15, 'color': BLUE, 
        'shoot_cooldown': 250, 'damage': 40,
        'desc': "Especial: Disparos de energia ultra-rápidos."
    }
}

# =====================================================================
# SISTEMA VISUAL (PARALLAX E PARTÍCULAS)
# =====================================================================

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(4, 8)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(random.uniform(-3, 3), random.uniform(-5, 2))
        self.life = 255

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.life -= 10
        if self.life <= 0: self.kill()
        else: self.image.set_alpha(self.life)

class BackgroundLayer:
    def __init__(self, speed_factor, color, type='stars'):
        self.speed_factor = speed_factor
        self.color = color
        self.type = type
        self.elements = []
        if type == 'stars':
            for _ in range(80): self.elements.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 3)])
        elif type == 'mountains':
            for i in range(0, SCREEN_WIDTH + 400, 250): self.elements.append([i, SCREEN_HEIGHT, random.randint(150, 350)])

    def draw(self, surface, scroll):
        if self.type == 'stars':
            for s in self.elements:
                x = (s[0] - scroll * self.speed_factor) % SCREEN_WIDTH
                pygame.draw.circle(surface, self.color, (int(x), s[1]), s[2])
        elif self.type == 'mountains':
            for m in self.elements:
                x = (m[0] - scroll * self.speed_factor) % (SCREEN_WIDTH + 250)
                pts = [(x - 200, m[1]), (x, m[1] - m[2]), (x + 200, m[1])]
                pygame.draw.polygon(surface, self.color, pts)

# =====================================================================
# OBJETOS DE COMBATE
# =====================================================================

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, color, damage):
        super().__init__()
        self.image = pygame.Surface((15, 6))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = 12 * direction
        self.damage = damage

    def update(self):
        self.rect.x += self.vel
        if self.rect.right < -500 or self.rect.left > SCREEN_WIDTH + 5000:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, plat_rect):
        super().__init__()
        self.image = pygame.Surface((40, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (180, 50, 50), (0, 0, 40, 30))
        pygame.draw.circle(self.image, WHITE, (10, 10), 4) # Olho
        pygame.draw.circle(self.image, WHITE, (30, 10), 4) # Olho
        self.rect = self.image.get_rect(midbottom=(x, y))
        
        self.plat_rect = plat_rect
        self.speed = random.uniform(1.5, 3.0)
        self.direction = 1
        self.health = 40

    def update(self, scroll):
        self.rect.x += self.speed * self.direction
        
        # Inverter ao chegar na borda da plataforma
        if self.rect.right > self.plat_rect.right or self.rect.left < self.plat_rect.left:
            self.direction *= -1

# =====================================================================
# JOGADOR E LÓGICA PRINCIPAL
# =====================================================================

class Player(pygame.sprite.Sprite):
    def __init__(self, game, char_class):
        super().__init__()
        self.game = game
        self.stats = CLASSES[char_class]
        self.char_class = char_class
        
        self.w, self.h = 44, 64
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        
        self.pos = pygame.math.Vector2(200, SCREEN_HEIGHT - 120)
        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.facing = 1 # 1 para direita, -1 para esquerda
        
        self.health = self.stats['hp']
        self.max_health = self.health
        self.last_shot = 0
        self.invincible_until = 0
        
        self.draw_player()

    def draw_player(self):
        self.image.fill((0, 0, 0, 0))
        c = self.stats['color']
        pygame.draw.rect(self.image, c, (8, 18, 28, 40), border_radius=6)
        pygame.draw.rect(self.image, WHITE, (10, 2, 24, 22), border_radius=10)
        pygame.draw.rect(self.image, BLACK, (14, 8, 16, 6))

    def jump(self):
        if self.on_ground:
            self.vel.y = self.stats['jump']
            self.on_ground = False

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.stats['shoot_cooldown']:
            p = Projectile(self.rect.centerx, self.rect.centery, self.facing, self.stats['color'], self.stats['damage'])
            self.game.projectiles.add(p)
            self.game.all_sprites.add(p)
            self.last_shot = now

    def update(self):
        self.vel.y += 0.65
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = -self.stats['speed']
            self.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = self.stats['speed']
            self.facing = 1
        else:
            self.vel.x *= 0.8
            
        self.pos.x += self.vel.x
        self.rect.x = self.pos.x
        self.game.check_collisions(self, 'x')
        
        self.pos.y += self.vel.y
        self.rect.y = self.pos.y
        self.game.check_collisions(self, 'y')

# =====================================================================
# GAME ENGINE
# =====================================================================

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "MENU"
        self.selected_class = "Guerreiro"
        self.world_scroll = 0
        self.score = 0
        
        self.parallax = [BackgroundLayer(0.1, (50, 50, 70), 'stars'), BackgroundLayer(0.4, (20, 20, 35), 'mountains')]
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        
        self.font_title = pygame.font.SysFont("Verdana", 48, bold=True)
        self.font_ui = pygame.font.SysFont("Verdana", 22, bold=True)

    def generate_level(self):
        self.all_sprites.empty(); self.platforms.empty(); self.enemies.empty(); self.projectiles.empty(); self.particles.empty()
        self.score = 0; self.world_scroll = 0
        self.player = Player(self, self.selected_class)
        self.all_sprites.add(self.player)
        
        # Solo inicial
        start_plat = Platform(-200, SCREEN_HEIGHT - 60, 1500, 60)
        self.platforms.add(start_plat); self.all_sprites.add(start_plat)
        
        # Gerar percurso
        for i in range(1, 40):
            w = random.randint(200, 500)
            x = i * 600 + random.randint(-100, 100)
            y = random.randint(300, 550)
            p = Platform(x, y, w, 35)
            self.platforms.add(p); self.all_sprites.add(p)
            
            # Chance de inimigo na plataforma
            if random.random() < 0.6:
                e = Enemy(x + w//2, y, p.rect)
                self.enemies.add(e); self.all_sprites.add(e)

    def check_collisions(self, sprite, axis):
        hits = pygame.sprite.spritecollide(sprite, self.platforms, False)
        if axis == 'x':
            for hit in hits:
                if sprite.vel.x > 0: sprite.rect.right = hit.rect.left
                if sprite.vel.x < 0: sprite.rect.left = hit.rect.right
                sprite.pos.x = sprite.rect.x
        if axis == 'y':
            for hit in hits:
                if sprite.vel.y > 0:
                    sprite.rect.bottom = hit.rect.top
                    sprite.on_ground = True
                    sprite.vel.y = 0
                if sprite.vel.y < 0:
                    sprite.rect.top = hit.rect.bottom
                    sprite.vel.y = 0
                sprite.pos.y = sprite.rect.y
            if not hits: sprite.on_ground = False

    def handle_combat(self):
        # 1. Tiros acertam Inimigos
        hits = pygame.sprite.groupcollide(self.enemies, self.projectiles, False, True)
        for enemy, projs in hits.items():
            for p in projs: enemy.health -= p.damage
            if enemy.health <= 0:
                self.score += 100
                self.spawn_explosion(enemy.rect.center, RED)
                enemy.kill()

        # 2. Jogador pula em Inimigos (Stomp)
        stomp_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for enemy in stomp_hits:
            if self.player.vel.y > 0 and self.player.rect.bottom < enemy.rect.centery + 10:
                damage = 40 if self.player.char_class != 'Guerreiro' else 80
                enemy.health -= damage
                self.player.vel.y = -12 # Pulo de volta
                if enemy.health <= 0:
                    self.score += 150
                    self.spawn_explosion(enemy.rect.center, RED)
                    enemy.kill()
            else:
                # Dano no jogador
                now = pygame.time.get_ticks()
                if now > self.player.invincible_until:
                    self.player.health -= 25
                    self.player.invincible_until = now + 1500
                    self.player.vel.y = -8
                    self.spawn_explosion(self.player.rect.center, WHITE)

    def spawn_explosion(self, pos, color):
        for _ in range(15):
            self.particles.add(Particle(pos[0], pos[1], color))

    def draw_hud(self):
        # Barra de HP
        pygame.draw.rect(self.screen, (60, 0, 0), (20, 20, 300, 30), border_radius=6)
        pct = max(0, self.player.health / self.player.max_health)
        pygame.draw.rect(self.screen, RED, (20, 20, 300 * pct, 30), border_radius=6)
        
        t_score = self.font_ui.render(f"Score: {self.score}", True, YELLOW)
        self.screen.blit(t_score, (20, 60))
        t_class = self.font_ui.render(f"Classe: {self.player.char_class}", True, WHITE)
        self.screen.blit(t_class, (20, 90))

    async def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                
                if self.state == "MENU":
                    if event.type == pygame.KEYDOWN:
                        k = list(CLASSES.keys())
                        idx = k.index(self.selected_class)
                        if event.key == pygame.K_UP: self.selected_class = k[(idx - 1) % len(k)]
                        if event.key == pygame.K_DOWN: self.selected_class = k[(idx + 1) % len(k)]
                        if event.key == pygame.K_SPACE: self.generate_level(); self.state = "PLAYING"
                
                elif self.state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_SPACE, pygame.K_w, pygame.K_UP]: self.player.jump()
                        if event.key == pygame.K_e or event.key == pygame.K_k: self.player.shoot()

            # LÓGICA
            if self.state == "PLAYING":
                self.player.update()
                self.enemies.update(self.world_scroll)
                self.projectiles.update()
                self.particles.update()
                self.handle_combat()
                
                # Câmera
                target = self.player.pos.x - SCREEN_WIDTH // 3
                self.world_scroll += (target - self.world_scroll) * 0.1
                
                if self.player.health <= 0: self.state = "MENU"

            # DESENHO
            self.screen.fill(SKY_COLOR)
            for layer in self.parallax: layer.draw(self.screen, self.world_scroll)
            
            if self.state == "MENU":
                self.draw_menu()
            else:
                # Renderizar tudo com scroll
                for grp in [self.platforms, self.enemies, self.projectiles, [self.player]]:
                    for sprite in grp:
                        self.screen.blit(sprite.image, (sprite.rect.x - self.world_scroll, sprite.rect.y))
                for p in self.particles:
                    self.screen.blit(p.image, (p.rect.x - self.world_scroll, p.rect.y))
                self.draw_hud()

            pygame.display.flip()
            await asyncio.sleep(0)
            self.clock.tick(FPS)

    def draw_menu(self):
        self.draw_text("ENTRE MUNDOS RPG", self.font_title, ORANGE, SCREEN_WIDTH//2, 100)
        y = 220
        for name in CLASSES:
            color = CLASSES[name]['color'] if self.selected_class == name else (70, 70, 80)
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 60)
            pygame.draw.rect(self.screen, color, rect, border_radius=15)
            self.draw_text(name, self.font_ui, WHITE, SCREEN_WIDTH//2, y + 30)
            if self.selected_class == name:
                self.draw_text(CLASSES[name]['desc'], self.font_ui, YELLOW, SCREEN_WIDTH//2, y + 85)
            y += 115
        self.draw_text("Pressione ESPAÇO para Lutar | E para Atirar", self.font_ui, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)

    def draw_text(self, text, font, color, x, y):
        img = font.render(text, True, color)
        self.screen.blit(img, img.get_rect(center=(x, y)))

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((60, 60, 75))
        pygame.draw.rect(self.image, (80, 80, 100), (0, 0, w, 5)) # Topo
        self.rect = self.image.get_rect(topleft=(x, y))

if __name__ == "__main__":
    g = Game()
    asyncio.run(g.run())
