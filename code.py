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
import json
import storage

connected =digitalio.DigitalInOut(board.VBUS_SENSE)
connected.direction = digitalio.Direction.INPUT

if not connected.value:
    storage.remount("/", False)

from adafruit_display_text.label import Label
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.line import Line
from adafruit_bitmap_font import bitmap_font

keys = keypad.Keys((board.GP28,board.GP20, board.GP21, board.GP18, board.GP19), value_when_pressed=False, pull=False)
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


class HighScores:
    def __init__(self):
        self.highscores = {}
        self.filename = "data.json"
        with open(self.filename, 'r') as file:
            self.highscores = json.load(file)

    def get_highscore(self, game):
        return self.highscores[game]

    def update_highscores(self, game, score):
        if self.highscores[game][0] < score[0]:
            self.highscores[game] = score
            with open(self.filename, 'w') as file:
                json.dump(self.highscores, file)

# Sounds
def beep(freq_0, freq_1, repeat, lenght = 0.01):
    pwm.duty_cycle = 0xfff
    for i in range(repeat):
        pwm.frequency = freq_0
        time.sleep(lenght)
        if freq_1 > 0:
            pwm.frequency = freq_1
        time.sleep(lenght)
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

class Show():
    def __init__(self, display, display_group, keys):
        self.display = display
        self.display_group = display_group
        self.keys = keys
        self.splash = displayio.Group()  # splash screen
        self.scenes = ((self.rainbow_fill, []),
                       (self.scroll_image, ['images/dog1.bmp']), #
                       (self.line_filler, []),
                       (self.scroll_text,
        ["Ellie's room, stay cool!! ...",
         "No little Brothers allowed!",
         "Woof Woof, all is good..."]))

    def exit_pressed(self):
        event = self.keys.events.get()
        if event:
            if event.key_number == 0:
                if event.pressed:
                    return True
        return False

    def end_scene(self):
        while len(self.splash) > 0:
            self.splash.pop(0)
        self.display.root_group = self.display_group

    def rainbow_fill(self):
        self.display.root_group = self.splash
        for c in range(63):
            w = Line(c, 0, c, 32, palette[c])
            self.splash.append(w)
            display.refresh(minimum_frames_per_second=0)
            if self.exit_pressed():
                return True
        time.sleep(2)
        for c in range(63):
            self.splash.pop()
            time.sleep(0.01)
            display.refresh(minimum_frames_per_second=0)
            if self.exit_pressed():
                return True
        self.end_scene()
        return False

    def scroll_text(self, text0, text1, text2, speed =.01):
        self.display.root_group = self.splash
        scrolling_label1 = Label(text=text0, font=terminalio.FONT, color=palette[58], line_spacing=.7, scale=1)
        scrolling_label2 = Label(text=text1, font=terminalio.FONT, color=palette[34], line_spacing=.7, scale=1)
        scrolling_label3 = Label(text=text2, font=terminalio.FONT, color=palette[12], line_spacing=.7, scale=1)
        self.splash.append(scrolling_label1)
        self.splash.append(scrolling_label2)
        self.splash.append(scrolling_label3)
        scrolling_label1.y = 5
        scrolling_label1.x = 0
        scrolling_label2.y = 15
        scrolling_label2.x = 0
        scrolling_label3.y = 25
        scrolling_label3.x = 0
        for x in range(64, -8 * len(text1) - 64, -1):
            time.sleep(speed)
            scrolling_label1.x = x
            scrolling_label2.x = x
            scrolling_label3.x = x
            if self.exit_pressed():
                return True
            display.refresh(minimum_frames_per_second=0)
        self.end_scene()
        return False

    def scroll_image(self, image):
        self.display.root_group = self.splash
        b, p = adafruit_imageload.load(image)
        t = displayio.TileGrid(b, pixel_shader=p)
        t.x = 0
        self.splash.append(t)
        for x in range(64, 10, -1):
            t.x = x
            time.sleep(.001)
            display.refresh(minimum_frames_per_second=0)
            if self.exit_pressed():
                return True
        time.sleep(2)
        for y in range(0, -30, -1):
            t.y = y
            time.sleep(.001)
            display.refresh(minimum_frames_per_second=0)
            if self.exit_pressed():
                return True
        self.end_scene()
        return False

    def line_filler(self):
        self.display.root_group = self.splash
        for c in range(31, 0, -1):
            w0 = Line(0, 0, 0, 31, palette[c + 20])
            w1 = Line(63, 0, 63, 31, palette[c + 20])
            self.splash.append(w0)
            self.splash.append(w1)
            while w0.x < c:
                w0.x = w0.x + 1
                w1.x = w1.x - 1
                display.refresh(minimum_frames_per_second=0)
                if self.exit_pressed():
                    return True
        self.end_scene()
        return False

    def run(self):
