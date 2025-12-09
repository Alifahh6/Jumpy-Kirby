import pygame
import random
import os
from pygame import mixer
import sys

# ================== SAFE PATH HELPERS ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def asset(file):
    full = os.path.join(ASSETS_DIR, file)
    if not os.path.exists(full):
        print("Asset missing:", full)
        sys.exit(1)
    return full

# ================== LOAD / SAVE HIGHSCORE ==================
def load_highscore():
    if not os.path.exists("score.txt"):
        return 0
    with open("score.txt", "r") as f:
        return int(f.read())

def save_highscore(new_score):
    with open("score.txt", "w") as f:
        f.write(str(new_score))

highscore = load_highscore()

# ================== INITIAL SETUP ==================
pygame.init()
mixer.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jumpy Game OOP")

clock = pygame.time.Clock()
FPS = 60

WHITE = (255,255,255)
BLACK = (0,0,0)

font_small = pygame.font.SysFont("Lucida Sans", 20)
font_big = pygame.font.SysFont("Lucida Sans", 28)
font_title = pygame.font.SysFont("Lucida Sans", 40)

# ================== LOAD MEDIA ==================
pygame.mixer.music.load(asset("fuyu-biyori bgm.mp3"))
pygame.mixer.music.play(-1)
jump_fx = pygame.mixer.Sound(asset("jump.mp3"))
death_fx = pygame.mixer.Sound(asset("death.mp3"))

jumpy_image   = pygame.image.load(asset("caracter.png")).convert_alpha()
platform_image = pygame.image.load(asset("wood.png")).convert_alpha()
bird_sheet_img = pygame.image.load(asset("bird.png")).convert_alpha()

