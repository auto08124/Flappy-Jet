import pygame
import random
import sys
import os
import json

# Initialize pygame
pygame.init()
FPS = 120

# Screen settings
WIDTH, HEIGHT = 800, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Jet")

# Save file path
SAVE_FILE = "flappy_jet_save.json"

# Load sounds
score_sound = pygame.mixer.Sound('Background/SOUND/SCORE.mp3')
hit_sound = pygame.mixer.Sound('Background/SOUND/DEATH.mp3')
jump_sound = pygame.mixer.Sound('Background/SOUND/Cartoon Jump Sound Effect.mp3')
coin_sound = pygame.mixer.Sound('Background/SOUND/sound1.wav')
explosion_sound = pygame.mixer.Sound('Background/SOUND/Explosion.wav')
game_over_sounds = [
    pygame.mixer.Sound('Background/SOUND/To Be Continued.mp3'),
    pygame.mixer.Sound('Background/SOUND/Emotional Damage.mp3'),
    pygame.mixer.Sound('Background/SOUND/AUN1.mp3')
]

# Set volumes
score_sound.set_volume(0.03)
hit_sound.set_volume(0.3)
jump_sound.set_volume(0.03)
coin_sound.set_volume(0.15)
explosion_sound.set_volume(0.05)
for sound in game_over_sounds:
    sound.set_volume(0.3)