#        random.shuffle(self.scenes)
        while True:
            for sc in self.scenes:
                if sc[0](*sc[1]):
                    self.end_scene()
                    return


class GameBaseClass:
    def __init__(self, display, display_group, keys, palette, splash, highscores=None, players=1, game='snake'):
        self.game = game
        self.display = display
        self.display_group = display_group
        self.keys = keys
        self.palette = palette
        self.splash = splash
        self.highscores = highscores
        self.score0 = 0
        self.score1 = 0
        self.level = 0
        self.score0_label = Label(text=str(self.score0), font=score_font, color=self.palette[39], line_spacing=.7, scale=1)
        self.score1_label = Label(text=str(self.score1), font=score_font, color=self.palette[39], line_spacing=.7, scale=1)
        self.score0_label.x = 1
        self.score0_label.y = 3
        self.score1_label.x = 55
        self.score1_label.y = 3
        self.level_header = Label(text='L', font=score_font, color=self.palette[23], line_spacing=.7, scale=1)
        self.level_label = Label(text=str(self.level), font=score_font, color=self.palette[45], line_spacing=.7, scale=1)
        self.level_label.x = 20
        self.level_label.y = 3
        self.level_header.x = 16
        self.level_header.y = 3


        self.screen_top = 5
        self.field_div =  Line(0, self.screen_top, 63, self.screen_top, self.palette[59])
        self.gameinfo = displayio.Group()
        self.gameinfo.append(self.field_div)
        self.gameinfo.append(self.level_label)
        self.gameinfo.append(self.level_header)
        self.gameinfo.append(self.score0_label)
        if self.highscores:
            self.highscore_header = Label(text='H', font=score_font, color=self.palette[23], line_spacing=.7, scale=1)
            self.highscore_label = Label(text=str(self.highscores.get_highscore(self.game)[0]), font=score_font, color=self.palette[45], line_spacing=.7, scale=1)
            self.highscore_name = Label(text=self.highscores.get_highscore(self.game)[1], font=score_font, color=self.palette[12], line_spacing=.7, scale=1)
            self.highscore_label.x = 30
            self.highscore_label.y = 3
            self.highscore_header.x = 25
            self.highscore_header.y = 3
            self.highscore_name.x = 40
            self.highscore_name.y = 3
            self.gameinfo.append(self.highscore_label)
            self.gameinfo.append(self.highscore_header)
            self.gameinfo.append(self.highscore_name)

        if players > 1:
            self.gameinfo.append(self.score1_label)

    def update_highscores(self, score):
        print(score, self.game)
        self.highscores.update_highscores(self.game, score)
        self.highscore_label.text =str(self.highscores.get_highscore(self.game)[0])
        self.highscore_name.text=self.highscores.get_highscore(self.game)[1]

    def get_name(self):
        splash = displayio.Group()  # splash screen
        cursor = Line(20, 25, 25, 25, self.palette[56])
        letter = 97
        name = ['a']
        prompt = Label(text="New Highscore!! Enter name...", font=terminalio.FONT, color=self.palette[3], line_spacing=.7, scale=1)
        prompt.x = 64
        prompt.y = 10
        label = Label(text="".join(name), font=terminalio.FONT, color=self.palette[15], line_spacing=.7, scale=1)
        label.x = 20
        label.y = 20
        splash.append(cursor)
        splash.append(prompt)
        splash.append(label)
        self.display_group.append(splash)
        while True:
            prompt.x = prompt.x - 1
            if prompt.x < -1*prompt.bounding_box[2]:
                prompt.x = 64
            event = self.keys.events.get()
            if event:
                if event.pressed:
                    beep(900, 0, 1)
                    if event.key_number == 0:
                        if len(name) < 3:
                            cursor.x = cursor.x + 5
                            name.append('a')
                            letter = 97
                            label.text = "".join(name)
                        else:
                            self.display_group.remove(splash)
                            del splash
                            return label.text
                    if event.key_number == 1:
                        letter = letter + 1
                        name[len(name) - 1] = chr(letter)
                        label.text = "".join(name)
                    if event.key_number == 2:
                        letter = letter - 1
                        name[len(name) - 1] = chr(letter)
                        label.text = "".join(name)
                else:
                    # Released
                    continue
            self.display.refresh(minimum_frames_per_second=0)

