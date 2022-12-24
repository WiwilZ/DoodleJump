import pygame
from pygame.locals import *
from pygame.math import Vector2
import random
import sys

WIDTH, HEIGHT = 600, 800
pygame.init()
display_surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF, vsync=1)
pygame.display.set_caption("Doodle Jump")


class Background:
    def draw(self, display_surface):
        display_surface.fill((255, 250, 240))
        for i in range(0, WIDTH, 14):
            pygame.draw.line(display_surface, (240, 230, 140), (i, 0), (i, HEIGHT))
        for i in range(0, HEIGHT, 14):
            pygame.draw.line(display_surface, (240, 230, 140), (0, i), (WIDTH, i))

    def update(self):
        pass


class Player:
    images = [pygame.image.load(f"assets/player_{name}.png").convert_alpha() for name in
              ('left', 'right', 'left_jump', 'right_jump')]
    width, height = images[0].get_size()
    ACC = Vector2(0, 0.6)
    INITIAL_Y_VEL = 13
    
    def __init__(self, pos):
        self.pos = pos
        self.vel = Vector2(0, -self.INITIAL_Y_VEL)
        self.direction = 0
        self.surf = self.images[0]
        self.rect = self.surf.get_rect()
        self.rect.midbottom = self.pos  # 把锚点设为中下点
        self.level = 0
        self.stay = False

    def draw(self, display_surface):
        display_surface.blit(self.surf, self.rect)

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


class Platform:
    images = [pygame.image.load(f"assets/platform_{name}.png").convert_alpha() for name in
              ('green', 'blue', 'red', 'red_break')]
    width, height = images[0].get_size()

    def __init__(self, pos, level):
        self.pos = pos
        self.rect = self.surf.get_rect()
        self.rect.midtop = self.pos  # 把锚点设为中上点
        self.level = level

    def draw(self, display_surface):
        display_surface.blit(self.surf, self.rect)

    def update(self):
        self.rect.midtop = self.pos


class GreenPlatform(Platform):
    def __init__(self, pos, level):
        self.surf = self.images[0]
        super().__init__(pos, level)


class BluePlatform(Platform):
    def __init__(self, pos, level):
        self.surf = self.images[1]
        super().__init__(pos, level)
        self.vel = Vector2(8, 0)

    def update(self):
        if not (self.width / 2 <= self.pos.x <= WIDTH - self.width / 2):
            self.vel.x = -self.vel.x
        self.pos += self.vel
        self.rect.midtop = self.pos


class RedPlatform(Platform):
    def __init__(self, pos, level):
        self.surf = self.images[2]
        super().__init__(pos, level)

    def set_broken(self):
        self.surf = self.images[3]
        self.rect = self.surf.get_rect()


class Spring:
    images = [
        pygame.image.load("assets/spring.png").convert_alpha(),
        pygame.image.load("assets/spring_bounce.png").convert_alpha(),
    ]
    width, height = images[0].get_size()

    def __init__(self, pos):
        self.is_released = False
        self.pos = pos
        self.surf = self.images[0]
        self.rect = self.surf.get_rect()
        self.rect.midbottom = self.pos  # 把锚点设为中下点

    def draw(self, display_surface):
        display_surface.blit(self.surf, self.rect)

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
        self.player = None
        self.springs = []
        self.platforms = []
        self.level = 0
        self.platformLevel = 1

    def add_platform_and_spring(self, y):
        x = random.uniform(Platform.width // 2, WIDTH - Platform.width // 2)
        p = random.choice([GreenPlatform] * 6 + [BluePlatform] * 3 + [RedPlatform])
        self.platforms.append(p(Vector2(x, y), self.platformLevel))
        if p == GreenPlatform and random.randint(1, 5) == 1:
            self.springs.append(Spring(Vector2(x + (Platform.width - Spring.width) / 2 * random.uniform(-1, 1), y + 2)))
        self.platformLevel += 1
        
    def detect_collision(self):
        # 与平台碰撞
        for platform in self.platforms:
            if self.player.vel.y >= 0 and abs(self.player.pos.y - platform.pos.y) < 5 and abs(
                    self.player.pos.x - platform.pos.x) < (Player.width + Platform.width) / 2:
                if isinstance(platform, RedPlatform):
                    platform.set_broken()
                else:
                    self.player.vel.y = -Player.INITIAL_Y_VEL
                    self.level += max(platform.level - self.player.level, 0)
                    self.player.pos.y = platform.pos.y
                    self.player.level = max(platform.level, self.player.level)
                    self.player.stay = True

        # 与弹簧碰撞
        for spring in self.springs:
            if self.player.vel.y >= 0 and abs(self.player.pos.y - spring.rect.top) < 5 and abs(
                    self.player.pos.x - spring.pos.x) < (Player.width + Spring.width) / 2 and not spring.is_released:
                self.player.vel.y = -Player.INITIAL_Y_VEL * 1.5
                spring.set_released()

    def run(self):
        self.level = 0
        self.platformLevel = 1
        self.player = Player(Vector2(WIDTH / 2, HEIGHT - 50))
        self.springs = []
        self.platforms = [GreenPlatform(Vector2(self.player.pos), 0)]
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
