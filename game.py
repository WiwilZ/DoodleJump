import math
import random
import sys
from itertools import chain

import pygame
from pygame.locals import *
from pygame.math import Vector2

WIDTH, HEIGHT = 600, 800
pygame.init()
display_surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF, vsync=1)
pygame.display.set_caption("Doodle Jump")

# 声音
jump_sound = pygame.mixer.Sound('assets/sound/jump.wav')
high_jump_sound = pygame.mixer.Sound('assets/sound/highJump2.wav')
death_sound = pygame.mixer.Sound('assets/sound/death.wav')

# 字体
font = pygame.freetype.Font("assets/font/al-seana.ttf", 36)


def load_image(filepath):
    return pygame.image.load(f"assets/image/{filepath}.png").convert_alpha()


class Entity:
    def __init__(self, surf: pygame.Surface):
        self.surf = surf
        self.rect = self.surf.get_rect()

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surf, self.rect)

    def update(self):
        pass


class Background(Entity):
    def __init__(self):
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.fill((255, 250, 240))
        for i in range(0, WIDTH, 14):
            pygame.draw.line(surf, (240, 230, 140), (i, 0), (i, HEIGHT))
        for i in range(0, HEIGHT, 14):
            pygame.draw.line(surf, (240, 230, 140), (0, i), (WIDTH, i))
        super().__init__(surf)


class Player(Entity):
    images = [load_image(f"player/{name}") for name in ('idle_left', 'idle_right', 'jump_left', 'jump_right')]
    width, height = images[0].get_size()
    ACC = Vector2(0, 0.7)
    INITIAL_SPEED_Y = 15

    def __init__(self, pos: Vector2):
        super().__init__(self.images[0])
        self.pos = pos
        self.vel = Vector2(0, -self.INITIAL_SPEED_Y)
        self.direction = 0
        self.level = 0
        self.stay = False
        self.rect.midbottom = self.pos  # 把锚点设为中下点

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_LEFT] or pressed_keys[K_a]:
            self.vel.x = -5
            self.direction = 0
        elif pressed_keys[K_RIGHT] or pressed_keys[K_d]:
            self.vel.x = 5
            self.direction = 1
        else:
            self.vel.x = 0

        self.vel += self.ACC
        self.pos += self.vel + 0.5 * self.ACC

        if self.pos.x < 0:
            self.pos.x = WIDTH
        elif self.pos.x > WIDTH:
            self.pos.x = 0

        if self.direction == 0:
            self.surf = self.images[0 if self.vel.y < 0 else 2]
        else:
            self.surf = self.images[1 if self.vel.y < 0 else 3]
        self.rect.midbottom = self.pos
        self.stay = False


class Platform(Entity):
    images = [load_image(f"platform/{name}") for name in ('green', 'blue', 'red', 'broken')]
    width, height = images[0].get_size()

    '''type: 0: green 1: blue 2: red 3: green with spring'''

    def __init__(self, pos: Vector2, type: int, level: int):
        super().__init__(self.images[type % 3])
        self.pos = pos
        self.type = type
        self.level = level
        self.speed = 8 if type == 1 else 0
        if type == 3:
            self.spring = Spring(pos + Vector2((Platform.width - Spring.width) / 2 * random.uniform(-1, 1), 0))
        self.is_broken = False  # for red
        self.rect.midtop = self.pos  # 把锚点设为中上点

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        if self.type == 3:
            self.spring.draw(screen)

    def update(self):
        if not (self.width / 2 < self.pos.x < WIDTH - self.width / 2):
            self.speed = -self.speed
        self.pos.x += self.speed
        self.rect.midtop = self.pos
        if self.type == 3:
            self.spring.update()

    def is_collide_with(self, player: Player):
        if self.type == 2:
            if self.is_broken:
                return False
        elif self.type == 3:
            if (not self.spring.is_released
                    and abs(player.pos.x - self.spring.pos.x) < (Player.width + Spring.width) / 2
                    and abs(player.rect.bottom - self.spring.rect.top) < 10):
                return True
        return (abs(player.pos.x - self.pos.x) < (Player.width + Platform.width) / 2
                and abs(player.rect.bottom - self.rect.top) < 10)

    def drop(self, delta):
        self.pos.y += delta
        if self.type == 3:
            self.spring.pos.y += delta

    def set_broken(self):
        self.is_broken = True
        self.surf = self.images[3]
        self.rect = self.surf.get_rect()