class SplashBaseClass:
    def __init__(self, display, display_group, palette):
        self.display = display
        self.display_group = display_group
        self.palette = palette
        self.text = "empty"
        self.splash = Label(text=self.text, font=terminalio.FONT, color=self.palette[15], line_spacing=.7, scale=1)

class Splash(SplashBaseClass):
    def __init__(self, display, display_group, palette):
        super().__init__(display, display_group, palette)

    def run(self, text, repeat = 3, color=0):
        self.splash.x = 10
        self.splash.y = -5
        self.text = text
        self.splash.text = self.text
        if color>0:
            self.splash.color = color
        else:
            self.splash.color = self.palette[15]
        self.display_group.append(self.splash)
        for i in range(20):
            self.splash.y += 1
            self.display.refresh(minimum_frames_per_second=0)
        for i in range(repeat):
            self.display.refresh(minimum_frames_per_second=0)
            beep(1500, 1800, 1, .05)
            self.splash.text = ""
            self.display.refresh(minimum_frames_per_second=0)
            beep(1500, 1800, 1, .05)
            self.splash.text = self.text
        self.display_group.remove(self.splash)
        self.display.refresh(minimum_frames_per_second=0)

class Jump(GameBaseClass):
    def __init__(self, display, display_group, keys, palette, bitmap, splash, game='jump'):
        super().__init__(display, display_group, keys, palette, splash)
        self.bitmap = bitmap
        self.ball = Circle(5, 5, 2, fill=palette[56], outline=palette[56])
        self.character = Circle(5, 5, 2, fill=palette[23], outline=palette[23])

        self.field = displayio.Group()
        self.field.append(self.ball)
        self.field.append(self.character)


    def run(self):
        self.play = True
        self.display_group.append(self.gameinfo)
        self.display_group.append(self.field)
        self.jump_up = False
        self.fall_down = False
        self.ball.x = 70
        self.ball.y = 25
        self.character.x = 30
        self.character.y = 25
        while self.play:
            event = self.keys.events.get()
            if event:
                if event.pressed:
                    beep(900, 0, 1)
                    if event.key_number == 0 and not self.fall_down:
                        self.jump_up = True
                else:
                    # Released
                    continue
            self.ball.x = self.ball.x - 1
            if self.ball.x < -5:
                self.ball.x = 70
            display.refresh(minimum_frames_per_second=0)
            self.ball.x
            time.sleep(.05)
            # if self.character.x < self.ball.x + 4 and  self.character.x > self.ball.x - 4:
            #     beep(1000, 0, 1, .05)
            #     self.play = False
            if self.jump_up:
                self.character.y = self.character.y - 1
                if self.character.y < 20:
                    self.fall_down = True
                    self.jump_up = False
            if self.fall_down:
                self.character.y = self.character.y + 1
                if self.character.y > 25:
                    self.fall_down = False
        self.display_group.remove(self.gameinfo)
        self.display_group.remove(self.field)


