import time
import digitalio
import displayio
import rgbmatrix
import framebufferio
import adafruit_imageload
import terminalio
import pwmio
import board
import keypad
import random


from adafruit_display_text.label import Label
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

keys = keypad.Keys((board.GP28,board.GP20, board.GP21, board.GP18, board.GP19), value_when_pressed=False, pull=False)

# Hardware
# Buzzer
pwm = pwmio.PWMOut(board.GP22, variable_frequency=True)


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

# Sounds
def edgebeep():
    pwm.frequency = 1300
    pwm.duty_cycle = 0x7fff
    time.sleep(.01)
    pwm.duty_cycle = 0

def clickbeep():
    pwm.frequency = 1500
    pwm.duty_cycle = 0x7fff
    time.sleep(.001)
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
s_palette = displayio.Palette(4)
s_palette[0] = 0x000000 # red
s_palette[1] = 0xFF0000 # green
s_palette[2] = 0x00FF00 # blue
s_palette[3] = 0x0000FF # blue
bitmap = displayio.Bitmap(64, 32, 4)
tile_grid = displayio.TileGrid(bitmap, pixel_shader=s_palette)
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

def game_over():
    # Popup screen for game win
    text = "Game Over..."
    win_screen = Label(text=text, font=terminalio.FONT, color=palette[15], line_spacing=.7, scale=1)
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
        win_screen.text = text
    g.remove(win_screen)
    display.refresh(minimum_frames_per_second=0)


# Startup/Welcome screen
def welcome_screen():
    splash = displayio.Group()  # splash screen
    display.root_group = splash
    for c in range(63):
        w = Line(c, 0, c, 32, palette[c])
        splash.append(w)
        display.refresh(minimum_frames_per_second=0)
    time.sleep(2)
    for c in range(63):
        splash.pop()
        time.sleep(0.01)
        display.refresh(minimum_frames_per_second=0)
    del splash
    display.root_group = g

# splash 1
def splash_0():
    splash = displayio.Group()  # splash screen
    display.root_group = splash
    for c in range(31, 0, -1):
        w0 = Line(0, 0, 0, 31, palette[c+20])
        w1 = Line(63, 0, 63, 31, palette[c+20])
        splash.append(w0)
        splash.append(w1)
        while w0.x < c:
            w0.x = w0.x + 1
            w1.x = w1.x - 1
            display.refresh(minimum_frames_per_second=0)
    del splash
    display.refresh(minimum_frames_per_second=0)
    display.root_group = g