class Spring(Entity):
    images = [load_image(f"spring/{name}") for name in ('idle', 'released')]
    width, height = images[0].get_size()

    def __init__(self, pos: Vector2):
        super().__init__(self.images[0])
        self.is_released = False
        self.pos = pos
        self.rect.midbottom = self.pos  # 把锚点设为中下点

    def update(self):
        self.rect.midbottom = self.pos

    def set_released(self):
        self.is_released = True
        self.surf = self.images[1]
        self.rect = self.surf.get_rect()


class Game:
    FPS = 60
    SPEED_UP = 0.05
    MAX_SPEED = 4.0

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.background = Background()

    def reset(self):
        self.level = 0
        self.platform_level = 1
        self.player = Player(Vector2(WIDTH / 2, HEIGHT - 50))
        self.platforms = []

    def add_platform(self, y: float):
        x = random.uniform(math.ceil(Platform.width / 2), math.floor(WIDTH - Platform.width / 2))
        # 绿、蓝、红、弹簧按10 : 4 : 3 : 2的概率生成平台
        platform_type = random.choice([0] * 10 + [1] * 4 + [2] * 3 + [3] * 2)
        self.platforms.append(Platform(Vector2(x, y), platform_type, self.platform_level))
        self.platform_level += 1

    def detect_collision(self):
        for platform in self.platforms:
            if self.player.vel.y > 0 and platform.is_collide_with(self.player):
                if platform.type == 2:
                    if platform.is_broken:
                        continue
                    platform.set_broken()
                elif platform.type == 3:
                    if not platform.spring.is_released:
                        self.player.vel.y = -Player.INITIAL_SPEED_Y * 1.4
                        platform.spring.set_released()
                        pygame.mixer.Sound.play(high_jump_sound)
                        continue
                self.player.vel.y = -Player.INITIAL_SPEED_Y
                self.level += max(platform.level - self.player.level, 0)
                self.player.pos.y = platform.pos.y
                self.player.level = max(platform.level, self.player.level)
                self.player.stay = True
                pygame.mixer.Sound.play(jump_sound)

    def run(self):
        self.reset()
        # 第一个平台位于角色出生位置
        self.platforms.append(Platform(Vector2(self.player.pos), 0, 0))
        # 播放背景音乐
        pygame.mixer.music.load("assets/sound/music.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        # 生成上面的平台
        for y in range(int(self.player.pos.y - 60), 0, -60):
            self.add_platform(y)

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            for e in chain((self.background, self.player), self.platforms):
                e.update()
                e.draw(display_surface)

            # 显示得分
            font.render_to(display_surface, (450, 30), f"Score: {self.level}", fgcolor=(0, 0, 0), size=30)

            self.detect_collision()

            # 角色靠近上面立刻刷新平台
            if self.player.pos.y <= 400:
                delta = ((400 - self.player.pos.y) / 400) * 20
                for platform in self.platforms:
                    platform.drop(delta)
                self.player.pos.y += delta

            # 平台下落
            delta = min(self.level * self.SPEED_UP, self.MAX_SPEED)
            for platform in self.platforms:
                platform.drop(delta)

            # 移除掉出屏幕的平台
            for i, platform in enumerate(reversed(self.platforms)):
                if platform.pos.y > HEIGHT:
                    self.platforms = self.platforms[-i:]

            # 在上方新增平台
            y = self.platforms[-1].pos.y - 60
            if y >= -60:
                self.add_platform(y)

            # 玩家掉出屏幕重新开始
            if self.player.rect.top > HEIGHT:
                pygame.mixer.Sound.play(death_sound)
                pygame.init()
                self.run()

            pygame.display.update()
            self.clock.tick(self.FPS)


Game().run()
