import math
import random
import sys

import pygame
from pygame.locals import *
from pygame.math import Vector2

WIDTH, HEIGHT = 600, 800
pygame.init()
display_surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF, vsync=1)
pygame.display.set_caption("Doodle Jump")


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
    images = [pygame.image.load(f"assets/player/{name}.png").convert_alpha() for name in
              ('idle_left', 'idle_right', 'jump_left', 'jump_right')]
    width, height = images[0].get_size()
    ACC = Vector2(0, 0.6)
    INITIAL_SPEED_Y = 13

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
    images = [pygame.image.load(f"assets/platform/{name}.png").convert_alpha() for name in
              ('green', 'blue', 'red', 'broken')]
    width, height = images[0].get_size()

    def __init__(self, pos: Vector2, type: int, level: int):
        super().__init__(self.images[type])
        self.pos = pos
        self.type = type
        self.level = level
        self.speed = 8 if type == 1 else 0
        self.is_broken = False  # for red
        self.rect.midtop = self.pos  # 把锚点设为中上点

    def update(self):
        if not (self.width / 2 < self.pos.x < WIDTH - self.width / 2):
            self.speed = -self.speed
        self.pos.x += self.speed
        self.rect.midtop = self.pos

    def set_broken(self):
        self.is_broken = True
        self.surf = self.images[3]
        self.rect = self.surf.get_rect()


class Spring(Entity):
    images = [pygame.image.load(f"assets/spring/{name}.png").convert_alpha() for name in ('idle', 'released')]
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
    MAX_SPEED = 2.0

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.background = Background()

    def reset(self):
        self.level = 0
        self.platform_level = 1
        self.player = Player(Vector2(WIDTH / 2, HEIGHT - 50))
        self.springs = []
        self.platforms = []

    def add_platform_and_spring(self, y):
        x = random.uniform(math.ceil(Platform.width / 2), math.floor(WIDTH - Platform.width / 2))
        # 绿、蓝、红按6 : 3 : 1的概率生成平台
        platform_type = random.choice([0] * 6 + [1] * 3 + [2])
        self.platforms.append(Platform(Vector2(x, y), platform_type, self.platform_level))
        # 绿色平台 1/5 概率生成弹簧
        if platform_type == 0 and random.randint(1, 5) == 1:
            self.springs.append(Spring(Vector2(x + (Platform.width - Spring.width) / 2 * random.uniform(-1, 1), y + 2)))
        self.platform_level += 1

    def detect_collision(self):
        # 与平台碰撞
        for platform in self.platforms:
            if self.player.vel.y > 0 and abs(self.player.pos.y - platform.pos.y) < 10 and abs(
                    self.player.pos.x - platform.pos.x) < (Player.width + Platform.width) / 2:
                if platform.type == 2:  # red
                    if platform.is_broken:
                        continue
                    platform.set_broken()
                self.player.vel.y = -Player.INITIAL_SPEED_Y
                self.level += max(platform.level - self.player.level, 0)
                self.player.pos.y = platform.pos.y
                self.player.level = max(platform.level, self.player.level)
                self.player.stay = True

        # 与弹簧碰撞
        for spring in self.springs:
            if self.player.vel.y >= 0 and abs(self.player.pos.y - spring.rect.top) < 10 and abs(
                    self.player.pos.x - spring.pos.x) < (Player.width + Spring.width) / 2 and not spring.is_released:
                self.player.vel.y = -Player.INITIAL_SPEED_Y * 1.5
                spring.set_released()

    def run(self):
        self.reset()
        # 第一个平台位于角色出生位置
        self.platforms.append(Platform(Vector2(self.player.pos), 0, 0))
        # 生成上面的平台
        for y in range(int(self.player.pos.y - 60), 0, -60):
            self.add_platform_and_spring(y)

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            for e in [self.background, self.player] + self.platforms + self.springs:
                e.update()
                e.draw(display_surface)

            self.detect_collision()

            # 角色靠近上面立刻刷新平台
            if self.player.pos.y - 120 <= 0 and self.player.stay:
                for e in self.platforms + self.springs:
                    e.pos.y += HEIGHT - 120
                self.player.pos.y += HEIGHT - 120
                for y in range(int(self.player.pos.y - 120), 0, -60):
                    self.add_platform_and_spring(y)

            # 平台下落
            val = min(self.level * 0.01, self.MAX_SPEED)
            for e in self.platforms + self.springs:
                e.pos.y += val

            for i in range(len(self.platforms) - 1, -1, -1):
                if self.platforms[i] and self.platforms[i].pos.y > HEIGHT:
                    self.platforms.pop(i)
            for i in range(len(self.springs) - 1, -1, -1):
                if self.springs[i] and self.springs[i].pos.y > HEIGHT:
                    self.springs.pop(i)

            # 在上方新增平台
            y = self.platforms[-1].pos.y - 60
            if y >= 0:
                self.add_platform_and_spring(y)

            # 玩家掉出屏幕重新开始
            if self.player.rect.top > HEIGHT:
                pygame.init()
                self.run()

            pygame.display.update()
            self.clock.tick(self.FPS)


Game().run()