def snake():
    snake_head = (7,5)
    snake_body = [snake_head]
    snake_head = (snake_head[0] + 1, snake_head[1])
    snake_body.append(snake_head)
    for q in snake_body:
        draw_pixel(bitmap, q[0], q[1], 1)
    direction = 'right'
    fruit = (random.randint(0, 63), random.randint(0, 31))
    # Game scores
    score = 0
    score1_label = Label(text=str(score), font=score_font, color=palette[39], line_spacing=.7, scale=1)
    score1_label.x = 0
    score1_label.y = 5
    g.append(score1_label)
    level = 0.2
    play = True
    while play:
        event = keys.events.get()
        if event:
            if event.pressed:
                clickbeep()
                if event.key_number == 0:
                    play = False
                if event.key_number == 1:
                    direction = 'down'
                if event.key_number == 2:
                    direction = 'up'
                if event.key_number == 3:
                    direction = 'right'
                if event.key_number == 4:
                    direction = 'left'
        if direction == 'right':
            snake_head = (snake_head[0] + 1, snake_head[1]) 
        if direction == 'left':
            snake_head = (snake_head[0] - 1,  snake_head[1])
        if direction == 'down':
            snake_head = (snake_head[0], snake_head[1] + 1) 
        if direction == 'up':
            snake_head = (snake_head[0], snake_head[1] - 1) 
        if snake_head[0] > 63 or snake_head[1] > 31 or snake_head[0] < 0 or snake_head[1] < 0 or snake_head in snake_body:
            game_over()
            play = False
            bitmap.fill(0)
            g.remove(score1_label)
            continue
        snake_body.append(snake_head)
        draw_pixel(bitmap, snake_head[0], snake_head[1], 1)
        draw_pixel(bitmap, fruit[0], fruit[1], 2)
        if snake_head == fruit:
            goalbeep(1)
            fruit = (random.randint(0, 63), random.randint(0, 31))
            level = level - 0.01
            score = score+1
            score1_label.text = str(score)
        else:
            snake_tail = snake_body.pop(0)
            draw_pixel(bitmap, snake_tail[0], snake_tail[1], 0)
        display.refresh(minimum_frames_per_second=0)
        time.sleep(level)

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

    key1pressed = False
    key2pressed = False
    key3pressed = False
    key4pressed = False

    while playpong:
        play = True
        while play:
            display.refresh(minimum_frames_per_second=0)
            time.sleep(speed)
            ball.x = ball.x + ball_x_direction
            bally = bally + ball_y_direction
            ball.y = round(bally)
            print(playpong)
            event = keys.events.get()
            if event:
                if event.key_number == 0:
                    if event.pressed:
                        playpong = False
                        continue
                if event.key_number == 1:
                    if event.pressed:
                        key1pressed = True
                    else:
                        key1pressed = False
                if event.key_number == 2:
                    if event.pressed:
                        key2pressed = True
                    else:
                        key2pressed = False
                if event.key_number == 3:
                    if event.pressed:
                        key3pressed = True
                    else:
                        key3pressed = False
                if event.key_number == 4:
                    if event.pressed:
                        key4pressed = True
                    else:
                        key4pressed = False

            if key1pressed:
                if bob1.y > 0:
                    bob1.y = bob1.y - 1
            if key2pressed:
                if bob1.y < 31 - paddle_width:
                    bob1.y = bob1.y + 1
            if key3pressed:
                if bob2.y > 0:
                    bob2.y = bob2.y - 1
            if key4pressed:
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
    g.remove(score1_label)
    g.remove(score2_label)
    g.remove(bob1)
    g.remove(bob2)
    g.remove(ball)


def scroll_image():
    b, p = adafruit_imageload.load("images/dog1.bmp")
    t = displayio.TileGrid(b, pixel_shader=p)
    t.x = 0
    g.append(t)
    for x in range(64, 10, -1):
        t.x = x
        time.sleep(.001)
        display.refresh(minimum_frames_per_second=0)
    time.sleep(2)
    for y in range(0, -30, -1):
        t.y = y
        time.sleep(.001)
        display.refresh(minimum_frames_per_second=0)
    g.remove(t)

    

def scroll_text():
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

def lightshow():
    doshow = True
    while doshow:
        event = keys.events.get()
        if event:
            if event.key_number == 0:
                if event.pressed:
                    doshow = False
                    continue
        welcome_screen()
        scroll_image()
        splash_0()
        scroll_text()
        
    

mode = 'show'
#mode = 'pong'



def select_mode():
    modes = {'snake': None, 'pong': None, 'show': None}
    top_line = 8
    top_arrow = 7
    line_spacing = 8
    select_values = []

    border_width = 2
    border_color = palette[51]
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
        event = keys.events.get()
        if event:
            if event.pressed:
                if event.key_number == 0:
                    selectbeep(1)
                    q = int(arrow.y/line_spacing)
                    g.remove(border)
                    g.remove(arrow)
                    for m in modes.keys():
                        g.remove(modes[m])
                    return select_values[q]
                if event.key_number == 1:
                    arrow.y = arrow.y + line_spacing
                    display.refresh(minimum_frames_per_second=0)
                    edgebeep()
                if event.key_number == 2:
                    arrow.y = arrow.y - line_spacing
                    display.refresh(minimum_frames_per_second=0)
                    edgebeep()

        if arrow.y > top_arrow+line_spacing*(len(modes)-1):
            arrow.y = top_arrow+line_spacing*(len(modes)-1)
        if arrow.y < top_arrow:
            arrow.y = top_arrow
        display.refresh(minimum_frames_per_second=0)
 

while True:
    edgebeep()
    mode = select_mode()
    if mode == 'pong':
        pong()
    if mode == 'show':
        lightshow()
    if mode == 'snake':
        snake()