class Snake(GameBaseClass):
    def __init__(self, display, display_group, keys, palette, bitmap, splash, highscores):
        super().__init__(display, display_group, keys, palette, splash, highscores, game='snake')
        self.bitmap = bitmap

    def run(self):
        self.snake_head = (13,6)
        self.snake_body = [self.snake_head]
        self.snake_head = (self.snake_head[0] + 1, self.snake_head[1])
        self.snake_body.append(self.snake_head)
        self.direction = 'right'
        self.fruit = (random.randint(0, 63), random.randint(self.screen_top+1, 31))
        self.fruit_type = 2
        self.score0 = 0
        self.score0_label.text = str(self.score0)
        self.levels = [.2 - i*.01 for i in range(0, 20)]
        self.level = 0
        self.level_label.text = str(self.level)
        self.play = True

        for q in self.snake_body:
            draw_pixel(self.bitmap, q[0], q[1], 1)
        self.display_group.append(self.gameinfo)
        while self.play:
            event = self.keys.events.get()
            if event:
                if event.pressed:
                    beep(900, 0, 1)
                    if event.key_number == 0:
                        self.play = False
                        continue
                    if event.key_number == 1:
                        self.direction = 'down'
                    if event.key_number == 2:
                        self.direction = 'up'
                    if event.key_number == 3:
                        self.direction = 'right'
                    if event.key_number == 4:
                        self.direction = 'left'
                else:
                    # Released
                    continue
            if self.direction == 'right':
                self.snake_head = (self.snake_head[0] + 1, self.snake_head[1])
            if self.direction == 'left':
                self.snake_head = (self.snake_head[0] - 1,  self.snake_head[1])
            if self.direction == 'down':
                self.snake_head = (self.snake_head[0], self.snake_head[1] + 1)
            if self.direction == 'up':
                self.snake_head = (self.snake_head[0], self.snake_head[1] - 1)
            if self.snake_head[0] > 63 or self.snake_head[1] > 31 or self.snake_head[0] < 0 or self.snake_head[1] < self.screen_top or self.snake_head in self.snake_body:
                self.splash.run("Game Over...")
                self.play = False
                continue
            self.snake_body.append(self.snake_head)
            draw_pixel(self.bitmap, self.snake_head[0], self.snake_head[1], 1)
            draw_pixel(self.bitmap, self.fruit[0], self.fruit[1], self.fruit_type)
            if self.snake_head == self.fruit:
                if self.fruit_type == 2:
                    beep(1600, 0, 1)
                    self.score0 = self.score0+1
                else:
                    beep(1600, 1800, 1)
                    self.score0 = self.score0 + 3
                self.fruit = (random.randint(0, 63), random.randint(self.screen_top+1, 31))
                chance = random.randint(0, 10)
                if chance > 8:
                    self.fruit_type = 3
                else:
                    self.fruit_type = 2

                if self.score0 % 10 == 0:
                    self.level = self.level + 1
                    self.level_label.text = str(self.level)
                self.score0_label.text = str(self.score0)
            else:
                self.snake_tail = self.snake_body.pop(0)
                draw_pixel(self.bitmap, self.snake_tail[0], self.snake_tail[1], 0)
            self.display.refresh(minimum_frames_per_second=0)
            time.sleep(self.levels[self.level])
        current_highscore = self.highscores.get_highscore(self.game)[0]
        if self.score0 > current_highscore:
            beep(1600, 1800, 2)
            name = self.get_name()
            score = [self.score0, name]
            self.update_highscores(score)
        self.bitmap.fill(0)
        self.display_group.remove(self.gameinfo)