menu_bg = pygame.transform.scale(pygame.image.load(asset("mainmenu.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))
game_over_bg = pygame.transform.scale(pygame.image.load(asset("gameover.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))

background_day     = pygame.transform.scale(pygame.image.load(asset("background1.jpg")), (SCREEN_WIDTH, SCREEN_HEIGHT))
background_evening = pygame.transform.scale(pygame.image.load(asset("background2.jpg")), (SCREEN_WIDTH, SCREEN_HEIGHT))
background_night   = pygame.transform.scale(pygame.image.load(asset("background3.jpg")), (SCREEN_WIDTH, SCREEN_HEIGHT))

# ================== BUTTON IMAGES ==================
start_img   = pygame.transform.scale(pygame.image.load(asset("start.png")).convert_alpha(), (220, 80))
exit_img    = pygame.transform.scale(pygame.image.load(asset("exit.png")).convert_alpha(), (220, 80))
restart_img = pygame.transform.scale(pygame.image.load(asset("restart.png")).convert_alpha(), (220, 80))

# ================== BUTTON CLASS ==================
class ImageButton:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self):
        screen.blit(self.image, self.rect)

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos))

# ================== BUTTON INSTANCE ==================
start_button   = ImageButton(SCREEN_WIDTH//2, 410, start_img)
quit_button    = ImageButton(SCREEN_WIDTH//2, 480, exit_img)
restart_button = ImageButton(SCREEN_WIDTH//2, 380, restart_img)


# ================== CONSTANTS ==================
SCROLL_THRESH = 200
GRAVITY = 0.75
JUMP_VELOCITY = -14
MAX_FALL = 10
HORIZ_SPEED = 5
MAX_PLATFORMS = 10

# ================== GAME STATE ==================
scroll = 0
score = 0.0
bg_scroll = 0
game_over = False
game_state = "menu"

platform_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

# ================== SPRITES ======================
class SpriteSheet:
    def __init__(self, sheet):
        self.sheet = sheet

    def get_image(self, frame, w, h, scale, color):
        img = pygame.Surface((w,h), pygame.SRCALPHA)
        img.blit(self.sheet, (0,0), (frame*w,0,w,h))
        img = pygame.transform.scale(img, (int(w*scale), int(h*scale)))
        img.set_colorkey(color)
        return img

class Player:
    def __init__(self,x,y):
        self.image = pygame.transform.scale(jumpy_image,(45,45))
        self.rect = self.image.get_rect(center=(x,y))
        self.vel_y = 0
        self.flip = False
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        global scroll
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx = -HORIZ_SPEED; self.flip = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = HORIZ_SPEED;  self.flip = False

        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL: self.vel_y = MAX_FALL
        dy += self.vel_y

        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH: dx = SCREEN_WIDTH - self.rect.right

        for p in platform_group:
            if p.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y > 0 and self.rect.bottom <= p.rect.centery:
                    self.rect.bottom = p.rect.top
                    dy = 0
                    self.vel_y = JUMP_VELOCITY
                    jump_fx.play()

        if self.rect.top <= SCROLL_THRESH and self.vel_y < 0:
            scroll = -dy
        else:
            scroll = 0

        self.rect.x += dx
        self.rect.y += dy + scroll
        self.mask = pygame.mask.from_surface(self.image)
        return scroll

    def draw(self):
        screen.blit(pygame.transform.flip(self.image,self.flip,False),self.rect)

class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,width):
        super().__init__()
        self.image = pygame.transform.scale(platform_image,(width,12))
        self.rect = self.image.get_rect(topleft=(x,y))

    def update(self,scroll):
        self.rect.y += scroll
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y,direction,sheet):
        super().__init__()
        self.anim = [SpriteSheet(sheet).get_image(i,32,32,1.5,(0,0,0)) for i in range(8)]
        self.frame=0
        self.image=self.anim[self.frame]
        self.rect=self.image.get_rect(center=(x,y))
        self.direction=direction
        self.anim_timer=0
        self.mask = pygame.mask.from_surface(self.image)

    def update(self,scroll):
        self.anim_timer+=1
        if self.anim_timer>6:
            self.anim_timer=0
            self.frame=(self.frame+1)%len(self.anim)
            self.image=self.anim[self.frame]
            self.mask=pygame.mask.from_surface(self.image)

        self.rect.x += self.direction*2
        self.rect.y += scroll
        if self.rect.right<0 or self.rect.left>SCREEN_WIDTH or self.rect.top>SCREEN_HEIGHT:
            self.kill()

def get_game_bg():
    if score < 200: return background_day
    if score < 800: return background_evening
    return background_night

def reset_game():
    global platform_group, enemy_group, player, score, bg_scroll, game_over
    score = 0.0
    bg_scroll = 0
    game_over = False
    platform_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()

    first_y = SCREEN_HEIGHT - 80
    first = Platform(SCREEN_WIDTH//2 - 50, first_y, 100)
    platform_group.add(first)

    y = first_y - 65
    prev_x = SCREEN_WIDTH//2
    for i in range(8):
        pw = random.randint(50,90)
        x = max(40, min(prev_x + random.randint(-120,120), SCREEN_WIDTH - pw - 40))
        platform_group.add(Platform(x, y, pw))
        prev_x = x
        y -= 65

    player = Player(SCREEN_WIDTH//2, first_y - 20)

reset_game()

# ================== GAME LOOP ==================
run = True
while run:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run=False

        if game_state=="menu":
            if start_button.clicked(event):
                game_state="play"
                reset_game()
            if quit_button.clicked(event):
                run=False

        if game_over:
            if restart_button.clicked(event):
                reset_game()
                game_over=False
                game_state="play"

    if game_state=="menu":
        screen.blit(menu_bg,(0,0))
        screen.blit(font_big.render(f"Best Score: {int(highscore)}", True, WHITE), (SCREEN_WIDTH//2 - 100, 270))
        start_button.draw()
        quit_button.draw()
        pygame.display.update()
        continue

    if not game_over:
        screen.blit(get_game_bg(),(0,bg_scroll))
        screen.blit(get_game_bg(),(0,-SCREEN_HEIGHT+bg_scroll))

        sc = player.move()
        bg_scroll+=sc
        if bg_scroll>=SCREEN_HEIGHT: bg_scroll=0

        if len(platform_group)<MAX_PLATFORMS and random.random()<0.4:
            w=random.randint(50,90)
            x=random.randint(40,SCREEN_WIDTH-w-40)
            y=random.randint(-100,-20)
            platform_group.add(Platform(x,y,w))
            if random.random()<0.12:
                enemy_group.add(Enemy(x+w//2,y-40,random.choice([-1,1]),bird_sheet_img))

        platform_group.update(sc)
        enemy_group.update(sc)

        platform_group.draw(screen)
        enemy_group.draw(screen)
        player.draw()

        if sc>0: score+=1

        hits = pygame.sprite.spritecollide(player,enemy_group,False)
        for e in hits:
            if pygame.sprite.collide_mask(player,e):
                game_over=True
                death_fx.play()
                if score>highscore:
                    highscore=score
                    save_highscore(int(highscore))

        if player.rect.top>SCREEN_HEIGHT:
            game_over=True
            death_fx.play()
            if score>highscore:
                highscore=score
                save_highscore(int(highscore))

        screen.blit(font_small.render(f"Score: {int(score)}",True,WHITE),(10,10))

    else:
        screen.blit(game_over_bg,(0,0))
        score_text = font_big.render(f"Score: {int(score)}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 200))

        best_text = font_big.render(f"Best Score: {int(highscore)}", True, WHITE)
        screen.blit(best_text, (SCREEN_WIDTH//2 - best_text.get_width()//2, 240))

        restart_button.draw()

    pygame.display.update()

pygame.quit()