# Background music
pygame.mixer.music.load('Background/SOUND/We are.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

# Load background
background = pygame.image.load('Background/Background/SKY.jpg')
background = pygame.transform.scale(background, (800, 650))

# Animation variables
current_frame = 0
animation_speed = 0.2
frame_counter = 0
explosion_frame = 0
explosion_speed = 0.4
explosion_counter = 0
explosion_active = False
explosion_x = 0
explosion_y = 0

def create_thrust_frame(base_frame):
    thrust_frame = base_frame.copy()
    
    # Create blue engine glow with three layers
    layers = [
        {"size": (45, 25), "color": (100, 200, 255, 200), "offset": (-8, 12)},  # Outer (lightest)
        {"size": (35, 20), "color": (50, 150, 255, 180), "offset": (-5, 15)},   # Middle
        {"size": (25, 15), "color": (0, 100, 255, 220), "offset": (-2, 18)}     # Inner (brightest)
    ]
    
    for layer in layers:
        glow = pygame.Surface(layer["size"], pygame.SRCALPHA)
        pygame.draw.ellipse(glow, layer["color"], (0, 0, layer["size"][0], layer["size"][1]))
        thrust_frame.blit(glow, layer["offset"])
    
    # Add small white core
    core = pygame.Surface((10, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(core, (255, 255, 255, 200), (0, 0, 10, 6))
    thrust_frame.blit(core, (5, 22))
    
    return thrust_frame

# Load jet animation with thrust frames
jet_frames = []
thrust_frames = []

try:
    # Try to load 4 animation frames (jet1.png to jet4.png)
    for i in range(1, 5):
        # Load normal jet frame
        frame = pygame.image.load(f'Background/Jet/jet1{i}.png').convert_alpha()
        frame = pygame.transform.scale(frame, (90, 50))
        jet_frames.append(frame)
        # Create blue thrust version
        thrust_frames.append(create_thrust_frame(frame))

except:
    # Fallback if no animation frames found
    try:
        frame = pygame.image.load('Background/Jet/Jetbg 1.png').convert_alpha()
        frame = pygame.transform.scale(frame, (90, 50))
    except:
        # Create a simple placeholder if no image found
        frame = pygame.Surface((90, 50), pygame.SRCALPHA)
        pygame.draw.polygon(frame, (200, 200, 200), [(10,25), (80,10), (80,40)])  # Jet body
    
    jet_frames.append(frame)
    thrust_frames.append(create_thrust_frame(frame))

# Make sure we have at least one frame
if not jet_frames:
    # Create a simple placeholder if everything failed
    frame = pygame.Surface((90, 50), pygame.SRCALPHA)
    pygame.draw.polygon(frame, (200, 200, 200), [(10,25), (80,10), (80,40)])  # Jet body
    jet_frames.append(frame)
    thrust_frames.append(create_thrust_frame(frame))

# Load explosion
explosion_frames = []
try:
    for i in range(1, 9): 
        frame = pygame.image.load(f'GAME/Explosion/Explosion01_frame2{i}.png')
        frame = pygame.transform.scale(frame, (120, 120))
        explosion_frames.append(frame)
except:
    for i in range(6):
        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        radius = 20 + i*15
        color = (255, 165 - i*20, 0, 200 - i*30)
        pygame.draw.circle(surf, color, (60, 60), radius)
        explosion_frames.append(surf)

# Load coin
try:
    coin_img = pygame.image.load('Background/Coin/Coin1.png')
    coin_img = pygame.transform.scale(coin_img, (30, 30))
except:
    coin_img = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(coin_img, (255, 215, 0), (15, 15), 15)
    pygame.draw.circle(coin_img, (255, 255, 0), (15, 15), 12)

# Pipe setup
pipe_img = pygame.image.load('Background/Background/pipe.png')
pipe_width = 100
pipe_img = pygame.transform.scale(pipe_img, (pipe_width, HEIGHT))
pipe_img_flipped = pygame.transform.flip(pipe_img, False, True)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
NEON_GREEN = (57, 255, 20)
NEON_BLUE = (0, 160, 255)
GOLD = (255, 215, 0)

# Game variables
bird_x = 50
bird_y = HEIGHT // 2
bird_velocity = 0
gravity = 0.2
jump_strength = -6.5 
air_resistance = 0.95
score = 0
coins_collected = 0
high_score = 0
last_score = 0
total_coins = 0

pipe_gap = 200
pipe_velocity = 4

# Coin variables
coins = []
coin_spawn_timer = 0
coin_spawn_interval = 150
coin_speed = 3

# Fonts
font = pygame.font.SysFont("Arial", 25)
game_over_font = pygame.font.SysFont("Arial", 64)

# Clock
clock = pygame.time.Clock()

def load_game():
    global high_score, total_coins
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            high_score = data.get('high_score', 0)
            total_coins = data.get('total_coins', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        high_score = 0
        total_coins = 0

def save_game():
    data = {
        'high_score': high_score,
        'total_coins': total_coins
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def draw_bird(x, y):
    global current_frame, frame_counter
    frame_counter += animation_speed
    if frame_counter >= 1:
        current_frame = (current_frame + 1) % len(jet_frames)
        frame_counter = 0
    
    # Rotate jet based on velocity
    angle = bird_velocity * -4  
    
    # Use thrust frames when ascending (space pressed)
    if bird_velocity < 0:  # Negative velocity means ascending
        frame_to_draw = thrust_frames[current_frame]
    else:
        frame_to_draw = jet_frames[current_frame]
    
    rotated_jet = pygame.transform.rotate(frame_to_draw, angle)
    screen.blit(rotated_jet, (x, y))

def create_pipe():
    height = random.randint(100, HEIGHT - pipe_gap - 100)
    top_pipe = pygame.Rect(WIDTH, 0, pipe_width, height)
    bottom_pipe = pygame.Rect(WIDTH, height + pipe_gap, pipe_width, HEIGHT - height - pipe_gap)
    return top_pipe, bottom_pipe

def move_pipes(pipes):
    for pipe in pipes:
        pipe[0].x -= pipe_velocity
        pipe[1].x -= pipe_velocity

def draw_pipes(pipes):
    for pipe in pipes:
        screen.blit(pipe_img_flipped, (pipe[0].x, pipe[0].bottom - HEIGHT))
        screen.blit(pipe_img, (pipe[1].x, pipe[1].top))

def spawn_coin():
    y = random.randint(100, HEIGHT - 100)
    coin_rect = pygame.Rect(WIDTH, y, 30, 30)
    coins.append(coin_rect)

def move_coins():
    for coin in coins[:]:
        coin.x -= coin_speed
        if coin.right < 0:
            coins.remove(coin)

def draw_coins():
    for coin in coins:
        screen.blit(coin_img, coin)

def check_coin_collision(bird_rect):
    global coins_collected, score, total_coins
    for coin in coins[:]:
        if bird_rect.colliderect(coin):
            coins.remove(coin)
            coins_collected += 1
            total_coins += 1
            score += 5
            coin_sound.play()

def trigger_explosion(x, y):
    global explosion_active, explosion_x, explosion_y, explosion_frame, explosion_counter
    explosion_active = True
    explosion_x = x - 60
    explosion_y = y - 60
    explosion_frame = 0
    explosion_counter = 0
    explosion_sound.play()

def update_explosion():
    global explosion_active, explosion_frame, explosion_counter
    if explosion_active:
        explosion_counter += explosion_speed
        if explosion_counter >= 1:
            explosion_frame += 1
            explosion_counter = 0
            if explosion_frame >= len(explosion_frames):
                explosion_active = False

def draw_explosion():
    if explosion_active:
        screen.blit(explosion_frames[explosion_frame], (explosion_x, explosion_y))

def reset_game():
    global bird_y, bird_velocity, score, coins_collected, current_frame, frame_counter, explosion_active
    bird_y = HEIGHT // 2
    bird_velocity = 0
    score = 0
    coins_collected = 0
    current_frame = 0
    frame_counter = 0
    explosion_active = False
    coins.clear()
    return [create_pipe()]

def show_game_over():
    screen.blit(background, (0, 0))
    
    game_over_text = game_over_font.render("GAME OVER", True, NEON_BLUE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 5))

    score_box = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 3, 100, 130)
    pygame.draw.rect(screen, WHITE, score_box, border_radius=10)
    pygame.draw.rect(screen, BLACK, score_box, 2)

    score_text = font.render("SCORE", True, RED)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 10))

    score_value = font.render(str(last_score), True, BLACK)
    screen.blit(score_value, (WIDTH // 2 - score_value.get_width() // 2, HEIGHT // 3 + 40))

    best_text = font.render("BEST", True, RED)
    screen.blit(best_text, (WIDTH // 2 - best_text.get_width() // 2, HEIGHT // 3 + 70))

    best_value = font.render(str(high_score), True, BLACK)
    screen.blit(best_value, (WIDTH // 2 - best_value.get_width() // 2, HEIGHT // 3 + 100))

    retry_text = font.render("Press R to Restart", True, NEON_GREEN)
    screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 50))

    quit_text = font.render("Press Q to Quit", True, NEON_BLUE)
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 90))

    reset_text = font.render("Press Z to Reset Scores", True, RED)
    screen.blit(reset_text, (WIDTH // 2 - reset_text.get_width() // 2, HEIGHT // 2 + 130))

    pygame.display.flip()

def game_loop():
    global bird_y, bird_velocity, score, high_score, last_score, current_frame, frame_counter, coin_spawn_timer, total_coins, coins_collected

    load_game()
    pipes = reset_game()
    run_game = True
    pygame.mixer.music.play(-1, 0.0)

    while run_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = jump_strength
                    jump_sound.play()
                    current_frame = 0
                    frame_counter = 0
                elif event.key == pygame.K_q:
                    save_game()
                    pygame.quit()
                    sys.exit()

        # Apply gravity
        bird_velocity += gravity
        bird_velocity *= air_resistance
        bird_y += bird_velocity

        # Check boundaries
        if bird_y <= 0:
            bird_y = 0
            bird_velocity = 0
        if bird_y >= HEIGHT - jet_frames[0].get_height():
            bird_y = HEIGHT - jet_frames[0].get_height()
            bird_velocity = 0
            last_score = score
            if score > high_score:
                high_score = score
            save_game()
            trigger_explosion(bird_x, bird_y)
            
            for _ in range(10):
                screen.blit(background, (0, 0))
                draw_pipes(pipes)
                draw_coins()
                draw_explosion()
                screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 10))
                screen.blit(font.render(f"Coins: {coins_collected}", True, GOLD), (10, 40))
                pygame.display.update()
                clock.tick(60)
                update_explosion()

            random.choice(game_over_sounds).play()
            show_game_over()
            waiting = True
            pygame.mixer.music.stop()

            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        save_game()
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            pygame.mixer.stop()
                            pipes = reset_game()
                            waiting = False
                        elif event.key == pygame.K_q:
                            save_game()
                            pygame.quit()
                            sys.exit()
                        elif event.key == pygame.K_z:
                            high_score = 0
                            total_coins = 0
                            coins_collected = 0
                            save_game()
                            show_game_over()

        move_pipes(pipes)
        if pipes[0][0].x < -pipe_width:
            pipes.pop(0)
            pipes.append(create_pipe())
            score += 1
            score_sound.play()

        coin_spawn_timer += 1
        if coin_spawn_timer >= coin_spawn_interval:
            spawn_coin()
            coin_spawn_timer = 0
        move_coins()

        bird_rect = pygame.Rect(bird_x, bird_y, jet_frames[0].get_width(), jet_frames[0].get_height())
        check_coin_collision(bird_rect)
        
        for pipe in pipes:
            if pipe[0].colliderect(bird_rect) or pipe[1].colliderect(bird_rect):
                last_score = score
                if score > high_score:
                    high_score = score
                save_game()
                trigger_explosion(bird_x, bird_y)
                
                for _ in range(10):
                    screen.blit(background, (0, 0))
                    draw_pipes(pipes)
                    draw_coins()
                    draw_explosion()
                    screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 10))
                    screen.blit(font.render(f"Coins: {coins_collected}", True, GOLD), (10, 40))
                    pygame.display.update()
                    clock.tick(60)
                    update_explosion()

                random.choice(game_over_sounds).play()
                show_game_over()
                waiting = True
                pygame.mixer.music.stop()

                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            save_game()
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                pygame.mixer.stop()
                                pipes = reset_game()
                                waiting = False
                            elif event.key == pygame.K_q:
                                save_game()
                                pygame.quit()
                                sys.exit()
                            elif event.key == pygame.K_z:
                                high_score = 0
                                total_coins = 0
                                coins_collected = 0
                                save_game()
                                show_game_over()

        update_explosion()

        screen.blit(background, (0, 0))
        draw_pipes(pipes)
        draw_coins()
        if not explosion_active:
            draw_bird(bird_x, bird_y)
        draw_explosion()
        
        screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Coins: {coins_collected}", True, GOLD), (10, 40))
        screen.blit(font.render(f"High Score: {high_score}", True, NEON_BLUE), (10, 70))

        pygame.display.update()
        clock.tick(60)

game_loop()