class Pong(GameBaseClass):
    def __init__(self, display, display_group, keys, palette, splash, highscores, players = 2):
        super().__init__(display, display_group, keys, palette, splash, highscores, players, game='pong')
             # main screen
        self.speed = 0.04
        self.playpong = True
        self.field = displayio.Group()
        self.ball_x_direction = 1
        self.ball_y_direction = .7

        # Pong game ball
        self.ball_radius = 2
        self.ballx = 14
        self.bally = 15
        self.ball = Circle(self.ballx, self.bally, self.ball_radius, fill=palette[56], outline=palette[56])
        self.field.append(self.ball)

        self.player1_color = self.palette[2]
        self.player2_color = self.palette[34]

        self.field.append(self.gameinfo)

        # Pong game paddles
        self.paddle_width = 6
        self.bob1 = Line(0, 12, 0, 12 + self.paddle_width, self.player1_color)
        self.bob2 = Line(63, 12, 63, 12 + self.paddle_width, self.player2_color)
        self.field.append(self.bob1)
        self.field.append(self.bob2)

        self.levels = [.05 - i*.001 for i in range(0, 20)]

    def run(self):
        self.level = 0
        self.level_label.text = str(self.level)
        self.playpong = True
        self.ball_x_direction = 1
        self.ball_y_direction = .7
        self.ballx = 14
        self.bally = 15
        self.score0 = 0
        self.score0_label.text = str(self.score0)
        self.score1 = 0
        self.score1_label.text = str(self.score1)
        self.display_group.append(self.field)
        self.key1pressed = False
        self.key2pressed = False
        self.key3pressed = False
        self.key4pressed = False
        self.hits = 0
        while self.playpong:
            self.play = True
            while self.play:
                display.refresh(minimum_frames_per_second=0)
                time.sleep(self.levels[self.level])
                self.ball.x = self.ball.x + self.ball_x_direction
                self.bally = self.bally + self.ball_y_direction
                self.ball.y = round(self.bally)
                event = keys.events.get()
                if event:
                    if event.key_number == 0:
                        if event.pressed:
                            self.playpong = False
                            break
                    if event.key_number == 1:
                        if event.pressed:
                            self.key1pressed = True
                        else:
                            self.key1pressed = False
                    if event.key_number == 2:
                        if event.pressed:
                            self.key2pressed = True
                        else:
                            self.key2pressed = False
                    if event.key_number == 3:
                        if event.pressed:
                            self.key3pressed = True
                        else:
                            self.key3pressed = False
                    if event.key_number == 4:
                        if event.pressed:
                            self.key4pressed = True
                        else:
                            self.key4pressed = False

                if self.key2pressed:
                    if self.bob1.y > 0:
                        self.bob1.y = self.bob1.y - 1
                if self.key1pressed:
                    if self.bob1.y < 31 - self.paddle_width:
                        self.bob1.y = self.bob1.y + 1
                if self.key4pressed:
                    if self.bob2.y > 0:
                        self.bob2.y = self.bob2.y - 1
                if self.key3pressed:
                    if self.bob2.y < 31 - self.paddle_width:
                        self.bob2.y = self.bob2.y + 1

                # Bounce on paddle
                if self.ball.x == 63 - self.ball_radius * 2:
                    if self.ball.y > self.bob2.y - self.ball_radius and self.ball.y < self.bob2.y + self.paddle_width + self.ball_radius:
                        self.ball_x_direction = self.ball_x_direction * -1
                        beep(1800, 0 , 1, .02)
                        self.hits = self.hits + 1
                if self.ball.x == 0:
                    if self.ball.y > self.bob1.y - self.ball_radius and self.ball.y < self.bob1.y + self.paddle_width + self.ball_radius:
                        self.ball_x_direction = self.ball_x_direction * -1
                        beep(1800, 0 , 1, .02)
                        self.hits = self.hits + 1
                if self.hits == 10:
                    self.splash.run("Level Up!!", 2, palette[59])
                    self.level = self.level + 1
                    self.level_label.text = str(self.level)
                    self.hits = 0

                # Missed paddle, score points
                if self.ball.x < -5 or self.ball.x > 63 + 5:
                    if self.ball.x < -5:
                        self.score1 = self.score1 + 1
                        self.score1_label.text = str(self.score1)
                    else:
                        self.score0 = self.score0 + 1
                        self.score0_label.text = str(self.score0)
                    self.ball.x = 30
                    self.play = False
                    self.splash.run("Score!!", 1)
                    self.hits = 0


                # Bounce on top/bottom screen edge
                if self.ball.y == 0:
                    beep(1300, 0, 1, .01)
                    self.ball_y_direction = self.ball_y_direction * - 1
                if self.ball.y == 31 - 2 * self.ball_radius:
                    beep(1300, 0, 1, .01)
                    self.ball_y_direction = self.ball_y_direction * - 1
        self.display_group.remove(self.field)
        if max(self.score0, self.score1) > self.highscores.get_highscore(self.game)[0]:
            beep(700, 1500, 3)
            name = self.get_name()
            score = [max(self.score0, self.score1), name]
            self.update_highscores(score)

