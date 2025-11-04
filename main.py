import pygame
import random
import os
from datetime import datetime
import math
import json
import asyncio # <--- ADICIONADO PARA PYGBAG

# ----------------- Constantes de Configuração -----------------
WIDTH, HEIGHT = 1700, 1000
FPS = 60
TITLE = "Entre Mundos"

# --- Constantes de Gameplay ---
PLAYER_ACC = 0.5 
PLAYER_FRICTION = -0.15 
PLAYER_SLIPPERY_FRICTION = -0.04 
PLAYER_JUMP = -17 
PLAYER_SPEED = 4.5
PLAYER_DASH_SPEED = 14
STOMP_TOLERANCE = 15
COYOTE_TIME = 100 # ms
JUMP_BUFFER = 100 # ms
DASH_TIME = 150 # ms
SHOCKWAVE_RADIUS = 150
SHOCKWAVE_FORCE = 18
MAGNET_RADIUS = 200
INVINCIBILITY_TIME = 1000 # 1 segundo
ENEMY_DAMAGE = 25
SPIKE_DAMAGE = 40
BOSS_STOMP_DAMAGE = 20
EXPLOSION_DAMAGE = 60
HEALTH_PACK_AMOUNT = 25
EXPLODE_FUSE_TIME = 3000
GROUND_POUND_FORCE = 2.5
GROUND_POUND_DAMAGE = 35

# ----------------- Cores -----------------
BLACK = (0, 0, 0); WHITE = (255, 255, 255); RED = (255, 0, 0); GREEN = (0, 255, 0); BLUE = (0, 0, 255)
GRAY = (100, 100, 100); DARKGRAY = (50, 50, 50); YELLOW = (255, 255, 0); ORANGE = (255, 165, 0)
OFF_WHITE = (220, 220, 220)

# --- Cor do Personagem ---
PLAYER_BODY_COLOR = (0, 150, 255)  # Tronco Azul
PLAYER_LEG_COLOR = (150, 111, 214) # Pernas Roxas
PLAYER_HEAD_COLOR = (255, 255, 100) # Visor Amarelo
PLAYER_ARM_COLOR = (230, 230, 230) # Braços Brancos (para atirar)

PLAYER_ACCENT_COLOR = (0, 150, 255)
PARTICLE_DUST_COLOR = (130, 100, 100)
PARTICLE_COIN_COLOR = YELLOW
BUTTON_COLOR = GRAY
BUTTON_HOVER_COLOR = DARKGRAY
PAUSE_OVERLAY_COLOR = (0, 0, 0, 150)
HEALTH_BAR_GREEN = (40, 200, 60)
HEALTH_BAR_RED = (180, 40, 40)
VINE_COLOR = (34, 139, 34)
CRYSTAL_COLOR = (180, 180, 255)
PURPLE_CRYSTAL = (150, 111, 214)
ELECTRIC_BLUE = (100, 180, 255)
ELECTRIC_YELLOW = (255, 255, 100)

# --- Cores dos Dragões (Apenas para o Chefe) ---
DRAGON_STORM_BODY = (40, 50, 100)
DRAGON_STORM_WING_PRIMARY = (200, 150, 50)
DRAGON_STORM_WING_SECONDARY = (20, 100, 150)


# --- Cores dos Temas ---
THEME_FOREST = {'bg': (10, 20, 30), 'platform_top': (34, 139, 34), 'platform_bottom': (139, 69, 19), 'slippery': (150, 200, 255)}
THEME_CAVE = {'bg': (20, 10, 30), 'platform_top': (80, 80, 150), 'platform_bottom': (40, 40, 80), 'slippery': (150, 200, 255)}
THEME_VOLCANO = {'bg': (40, 10, 0), 'platform_top': (255, 100, 0), 'platform_bottom': (50, 20, 20), 'slippery': (200, 100, 100)}
THEME_ELECTRIC = {'bg': (10, 0, 20), 'platform_top': (100, 50, 150), 'platform_bottom': (30, 0, 50), 'slippery': ELECTRIC_BLUE}

# =====================================================================
# ----------------- CLASSES DOS SPRITES -------------------------------
# =====================================================================

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.w, self.h = 40, 60 # Novo tamanho
        
        self.pos = pygame.math.Vector2(WIDTH // 4, HEIGHT - 100)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, PLAYER_ACC)

        self.on_ground = False
        self.on_slippery = False
        self.direction = 'right'
        self.status = 'idle'
        self.score = 0
        self.lives = 3
        self.max_health = 100
        self.health = self.max_health
        
        self.coyote_timer = 0
        self.jump_buffer_timer = 0
        self.last_on_ground_time = 0
        self.is_dashing = False
        self.dash_end_time = 0
        self.is_ground_pounding = False
        self.score_multiplier = 1
        self.invincible = False
        self.invincible_timer = 0
        
        self.is_shooting = False
        self.shoot_timer = 0
        
        self.powerups = {
            'pulo_duplo': False, 'super_pulo': False, 'dash': False,
            'tiro_forte': False, 'onda_de_choque': False, 'escudo': False,
            'ima_de_moedas': False, 'pontos_em_dobro': False
        }
        self.can_double_jump = False
        
        self.walk_frame = 0.0
        self.last_update = pygame.time.get_ticks()
        
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        self.hitbox = pygame.Rect(0, 0, 24, 50)
        self.hitbox.center = self.rect.center

    def _update_sprite_image(self):
        self.image.fill((0, 0, 0, 0))
        now = pygame.time.get_ticks()
        status = self.get_status() # idle, walk, jump, ground_pound
        
        self.walk_frame += 0.25 
        
        bob = math.sin(now * 0.005) * 2 
        body_w = 20
        body_h = 22
        body_x = (self.w - body_w) // 2
        body_y = 20 + bob
        
        head_w = 16
        head_h = 16
        head_x = (self.w - head_w) // 2
        head_y = body_y - head_h + 5 
        
        leg_w = 8
        leg_h = 20
        hip_y = body_y + body_h - 5
        leg_l_x_base = self.w // 2 - 9
        leg_r_x_base = self.w // 2 + 1
        leg_y_base = hip_y # <-- CORREÇÃO: Mudei de 'leg_y' para 'leg_y_base'

        if status == 'walk':
            anim_cycle = math.sin(self.walk_frame)
            leg_l_x = leg_l_x_base + (anim_cycle * 6)
            leg_l_y = leg_y_base - (anim_cycle * 4 if anim_cycle > 0 else 0) # Perna "da frente" sobe
            leg_r_x = leg_r_x_base - (anim_cycle * 6)
            leg_r_y = leg_y_base - (-anim_cycle * 4 if anim_cycle < 0 else 0) # Perna "da frente" sobe
        elif status == 'jump' or status == 'ground_pound':
            leg_l_x = leg_l_x_base + 2
            leg_r_x = leg_r_x_base - 2
            leg_l_y = leg_y_base - 5
            leg_r_y = leg_y_base - 5
        elif status == 'dash':
            body_y = 25
            head_y = 25
            leg_l_x = leg_l_x_base - 10
            leg_r_x = leg_r_x_base - 10
            leg_l_y = leg_y_base
            leg_r_y = leg_y_base
        else: # Idle
            leg_l_x = leg_l_x_base
            leg_r_x = leg_r_x_base
            leg_l_y = leg_y_base
            leg_r_y = leg_y_base
        
        if status == 'dash':
            pygame.draw.rect(self.image, PLAYER_BODY_COLOR, (body_x - 10, body_y, body_h, body_w), border_radius=3)
            pygame.draw.rect(self.image, PLAYER_HEAD_COLOR, (body_x + body_h - 10, head_y, head_h, head_w), border_radius=3)
            pygame.draw.rect(self.image, PLAYER_LEG_COLOR, (leg_l_x, leg_l_y - 3, leg_h, leg_w), border_radius=2)
            pygame.draw.rect(self.image, PLAYER_LEG_COLOR, (leg_r_x, leg_r_y + 3, leg_h, leg_w), border_radius=2)
            pygame.draw.line(self.image, PLAYER_ARM_COLOR, (body_x + body_h - 5, body_y + 10), (body_x + body_h + 10, body_y + 10), 6)
        else:
            pygame.draw.rect(self.image, PLAYER_LEG_COLOR, (leg_l_x, leg_l_y, leg_w, leg_h), border_radius=2)
            pygame.draw.rect(self.image, PLAYER_LEG_COLOR, (leg_r_x, leg_r_y, leg_w, leg_h), border_radius=2)
            pygame.draw.rect(self.image, PLAYER_BODY_COLOR, (body_x, body_y, body_w, body_h), border_radius=3) 
            pygame.draw.rect(self.image, PLAYER_HEAD_COLOR, (head_x, head_y, head_w, head_h), border_radius=3)

        if self.is_shooting and status != 'dash':
            arm_length = 15
            arm_width = 6
            
            mouse_pos = pygame.mouse.get_pos()
            dx = mouse_pos[0] - (self.rect.centerx)
            dy = mouse_pos[1] - (self.rect.centery - 5) 
            aim_angle_rad = math.atan2(dy, dx)
            
            arm_start_pos = (self.w // 2, body_y + 5)
            arm_end_pos = (arm_start_pos[0] + math.cos(aim_angle_rad) * arm_length,
                           arm_start_pos[1] + math.sin(aim_angle_rad) * arm_length)
                           
            pygame.draw.line(self.image, PLAYER_ARM_COLOR, arm_start_pos, arm_end_pos, arm_width)
            
            gun_start = arm_end_pos
            gun_end = (gun_start[0] + math.cos(aim_angle_rad) * 8,
                       gun_start[1] + math.sin(aim_angle_rad) * 8)
            pygame.draw.line(self.image, DARKGRAY, gun_start, gun_end, arm_width)

        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)
        
        if self.invincible:
            if pygame.time.get_ticks() % 200 < 100:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)
        
    def jump(self):
        self.is_ground_pounding = False
        self.vel.y = PLAYER_JUMP * 1.5 if self.powerups['super_pulo'] else PLAYER_JUMP

    def short_jump(self):
        if self.vel.y < 0: self.vel.y *= 0.5

    def ground_pound(self):
        if not self.on_ground and not self.is_ground_pounding:
            self.is_ground_pounding = True
            self.vel.y, self.vel.x = 0, 0

    def dash(self):
        if self.powerups['dash'] and not self.is_dashing:
            self.is_dashing = True; self.dash_end_time = pygame.time.get_ticks() + DASH_TIME; self.vel.y = 0

    def shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        is_strong = self.powerups['tiro_forte']
        
        shot_origin = pygame.math.Vector2(self.rect.centerx, self.rect.centery - 5)
        
        p = Projectile(self.game, shot_origin, mouse_pos, strong=is_strong)
        self.game.all_sprites.add(p)
        self.game.projectiles.add(p)
        
        self.is_shooting = True
        self.shoot_timer = pygame.time.get_ticks() + 200 # Mostra braço por 200ms
    
    def attack(self):
        pass

    def activate_powerup(self, type):
        if type == 'vida_extra': self.lives += 1
        elif type == 'kit_medico': self.add_health(HEALTH_PACK_AMOUNT)
        elif type in self.powerups:
            self.powerups[type] = True
            if type == 'pontos_em_dobro': self.score_multiplier = 2
    
    def add_health(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def reset_powerups(self):
        for key in self.powerups: self.powerups[key] = False
        self.score_multiplier = 1
        
    def take_damage(self, amount):
        if self.invincible: return
        if self.powerups['escudo']:
            self.powerups['escudo'] = False
            self.game.create_particles(self.rect.center, (0, 150, 255), 20)
        else: self.health -= amount
        self.game.screen_shake = 5
        if self.health <= 0:
            self.health = 0; self.game.player_death()
        else: 
            self.invincible = True; self.invincible_timer = pygame.time.get_ticks() + INVINCIBILITY_TIME
            
    def knockback(self, enemy):
        self.vel.y = -5; self.vel.x = -8 if enemy.rect.centerx > self.rect.centerx else 8

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        was_on_ground = self.on_ground

        if self.invincible and now > self.invincible_timer: self.invincible = False
        if self.is_shooting and now > self.shoot_timer: self.is_shooting = False
        
        if not self.is_ground_pounding:
            friction = PLAYER_SLIPPERY_FRICTION if self.on_slippery else PLAYER_FRICTION
            self.acc = pygame.math.Vector2(0, PLAYER_ACC)
            if self.is_dashing:
                if now % 20 < self.game.clock.get_time(): 
                    self.game.create_particles(self.rect.center, PLAYER_ACCENT_COLOR, 1)
                dash_dir = 1 if self.direction == 'right' else -1
                self.vel.x = PLAYER_DASH_SPEED * dash_dir
                if now > self.dash_end_time: self.is_dashing = False
            else:
                self.acc.x = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
                    self.acc.x = -PLAYER_ACC * 2
                    self.direction = 'left'
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
                    self.acc.x = PLAYER_ACC * 2
                    self.direction = 'right'

                self.vel.x += self.acc.x
                self.vel.x *= (1 + friction)
                if abs(self.vel.x) < 0.5: self.vel.x = 0
                self.vel.x = max(-PLAYER_SPEED, min(PLAYER_SPEED, self.vel.x))
            
            if self.jump_buffer_timer > now and (self.on_ground or self.coyote_timer > now):
                self.jump(); self.jump_buffer_timer = 0; self.on_ground = False
            
            if not self.is_dashing: self.vel.y += self.acc.y
        else:
            self.vel.y += GROUND_POUND_FORCE

        self.pos.x += self.vel.x
        self.hitbox.centerx = self.pos.x
        self.check_horizontal_collisions()

        self.pos.y += self.vel.y
        self.hitbox.centery = self.pos.y
        self.check_vertical_collisions()

        self.rect.center = self.pos
        self.hitbox.center = self.rect.center

        if self.on_ground and not was_on_ground:
            if self.is_ground_pounding:
                self.is_ground_pounding = False
                self.vel.y = -8
                self.game.screen_shake = 15
                self.game.create_particles(self.rect.midbottom, WHITE, 30)
                
                shockwave = Shockwave(self.rect.midbottom)
                self.game.all_sprites.add(shockwave)
                for enemy in self.game.enemies:
                    dist_vec = pygame.math.Vector2(enemy.rect.center) - pygame.math.Vector2(self.rect.midbottom)
                    if 0 < dist_vec.length() < SHOCKWAVE_RADIUS:
                        if hasattr(enemy, 'take_damage'):
                            enemy.take_damage(GROUND_POUND_DAMAGE)
                        if hasattr(enemy, 'knockback'):
                            knockback_force = (SHOCKWAVE_RADIUS - dist_vec.length()) / SHOCKWAVE_RADIUS
                            force_vec = dist_vec.normalize() * SHOCKWAVE_FORCE * knockback_force
                            force_vec.y = -abs(force_vec.y * 0.5)
                            enemy.knockback(force_vec)
            else:
                self.game.create_particles(self.rect.midbottom, PARTICLE_DUST_COLOR, 10)
            self.last_on_ground_time = now
        
        self.coyote_timer = self.last_on_ground_time + COYOTE_TIME
        
        self._update_sprite_image()
        if self.pos.y > HEIGHT + self.h: self.game.player_death()

    def check_horizontal_collisions(self):
        hits = [p for p in self.game.platforms if self.hitbox.colliderect(p.rect)]
        for plat in hits:
            if self.vel.x > 0:
                self.hitbox.right = plat.rect.left
            elif self.vel.x < 0:
                self.hitbox.left = plat.rect.right
            self.pos.x = self.hitbox.centerx
            self.rect.centerx = self.pos.x

    def check_vertical_collisions(self):
        self.on_ground = False
        self.on_slippery = False
        hits = [p for p in self.game.platforms if self.hitbox.colliderect(p.rect)]
        for plat in hits:
            if self.vel.y > 0:
                self.hitbox.bottom = plat.rect.top
                self.on_ground = True
                self.can_double_jump = True
                self.vel.y = 0
                if isinstance(plat, SlipperyPlatform):
                    self.on_slippery = True
            elif self.vel.y < 0:
                self.hitbox.top = plat.rect.bottom
                self.vel.y = 0
            self.pos.y = self.hitbox.centery
            self.rect.centery = self.pos.y
        
    def get_status(self):
        if self.is_ground_pounding: return 'ground_pound'
        if self.is_dashing: return 'dash'
        if not self.on_ground: return 'jump'
        if abs(self.vel.x) > 0.5: return 'walk'
        return 'idle'

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, theme_colors, is_slippery=False):
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        bottom_h = h * 0.7
        pygame.draw.rect(self.image, theme_colors['platform_bottom'], (0, h - bottom_h, w, bottom_h))
        top_h = h * 0.3
        pygame.draw.rect(self.image, theme_colors['platform_top'], (0, 0, w, h - bottom_h))
        if is_slippery:
            pygame.draw.rect(self.image, theme_colors['slippery'], (0,0,w,5))
        self.rect = self.image.get_rect(topleft=(x, y))
    def update(self, keys, player): pass

