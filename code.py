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
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

# Hardware
# Buzzer
pwm = pwmio.PWMOut(board.GP22, variable_frequency=True)

# Green buttons
green_up = digitalio.DigitalInOut(board.GP18)
green_up.direction = digitalio.Direction.INPUT
green_down = digitalio.DigitalInOut(board.GP19)
green_down.direction = digitalio.Direction.INPUT

# Blue buttons
blue_up = digitalio.DigitalInOut(board.GP20)
blue_up.direction = digitalio.Direction.INPUT
blue_down = digitalio.DigitalInOut(board.GP21)
blue_down.direction = digitalio.Direction.INPUT

# rgb matrix LED display
displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, bit_depth=2,
    rgb_pins=[board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5],
    addr_pins=[board.GP6, board.GP7, board.GP8, board.GP9],
    clock_pin=board.GP10, latch_pin=board.GP11, output_enable_pin=board.GP12)
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

g = displayio.Group()       # main screen
border = displayio.Group()
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

def selectbeep(repeat):
    pwm.duty_cycle = 0x7fff
    for i in range(repeat):
        pwm.frequency = 1200
        time.sleep(.05)
        pwm.frequency = 2400
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





display.root_group = g
target_fps = 1

# Sounds and popup screen for game win
def paddlebal_win():
    # Popup screen for game win
    win_screen = Label(text=str("Score!!"), font=terminalio.FONT, color=palette[15], line_spacing=.7, scale=1)
    win_screen.x = 10
    win_screen.y = -5
    g.append(win_screen)
    for i in range(20):
        win_screen.y += 1
        display.refresh(minimum_frames_per_second=0)
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
    for c in range(63):
        splash.pop()
        time.sleep(0.01)
        display.refresh(minimum_frames_per_second=0)
    display.root_group = g


def pong():
    speed = 0.04
    playpong = True
    ball_x_direction = 1
    ball_y_direction = .7

    # Pong game ball
    ball_radius = 2
    ballx = 14
    bally = 15
    ball = Circle(ballx, bally, ball_radius, fill=palette[56], outline=palette[56])
    g.append(ball)

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


    while playpong:
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
                speed = speed - 0.001
            if ball.x > 63 + 5:
                print(score1)
                score1 = score1 + 1
                score1_label.text = str(score1)
                ball.x = 0
                play = False
                paddlebal_win()
                speed = speed - 0.001

            # Bounce on top/bottom screen edge
            if ball.y == 0:
                edgebeep()
                ball_y_direction = ball_y_direction * - 1
            if ball.y == 31 - 2 * ball_radius:
                edgebeep()
                ball_y_direction = ball_y_direction * - 1

def scroll_image():
    b, p = adafruit_imageload.load("images/dog1.bmp")
    t = displayio.TileGrid(b, pixel_shader=p)
    t.x = 0
    g.append(t)
    for x in range(64, 10, -1):
        t.x = x
        time.sleep(.001)
        display.refresh(minimum_frames_per_second=0)
    text1="Ellie's room, stay cool!! ..."
    scrolling_label1 = Label(text=text1, font=terminalio.FONT, color=palette[58], line_spacing=.7, scale=1)
    text2="No little Brothers allowed!"
    scrolling_label2 = Label(text=text2, font=terminalio.FONT, color=palette[34], line_spacing=.7, scale=1)
    text3="Woof Woof, all is good..."
    scrolling_label3 = Label(text=text3, font=terminalio.FONT, color=palette[12], line_spacing=.7, scale=1)
    g.append(scrolling_label1)
    g.append(scrolling_label2)
    g.append(scrolling_label3)
    scrolling_label1.y=5
    scrolling_label1.x=0
    scrolling_label2.y=15
    scrolling_label2.x=0
    scrolling_label3.y=25
    scrolling_label3.x=0
    for x in range(64, -8*len(text1) - 64, -1):
        time.sleep(.01)
        scrolling_label1.x = x
        scrolling_label2.x = x
        scrolling_label3.x = x
        display.refresh(minimum_frames_per_second=0)
    g.remove(scrolling_label1)
    g.remove(scrolling_label2)
    g.remove(scrolling_label3)
    g.remove(t)

def lightshow():
    doshow = True
    while doshow:    
        welcome_screen()
        scroll_image()
        if not blue_down.value:
            doshow = False
        
    

mode = 'show'
#mode = 'pong'



def select_mode():
    modes = {'pong': None, 'show': None}
    top_line = 8
    top_arrow = 7
    line_spacing = 8
    select_values = []

    border_width = 3
    border_color = palette[32]
    for c in range(border_width):
        w = Line(c, 0, c, 32, border_color)
        border.append(w)
    for c in range(border_width, 64 - border_width):
        w = Line(c, 0, c, border_width, border_color)
        border.append(w)
        w = Line(c, 32-border_width, c, 32, border_color)
        border.append(w)
    for c in range(64 - border_width, 64):
        w = Line(c, 0, c, 32, border_color)
        border.append(w)
    g.append(border)
    line = top_line
    for m in modes.keys():
        modes[m] = Label(text=m, font=terminalio.FONT, color=palette[56], line_spacing=.7, scale=1)
        modes[m].x = 10
        modes[m].y = line
        line = line + line_spacing
        g.append(modes[m])
        select_values.append(m)
    arrow = Triangle(0, 0, 4, 2, 0, 4 , fill=palette[48], outline=palette[48])
    arrow.y = top_arrow
    arrow.x = 3
    g.append(arrow)
    select = True
    while select:
        if not green_down.value:
            arrow.y = arrow.y + line_spacing
            display.refresh(minimum_frames_per_second=0)
            edgebeep()
            while not green_down.value:
                time.sleep(.001)
        if not green_up.value:
            arrow.y = arrow.y - line_spacing
            display.refresh(minimum_frames_per_second=0)
            edgebeep()
            while not green_up.value:
                time.sleep(.001)
        if arrow.y > top_arrow+line_spacing*(len(modes)-1):
            arrow.y = top_arrow+line_spacing*(len(modes)-1)
        if arrow.y < top_arrow:
            arrow.y = top_arrow
        if not blue_up.value:
            selectbeep(1)
            q = int(arrow.y/line_spacing)
            g.remove(border)
            g.remove(arrow)
            for m in modes.keys():
                g.remove(modes[m])
            return select_values[q]
        display.refresh(minimum_frames_per_second=0)
 

while True:
    edgebeep()
    mode = select_mode()
    if mode == 'pong':
        pong()
    if mode == 'show':
        lightshow()