import pygame
import random
import time
from itertools import cycle

# Initialize Pygame
pygame.init()

# Audio
hit_sounds = ['Audio/hit1.mp3', 'Audio/hit2.mp3', 'Audio/hit3.mp3', 'Audio/hit4.mp3']
pygame.mixer.init()
BACKGROUND_CHANNEL = 0
SHOOTING_CHANNEL = 1
HIT_CHANNEL = 2  # Adding a new dedicated channel for hit sounds

def play_sound(file_path, loop=False, channel=None):
    """Plays a sound file on the specified Pygame mixer channel."""
    try:
        sound = pygame.mixer.Sound(file_path)
        if loop:
            pygame.mixer.Channel(channel).play(sound, -1)
        else:
            pygame.mixer.Channel(channel).play(sound)
        return sound
    except pygame.error as e:
        print(f"Error loading sound {file_path}: {e}")

def stop_sound(channel):
    """Stops playback on the specified Pygame mixer channel."""
    pygame.mixer.Channel(channel).stop()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Space Shooter')

# Load images
background = pygame.image.load('background.jpg')
player_image = pygame.image.load('player.png')
player_image = pygame.transform.scale(player_image, (50, 50))
enemy_images = [pygame.transform.scale(pygame.image.load(f'enemy{i}.png'), (50, 50)) for i in range(1, 6)]
bullet_image = pygame.image.load('bullet.png')
bullet_image = pygame.transform.scale(bullet_image, (5, 10))

# Load frames for the special enemy animation
special_enemy_frames = [pygame.image.load(f'specialEnemy/special_enemy1_frame{j}.png') for j in range(25)]
special_enemy_animation = cycle(special_enemy_frames)

# Colors
WHITE = (255, 255, 255)

# Player
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT - 60
player_speed = 7

# Bullet
bullet_speed = 10
bullets = []

# Enemy
enemy_speed_min = 3
enemy_speed_max = 7
enemies = []

# Special Enemy
special_enemy = None
special_enemy_spawned = False
special_enemy_speed = 5

# Slices for enemy spawning
slices = SCREEN_WIDTH // 5

# Scoring and complexity
score = 0
complexity_increase_thresholds = [random.randint(300, 350) for _ in range(10)]
complexity_level = 1

# Font
font = pygame.font.Font(None, 36)

# Game loop flag
running = True
game_over = False
clock = pygame.time.Clock()

# Start background music on its own channel
play_sound('background.mp3', loop=True, channel=BACKGROUND_CHANNEL)

# Function to reset the game
def reset_game():
    global player_x, player_y, bullets, enemies, special_enemy, score, game_over, complexity_level, special_enemy_spawned
    player_x = SCREEN_WIDTH // 2
    player_y = SCREEN_HEIGHT - 60
    bullets = []
    enemies = []
    special_enemy = None
    special_enemy_spawned = False
    score = 0
    game_over = False
    complexity_level = 1
    complexity_increase_thresholds.clear()
    complexity_increase_thresholds.extend([random.randint(300, 350) for _ in range(10)])

mouse_pressed_prev = False

# Game loop
while running:
    screen.blit(background, (0, 0))  # Draw background

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            stop_sound(SHOOTING_CHANNEL)
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            reset_game()

    if not game_over:
        # Player movement with cursor
        player_x, _ = pygame.mouse.get_pos()
        player_x = max(0, min(player_x, SCREEN_WIDTH - 50))

        # Shooting bullets
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Check if the left mouse button is pressed

        if mouse_pressed:
            if not mouse_pressed_prev:  # If it was not previously pressed
                play_sound('fire.mp3', channel=SHOOTING_CHANNEL)  # Play shooting sound on the shooting channel
            bullets.append(pygame.Rect(player_x + 22, player_y, 5, 10))  # Add a bullet
        else:
            stop_sound(SHOOTING_CHANNEL)  # Stop sound if mouse button is released

        mouse_pressed_prev = mouse_pressed

        # Update bullet positions
        bullets = [b for b in bullets if b.y > 0]
        for bullet in bullets:
            bullet.y -= bullet_speed

        # Spawn enemies
        if random.randint(1, 50) == 1:
            enemy_x = random.choice([i * slices for i in range(5)])
            enemy_speed = random.randint(enemy_speed_min, enemy_speed_max) * complexity_level
            enemy_image = random.choice(enemy_images)
            enemies.append([pygame.Rect(enemy_x, 0, 50, 50), enemy_speed, enemy_image])

        # Spawn special enemy
        if not special_enemy_spawned and random.randint(1, 200) == 1:
            special_enemy_x = random.choice([i * slices for i in range(5)])
            special_enemy = pygame.Rect(special_enemy_x, 0, 50, 50)
            special_enemy_spawned = True

        # Update enemy positions
        enemies = [e for e in enemies if e[0].y < SCREEN_HEIGHT]
        for enemy in enemies:
            enemy[0].y += enemy[1]
            if enemy[0].colliderect(pygame.Rect(player_x, player_y, 50, 50)):
                game_over = True

        # Update special enemy position
        if special_enemy:
            special_enemy.y += special_enemy_speed
            if special_enemy.y >= SCREEN_HEIGHT:
                special_enemy = None
                special_enemy_spawned = False

        # Collision detection and scoring
        for bullet in bullets:
            if bullet.y < SCREEN_HEIGHT:  # Check if bullet is within visible area
                for enemy in enemies:
                    if enemy[0].y >= 0 and enemy[0].y < SCREEN_HEIGHT and bullet.colliderect(enemy[0]):
                        bullets.remove(bullet)
                        enemies.remove(enemy)
                        score += 10
                        play_sound(random.choice(hit_sounds), loop=False, channel=HIT_CHANNEL)
                        time.sleep(0.05)  # Add a slight delay to prevent overlapping sounds
                        break

                # Check collision with special enemy only if it's visible
                if special_enemy and special_enemy.y < SCREEN_HEIGHT and bullet.colliderect(special_enemy):
                    bullets.remove(bullet)
                    special_enemy = None
                    special_enemy_spawned = False
                    game_over = True
                    break

        # Increase complexity based on score
        if complexity_increase_thresholds and score >= complexity_increase_thresholds[0]:
            complexity_level += 1
            complexity_increase_thresholds.pop(0)

        # Draw player
        screen.blit(player_image, (player_x, player_y))

        # Draw bullets
        for bullet in bullets:
            screen.blit(bullet_image, (bullet.x, bullet.y))

        # Draw enemies
        for enemy in enemies:
            screen.blit(enemy[2], (enemy[0].x, enemy[0].y))

        # Draw special enemy (animated GIF)
        if special_enemy:
            current_frame = next(special_enemy_animation)
            screen.blit(current_frame, (special_enemy.x, special_enemy.y))

        # Draw score
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))

    else:
        # Display game over
        stop_sound(SHOOTING_CHANNEL) 
        game_over_text = font.render('GAME OVER', True, WHITE)
        final_score_text = font.render(f'Final Score: {score}', True, WHITE)
        restart_text = font.render('Press R to Restart', True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