class SlipperyPlatform(Platform):
    def __init__(self, x, y, w, h, theme_colors):
        super().__init__(x, y, w, h, theme_colors, is_slippery=True)

class GroundPoint(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = True

    def deactivate(self): self.active = False
    def activate(self): self.active = True
    def update(self, keys, player):
        self.image.set_alpha(255 if self.active else 0)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (10, 10), 10)
        pygame.draw.circle(self.image, (218, 165, 32), (10, 10), 8)
        self.rect = self.image.get_rect(center=(x, y))
    def update(self, keys, player):
        if player.powerups['ima_de_moedas']:
            dir_vec = pygame.math.Vector2(player.rect.center) - self.rect.center
            if 0 < dir_vec.length() < MAGNET_RADIUS:
                dir_vec.normalize_ip(); self.rect.move_ip(dir_vec * 5)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, platform, theme, chasing=False, speed=3):
        super().__init__()
        self.game = game
        self.theme = theme
        self.w, self.h = 50, 60
        
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.pos = pygame.math.Vector2(x, platform.rect.top)
        self.rect = self.image.get_rect(bottomleft=self.pos)
        self.vel = pygame.math.Vector2(0,0)
        self.dir = random.choice([-1, 1]); self.chasing = chasing; self.speed = speed
        self.on_ground = False
        self.max_health = 30; self.health = self.max_health
        self.last_ability = pygame.time.get_ticks(); self.ability_cooldown = 5000
        self.walk_frame = 0.0
        self.draw_self() 

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0: self.kill()

    def knockback(self, force_vector):
        self.vel += force_vector
        self.on_ground = False

    def kill(self):
        particle_color = {'forest': GREEN, 'cave': CRYSTAL_COLOR, 'volcano': ORANGE, 'electric': ELECTRIC_BLUE}.get(self.theme, RED)
        self.game.create_particles(self.rect.center, particle_color, 15)
        super().kill()

    def draw_self(self):
        # Define cores com base no self.theme
        colors = {
            'forest': {'body': VINE_COLOR, 'arm': (20, 100, 20), 'eye': BLACK},
            'cave': {'body': (160, 160, 220), 'arm': PURPLE_CRYSTAL, 'eye': WHITE},
            'volcano': {'body': DARKGRAY, 'arm': (100, 100, 100), 'eye': ORANGE},
            'electric': {'body': (90, 90, 130), 'arm': ELECTRIC_BLUE, 'eye': ELECTRIC_YELLOW}
        }
        theme_colors = colors.get(self.theme, colors['forest'])
        body_color = theme_colors['body']
        arm_color = theme_colors['arm']
        eye_color = theme_colors['eye']

        self.image.fill((0,0,0,0))
        
        body_bob = math.sin(self.walk_frame) * 2
        arm_angle = math.sin(self.walk_frame * 0.7) * 25 

        body_rect = pygame.Rect(10, 15 + body_bob, 30, 45)
        
        arm_back_surf = pygame.Surface((10, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(arm_back_surf, arm_color, arm_back_surf.get_rect())
        rotated_arm_back = pygame.transform.rotate(arm_back_surf, arm_angle)
        arm_back_rect = rotated_arm_back.get_rect(center=(12, 35 + body_bob))
        
        arm_front_surf = pygame.Surface((10, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(arm_front_surf, arm_color, arm_front_surf.get_rect())
        rotated_arm_front = pygame.transform.rotate(arm_front_surf, -arm_angle)
        arm_front_rect = rotated_arm_front.get_rect(center=(self.w - 12, 35 + body_bob))

        if self.dir == 1:
            self.image.blit(rotated_arm_back, arm_back_rect)
            pygame.draw.ellipse(self.image, body_color, body_rect, 0)
            pygame.draw.circle(self.image, eye_color, (self.w - 20, 30 + body_bob), 4)
            self.image.blit(rotated_arm_front, arm_front_rect)
        else:
            self.image.blit(rotated_arm_front, arm_front_rect) 
            pygame.draw.ellipse(self.image, body_color, body_rect, 0)
            pygame.draw.circle(self.image, eye_color, (20, 30 + body_bob), 4)
            self.image.blit(rotated_arm_back, arm_back_rect)
    
    def use_ability(self):
        now = pygame.time.get_ticks()
        if now - self.last_ability > self.ability_cooldown:
            self.last_ability = now
            if self.theme == 'forest': 
                self.health = min(self.max_health, self.health + 10)
                self.game.create_particles(self.rect.center, GREEN, 15)
            elif self.theme == 'cave': 
                shard = CrystalShard(self.game, self.rect.midbottom)
                self.game.all_sprites.add(shard); self.game.hazards.add(shard)
            elif self.theme == 'volcano': 
                trail = FireTrail(self.game, self.rect.midbottom)
                self.game.all_sprites.add(trail); self.game.hazards.add(trail)
            elif self.theme == 'electric':
                discharge = ElectricDischarge(self.game, self.rect.center, ELECTRIC_BLUE, radius=60, damage=10)
                self.game.all_sprites.add(discharge); self.game.hazards.add(discharge)


    def update(self, keys, player):
        if self.on_ground: self.use_ability()
        
        ground_check = self.rect.move(0, 2)
        hits = [p for p in self.game.platforms if p.rect.colliderect(ground_check)]
        self.on_ground = bool(hits)
        
        if self.on_ground:
            self.vel.y = 0
            if hits: self.pos.y = hits[0].rect.top
            self.vel.x *= 0.8
            if abs(self.vel.x) < 0.5: self.vel.x = 0

            if self.chasing and abs(self.rect.centerx - player.rect.centerx) < 300:
                self.dir = 1 if player.rect.centerx > self.rect.centerx else -1
            self.pos.x += self.dir * self.speed

            probe_x = self.rect.centerx + (self.rect.width / 2 + 5) * self.dir
            probe_y = self.rect.bottom + 1
            ground_check_rect = pygame.Rect(probe_x, probe_y, 5, 5)
            if not any(plat.rect.colliderect(ground_check_rect) for plat in self.game.platforms):
                self.dir *= -1
        else:
            self.vel.y += PLAYER_ACC
        
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y
        self.rect.bottomleft = self.pos
        
        self.walk_frame += 0.1
        self.draw_self()

class ExplodingEnemy(pygame.sprite.Sprite):
    def __init__(self, game, pos, theme, speed=3):
        super().__init__()
        self.is_exploding = False
        self.game = game; self.theme = theme
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos); self.speed = speed
        self.explode_time = pygame.time.get_ticks() + EXPLODE_FUSE_TIME 
        self.vel = (self.game.player.pos - self.pos).normalize() * self.speed if (self.game.player.pos - self.pos).length() > 0 else pygame.math.Vector2(self.speed, 0)
    
    def knockback(self, force_vector): self.vel += force_vector

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if now >= self.explode_time or pygame.sprite.spritecollideany(self, self.game.platforms) or self.rect.colliderect(player.rect):
            self.explode(); return
        if self.game.player.alive():
            direction = (self.game.player.pos - self.pos)
            if direction.length() > 0: self.vel = direction.normalize() * self.speed
        self.pos += self.vel
        self.rect.center = self.pos
        
        time_left = self.explode_time - now
        pulse_factor = abs(math.sin(now * 0.02))
        radius = 15 + int(pulse_factor * 5)
        self.image.fill((0,0,0,0))
        colors = {
            'forest': ((150, 255, 0), GREEN), 
            'cave': ((100, 100, 255), CRYSTAL_COLOR), 
            'volcano': (YELLOW, RED),
            'electric': (ELECTRIC_BLUE, WHITE)
            }
        base_color, final_flash_color = colors.get(self.theme, (YELLOW, RED))
        color = final_flash_color if time_left < 1000 and (now // 100) % 2 == 0 else base_color
        pygame.draw.circle(self.image, color, (20, 20), radius)
        pygame.draw.rect(self.image, DARKGRAY, (15, 2, 10, 8))

    def explode(self):
        if self.is_exploding: return
        self.is_exploding = True
        self.game.screen_shake = 15
        
        if self.theme == 'electric':
            self.game.all_sprites.add(Explosion(self.game, self.rect.center, ELECTRIC_BLUE, radius=120, damage=EXPLOSION_DAMAGE))
            for _ in range(5):
                self.game.all_sprites.add(Lightning(self.game, self.rect.center, is_projectile=True))
        else:
            particle_color = {'forest': GREEN, 'cave': BLUE}.get(self.theme, ORANGE)
            self.game.all_sprites.add(Explosion(self.game, self.rect.center, particle_color, radius=80, damage=EXPLOSION_DAMAGE))

        if math.hypot(self.rect.centerx - self.game.player.rect.centerx, self.rect.centery - self.game.player.rect.centery) < 80:
            self.game.player.take_damage(EXPLOSION_DAMAGE)
        self.kill()

class FlyingEnemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, theme):
        super().__init__()
        self.game = game; self.theme = theme
        self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
        self.draw_self()
        self.rect = self.image.get_rect(center=(x, y))
        self.start_x = x; self.speed = 2; self.range = 100
        self.last_shot = 0; self.shoot_cooldown = 2000

    def draw_self(self):
        colors = {
            'forest': {'body': (139, 69, 19), 'detail': GREEN},
            'cave': {'body': (120, 120, 180), 'detail': CRYSTAL_COLOR},
            'volcano': {'body': DARKGRAY, 'detail': ORANGE},
            'electric': {'body': (60, 60, 90), 'detail': ELECTRIC_YELLOW}
        }
        c = colors.get(self.theme, colors['forest'])
        pygame.draw.ellipse(self.image, c['body'], (0, 0, 40, 20))
        pygame.draw.ellipse(self.image, c['detail'], (15, 5, 10, 10))
        pygame.draw.rect(self.image, GRAY, (5, -2, 5, 5)); pygame.draw.rect(self.image, GRAY, (30, -2, 5, 5))

    def update(self, keys, player):
        self.rect.centerx = self.start_x + math.sin(pygame.time.get_ticks() * 0.001 * self.speed) * self.range
        now = pygame.time.get_ticks()
        if abs(self.rect.centerx - player.rect.centerx) < 400 and now - self.last_shot > self.shoot_cooldown:
            self.last_shot = now
            laser_color = {'cave': CRYSTAL_COLOR, 'volcano': ORANGE, 'electric': ELECTRIC_YELLOW}.get(self.theme, RED)
            laser = Laser(self.game, self.rect.center, player.rect.center, color=laser_color)
            self.game.all_sprites.add(laser); self.game.enemies.add(laser)
    
    def knockback(self, force_vector):
        self.rect.move_ip(force_vector)

class BatEnemy(pygame.sprite.Sprite):
    def __init__(self, game, pos, theme):
        super().__init__()
        self.game = game; self.theme = theme
        self.image = pygame.Surface((30, 20), pygame.SRCALPHA)
        self.draw_self()
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.start_pos = pygame.math.Vector2(pos) 
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = random.uniform(3.0, 5.0)
        if self.theme == 'electric': self.speed *= 1.5
        self.state = 'waiting'; self.swoop_cooldown = 2000; self.last_swoop = 0

    def draw_self(self):
        color = {'cave': (150, 150, 200), 'volcano': (100, 40, 40), 'electric': (180, 180, 255)}.get(self.theme, DARKGRAY)
        pygame.draw.polygon(self.image, color, [(0,5), (15,20), (30,5), (15,0)])
        if self.theme == 'volcano': pygame.draw.circle(self.image, RED, (15,8), 3)
        elif self.theme == 'electric': pygame.draw.circle(self.image, YELLOW, (15,8), 3)
    
    def knockback(self, force_vector): self.vel += force_vector

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if not player.alive(): return
        dist_to_player = self.pos.distance_to(player.pos)
        
        if self.state == 'waiting':
            if dist_to_player < 250 and now - self.last_swoop > self.swoop_cooldown:
                self.state = 'swooping'
                if (player.pos - self.pos).length() > 0:
                    self.vel = (player.pos - self.pos).normalize() * self.speed
        elif self.state == 'swooping':
            if dist_to_player > 300 or self.pos.y < 0: 
                self.state = 'returning'
        elif self.state == 'returning':
            direction = (self.start_pos - self.pos)
            if direction.length() < self.speed:
                self.state = 'waiting'
                self.vel = pygame.math.Vector2(0,0)
                self.pos = self.start_pos
                self.last_swoop = now
            else:
                self.vel = direction.normalize() * self.speed
        
        self.pos += self.vel
        self.rect.center = self.pos

class MiniStormDragon(pygame.sprite.Sprite):
    def __init__(self, game, pos, theme):
        super().__init__()
        self.game = game; self.theme = theme
        self.w, self.h = 60, 50
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.draw_self()
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.start_pos = pygame.math.Vector2(pos) 
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = random.uniform(3.0, 5.0)
        self.state = 'waiting'; self.swoop_cooldown = 2000; self.last_swoop = 0
        self.last_shot = 0; self.shot_cooldown = 1500
        self.max_health = 40; self.health = self.max_health

    def draw_self(self):
        self.image.fill((0,0,0,0))
        pygame.draw.ellipse(self.image, DRAGON_STORM_BODY, (5, 10, 40, 25))
        pygame.draw.circle(self.image, DRAGON_STORM_BODY, (40, 15), 10)
        pygame.draw.circle(self.image, ELECTRIC_YELLOW, (43, 13), 3)
        # Asas
        wing_angle = math.sin(pygame.time.get_ticks() * 0.005) * 15
        pygame.draw.polygon(self.image, DRAGON_STORM_WING_SECONDARY, [(20, 15), (10, 0 + wing_angle), (30, 0 + wing_angle)])
        pygame.draw.polygon(self.image, DRAGON_STORM_WING_PRIMARY, [(25, 15), (15, 5 + wing_angle), (35, 5 + wing_angle)])

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0: self.kill()

    def knockback(self, force_vector): 
        self.vel += force_vector

    def kill(self):
        particle_color = ELECTRIC_BLUE
        self.game.create_particles(self.rect.center, particle_color, 15)
        super().kill()

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if not player.alive(): return
        dist_to_player = self.pos.distance_to(player.pos)
        
        if self.state == 'waiting':
            # Atira no jogador se estiver no alcance
            if dist_to_player < 300 and now - self.last_shot > self.shot_cooldown:
                self.last_shot = now
                proj = Projectile(self.game, self.rect.center, player.rect.center, speed=8, projectile_type='electricball')
                self.game.all_sprites.add(proj); self.game.enemies.add(proj)

            # Decide mergulhar
            if dist_to_player < 250 and now - self.last_swoop > self.swoop_cooldown:
                self.state = 'swooping'
                if (player.pos - self.pos).length() > 0:
                    self.vel = (player.pos - self.pos).normalize() * self.speed
        elif self.state == 'swooping':
            if dist_to_player > 300 or self.pos.y < 0: 
                self.state = 'returning'
        elif self.state == 'returning':
            direction = (self.start_pos - self.pos)
            if direction.length() < self.speed:
                self.state = 'waiting'
                self.vel = pygame.math.Vector2(0,0)
                self.pos = self.start_pos
                self.last_swoop = now
            else:
                self.vel = direction.normalize() * self.speed
        
        self.pos += self.vel
        self.rect.center = self.pos
        self.draw_self() # Re-desenha para animar asas

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, color, particle_type='default'):
        super().__init__()
        self.image = pygame.Surface((4, 4)); self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        
        if particle_type == 'portal':
            self.vel = pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(-2, -0.5)) # Move para cima
            self.lifespan = random.randint(40, 60)
        else: # Padrão
            self.vel = pygame.math.Vector2(random.uniform(-3, 3), random.uniform(-5, 0))
            self.lifespan = random.randint(20, 40)
            
        self.max_lifespan = self.lifespan

    def update(self, keys, player):
        self.rect.move_ip(self.vel); self.lifespan -= 1
        if self.lifespan <= 0: self.kill()
        
        alpha = max(0, 255 * (self.lifespan / self.max_lifespan))
        self.image.set_alpha(int(alpha))

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface((25, 25), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.draw_image()
    def draw_image(self):
        if self.type == 'kit_medico':
            self.image.fill(WHITE)
            pygame.draw.rect(self.image, RED, (10, 5, 5, 15)); pygame.draw.rect(self.image, RED, (5, 10, 15, 5))
        elif self.type == 'pulo_duplo': pygame.draw.ellipse(self.image, WHITE, (5, 0, 15, 25))
        elif self.type == 'escudo': pygame.draw.circle(self.image, BLUE, (12, 12), 12, 3)
        elif self.type == 'vida_extra': self.image.fill(GREEN); self.image.blit(pygame.font.SysFont("Courier", 18, True).render("+1", True, WHITE), (1,3))
        elif self.type == 'tiro_forte': 
            pygame.draw.rect(self.image, ORANGE, (5, 8, 15, 8))
            pygame.draw.rect(self.image, RED, (3, 6, 19, 12), 2)
        elif self.type == 'dash': pygame.draw.polygon(self.image, YELLOW, [(0,12), (12,0), (12,25)])
        elif self.type == 'super_pulo': pygame.draw.rect(self.image, GREEN, (8, 0, 8, 25))
        elif self.type == 'onda_de_choque': pygame.draw.circle(self.image, WHITE, (12, 12), 12); pygame.draw.circle(self.image, BLACK, (12, 12), 8)
        elif self.type == 'ima_de_moedas': pygame.draw.circle(self.image, RED, (12, 12), 12); pygame.draw.circle(self.image, WHITE, (12, 12), 8)
        elif self.type == 'pontos_em_dobro': 
            pygame.draw.circle(self.image, WHITE, (12, 12), 12)
            self.image.blit(pygame.font.SysFont("Courier", 18, True).render("x2", True, BLACK), (1,3))
    def update(self, keys, player): pass

class Door(pygame.sprite.Sprite):
    def __init__(self, game, midbottom_pos, next_theme_name):
        super().__init__()
        self.game = game
        
        # --- Define Font and Text first ---
        try:
            font = pygame.font.Font(self.game.font_path, 18)
        except (pygame.error, FileNotFoundError, TypeError):
            font = pygame.font.SysFont("Courier", 18, bold=True)
            
        text_surf = font.render("Avançar!", True, WHITE)
        text_rect = text_surf.get_rect()

        # --- Define dimensions based on text and portal ---
        self.w_portal = 60 # Portal width
        self.h_portal = 90 # Portal height
        self.h_text = 40 # Space for text
        
        # Calculate final width: must be at least as wide as the text or the portal
        self.w_total = max(self.w_portal, text_rect.width + 20) # Add 20px padding for text
        self.h_total = self.h_portal + self.h_text
        
        self.image = pygame.Surface((self.w_total, self.h_total), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=midbottom_pos)
        
        self.next_theme_name = next_theme_name
        self.particle_color = self.get_next_theme_color()
        self.last_particle = pygame.time.get_ticks()
        self.particle_cooldown = 100

        # --- Draw elements centered on the new surface width ---
        
        # Portal (centered horizontally)
        portal_x = (self.w_total - self.w_portal) // 2
        portal_rect = pygame.Rect(portal_x, self.h_text, self.w_portal, self.h_portal)
        pygame.draw.ellipse(self.image, BLACK, portal_rect)
        
        # Texto (centered horizontally)
        text_rect.center = (self.w_total // 2, self.h_text // 2)
        self.image.blit(text_surf, text_rect)
        
        # Salva a largura do portal para as partículas
        self.portal_center_x_rel = portal_rect.centerx


    def get_next_theme_color(self):
        if self.next_theme_name == 'forest': return GREEN
        if self.next_theme_name == 'cave': return CRYSTAL_COLOR
        if self.next_theme_name == 'volcano': return ORANGE
        if self.next_theme_name == 'electric': return ELECTRIC_YELLOW
        return WHITE

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if now - self.last_particle > self.particle_cooldown:
            self.last_particle = now
            px = self.rect.x + self.portal_center_x_rel + random.randint(-self.w_portal // 3, self.w_portal // 3)
            py = self.rect.y + self.h_text + self.h_portal // 2
            self.game.create_particles((px, py), self.particle_color, 1, particle_type='portal')

class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y, theme_name, size=40):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = {'cave': CRYSTAL_COLOR, 'volcano': (80, 30, 30)}.get(theme_name, VINE_COLOR)
        pygame.draw.polygon(self.image, color, [(size//2, 0), (size, size), (0, size)])
        self.rect = self.image.get_rect(midbottom=(x, y))
    def update(self, keys, player): pass

class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, pos, target_pos, speed=15, strong=False, color=None, projectile_type='bullet'):
        super().__init__()
        self.game = game
        self.projectile_type = projectile_type
        
        if self.projectile_type in ('fireball', 'electricball'):
            size = 30 if self.projectile_type == 'fireball' else 25
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            if self.projectile_type == 'fireball':
                pygame.draw.circle(self.image, ORANGE, (size//2, size//2), size//2)
                pygame.draw.circle(self.image, YELLOW, (size//2, size//2), size//3)
                self.damage = 30
            else:
                pygame.draw.circle(self.image, WHITE, (size//2, size//2), size//2)
                pygame.draw.circle(self.image, ELECTRIC_BLUE, (size//2, size//2), size//3)
                self.damage = 40
        else: # Bullet
            self.image = pygame.Surface((16, 8) if strong else (10, 5), pygame.SRCALPHA)
            self.damage = 20 if strong else 10
            fill_color = color or (ORANGE if strong else YELLOW)
            self.image.fill(fill_color)
            
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        try:
            direction = (pygame.math.Vector2(target_pos) - self.pos).normalize()
        except ValueError:
            direction = pygame.math.Vector2(1, 0) # Padrão se o vetor for zero
            
        self.vel = direction * speed
        
        if self.projectile_type == 'bullet':
            angle = self.vel.angle_to(pygame.math.Vector2(1, 0))
            self.image = pygame.transform.rotate(self.image, -angle)
            self.rect = self.image.get_rect(center=self.pos)

    def update(self, keys, player):
        self.pos += self.vel
        self.rect.center = self.pos
        
        # A explosão agora é acionada pelo projétil
        collided_enemy = pygame.sprite.spritecollideany(self, self.game.enemies)
        collided_platform = pygame.sprite.spritecollideany(self, self.game.platforms)

        # Projéteis de jogador não devem colidir com o jogador
        if collided_enemy == self.game.player:
            collided_enemy = None
            
        # Projéteis de inimigos (que não são balas) não devem colidir com outros inimigos
        if self in self.game.projectiles:
            pass # É um projétil de jogador, pode colidir com inimigo
        else:
            if collided_enemy:
                collided_enemy = None # É projétil de inimigo, ignora colisão com inimigo

        if self.projectile_type in ('fireball', 'electricball') and (collided_enemy or collided_platform):
            color = ORANGE if self.projectile_type == 'fireball' else ELECTRIC_BLUE
            self.game.all_sprites.add(Explosion(self.game, self.rect.center, color, radius=80, damage=self.damage))
            self.kill()

        if not self.game.screen.get_rect().colliderect(self.rect):
            self.kill()

class MovingPlatform(Platform):
    def __init__(self, x, y, w, h, theme_colors, speed, is_slippery=False):
        super().__init__(x, y, w, h, theme_colors, is_slippery)
        self.start_pos = pygame.math.Vector2(x, y)
        self.end_pos = pygame.math.Vector2(x + random.randint(100, 300), y)
        self.vel = (self.end_pos - self.start_pos).normalize() * speed if (self.end_pos - self.start_pos).length() > 0 else pygame.math.Vector2(0, 0)
        
    def update(self, keys, player):
        self.rect.move_ip(self.vel)
        if (self.vel.x > 0 and self.rect.right > self.end_pos.x) or \
           (self.vel.x < 0 and self.rect.left < self.start_pos.x):
            self.vel.x *= -1

class Fireball(pygame.sprite.Sprite):
    def __init__(self, game, platform_rect):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORANGE, (10, 10), 10); pygame.draw.circle(self.image, YELLOW, (10, 10), 6)
        self.rect = self.image.get_rect(center=platform_rect.midtop)
        self.vel = pygame.math.Vector2(random.choice([-2, 2]), -10)
    def knockback(self, force_vector): self.vel += force_vector
    def update(self, keys, player):
        self.vel.y += PLAYER_ACC
        self.rect.move_ip(self.vel)
        if pygame.sprite.spritecollide(self, self.game.platforms, False) and self.vel.y > 0: self.vel.y = -10
        if self.rect.top > HEIGHT: self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((15, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, ORANGE, (0, 0, 15, 40)); pygame.draw.ellipse(self.image, YELLOW, (2, 5, 11, 30))
        self.rect = self.image.get_rect(center=(x, -50))
        self.speed = random.randint(5, 10)
    def knockback(self, force_vector): self.rect.move_ip(force_vector)
    def update(self, keys, player):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT: self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.max_health = 100 + 50 * (self.game.level // 4)
        self.health = self.max_health
        self.body_parts = {}
        self.name = "CHEFE" # Nome padrão

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.game.boss_defeated()
            self.kill()

    def knockback(self, force_vector):
        self.rect.move_ip(force_vector * 0.2) 
    
    def _clamp_to_screen(self):
        self.rect.clamp_ip(self.game.screen.get_rect())
        if self.rect.bottom > HEIGHT - 40: self.rect.bottom = HEIGHT - 40
        if hasattr(self, 'pos'): self.pos = pygame.math.Vector2(self.rect.center)

    def _draw_limb(self, surface, part, angle, pivot, offset, flip_mult=1):
        part_to_draw = part if flip_mult == 1 else pygame.transform.flip(part, True, False)
        final_angle = angle if flip_mult == 1 else 180 - angle
        rotated_part = pygame.transform.rotate(part_to_draw, final_angle)
        rect = rotated_part.get_rect(center=pivot + offset)
        surface.blit(rotated_part, rect)

    def _create_body_parts(self, colors, sizes):
        self.body_parts['torso'] = pygame.Surface(sizes['torso'], pygame.SRCALPHA)
        pygame.draw.rect(self.body_parts['torso'], colors['torso'], self.body_parts['torso'].get_rect(), 0, 8)
        self.body_parts['head'] = pygame.Surface(sizes['head'], pygame.SRCALPHA)
        pygame.draw.rect(self.body_parts['head'], colors['head'], self.body_parts['head'].get_rect(), 0, 6)
        self.body_parts['arm'] = pygame.Surface(sizes['arm'], pygame.SRCALPHA)
        pygame.draw.rect(self.body_parts['arm'], colors['arm'], self.body_parts['arm'].get_rect(), 0, 4)
        self.body_parts['leg'] = pygame.Surface(sizes['leg'], pygame.SRCALPHA)
        pygame.draw.rect(self.body_parts['leg'], colors['leg'], self.body_parts['leg'].get_rect(), 0, 4)

class ForestGuardian(Boss):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Guardião da Floresta"
        self.w, self.h = 150, 180
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        colors = {'head': (100, 50, 20), 'torso': (139, 69, 19), 'arm': (139, 69, 19), 'leg': (139, 69, 19)}
        sizes = {'head': (30, 30), 'torso': (50, 80), 'arm': (15, 70), 'leg': (20, 75)}
        self._create_body_parts(colors, sizes)
        self.rect = self.image.get_rect(midbottom=(WIDTH - 150, HEIGHT - 40))
        self.speed = 2; self.direction = -1
        self.last_attack = pygame.time.get_ticks(); self.attack_cooldown = 2000
        self.walk_frame = 0; self.is_attacking = False

    def update(self, keys, player):
        self.rect.x += self.speed * self.direction
        if self.rect.left < WIDTH / 2 or self.rect.right > WIDTH: self.direction *= -1
        now = pygame.time.get_ticks()
        if self.is_attacking and now > self.last_attack + 500: self.is_attacking = False
        if now - self.last_attack > self.attack_cooldown:
            self.last_attack = now; self.is_attacking = True
            attack_type = random.choice(['vines', 'seeds'])
            if attack_type == 'vines' and player.alive(): self.vine_attack(player)
            else: self.seed_barrage()
        self._update_image(); self._clamp_to_screen()

    def _update_image(self):
        self.image.fill((0,0,0,0))
        torso_center = pygame.math.Vector2(self.w / 2, self.h / 2 + 20)
        shoulder_pos = torso_center + pygame.math.Vector2(0, -35)
        hip_pos = torso_center + pygame.math.Vector2(0, 40)
        self.walk_frame += 0.1
        leg_angle = math.sin(self.walk_frame) * 30
        arm_angle = -90 if self.is_attacking else math.sin(self.walk_frame * 0.5) * 10
        flip_mult = -1 if self.direction > 0 else 1
        self._draw_limb(self.image, self.body_parts['leg'], -leg_angle, hip_pos, pygame.math.Vector2(15 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['leg'], leg_angle, hip_pos, pygame.math.Vector2(-15 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['torso'], 0, torso_center, pygame.math.Vector2(0, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(30 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(-30 * flip_mult, 0), flip_mult)
        head_pos = torso_center + pygame.math.Vector2(0, -55)
        self._draw_limb(self.image, self.body_parts['head'], 0, head_pos, pygame.math.Vector2(0, 0), flip_mult)
        
    def vine_attack(self, player):
        vine = Vine(self.game, (player.rect.centerx, HEIGHT - 40))
        self.game.all_sprites.add(vine); self.game.enemies.add(vine)

    def seed_barrage(self):
        for i in range(-1, 2):
            p = Projectile(self.game, self.rect.midtop, (0, self.rect.centery + i * 50), speed=8)
            self.game.all_sprites.add(p); self.game.enemies.add(p)

class Vine(pygame.sprite.Sprite):
    def __init__(self, game, pos):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 100), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, VINE_COLOR, [(0, 100), (10, 0), (20, 100)])
        self.rect = self.image.get_rect(midbottom=pos)
        self.spawn_time = pygame.time.get_ticks()
    def knockback(self, force_vector): pass
    def update(self, keys, player):
        if pygame.time.get_ticks() - self.spawn_time > 750: self.kill()

class CrystalHorror(Boss):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Horror de Cristal"
        self.w, self.h = 120, 150
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        colors = {'head': (200, 200, 255), 'torso': CRYSTAL_COLOR, 'arm': CRYSTAL_COLOR, 'leg': CRYSTAL_COLOR}
        sizes = {'head': (25, 25), 'torso': (40, 70), 'arm': (12, 60), 'leg': (15, 65)}
        self._create_body_parts(colors, sizes)
        self.rect = self.image.get_rect(center=(WIDTH / 2, 150))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.state = 'top_phase' 
        self.last_state_change = self.last_attack = pygame.time.get_ticks()
        self.attack_cooldown = 1500; self.dive_speed = 12
        self.top_pos = pygame.math.Vector2(WIDTH / 2, 150)
        self.bottom_pos = pygame.math.Vector2(WIDTH / 2, HEIGHT - 120)
        self.angle = 0

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if self.state == 'top_phase':
            self.angle += 0.02
            self.pos.x = self.top_pos.x + math.sin(self.angle) * (WIDTH / 4)
            self.pos.y = self.top_pos.y + math.cos(self.angle * 2) * 50
            if now - self.last_attack > self.attack_cooldown:
                self.last_attack = now; self.top_attack(player)
            if now - self.last_state_change > 8000:
                self.state = 'diving'; self.bottom_pos.x = player.pos.x
        elif self.state == 'diving':
            direction = (self.bottom_pos - self.pos)
            if direction.length() < self.dive_speed:
                self.pos = self.bottom_pos; self.state = 'bottom_phase'
                self.last_state_change = now; self.bottom_attack() 
            else: self.pos += direction.normalize() * self.dive_speed
        elif self.state == 'bottom_phase':
            if now - self.last_attack > self.attack_cooldown / 2: 
                self.last_attack = now; self.bottom_attack()
            if now - self.last_state_change > 4000: self.state = 'returning'
        elif self.state == 'returning':
            direction = (self.top_pos - self.pos)
            if direction.length() < self.dive_speed:
                self.pos = self.top_pos; self.state = 'top_phase'
                self.last_state_change = now; self.angle = 0 
            else: self.pos += direction.normalize() * self.dive_speed
        self.rect.center = self.pos
        self._update_image(); self._clamp_to_screen()

    def _update_image(self):
        self.image.fill((0,0,0,0))
        torso_center = pygame.math.Vector2(self.w / 2, self.h / 2)
        shoulder_pos = torso_center + pygame.math.Vector2(0, -30)
        hip_pos = torso_center + pygame.math.Vector2(0, 35)
        arm_angle = leg_angle = 0
        if self.state in ['diving', 'returning']: arm_angle = leg_angle = 170
        elif self.state == 'bottom_phase': arm_angle = -90
        else:
            arm_angle = math.sin(self.angle * 2) * 20
            leg_angle = math.sin(self.angle * 2) * 15
        self._draw_limb(self.image, self.body_parts['leg'], leg_angle, hip_pos, pygame.math.Vector2(10, 0))
        self._draw_limb(self.image, self.body_parts['leg'], leg_angle, hip_pos, pygame.math.Vector2(-10, 0))
        self._draw_limb(self.image, self.body_parts['torso'], 0, torso_center, pygame.math.Vector2(0, 0))
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(25, 0))
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(-25, 0))
        head_pos = torso_center + pygame.math.Vector2(0, -45)
        self._draw_limb(self.image, self.body_parts['head'], 0, head_pos, pygame.math.Vector2(0, 0))
        
    def top_attack(self, player):
        if random.choice(['shard', 'bats']) == 'shard' and player.alive():
            p = Projectile(self.game, self.rect.center, player.rect.center, speed=10, strong=True)
            self.game.all_sprites.add(p); self.game.enemies.add(p)
        else:
            for _ in range(2):
                bat = BatEnemy(self.game, self.rect.center, 'cave')
                self.game.all_sprites.add(bat); self.game.enemies.add(bat)

    def bottom_attack(self):
        for i in range(3):
            shard = CrystalShard(self.game, (self.pos.x + random.randint(-150, 150), HEIGHT - 40))
            self.game.all_sprites.add(shard); self.game.hazards.add(shard)
            
class VolcanoBehemoth(Boss):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Beemote Vulcânico"
        self.w, self.h = 160, 200
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        colors = {'head': ORANGE, 'torso': DARKGRAY, 'arm': DARKGRAY, 'leg': DARKGRAY}
        sizes = {'head': (40, 40), 'torso': (70, 100), 'arm': (25, 90), 'leg': (30, 95)}
        self._create_body_parts(colors, sizes)
        self.rect = self.image.get_rect(midbottom=(WIDTH - 200, HEIGHT - 40))
        self.state = 'idle'
        self.last_action = pygame.time.get_ticks(); self.action_cooldown = 3000
        self.charge_speed = 15; self.direction = -1

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if self.state == 'charging':
            self.rect.x += self.charge_speed * self.direction
            if not self.game.screen.get_rect().colliderect(self.rect):
                self.state = 'idle'; self.last_action = now; self.direction *= -1
        elif now - self.last_action > self.action_cooldown:
            self.last_action = now
            self.state = random.choice(['meteors', 'geysers', 'prepare_charge'])
        
        if self.state == 'meteors':
            for _ in range(5):
                m = Meteor(random.randint(0, WIDTH))
                self.game.all_sprites.add(m); self.game.enemies.add(m)
            self.state = 'idle'
        elif self.state == 'geysers':
            if self.game.platforms:
                for i in range(3):
                    pos_x = random.randint(self.game.platforms.sprites()[0].rect.left, self.game.platforms.sprites()[0].rect.right)
                    fb = Fireball(self.game, pygame.Rect(pos_x, self.game.platforms.sprites()[0].rect.top, 1, 1))
                    self.game.all_sprites.add(fb); self.game.enemies.add(fb)
            self.state = 'idle'
        elif self.state == 'prepare_charge': self.state = 'charging' 
        self._update_image(); self._clamp_to_screen()

    def _update_image(self):
        self.image.fill((0,0,0,0))
        torso_center = pygame.math.Vector2(self.w / 2, self.h / 2 + 30)
        shoulder_pos = torso_center + pygame.math.Vector2(0, -45)
        hip_pos = torso_center + pygame.math.Vector2(0, 50)
        arm_angle = {'meteors': -110, 'geysers': -110, 'charging': 20}.get(self.state, math.sin(pygame.time.get_ticks() * 0.001) * 10)
        flip_mult = -1 if self.direction > 0 else 1
        self._draw_limb(self.image, self.body_parts['leg'], 0, hip_pos, pygame.math.Vector2(20 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['leg'], 0, hip_pos, pygame.math.Vector2(-20 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['torso'], 0, torso_center, pygame.math.Vector2(0, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(40 * flip_mult, 0), flip_mult)
        self._draw_limb(self.image, self.body_parts['arm'], arm_angle, shoulder_pos, pygame.math.Vector2(-40 * flip_mult, 0), flip_mult)
        head_pos = torso_center + pygame.math.Vector2(0, -65)
        self._draw_limb(self.image, self.body_parts['head'], 0, head_pos, pygame.math.Vector2(0, 0), flip_mult)

class StormDragon(Boss):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Dragão da Tempestade"
        self.max_health *= 1.5 # Mais vida
        self.health = self.max_health
        self.w, self.h = 250, 200
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(WIDTH / 2, HEIGHT / 3))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.state = 'hovering'
        self.last_attack = pygame.time.get_ticks()
        self.attack_cooldown = 2500
        self.fury_mode = False
        self.fury_timer = 0
        self.fury_duration = 5000 # 5 segundos de fúria
        self.last_fury = pygame.time.get_ticks()
        self.fury_cooldown = 15000 # Fúria a cada 15 segundos
        self.direction = 1
        self.hover_center_y = HEIGHT / 3
        self._draw_base_sprite()

    def _draw_base_sprite(self):
        self.base_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # Corpo
        pygame.draw.ellipse(self.base_image, DRAGON_STORM_BODY, (50, 60, 150, 80))
        # Pescoço e Cabeça
        pygame.draw.lines(self.base_image, DRAGON_STORM_BODY, False, [(180, 100), (200, 70), (220, 60)], 15)
        pygame.draw.circle(self.base_image, DRAGON_STORM_BODY, (230, 55), 20)
        pygame.draw.circle(self.base_image, ELECTRIC_YELLOW, (235, 50), 5)
        # Cauda
        pygame.draw.lines(self.base_image, DRAGON_STORM_BODY, False, [(50, 100), (20, 120), (10, 100)], 10)
        # Pernas
        pygame.draw.rect(self.base_image, DRAGON_STORM_BODY, (80, 130, 15, 30))
        pygame.draw.rect(self.base_image, DRAGON_STORM_BODY, (150, 130, 15, 30))

    def _update_wings(self):
        self.image.blit(self.base_image, (0,0))
        now = pygame.time.get_ticks()
        wing_angle = math.sin(now * 0.003) * 30
        
        # Asa Esquerda (Primária)
        wing_left_surf = pygame.Surface((100, 120), pygame.SRCALPHA)
        pygame.draw.polygon(wing_left_surf, DRAGON_STORM_WING_PRIMARY, [(0,100), (100,0), (100,120)])
        rotated_wing_left = pygame.transform.rotate(wing_left_surf, wing_angle + 20)
        self.image.blit(rotated_wing_left, (30, -20))

        # Asa Direita (Secundária)
        wing_right_surf = pygame.Surface((100, 120), pygame.SRCALPHA)
        pygame.draw.polygon(wing_right_surf, DRAGON_STORM_WING_SECONDARY, [(0,0), (100,100), (0,120)])
        rotated_wing_right = pygame.transform.rotate(wing_right_surf, -wing_angle - 20)
        self.image.blit(rotated_wing_right, (120, -20))

        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        
        if not self.fury_mode and now - self.last_fury > self.fury_cooldown:
            self.fury_mode = True
            self.fury_timer = now + self.fury_duration
            self.attack_cooldown = 1000 
            print("Dragão da Tempestade entrou em Fúria!")
        elif self.fury_mode and now > self.fury_timer:
            self.fury_mode = False
            self.attack_cooldown = 2500
            self.last_fury = now
            print("Fúria do Dragão da Tempestade acabou.")

        self.pos.y = self.hover_center_y + math.sin(now * 0.001) * 30
        self.pos.x += self.direction * 3
        if self.pos.x < 150 or self.pos.x > WIDTH - 150:
            self.direction *= -1
        self.rect.center = self.pos

        if now - self.last_attack > self.attack_cooldown:
            self.last_attack = now
            attack_choice = random.random()
            if self.fury_mode:
                if attack_choice < 0.6: self.fury_lightning_bolts(player)
                else: self.orb_barrage(player)
            else:
                if attack_choice < 0.4: self.orb_barrage(player)
                elif attack_choice < 0.7: self.aura_pulse()
                else: self.lightning_rain()
        
        if not self.fury_mode and random.random() < 0.05:
            self.aura_pulse(passive=True)
            
        self._update_wings()
        self._clamp_to_screen()

    def orb_barrage(self, player):
        print("Ataque: Rajada de Orbes")
        num_orbs = 5 if not self.fury_mode else 8
        for i in range(num_orbs):
            angle_offset = (i - num_orbs // 2) * 10
            target_pos = player.pos + pygame.math.Vector2(0, random.randint(-50, 50)).rotate(angle_offset)
            proj = Projectile(self.game, self.rect.center, target_pos, speed=10, projectile_type='electricball')
            self.game.all_sprites.add(proj); self.game.enemies.add(proj)

    def aura_pulse(self, passive=False):
        radius = 80 if passive else 150
        print(f"Ataque: Pulso Elétrico {'(Passivo)' if passive else ''}")
        self.game.all_sprites.add(Explosion(self.game, self.rect.center, ELECTRIC_BLUE, radius=radius, damage=15 if passive else 30))

    def lightning_rain(self):
        print("Ataque: Chuva de Raios")
        num_bolts = 5 if not self.fury_mode else 8
        for _ in range(num_bolts):
            x_pos = random.randint(0, WIDTH)
            self.game.all_sprites.add(Lightning(self.game, (x_pos, 0)))

    def fury_lightning_bolts(self, player):
        print("Ataque Fúria: Raios Dispersos")
        num_bolts = 3
        spread_angle = 60
        base_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() > 0 else pygame.math.Vector2(0,1)
        
        for i in range(num_bolts):
            angle = (i - num_orbs // 2) * (spread_angle / (num_bolts -1) if num_bolts > 1 else 0)
            direction = base_dir.rotate(angle)
            start_pos = self.rect.center + direction * 50
            end_pos = start_pos + direction * 300
            self.game.all_sprites.add(Lightning(self.game, start_pos, is_projectile=True, end_pos=end_pos))

class Explosion(pygame.sprite.Sprite):
    def __init__(self, game, center, color=ORANGE, radius=50, damage=0):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.frame = 0
        self.anim_speed = 30
        self.last_update = pygame.time.get_ticks()
        self.color = color
        self.radius = radius

        if damage > 0:
            for enemy in pygame.sprite.spritecollide(self, self.game.enemies, False, pygame.sprite.collide_circle):
                if not isinstance(enemy, Boss):
                    if hasattr(enemy, 'take_damage'):
                        enemy.take_damage(damage)
                    else:
                        enemy.kill()

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.anim_speed:
            self.last_update = now
            self.frame += 1
            if self.frame > 5:
                self.kill()
                return
            self.image.fill((0,0,0,0))
            current_radius = self.frame * (self.radius / 5)
            alpha = 255 * (1 - (self.frame / 5))
            try:
                color_with_alpha = self.color + (int(alpha),)
            except TypeError: 
                color_with_alpha = (self.color[0], self.color[1], self.color[2], int(alpha))
            pygame.draw.circle(self.image, color_with_alpha, self.image.get_rect().center, int(current_radius))
                
class Laser(pygame.sprite.Sprite):
    def __init__(self, game, start_pos, target_pos, color=RED):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA); pygame.draw.circle(self.image, color, (5, 5), 5)
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.math.Vector2(start_pos)
        direction = (pygame.math.Vector2(target_pos) - self.pos)
        self.vel = direction.normalize() * 12 if direction.length() > 0 else pygame.math.Vector2(0,0)
    def knockback(self, force_vector): pass
    def update(self, keys, player):
        self.pos += self.vel
        self.rect.center = self.pos
        if not self.game.screen.get_rect().colliderect(self.rect): self.kill()

class Star(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((2, 2)); self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.alpha = random.randint(50, 255); self.alpha_dir = -1
        self.twinkle_speed = random.randint(1, 4); self.depth = 0.2
    def update(self, keys, player):
        self.alpha += self.alpha_dir * self.twinkle_speed
        if self.alpha <= 50 or self.alpha >= 255: self.alpha_dir *= -1
        self.image.set_alpha(self.alpha)
        
class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((random.randint(80, 150), random.randint(30, 60)), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (50, 50, 70), self.image.get_rect())
        self.rect = self.image.get_rect(center=(x,y))
        self.speed = random.uniform(0.2, 0.5); self.depth = 0.4
    def update(self, keys, player):
        self.rect.x -= self.speed
        if self.rect.right < 0: self.rect.left = WIDTH

class GlowingCrystal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (150, 150, 255), [(10, 0), (20, 30), (0, 30)])
        self.rect = self.image.get_rect(center=(x,y))
        self.pulse_speed = random.uniform(0.001, 0.003); self.depth = 0.3
    def update(self, keys, player):
        self.image.set_alpha(128 + math.sin(pygame.time.get_ticks() * self.pulse_speed) * 127)

class Ember(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((3, 3))
        self.image.fill(random.choice([ORANGE, YELLOW, RED]))
        self.rect = self.image.get_rect(center=(x,y))
        self.vel_y = -random.uniform(0.5, 1.5); self.depth = 0.25
    def update(self, keys, player):
        self.rect.y += self.vel_y
        if self.rect.bottom < 0: self.rect.top = HEIGHT

class CrystalShard(pygame.sprite.Sprite):
    def __init__(self, game, pos):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, CRYSTAL_COLOR, [(10, 0), (20, 20), (0, 20)])
        self.rect = self.image.get_rect(midbottom=pos)
        self.spawn_time = pygame.time.get_ticks()
    def knockback(self, force_vector): pass
    def update(self, keys, player):
        if pygame.time.get_ticks() - self.spawn_time > 3000: self.kill()

class FireTrail(pygame.sprite.Sprite):
    def __init__(self, game, pos):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((25, 10), pygame.SRCALPHA); self.image.fill(ORANGE)
        self.rect = self.image.get_rect(midbottom=pos)
        self.spawn_time = pygame.time.get_ticks()
    def knockback(self, force_vector): pass
    def update(self, keys, player):
        if pygame.time.get_ticks() - self.spawn_time > 2000: self.kill()

class Shockwave(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.center = center
        self.radius = 10
        self.max_radius = SHOCKWAVE_RADIUS
        self.image = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.anim_speed = 8

    def update(self, keys, player):
        self.radius += self.anim_speed
        if self.radius > self.max_radius:
            self.kill()
            return
        self.image.fill((0,0,0,0))
        alpha = 255 * (1 - (self.radius / self.max_radius))
        pygame.draw.circle(self.image, (255, 255, 255, alpha), self.image.get_rect().center, self.radius, width=5)

class Leaf(pygame.sprite.Sprite):
    def __init__(self, screen_rect):
        super().__init__()
        self.screen_rect = screen_rect
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, GREEN, self.image.get_rect())
        self.rect = self.image.get_rect(center=(random.randint(0, screen_rect.width), -20))
        self.speed_y = random.uniform(1, 3)
        self.speed_x = random.uniform(-1, 1)
        self.depth = 0.3 # Profundidade para menu
    
    def update(self, keys, player):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x + math.sin(self.rect.y * 0.1) * 0.5
        if self.rect.top > self.screen_rect.height:
            self.rect.center = (random.randint(0, self.screen_rect.width), -20)

class Lightning(pygame.sprite.Sprite):
    def __init__(self, game, pos, is_background=False, is_projectile=False, end_pos=None):
        super().__init__()
        self.game = game
        self.is_background = is_background
        self.is_projectile = is_projectile
        
        if is_projectile:
             self.image = pygame.Surface((300, 300), pygame.SRCALPHA) 
        else:
             self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
             
        self.rect = self.image.get_rect(topleft=(0,0) if is_background else pos)
        self.lifespan = 250
        self.spawn_time = pygame.time.get_ticks()
        self.depth = 0.1 

        if self.is_projectile:
            self.start_pos = pygame.math.Vector2(pos)
            if end_pos:
                 direction = (pygame.math.Vector2(end_pos) - self.start_pos)
                 self.vel = direction.normalize() * 15 if direction.length() > 0 else pygame.math.Vector2(0,0)
                 self.end_pos = pygame.math.Vector2(end_pos)
            else:
                self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 8
                self.end_pos = self.start_pos + self.vel * 2.5
            self.rect.center = self.start_pos 
            self.start_pos_rel = pygame.math.Vector2(self.image.get_rect().center) 
            self.end_pos_rel = self.start_pos_rel + (self.end_pos - self.start_pos) 
            self.create_bolt(self.start_pos_rel, self.end_pos_rel, 5)
        else:
            self.start_pos = pygame.math.Vector2(pos)
            self.end_pos = pygame.math.Vector2(pos[0] + random.randint(-40, 40), HEIGHT)
            self.create_bolt(self.start_pos, self.end_pos, 5)


    def create_bolt(self, start, end, thickness):
        points = [start]
        direction = end - start
        length = direction.length()
        if length == 0: return
        
        if length > 0: direction.normalize_ip()
        
        current_pos = pygame.math.Vector2(start)
        num_segments = max(1, int(length / 10)) 

        for _ in range(num_segments):
            current_pos += direction * 10
            offset = pygame.math.Vector2(direction.y, -direction.x) * random.uniform(-20, 20)
            points.append(current_pos + offset)
        points.append(end)

        pygame.draw.lines(self.image, ELECTRIC_YELLOW, False, points, thickness)
        pygame.draw.lines(self.image, WHITE, False, points, thickness // 2)
        self.mask = pygame.mask.from_surface(self.image)


    def update(self, keys, player):
        if self.is_projectile:
            self.rect.move_ip(self.vel)
            if not self.game.screen.get_rect().colliderect(self.rect):
                self.kill()

        if pygame.time.get_ticks() - self.spawn_time > self.lifespan:
            self.kill()
        
        if not self.is_background and not self.is_projectile:
             if pygame.sprite.collide_mask(self, player):
                player.take_damage(30)
                self.kill()

class ElectricDischarge(pygame.sprite.Sprite):
    def __init__(self, game, center, color, radius, damage):
        super().__init__()
        self.game = game
        self.radius = radius
        self.damage = damage
        self.color = color 
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.frame = 0
        self.anim_speed = 40
        self.last_update = pygame.time.get_ticks()
        self.hit_player = False

    def update(self, keys, player):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.anim_speed:
            self.last_update = now
            self.frame += 1
            if self.frame > 4:
                self.kill()
                return
            
            self.image.fill((0,0,0,0))
            current_radius = self.frame * (self.radius / 4)
            alpha = 255 * (1 - (self.frame / 4))
            color_with_alpha = (self.color[0], self.color[1], self.color[2], int(alpha))
            pygame.draw.circle(self.image, color_with_alpha, self.image.get_rect().center, int(current_radius), 4)

            if not self.hit_player and self.rect.colliderect(player.hitbox):
                if math.hypot(self.rect.centerx - player.hitbox.centerx, self.rect.centery - player.hitbox.centery) < current_radius:
                    player.take_damage(self.damage)
                    self.hit_player = True


class Game:
    def __init__(self):
        pygame.init()
        print("Iniciando Entre Mundos v1.0 - modo sem som ativo.")
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.paused = False
        self.screen_shake = 0
        self.player_name = ""
        self.name_input_active = False
        self.boss = None
        self.menu_play_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 - 50, 300, 50)
        self.menu_ranking_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 + 20, 300, 50)
        self.ranking_back_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT - 150, 300, 50)
        self.pause_continue_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 - 80, 300, 50)
        self.pause_restart_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 - 10, 300, 50)
        self.pause_menu_button_rect = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 + 60, 300, 50)
        self.hud_pause_button_rect = pygame.Rect(WIDTH - 50, 10, 40, 40)
        self.load_assets()

    def load_assets(self):
        self.font_path = os.path.join("assets", "ui", "PressStart2P-Regular.ttf")
        try:
            pygame.font.Font(self.font_path, 8)
        except pygame.error:
            print(f"Aviso: Fonte '{self.font_path}' não encontrada. Usando fonte padrão do sistema.")
            self.font_path = None

        self.ranking_file = "ranking.json"
        self._create_menu_background()

    def _create_menu_background(self):
        self.menu_bg_sprites = pygame.sprite.Group()
        for _ in range(100):
            star = Star(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            self.menu_bg_sprites.add(star)
    
    def _create_animated_background(self):
        self.background_sprites = pygame.sprite.Group()
        theme_name = self.get_theme_name()
        if theme_name == "forest":
            for _ in range(50): self.background_sprites.add(Star(random.randint(0, WIDTH), random.randint(0, int(HEIGHT * 0.7))))
            for _ in range(5): self.background_sprites.add(Cloud(random.randint(0, WIDTH), random.randint(50, 150)))
        elif theme_name == "cave":
            for _ in range(70): self.background_sprites.add(GlowingCrystal(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        elif theme_name == "volcano":
            for _ in range(100): self.background_sprites.add(Ember(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        elif theme_name == "electric":
            for _ in range(3): self.background_sprites.add(Lightning(self, (random.randint(0, WIDTH), 0), is_background=True))


    def new_game(self):
        self.state = 'playing'; self.player = Player(self)
        self.level = 1
        self.all_sprites = pygame.sprite.Group(); self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group(); self.coins = pygame.sprite.Group()
        self.doors = pygame.sprite.Group(); self.spikes = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group(); self.particles = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.ally_projectiles = pygame.sprite.Group() 
        self.hazards = pygame.sprite.Group() 
        self.all_sprites.add(self.player); self.setup_level(self.level)
        # self.run_game() # Removido para o loop async

    def run(self):
        # Esta função é para rodar localmente
        asyncio.run(self.run_async())


    async def run_async(self):
        # Loop principal assíncrono para pygbag
        self.running = True
        while self.running:
            if self.state == 'playing':
                # O loop de jogo principal agora acontece aqui
                self.events_game()
                self.update_game()
                self.draw_game()
                self.clock.tick(FPS)
            elif self.state == 'menu':
                self.run_menu() # Este loop síncrono interno irá rodar
                if self.state == 'playing':
                    self.new_game() # CORREÇÃO: Chamar new_game() QUANDO o menu sair para 'playing'
            elif self.state == 'game_over':
                self.run_game_over()
            elif self.state == 'win': # --- NOVO ESTADO DE VITÓRIA ---
                self.run_win_screen()
            elif self.state == 'ranking':
                self.run_ranking()
            elif self.state == 'quit':
                self.running = False
            
            await asyncio.sleep(0) # Permite que o navegador respire
        pygame.quit()


    def run_menu(self):
        menu_biome_timer = pygame.time.get_ticks()
        current_biome_index = 0
        biomes = ['forest', 'cave', 'volcano', 'electric']

        while self.state == 'menu':
            now = pygame.time.get_ticks()
            if now - menu_biome_timer > 5000:
                menu_biome_timer = now
                current_biome_index = (current_biome_index + 1) % len(biomes)
                self.menu_bg_sprites.empty()
                if biomes[current_biome_index] == 'forest':
                    for _ in range(5): self.menu_bg_sprites.add(Leaf(self.screen.get_rect()))
                elif biomes[current_biome_index] == 'cave':
                    for _ in range(70): self.menu_bg_sprites.add(GlowingCrystal(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
                elif biomes[current_biome_index] == 'volcano':
                    for _ in range(100): self.menu_bg_sprites.add(Ember(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
                elif biomes[current_biome_index] == 'electric':
                    for _ in range(3): self.menu_bg_sprites.add(Lightning(self, (random.randint(0, WIDTH), 0), is_background=True))


            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.state = 'quit'; self.running = False; return # Sai do loop
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: 
                    self.state = 'playing'; return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.menu_play_button_rect.collidepoint(event.pos): 
                        self.state = 'playing'; return
                    if self.menu_ranking_button_rect.collidepoint(event.pos): 
                        self.state = 'ranking'; return
            
            self.screen.fill(BLACK)
            self.menu_bg_sprites.update(None, None)
            self.menu_bg_sprites.draw(self.screen)
            self.draw_menu()
            pygame.display.flip(); self.clock.tick(FPS)

    def run_game(self):
        pass

    def run_game_over(self):
        self.name_input_active = True; self.player_name = ""
        while self.state == 'game_over':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.state = 'quit'; self.running = False; return
                if self.name_input_active: self.handle_name_input(event)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: 
                    self.state = 'menu'; return
            self.screen.fill(BLACK); self.draw_game_over(); pygame.display.flip(); self.clock.tick(FPS)
    
    def run_win_screen(self):
        self.name_input_active = True; self.player_name = ""
        while self.state == 'win':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.state = 'quit'; self.running = False; return
                if self.name_input_active: self.handle_name_input(event)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: 
                    self.state = 'menu'; return
            self.screen.fill(BLACK); 
            self.draw_win_screen();
            pygame.display.flip(); self.clock.tick(FPS)

    def run_ranking(self):
        while self.state == 'ranking':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.state = 'quit'; self.running = False; return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                    self.state = 'menu'; return
                if event.type == pygame.MOUSEBUTTONDOWN and self.ranking_back_button_rect.collidepoint(event.pos): 
                    self.state = 'menu'; return
            self.screen.fill(BLACK); self.draw_ranking_screen(); pygame.display.flip(); self.clock.tick(FPS)

    def events_game(self):
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.state = 'quit'; self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.paused = not self.paused
                if not self.paused:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.player.jump_buffer_timer = now + JUMP_BUFFER
                        if not self.player.on_ground and self.player.powerups['pulo_duplo'] and self.player.can_double_jump:
                            self.player.jump(); self.player.can_double_jump = False
                    if event.key in (pygame.K_DOWN, pygame.K_s) and not self.player.on_ground:
                        self.player.ground_pound()
                    if event.key == pygame.K_LSHIFT: self.player.dash()
                    if event.key == pygame.K_c: self.player.attack()
            
            if event.type == pygame.KEYUP and not self.paused and event.key in (pygame.K_UP, pygame.K_w):
                self.player.short_jump()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.paused:
                    if self.pause_continue_button_rect.collidepoint(event.pos): self.paused = False
                    if self.pause_restart_button_rect.collidepoint(event.pos): self.restart_level()
                    if self.pause_menu_button_rect.collidepoint(event.pos): 
                        self.state = 'menu'; self.paused = False
                elif self.hud_pause_button_rect.collidepoint(event.pos): self.paused = True
                else:
                    self.player.shoot() 

    def update_game(self):
        if self.paused: return
        keys = pygame.key.get_pressed()
        self.all_sprites.update(keys, self.player)


        self.background_sprites.update(keys, self.player)
        if self.get_theme_name() == 'volcano' and random.random() < 0.02 and not self.boss:
            m = Meteor(random.randint(0, WIDTH))
            self.all_sprites.add(m); self.enemies.add(m)
        self.handle_collisions()
        self.handle_camera()

    def draw_game(self):
        theme = self.get_theme_colors()
        render_offset = [random.randint(-4, 4), random.randint(-4, 4)] if self.screen_shake > 0 else [0, 0]
        if self.screen_shake > 0: self.screen_shake -= 1

        self.screen.fill(theme['bg'])
        self.background_sprites.draw(self.screen)
        for sprite in self.all_sprites: self.screen.blit(sprite.image, sprite.rect.move(render_offset))
        
        bar_w, bar_h = 200, 25
        health_pct = max(0, self.player.health / self.player.max_health)
        pygame.draw.rect(self.screen, HEALTH_BAR_RED, (10, 10, bar_w, bar_h))
        pygame.draw.rect(self.screen, HEALTH_BAR_GREEN, (10, 10, bar_w * health_pct, bar_h))
        self.draw_text(f"{int(self.player.health)}/{self.player.max_health}", 14, OFF_WHITE, 10 + bar_w/2, 12 + bar_h/2)
        
        self.draw_text(f"Vidas: {self.player.lives}", 16, OFF_WHITE, 10, 45, align="topleft")
        self.draw_text(f"Score: {self.player.score}", 16, OFF_WHITE, 10, 70, align="topleft")
        self.draw_text(f"Level: {self.level}", 16, OFF_WHITE, 10, 95, align="topleft")
        
        hud_y = 125
        for name, is_active in self.player.powerups.items():
            if is_active:
                self.draw_text(name.replace('_', ' ').title(), 16, OFF_WHITE, 10, hud_y, align="topleft")
                hud_y += 25

        if self.boss and self.boss.alive():
            bar_w = 400; bar_h = 25
            bar_pct = self.boss.health / self.boss.max_health
            self.draw_text(self.boss.name, 22, WHITE, WIDTH/2, 20)
            pygame.draw.rect(self.screen, RED, (WIDTH/2 - bar_w/2, 50, bar_w * bar_pct, bar_h))
            pygame.draw.rect(self.screen, OFF_WHITE, (WIDTH/2 - bar_w/2, 50, bar_w, bar_h), 2)


        pygame.draw.rect(self.screen, GRAY, self.hud_pause_button_rect)
        pygame.draw.rect(self.screen, BLACK, (self.hud_pause_button_rect.x + 10, self.hud_pause_button_rect.y + 10, 5, 20))
        pygame.draw.rect(self.screen, BLACK, (self.hud_pause_button_rect.x + 25, self.hud_pause_button_rect.y + 10, 5, 20))
        
        if self.paused: self.draw_pause_menu()
        pygame.display.flip()
    
    def draw_menu(self):
        self.draw_text(TITLE, 64, ORANGE, WIDTH // 2, HEIGHT // 4)

        mouse_pos = pygame.mouse.get_pos()
        play_color = BUTTON_HOVER_COLOR if self.menu_play_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, play_color, self.menu_play_button_rect)
        self.draw_text("Jogar", 28, OFF_WHITE, self.menu_play_button_rect.centerx, self.menu_play_button_rect.centery)
        ranking_color = BUTTON_HOVER_COLOR if self.menu_ranking_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, ranking_color, self.menu_ranking_button_rect)
        self.draw_text("Ranking", 28, OFF_WHITE, self.menu_ranking_button_rect.centerx, self.menu_ranking_button_rect.centery)

    def draw_pause_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR); self.screen.blit(overlay, (0, 0))
        self.draw_text("PAUSADO", 48, OFF_WHITE, WIDTH / 2, HEIGHT / 2 - 150)
        mouse_pos = pygame.mouse.get_pos()
        for btn_rect, text, size in [(self.pause_continue_button_rect, "Continuar", 28), 
                                     (self.pause_restart_button_rect, "Reiniciar Nível", 22), 
                                     (self.pause_menu_button_rect, "Voltar ao Menu", 22)]:
            color = BUTTON_HOVER_COLOR if btn_rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(self.screen, color, btn_rect)
            self.draw_text(text, size, OFF_WHITE, btn_rect.centerx, btn_rect.centery)

    def draw_game_over(self):
        self.draw_text("GAME OVER", 48, OFF_WHITE, WIDTH // 2, 100)
        if hasattr(self, 'final_score'):
            self.draw_text(f"Seu Score: {self.final_score}", 28, OFF_WHITE, WIDTH // 2, 200)
        if self.name_input_active:
            self.draw_text("Digite seu nome:", 22, OFF_WHITE, WIDTH//2, 280)
            pygame.draw.rect(self.screen, GRAY, (WIDTH//2 - 150, 310, 300, 40))
            self.draw_text(self.player_name, 28, OFF_WHITE, WIDTH//2, 330)
        else:
            self.draw_text("Top 5 Ranking:", 28, OFF_WHITE, WIDTH // 2, 300)
            for i, r in enumerate(self.load_ranking()): 
                self.draw_text(f"{i + 1}. {r['name']} - {r['score']}", 22, OFF_WHITE, WIDTH // 2, 350 + i * 30)
            self.draw_text("Pressione ENTER para voltar ao menu", 22, OFF_WHITE, WIDTH // 2, 600)

    def draw_win_screen(self):
        self.draw_text("VOCÊ VENCEU!", 48, GREEN, WIDTH // 2, 100)
        self.draw_text("Você selou os portais e salvou a realidade!", 22, WHITE, WIDTH // 2, 160)
        
        if hasattr(self, 'final_score'):
            self.draw_text(f"Seu Score Final: {self.final_score}", 28, OFF_WHITE, WIDTH // 2, 220)
        
        if self.name_input_active:
            self.draw_text("Digite seu nome para o ranking:", 22, OFF_WHITE, WIDTH//2, 280)
            pygame.draw.rect(self.screen, GRAY, (WIDTH//2 - 150, 310, 300, 40))
            self.draw_text(self.player_name, 28, OFF_WHITE, WIDTH//2, 330)
        else:
            self.draw_text("Top 5 Ranking:", 28, OFF_WHITE, WIDTH // 2, 300)
            for i, r in enumerate(self.load_ranking()): 
                self.draw_text(f"{i + 1}. {r['name']} - {r['score']}", 22, OFF_WHITE, WIDTH // 2, 350 + i * 30)
            self.draw_text("Pressione ENTER para voltar ao menu", 22, OFF_WHITE, WIDTH // 2, 600)
            
    def draw_ranking_screen(self):
        self.draw_text("RANKING - TOP 5", 48, OFF_WHITE, WIDTH // 2, 100)
        for i, r in enumerate(self.load_ranking()):
            self.draw_text(f"{i + 1}. {r['name']} - {r['score']}", 28, OFF_WHITE, WIDTH // 2, 200 + i * 40)
        mouse_pos = pygame.mouse.get_pos()
        back_color = BUTTON_HOVER_COLOR if self.ranking_back_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, back_color, self.ranking_back_button_rect)
        self.draw_text("Voltar", 28, OFF_WHITE, self.ranking_back_button_rect.centerx, self.ranking_back_button_rect.centery)
        self.draw_text("Pressione ESC para voltar", 20, GRAY, WIDTH // 2, HEIGHT - 40)

    def handle_name_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if len(self.player_name) > 0: self.save_ranking(self.player_name, self.final_score); self.name_input_active = False
            elif event.key == pygame.K_BACKSPACE: self.player_name = self.player_name[:-1]
            elif len(self.player_name) < 12: self.player_name += event.unicode
    
    def get_theme_name(self):
        return self.get_theme_name_by_level(self.level)

    def get_theme_name_by_level(self, level_num):
        if level_num >= 13: return "electric"
        if level_num >= 9: return "volcano"
        if level_num >= 5: return "cave"
        return "forest"

    def get_theme_colors(self):
        return {'forest': THEME_FOREST, 'cave': THEME_CAVE, 'volcano': THEME_VOLCANO, 'electric': THEME_ELECTRIC}[self.get_theme_name()]

    def _setup_level_common(self):
        # Lógica de dragão removida
        for grp_name in ['platforms', 'enemies', 'coins', 'doors', 'spikes', 'powerups', 'particles', 'projectiles', 'hazards', 'ally_projectiles']:
            if hasattr(self, grp_name):
                grp = getattr(self, grp_name)
                grp.empty()
        
        self.all_sprites.empty()
        
        self.all_sprites.add(self.player)
        self.boss = None
        self._create_animated_background()
        
        return None, False 

    def _restore_dragon(self, dragon_instance, was_mounted):
       pass 

    def setup_level(self, level):
        if level in [4, 8, 12, 16]: self.setup_boss_level(); return
        
        self._setup_level_common()
        
        theme_colors, theme_name = self.get_theme_colors(), self.get_theme_name()
        min_plat_width, max_plat_width = max(150, 400 - level*15), max(250, 600 - level*15)
        min_gap_width, max_gap_width = 60 + level*5, 160 + level*5
        enemy_speed, chase_chance = 3 + level*0.5, min(0.8, 0.25 + level*0.05)
        total_width, num_platforms = 0, 10 + level * 3
        
        plat = Platform(0, HEIGHT - 80, 500, 40, theme_colors); self.platforms.add(plat); total_width += 500
        last_y = HEIGHT - 80
        powerup_types = ['pulo_duplo', 'super_pulo', 'dash', 'tiro_forte', 'onda_de_choque', 'escudo', 'ima_de_moedas', 'pontos_em_dobro', 'vida_extra', 'kit_medico']

        for i in range(num_platforms):
            gap_width, plat_width = random.randint(min_gap_width, max_gap_width), random.randint(min_plat_width, max_plat_width)
            y = max(250, min(HEIGHT - 80, last_y + random.randint(-110, 110)))
            last_y = y
            plat_class = SlipperyPlatform if theme_name != 'forest' and random.random() < 0.3 else Platform
            plat = plat_class(total_width + gap_width, y, plat_width, 40, theme_colors)
            self.platforms.add(plat)
            total_width += gap_width + plat_width
            
            spawned_item = False
            if random.random() < 0.15:
                p = PowerUp(plat.rect.midtop - pygame.math.Vector2(0, 20), random.choice(powerup_types))
                self.powerups.add(p); spawned_item = True
            elif random.random() < 0.5: 
                self.coins.add(Coin(plat.rect.centerx, plat.rect.y - 25)); spawned_item = True

            if random.random() < min(0.6 + level * 0.05, 0.9): 
                spawn_type = random.random()
                
                if theme_name == 'electric':
                    if spawn_type < 0.15: # 15% chance for MiniStormDragon
                        self.enemies.add(MiniStormDragon(self, (random.randint(int(plat.rect.left), int(plat.rect.right)), plat.rect.y - 100), theme_name))
                    elif spawn_type < 0.30: # 15% chance for FlyingEnemy
                        self.enemies.add(FlyingEnemy(self, plat.rect.centerx, plat.rect.y - 60, theme_name))
                    else: # 70% chance for ground Enemy
                        self.enemies.add(Enemy(self, plat.rect.centerx, plat.rect.y, plat, theme_name, random.random() < chase_chance, enemy_speed))
                else: # Lógica original para outros biomas
                    if spawn_type < 0.15: # 15% chance for FlyingEnemy
                        self.enemies.add(FlyingEnemy(self, plat.rect.centerx, plat.rect.y - 60, theme_name))
                    elif spawn_type < 0.35: # 20% chance for ExplodingEnemy
                        self.enemies.add(ExplodingEnemy(self, (random.randint(int(plat.rect.left), int(plat.rect.right)), -50), theme_name))
                    else: # 65% chance for ground Enemy
                        self.enemies.add(Enemy(self, plat.rect.centerx, plat.rect.y, plat, theme_name, random.random() < chase_chance, enemy_speed))

            if random.random() < 0.2 + level * 0.05 and not spawned_item: self.spikes.add(Spike(plat.rect.centerx, plat.rect.y, theme_name))
        
        next_level_num = self.level + 1
        next_theme_name = self.get_theme_name_by_level(next_level_num)
        door_pos = (total_width - 150, plat.rect.top)
        door = Door(self, door_pos, next_theme_name)
        self.doors.add(door)
        self.all_sprites.add(self.platforms, self.enemies, self.coins, self.doors, self.spikes, self.powerups, self.particles, self.hazards)
        
        self.player.pos = pygame.math.Vector2(WIDTH // 4, HEIGHT-100); self.player.vel = pygame.math.Vector2(0,0); self.player.on_ground = False

        if level == 1: self.player.reset_powerups()

    def setup_boss_level(self):
        self._setup_level_common()
        
        self.platforms.add(Platform(0, HEIGHT - 40, WIDTH, 40, self.get_theme_colors()))
        self.all_sprites.add(self.platforms)
        
        if self.level == 4: self.boss = ForestGuardian(self)
        elif self.level == 8: self.boss = CrystalHorror(self)
        elif self.level == 12: self.boss = VolcanoBehemoth(self)
        elif self.level == 16: self.boss = StormDragon(self)

        if self.boss:
            self.all_sprites.add(self.boss); self.enemies.add(self.boss)
        
        self.player.pos = pygame.math.Vector2(100, HEIGHT - 100); self.player.vel = pygame.math.Vector2(0,0); self.player.on_ground = False
        
    def boss_defeated(self):
        self.screen_shake = 30
        if self.boss: self.create_particles(self.boss.rect.center, ORANGE, 100)
        
        print(f"🎉 Você derrotou o chefe do nível {self.level}!")

        # --- LÓGICA DE FINAL DO JOGO ---
        if self.level == 16: # Se for o último chefe
            self.final_score = self.player.score
            self.state = 'win' # Manda para a tela de vitória
        else:
            # Se não for o final, spawna o portal
            next_level_num = self.level + 1
            next_theme_name = self.get_theme_name_by_level(next_level_num)
            door_pos = (WIDTH - 100, HEIGHT - 40)
            door = Door(self, door_pos, next_theme_name)
            self.all_sprites.add(door)
            self.doors.add(door)
        
        self.boss = None

    def hitbox_collide(self, player_sprite, other_sprite):
        return player_sprite.hitbox.colliderect(other_sprite.rect)

    def handle_collisions(self):
        for coin in pygame.sprite.spritecollide(self.player, self.coins, True):
            self.player.score += 10 * self.player.score_multiplier
            self.create_particles(coin.rect.center, PARTICLE_COIN_COLOR, 5)

        for p_up in pygame.sprite.spritecollide(self.player, self.powerups, True): self.player.activate_powerup(p_up.type)
        if pygame.sprite.spritecollide(self.player, self.doors, False, collided=self.hitbox_collide):
             self.level += 1; self.setup_level(self.level)
        
        for proj, enemies_hit in pygame.sprite.groupcollide(self.projectiles, self.enemies, False, False).items():
            for enemy in enemies_hit:
                if isinstance(enemy, (Vine, Laser, Projectile)): continue
                if hasattr(enemy, 'take_damage'): enemy.take_damage(proj.damage)
                else: enemy.kill()
                self.player.score += 5 * self.player.score_multiplier
                proj.kill()
        
        if hasattr(self, 'ally_projectiles'):
            for proj, enemies_hit in pygame.sprite.groupcollide(self.ally_projectiles, self.enemies, False, False).items():
                if proj.projectile_type not in ['fireball', 'electricball']:
                    for enemy in enemies_hit:
                        if isinstance(enemy, (Vine, Laser, Projectile)): continue
                        if hasattr(enemy, 'take_damage'): enemy.take_damage(proj.damage)
                        else: enemy.kill()
                        proj.kill()
        
        if not self.player.invincible:
            if pygame.sprite.spritecollide(self.player, self.hazards, False, collided=self.hitbox_collide) or \
               pygame.sprite.spritecollide(self.player, self.spikes, False, collided=self.hitbox_collide):
                self.player.take_damage(SPIKE_DAMAGE)

            for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False, collided=self.hitbox_collide):
                if self.player.is_dashing:
                    if not isinstance(enemy, Boss):
                        enemy.kill(); self.player.score += 15
                elif isinstance(enemy, ExplodingEnemy):
                    if not enemy.is_exploding: enemy.explode()
                elif self.player.vel.y > 0 and self.player.hitbox.bottom < enemy.rect.centery + STOMP_TOLERANCE and not isinstance(enemy, (Vine, Lightning, MiniStormDragon, FlyingEnemy)):
                    if isinstance(enemy, Boss): enemy.take_damage(BOSS_STOMP_DAMAGE)
                    else: enemy.kill(); self.player.score += 20
                    self.player.vel.y = PLAYER_JUMP / 2
                else:
                    damage = 50 if isinstance(enemy, VolcanoBehemoth) and enemy.state == 'charging' else ENEMY_DAMAGE
                    self.player.take_damage(damage)
                    if not isinstance(enemy, (Vine, Lightning)): self.player.knockback(enemy)

    def handle_camera(self):
        if self.boss: return

        dead_zone_width = WIDTH / 4
        left_boundary, right_boundary = (WIDTH / 2) - (dead_zone_width / 2), (WIDTH / 2) + (dead_zone_width / 2)
        
        reference_rect = self.player.rect
        
        scroll_x = 0
        if reference_rect.right > right_boundary:
            scroll_x = reference_rect.right - right_boundary
        if reference_rect.left < left_boundary:
            scroll_x = reference_rect.left - left_boundary
        
        if scroll_x != 0:
            for sprite in self.all_sprites:
                if hasattr(sprite, 'pos'):
                    sprite.pos.x -= scroll_x
                sprite.rect.x -= scroll_x
            
            for sprite in self.all_sprites:
                 if hasattr(sprite, 'start_pos'): sprite.start_pos.x -= scroll_x
                 if hasattr(sprite, 'start_x'): sprite.start_x -= scroll_x
            
            for bg_sprite in self.background_sprites: bg_sprite.rect.x -= scroll_x * bg_sprite.depth

    def player_death(self):
        self.screen_shake = 10; self.player.lives -= 1
        if self.player.lives <= 0:
            self.state = 'game_over'; self.final_score = self.player.score
        else: 
            self.player.reset_powerups(); self.player.health = self.player.max_health
            self.setup_level(self.level)
    
    def restart_level(self):
        self.paused = False; self.player.reset_powerups()
        self.player.health = self.player.max_health;
        self.setup_level(self.level)

    def load_ranking(self):
        if not os.path.exists(self.ranking_file): return []
        try:
            with open(self.ranking_file, "r") as f:
                ranking = json.load(f)
            return sorted(ranking, key=lambda item: item['score'], reverse=True)[:5]
        except (json.JSONDecodeError, FileNotFoundError):
            return [{"name": "Erro", "score": 0, "date": ""}]

    def save_ranking(self, name, score):
        ranking = self.load_ranking()
        new_entry = {"name": name, "score": score, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        ranking.append(new_entry)
        with open(self.ranking_file, "w") as f:
            json.dump(sorted(ranking, key=lambda item: item['score'], reverse=True)[:5], f, indent=4)

    def draw_text(self, text, size, color, x, y, align="center"):
        try:
            font = pygame.font.Font(self.font_path, size)
        except (pygame.error, FileNotFoundError, TypeError):
            font = pygame.font.SysFont("Courier", size, bold=True) # Fallback para Courier
        text_surface = font.render(text, True, color); text_rect = text_surface.get_rect()
        setattr(text_rect, align, (x, y))
        self.screen.blit(text_surface, text_rect)
    
    def create_particles(self, pos, color, count, particle_type='default'):
        for _ in range(count):
            p = Particle(pos, color, particle_type)
            self.all_sprites.add(p); self.particles.add(p)

async def main():
    game = Game()
    await game.run_async()

if __name__ == "__main__":
    asyncio.run(main())