class SelectMode(GameBaseClass):
    def __init__(self, display, display_group, keys, palette, splash):
        super().__init__(display, display_group, keys, palette, splash)
        self.modes = {'jump': None, 'snake': None, 'pong': None, 'show': None}
        self.top_line = 8
        self.line = self.top_line
        self.top_arrow = 7
        self.line_spacing = 8
        self.lines_per_Screen = 3
        self.select_values = []
        self.border_width = 2
        self.border_color = palette[51]
        self.select_screen = displayio.Group()
        self.menu = displayio.Group()
        self.top_of_screen = self.top_arrow
        self.bottom_of_screen = self.top_arrow + self.line_spacing * (self.lines_per_Screen - 1)

        for c in range(self.border_width):
            w = Line(c, 0, c, 32, self.border_color)
            self.select_screen.append(w)
        for c in range(self.border_width, 64 - self.border_width):
            w = Line(c, 0, c, self.border_width, self.border_color)
            self.select_screen.append(w)
            w = Line(c, 32-self.border_width, c, 32, self.border_color)
            self.select_screen.append(w)
        for c in range(64 - self.border_width, 64):
            w = Line(c, 0, c, 32, self.border_color)
            self.select_screen.append(w)
        for m in self.modes.keys():
            self.modes[m] = Label(text=m, font=terminalio.FONT, color=palette[56], line_spacing=.7, scale=1)
            self.modes[m].x = 10
            self.modes[m].y = self.line
            self.line = self.line + self.line_spacing
            self.menu.append(self.modes[m])
            self.select_values.append(m)
        self.arrow = Triangle(0, 0, 4, 2, 0, 4 , fill=palette[48], outline=palette[48])
        self.arrow.y = self.top_arrow
        self.arrow.x = 3
        self.menu.append(self.arrow)
        self.select_screen.append(self.menu)
        self.select = True

    def run(self):
        self.display_group.append(self.select_screen)
        while self.select:
            event = self.keys.events.get()
            if event:
                if event.pressed:
                    if event.key_number == 0:
                        beep(1200, 1800, 1, 0.05)
                        q = int(self.arrow.y/self.line_spacing)
                        self.display_group.remove(self.select_screen)
                        return self.select_values[q]
                    if event.key_number == 1:
                        # down
                        if self.arrow.y == self.bottom_of_screen:
                            self.menu.y = self.menu.y - self.line_spacing
                            self.bottom_of_screen = self.bottom_of_screen +  self.line_spacing
                            self.top_of_screen = self.top_of_screen + self.line_spacing
                        self.arrow.y = self.arrow.y + self.line_spacing
                        self.display.refresh(minimum_frames_per_second=0)
                        beep(1200, 0, 1)
                    if event.key_number == 2:
                        # up
                        if self.arrow.y == self.top_of_screen and self.menu.y < 0:
                            self.menu.y = self.menu.y + self.line_spacing
                            self.bottom_of_screen = self.bottom_of_screen - self.line_spacing
                            self.top_of_screen = self.top_of_screen - self.line_spacing
                        self.arrow.y = self.arrow.y - self.line_spacing
                        self.display.refresh(minimum_frames_per_second=0)
                        beep(1200, 0, 1)

            if self.arrow.y > self.top_arrow+self.line_spacing*(len(self.modes)-1):
                self.arrow.y = self.top_arrow+self.line_spacing*(len(self.modes)-1)
            if self.arrow.y < self.top_arrow:
                self.arrow.y = self.top_arrow
            self.display.refresh(minimum_frames_per_second=0)

splash = Splash(display, g, palette)
select_mode = SelectMode(display, g, keys, palette, splash)
highscores = HighScores()
snake = Snake(display, g, keys, palette, bitmap, splash, highscores)
pong = Pong(display, g, keys, palette, splash, highscores)
jump = Jump(display, g, keys, palette, bitmap, splash)
show = Show(display, g, keys)

while True:
    beep(800, 1700, 3, .05)
    mode = select_mode.run()
    if mode == 'pong':
        pong.run()
    if mode == 'show':
        show.run()
    if mode == 'snake':
        snake.run()
    if mode == 'jump':
        jump.run()

