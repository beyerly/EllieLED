import time
import digitalio
import displayio
import rgbmatrix
import framebufferio
import adafruit_imageload
import terminalio
import pwmio
import board

from adafruit_display_text.label import Label
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

# Hardware
# Buzzer
pwm = pwmio.PWMOut(board.GP20, variable_frequency=True)

# Green buttons
green_up = digitalio.DigitalInOut(board.GP16)
green_up.direction = digitalio.Direction.INPUT
green_down = digitalio.DigitalInOut(board.GP17)
green_down.direction = digitalio.Direction.INPUT

# Blue buttons
blue_up = digitalio.DigitalInOut(board.GP18)
blue_up.direction = digitalio.Direction.INPUT
blue_down = digitalio.DigitalInOut(board.GP19)
blue_down.direction = digitalio.Direction.INPUT

# rgb matrix LED display
displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, bit_depth=2,
    rgb_pins=[board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5],
    addr_pins=[board.GP6, board.GP7, board.GP8, board.GP9],
    clock_pin=board.GP10, latch_pin=board.GP12, output_enable_pin=board.GP13)
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

g = displayio.Group()       # main screen
splash = displayio.Group()  # splash screen

# Sounds
def edgebeep():
    pwm.frequency = 1300
    pwm.duty_cycle = 0x7fff
    time.sleep(.01)
    pwm.duty_cycle = 0

def paddlebeep():
    pwm.frequency = 1800
    pwm.duty_cycle = 0x7fff
    time.sleep(.02)
    pwm.duty_cycle = 0

def goalbeep(repeat):
    pwm.duty_cycle = 0x7fff
    for i in range(repeat):
        pwm.frequency = 880
        time.sleep(.05)
        pwm.frequency = 1600
        time.sleep(.05)
    pwm.duty_cycle = 0

# Color palette
def gen_rainbow_palette():
    p = [0]
    step = 14

    def to_hex_24bit(r, g, b):
        return r << 16 | g << 8 | b

    for r in range(0, 255, step):
        p.append(to_hex_24bit(255, r, 0))
    for g in range(255, 0, -1 * step):
        p.append(to_hex_24bit(g, 255, 0))
    for r in range(0, 255, step):
        p.append(to_hex_24bit(0, 255 - r, r))
    for r in range(0, 75, step):
        p.append(to_hex_24bit(r, 0, 255 - r))
    for r in range(0, 75, step):
        p.append(to_hex_24bit(r + 75, 0, 130 + r))
    p.append(0XFFFFFF)
    return p

rbp = gen_rainbow_palette()
palette = displayio.Palette(len(rbp))
for c in range(len(palette)):
    palette[c] = rbp[c]
palette.make_transparent(0)

# Drawing functions
def draw_pixel(bitmap, x, y, color):
    bitmap[x, y] = color

def draw_line(bitmap):
    for x in range(32):
        draw_pixel(bitmap, x, 2, 3)

# Fonts
score_font = bitmap_font.load_font("fonts/4x6.bdf")
win_font = bitmap_font.load_font("fonts/VictoriaMedium-8.bdf")

# bitmap for images
bitmap = displayio.Bitmap(64, 32, 4)
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
g.append(tile_grid)

# Popup screen for game win
win_screen = Label(text=str("Score"), font=terminalio.FONT, color=palette[1], line_spacing=.7, scale=1)
win_screen.x = 10
win_screen.y = 15

player1_color = palette[2]
player2_color = palette[34]

# Game scores
score1 = 0
score1_label = Label(text=str(score1), font=score_font, color=player1_color, line_spacing=.7, scale=1)
score1_label.x = 0
score1_label.y = 5
score2 = 0
score2_label = Label(text=str(score2), font=score_font, color=player2_color, line_spacing=.7, scale=1)
score2_label.x = 60
score2_label.y = 5
g.append(score1_label)
g.append(score2_label)

# Pong game paddles
paddle_width = 6
bob1 = Line(0, 12, 0, 12 + paddle_width, player1_color)
bob2 = Line(63, 12, 63, 12 + +paddle_width, player2_color)
g.append(bob1)
g.append(bob2)

# Pong game ball
ball_radius = 2
ballx = 14
bally = 15
ball = Circle(ballx, bally, ball_radius, fill=palette[56], outline=palette[56])
g.append(ball)

ball_x_direction = 1
ball_y_direction = .7

display.root_group = g
target_fps = 1

# Sounds and popup screen for game win
def paddlebal_win():
    g.append(win_screen)
    for i in range(3):
        display.refresh(minimum_frames_per_second=0)
        goalbeep(2)
        win_screen.text = ""
        display.refresh(minimum_frames_per_second=0)
        goalbeep(2)
        win_screen.text = "Score!!"
    g.remove(win_screen)
    display.refresh(minimum_frames_per_second=0)

# Startup/Welcome screen
def welcome_screen():
    display.root_group = splash
    for c in range(63):
        w = Line(c, 0, c, 32, palette[c])
        splash.append(w)
        display.refresh(minimum_frames_per_second=0)
    welcome_label = Label(text="Welcome!", font=score_font, color=palette[1], line_spacing=.7, scale=1)
    welcome_label.x = 5
    welcome_label.y = 13
    splash.append(welcome_label)
    for n in range(3):
        welcome_label.text = "Welcome!!"
        display.refresh(minimum_frames_per_second=0)
        time.sleep(.5)
        welcome_label.text = ""
        display.refresh(minimum_frames_per_second=0)
        time.sleep(.5)
    display.root_group = g

welcome_screen()

play = True
speed = 0.04
while True:
    play = True
    while play:
        display.refresh(minimum_frames_per_second=0)
        time.sleep(speed)
        ball.x = ball.x + ball_x_direction
        bally = bally + ball_y_direction
        ball.y = round(bally)

        # Read green buttons
        if green_down.value == 0:
            if bob1.y > 0:
                bob1.y = bob1.y - 1
        if green_up.value == 0:
            if bob1.y < 31 - paddle_width:
                bob1.y = bob1.y + 1
        # Read blue buttons
        if blue_down.value == 0:
            if bob2.y > 0:
                bob2.y = bob2.y - 1
        if blue_up.value == 0:
            if bob2.y < 31 - paddle_width:
                bob2.y = bob2.y + 1

        # Bounce on paddle
        if ball.x == 63 - ball_radius * 2:
            if ball.y > bob2.y - ball_radius and ball.y < bob2.y + paddle_width + ball_radius:
                ball_x_direction = ball_x_direction * -1
                paddlebeep()
        if ball.x == 0:
            if ball.y > bob1.y - ball_radius and ball.y < bob1.y + paddle_width + ball_radius:
                ball_x_direction = ball_x_direction * -1
                paddlebeep()

        # Missed paddle, score points
        if ball.x < -5:
            score2 = score2 + 1
            score2_label.text = str(score2)
            ball.x = 63
            play = False
            paddlebal_win()
        if ball.x > 63 + 5:
            print(score1)
            score1 = score1 + 1
            score1_label.text = str(score1)
            ball.x = 0
            play = False
            paddlebal_win()

        # Bounce on top/bottom screen edge
        if ball.y == 0:
            edgebeep()
            ball_y_direction = ball_y_direction * - 1
        if ball.y == 31 - 2 * ball_radius:
            edgebeep()
            ball_y_direction = ball_y_direction * - 1
