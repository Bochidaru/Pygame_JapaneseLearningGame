import asyncio
import copy_lib
import time
import pygame
import random_lib
import json

import leaderboard_request

from wordlist import *
from convert import to_hiragana, to_roma, to_katakana

pygame.init()

WIDTH = 1000
HEIGHT = 700
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Japanese Typing!')
surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
timer = pygame.time.Clock()
fps = 60

score = 0
save_score = 0

# load image as theme
theme_list = ['1.png', '2.png', '3.png', '4.png', '5.png', '6.png']
random_theme_index = random_lib.randint(0, len(theme_list) - 1)

theme_image = pygame.image.load(f'assets/theme/{theme_list[random_theme_index]}').convert()
blurred_image = theme_image.copy()
pygame.Surface.blit(blurred_image, theme_image, (0, 0))
blurred_image.set_alpha(180)

# Font
header_font = pygame.font.Font('assets/fonts/square.ttf', 50)
header_font_2 = pygame.font.Font('assets/fonts/square.ttf', 25)
pause_font = pygame.font.Font('assets/fonts/1up.ttf', 38)
pause_font_for_mode = pygame.font.Font('assets/fonts/1up.ttf', 25)
banner_font = pygame.font.Font('assets/fonts/1up.ttf', 28)
banner_font_2 = pygame.font.Font('assets/fonts/1up.ttf', 20)
font = pygame.font.Font('assets/fonts/jp.ttf', 45)
font2 = pygame.font.Font('assets/fonts/jp.ttf', 30)
font3 = pygame.font.Font('assets/fonts/jp.ttf', 25)
arrow_font = pygame.font.Font('assets/fonts/jp.ttf', 70)
font_for_manual = pygame.font.Font('assets/fonts/jp.ttf', 20)
font_for_team_name = pygame.font.Font('assets/fonts/AldotheApache.ttf', 55)
font_for_music_option = pygame.font.Font('assets/fonts/square.ttf', 43)
font_combo = pygame.font.Font('assets/fonts/1up.ttf', 20)

# music and sounds
pygame.mixer.init()
music_channel = pygame.mixer.Channel(0)
music_channel.set_volume(0.3)
music1 = pygame.mixer.Sound(f'assets/background_music/1.ogg')
music2 = pygame.mixer.Sound(f'assets/background_music/2.ogg')
music3 = pygame.mixer.Sound(f'assets/background_music/3.ogg')
music4 = pygame.mixer.Sound(f'assets/background_music/4.ogg')
music5 = pygame.mixer.Sound(f'assets/background_music/5.ogg')
music_playlist_object = [music1, music2, music3, music4, music5]
music_playlist_index = random_lib.randint(0, len(music_playlist_object) - 1)
current_song_playlist_index = music_playlist_index
music_channel.play(music_playlist_object[music_playlist_index])

# music_channel.play(pygame.mixer.Sound('assets/sounds/music.ogg'), loops=-1)
# pygame.mixer.music.load('assets/sounds/music.ogg')
# pygame.mixer.music.set_volume(0)
# pygame.mixer.music.play(-1)
click = pygame.mixer.Sound('assets/sounds/click.ogg')
woosh = pygame.mixer.Sound('assets/sounds/Swoosh.ogg')
wrong = pygame.mixer.Sound('assets/sounds/Instrument Strum.ogg')
click.set_volume(0.3)
woosh.set_volume(0.2)
wrong.set_volume(0.3)

# game variables
level = 1
lives = 5
live_icon = pygame.image.load('assets/icon/heart_icon.png').convert_alpha()
word_objects = []

high_score = 0

combo = 0

pz = True
new_level = True
learn_mode = False
submit = ''
submit_to_english = ['', '', '']
active_string = ''
active_string_hiragana = ''
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q',
           'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '-', '\'']

# list show những từ đã gõ đúng và gõ sai trong phần history
all_words_appeared = []
hit_list = []
miss_list = []

# 2 letter, 3 letter, 4 letter, 5 letter, 6 letter, etc
choices = [True, True, True, False, False, False]

music_choices = [False, True]

mode_choices = [True, False, False]

hira_or_kata = [True, False]


def to_kana(input_romaji):
    if hira_or_kata[0]:
        return to_hiragana(input_romaji)
    if hira_or_kata[1]:
        return to_katakana(input_romaji)


mouse_detected = False
def one_click_accept():
    global mouse_detected
    mouse_butt = pygame.mouse.get_pressed()
    if mouse_butt[0]:
        if not mouse_detected:
            mouse_detected = True
            return True
        if mouse_detected:
            return False
    else:
        mouse_detected = False
        return False


def del_repetition(input_list):
    output_list = []
    for a in input_list:
        if a not in output_list:
            output_list.append(a)
    return output_list


def split_str_to_list(input_string):
    lst = ['', '', '']

    input_string = input_string.split(',')
    for i in range(len(input_string)):
        input_string[i] = input_string[i].strip()
        if len(input_string[i]) < 20:
            lst[i] = '- ' + input_string[i]

    if lst[0] == '' and lst[1] == '' and lst[2] != '':
        lst[0] = lst[2]
        lst[2] = ''
    elif lst[0] == '' and lst[1] != '' and lst[2] != '':
        lst[0] = lst[1]
        lst[1] = lst[2]
        lst[2] = ''
    elif lst[0] == '' and lst[1] != '' and lst[2] == '':
        lst[0] = lst[1]
        lst[1] = ''
    elif lst[0] != '' and lst[1] == '' and lst[2] != '':
        lst[1] = lst[2]
        lst[2] = ''

    return lst


def ja_to_en(word):
    index = 0
    for i in range(len(wordlist)):
        if wordlist[i] == word:
            index = i
            break
    return wordlist_translated[index]


class Word:
    def __init__(self, text, speed, y_pos, x_pos):
        self.text = text
        self.speed = speed
        self.y_pos = y_pos
        self.x_pos = x_pos

    def draw(self):
        if not learn_mode:
            color = 'black'
            screen.blit(font.render(self.text, True, color), (self.x_pos, self.y_pos))
            act_len = len(to_kana(active_string))
            check_kana = to_kana(active_string)
            if check_kana == self.text[:act_len]:
                screen.blit(font.render(to_kana(active_string), True, 'green'), (self.x_pos, self.y_pos))
        else:
            color = 'black'
            kana_surf = font.render(self.text, True, color)
            kana_rect = kana_surf.get_rect(topleft=(self.x_pos, self.y_pos))
            screen.blit(kana_surf, kana_rect)

            roma_surf = font3.render(to_roma(self.text), True, color)
            roma_rect = roma_surf.get_rect(midtop=(kana_rect.centerx, self.y_pos + 48))
            screen.blit(roma_surf, roma_rect)

            act_kana_len = len(to_kana(active_string))
            act_roma_len = len(active_string)
            check_kana = to_kana(active_string)

            if check_kana == self.text[:act_kana_len]:
                screen.blit(font.render(to_kana(active_string), True, 'pink'), kana_rect)
            if active_string == to_roma(self.text)[:act_roma_len]:
                screen.blit(font3.render(active_string, True, 'pink'), roma_rect)

    def update(self):
        self.x_pos -= self.speed


class Button:
    def __init__(self, x_pos, y_pos, text, clicked, surf, special=None):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.text = text
        self.clicked = clicked
        self.surf = surf
        self.special = special

    def draw(self):
        if self.special is True:
            cir = pygame.draw.circle(self.surf, pause_btn_color, (self.x_pos, self.y_pos), 35)
        else:
            cir = pygame.draw.circle(self.surf, '#3F6B9C', (self.x_pos, self.y_pos), 35)
        if cir.collidepoint(pygame.mouse.get_pos()):
            if one_click_accept():
                pygame.draw.circle(self.surf, (190, 35, 35), (self.x_pos, self.y_pos), 35)
                self.clicked = True
            else:
                pygame.draw.circle(self.surf, (190, 89, 135), (self.x_pos, self.y_pos), 35)
        pygame.draw.circle(self.surf, 'white', (self.x_pos, self.y_pos), 35, 3)
        self.surf.blit(pause_font.render(self.text, True, 'white'), (self.x_pos - 15, self.y_pos - 25))


class LengthChoiceButton:
    def __init__(self, x_pos, y_pos, text, clicked, surf):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.text = text
        self.clicked = clicked
        self.surf = surf

    def draw(self):
        cir = pygame.draw.circle(self.surf, '#d99ca5', (self.x_pos, self.y_pos), 35)
        if cir.collidepoint(pygame.mouse.get_pos()):
            butts = pygame.mouse.get_pressed()
            if butts[0]:
                pygame.draw.circle(self.surf, (190, 35, 35), (self.x_pos, self.y_pos), 35)
                self.clicked = True
            else:
                pygame.draw.circle(self.surf, (190, 89, 135), (self.x_pos, self.y_pos), 35)
        pygame.draw.circle(self.surf, 'white', (self.x_pos, self.y_pos), 35, 3)
        self.surf.blit(pause_font.render(self.text, True, '#8B4513'), (self.x_pos - 15, self.y_pos - 25))


class ModeButton:
    def __init__(self, x_pos, y_pos, text, clicked, surf, type):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.text = text
        self.clicked = clicked
        self.surf = surf
        self.type = type

    def draw(self):
        if self.type == 'Mode':
            rect = pygame.draw.rect(self.surf, '#3F6B9C', (self.x_pos, self.y_pos, 150, 60), 0, 10)
            if rect.collidepoint(pygame.mouse.get_pos()):
                if one_click_accept():
                    pygame.draw.rect(self.surf, (190, 35, 35), (self.x_pos, self.y_pos, 150, 60), 0, 10)
                    self.clicked = True
                else:
                    pygame.draw.rect(self.surf, (190, 89, 135), (self.x_pos, self.y_pos, 150, 60), 0, 10)
            pygame.draw.rect(self.surf, 'white', (self.x_pos, self.y_pos, 150, 60), 5, 10)
            len_text = len(self.text)
            if self.text == 'EASY':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 29, self.y_pos + 12))
            if self.text == 'MEDIUM':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 13, self.y_pos + 12))
            if self.text == 'HARD':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 29, self.y_pos + 12))
            if self.text == 'HIT!':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 39, self.y_pos + 12))
            if self.text == 'MISS!':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 29, self.y_pos + 12))
            if self.text == 'NEXT':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 29, self.y_pos + 12))
            if self.text == 'PREV':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 29, self.y_pos + 12))

        if self.type == 'Game_over':
            rect = pygame.draw.rect(self.surf, '#3F6B9C', (self.x_pos, self.y_pos, 220, 60), 0, 10)
            if rect.collidepoint(pygame.mouse.get_pos()):
                if one_click_accept():
                    pygame.draw.rect(self.surf, (190, 35, 35), (self.x_pos, self.y_pos, 220, 60), 0, 10)
                    self.clicked = True
                else:
                    pygame.draw.rect(self.surf, (190, 89, 135), (self.x_pos, self.y_pos, 220, 60), 0, 10)
            pygame.draw.rect(self.surf, 'white', (self.x_pos, self.y_pos, 220, 60), 5, 10)
            len_text = len(self.text)
            if self.text == 'RESTART':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 34, self.y_pos + 12))
            if self.text == 'MENU':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 65, self.y_pos + 12))
            if self.text == 'QUIT':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 70, self.y_pos + 12))
            if self.text == 'HISTORY':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 36, self.y_pos + 12))
            if self.text == 'ONLINERANK':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 5, self.y_pos + 12))
            if self.text == 'PLAY':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 65, self.y_pos + 12))
            if self.text == 'YES':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 75, self.y_pos + 12))
            if self.text == 'NO':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 90, self.y_pos + 12))
            if self.text == 'GAME MODE':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 15, self.y_pos + 12))
            if self.text == 'HIRAGANA':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 28, self.y_pos + 12))
            if self.text == 'KATAKANA':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 23, self.y_pos + 12))
            if self.text == 'SHOW THEME':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 2, self.y_pos + 12))
            if self.text == 'BACK':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 65, self.y_pos + 12))
            if self.text == 'NEXT':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 65, self.y_pos + 12))
            if self.text == 'SCOREBOARD':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos, self.y_pos + 12))

        if self.type == 'Menu':
            rect = pygame.draw.rect(self.surf, '#3F6B9C', (self.x_pos, self.y_pos, 400, 60), 0, 10)
            if rect.collidepoint(pygame.mouse.get_pos()):
                if one_click_accept():
                    pygame.draw.rect(self.surf, (190, 35, 35), (self.x_pos, self.y_pos, 400, 60), 0, 10)
                    self.clicked = True
                else:
                    pygame.draw.rect(self.surf, (190, 89, 135), (self.x_pos, self.y_pos, 400, 60), 0, 10)
            pygame.draw.rect(self.surf, 'white', (self.x_pos, self.y_pos, 400, 60), 5, 10)
            len_text = len(self.text)
            if self.text == 'BACK TO MENU':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 80, self.y_pos + 12))

        if self.type == 'Special_mode':
            rect = pygame.draw.rect(self.surf, '#3F6B9C', (self.x_pos, self.y_pos, 250, 60), 0, 10)
            if rect.collidepoint(pygame.mouse.get_pos()):
                if one_click_accept():
                    pygame.draw.rect(self.surf, (190, 35, 35), (self.x_pos, self.y_pos, 250, 60), 0, 10)
                    self.clicked = True
                else:
                    pygame.draw.rect(self.surf, (190, 89, 135), (self.x_pos, self.y_pos, 250, 60), 0, 10)
            pygame.draw.rect(self.surf, 'white', (self.x_pos, self.y_pos, 250, 60), 5, 10)
            len_text = len(self.text)
            if self.text == 'LEARN':
                if learn_mode:
                    self.surf.blit(pause_font_for_mode.render('LEARN', True, '#ffffcc'), (self.x_pos + 70, self.y_pos + 12))
                else:
                    self.surf.blit(pause_font_for_mode.render('COMPETITIVE', True, '#ffffcc'), (self.x_pos + 15, self.y_pos + 12))
            if self.text == 'SCOREBOARD':
                self.surf.blit(pause_font_for_mode.render(self.text, True, '#ffffcc'), (self.x_pos + 15, self.y_pos + 12))


pause_btn_color = (32, 42, 68)
combo_signal_list = [False, False, False, False, False, False]
get_time_signal = 0
word_color = 'white'
def draw_screen():
    # screen outlines for main game window and 'header' section
    word_background_color = (32, 42, 68)
    global pause_btn_color, word_color
    if not show_theme:
        word_color = 'white'
        word_background_color = (32, 42, 68)
        pause_btn_color = (32, 42, 68)
    else:
        if random_theme_index == 0:
            word_color = '#4f4a49'
            word_background_color = '#d9c8c6'
            pause_btn_color = '#d9c8c6'
        elif random_theme_index == 1:
            word_color = '#3f452f'
            word_background_color = '#a6b579'
            pause_btn_color = '#a6b579'
        elif random_theme_index == 2:
            word_color = 'white'
            word_background_color = '#737086'
            pause_btn_color = '#737086'
        elif random_theme_index == 3:
            word_color = 'white'
            word_background_color = '#738491'
            pause_btn_color = '#738491'
        elif random_theme_index == 4:
            word_color = '#403e45'
            word_background_color = '#baaed6'
            pause_btn_color = '#baaed6'
        elif random_theme_index == 5:
            word_color = '#fff2e6'
            word_background_color = '#bd8a7e'
            pause_btn_color = '#bd8a7e'
    pygame.draw.rect(screen, word_background_color, [0, HEIGHT - 100, WIDTH, 100], 0)
    pygame.draw.rect(screen, 'white', [0, 0, WIDTH, HEIGHT], 5)
    pygame.draw.line(screen, 'white', (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
    pygame.draw.line(screen, 'white', (250, HEIGHT - 100), (250, HEIGHT), 2)
    pygame.draw.line(screen, 'white', (900, HEIGHT - 100), (900, HEIGHT), 2)
    pygame.draw.line(screen, 'white', (610, HEIGHT - 100), (610, HEIGHT), 2)
    pygame.draw.rect(screen, 'black', [0, 0, WIDTH, HEIGHT], 2)
    # text for showing current level, player's current string, high score and pause options
    screen.blit(header_font.render(f'Level: {level}', True, word_color), (10, HEIGHT - 75))
    screen.blit(font2.render(f'"{active_string}"', True, word_color), (260, HEIGHT - 55))
    active_string_to_kana = to_kana(active_string)
    screen.blit(font2.render(f'"{active_string_to_kana}"', True, word_color), (260, HEIGHT - 100))

    screen.blit(font3.render(f'{submit_to_english[0]}', True, word_color), (620, HEIGHT - 105))
    screen.blit(font3.render(f'{submit_to_english[1]}', True, word_color), (620, HEIGHT - 75))
    screen.blit(font3.render(f'{submit_to_english[2]}', True, word_color), (620, HEIGHT - 45))

    global combo_signal_list, get_time_signal
    if combo == 3 and not combo_signal_list[0]:
        combo_signal_list[0] = True
        get_time_signal = pygame.time.get_ticks()
    elif combo == 6 and not combo_signal_list[1]:
        combo_signal_list[1] = True
        get_time_signal = pygame.time.get_ticks()
    elif combo == 10 and not combo_signal_list[2]:
        combo_signal_list[2] = True
        get_time_signal = pygame.time.get_ticks()
    elif combo == 15 and not combo_signal_list[3]:
        combo_signal_list[3] = True
        get_time_signal = pygame.time.get_ticks()
    elif combo == 20 and not combo_signal_list[4]:
        combo_signal_list[4] = True
        get_time_signal = pygame.time.get_ticks()
    elif combo == 30 and not combo_signal_list[5]:
        combo_signal_list[5] = True
        get_time_signal = pygame.time.get_ticks()

    pause_btn = Button(947, HEIGHT - 52, 'II', False, screen, True)
    pause_btn.draw()
    # draw lives, score, and high score on top of screen
    if not (show_game_over or show_history or show_rank_chart or learn_mode or show_check_user_name):

        live_surf_length = lives * 40 - 5
        live_surf = pygame.Surface((live_surf_length, 35), pygame.SRCALPHA)
        # live_surf.fill((50, 50, 50, 50))
        for i in range(lives):
            live_surf.blit(live_icon, (i*40, 0))
        live_rect = live_surf.get_rect(midtop=(200, 12))
        screen.blit(live_surf, live_rect)

        score_text = banner_font.render(f'Score: {score}', True, 'black')
        screen.blit(score_text, score_text.get_rect(midtop=(500, 10)))

        best_text = banner_font.render(f'Best: {high_score}', True, 'black')
        screen.blit(best_text, best_text.get_rect(midtop=(800, 10)))
    elif learn_mode:
        pass
    else:
        score_text = banner_font.render(f'Score: {score}', True, 'black')
        screen.blit(score_text, score_text.get_rect(midtop=(300, 10)))

        best_text = banner_font.render(f'Best: {high_score}', True, 'black')
        screen.blit(best_text, best_text.get_rect(midtop=(700, 10)))

    return pause_btn.clicked


def draw_combo(mark):
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    point = 0
    text = None
    if mark == 3:
        text = font_combo.render(f'Not Bad! +50', True, 'white')
    elif mark == 6:
        text = font_combo.render(f'Good! +100', True, '#02b802')
    elif mark == 10:
        text = font_combo.render(f'Very Good! +200', True, '#FFFF00')
    elif mark == 15:
        text = font_combo.render(f'EXCELLENT! +500', True, '#00ffe1')
    elif mark == 20:
        text = font_combo.render(f'GENIUS! +1000', True, '#FF0000')
    elif mark == 30:
        text = font_combo.render(f'JAPANESE GOD! +5000', True, '#a600ff')

    text_rect = text.get_rect(center=(WIDTH // 2, 70))
    surface.blit(text, text_rect)
    screen.blit(surface, (0, 0))


def draw_menu():
    choice_commits = copy_lib.deepcopy(choices)
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [200, 100, 600, 450], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 100, 600, 450], 5, 5)
    resume_btn = ModeButton(250, 135, 'PLAY', False, surface, 'Game_over')
    resume_btn.draw()

    back_menu_btn = ModeButton(300, 310, 'BACK TO MENU', False, surface, 'Menu')
    learn_mode_btn = ModeButton(235, 310, 'LEARN', False, surface, 'Special_mode')
    scoreboard_btn = ModeButton(515, 310, 'SCOREBOARD', False, surface, 'Special_mode')
    global word_color, learn_mode
    if new_level:
        surface.blit(font_for_team_name.render('Motivators', True, word_color), (628, 630))
        learn_mode_btn.draw()
        scoreboard_btn.draw()
        if learn_mode_btn.clicked:
            if learn_mode:
                learn_mode = False
            else:
                learn_mode = True

    else:
        back_menu_btn.draw()

    game_mode_btn = ModeButton(250, 220, 'GAME MODE', False, surface, 'Game_over')
    game_mode_btn.draw()

    surface.blit(header_font.render('MANUAL', True, 'white'), (600, 140))
    surface.blit(header_font.render('MUSIC', True, 'white'), (600, 225))
    surface.blit(header_font.render('Active Letter Lengths:', True, 'white'), (210, 395))

    manual_btn = Button(550, 165, '?', False, surface)
    manual_btn.draw()

    music_btn = Button(550, 250, 'I>', False, surface)
    music_btn.draw()

    for i in range(len(choices)):
        btn = LengthChoiceButton(295 + (i * 80), 495, str(i + 2), False, surface)
        btn.draw()
        if btn.clicked:
            if choice_commits[i]:
                choice_commits[i] = False
            else:
                choice_commits[i] = True
        if choices[i]:
            pygame.draw.circle(surface, 'yellow', (295 + (i * 80), 495), 38, 7)
    screen.blit(surface, (0, 0))
    return (resume_btn.clicked, choice_commits, back_menu_btn.clicked, manual_btn.clicked,
            music_btn.clicked, game_mode_btn.clicked, scoreboard_btn.clicked)


def draw_cannot_change_mode_while_playing():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [805, 250, 150, 185], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [805, 250, 150, 185], 5, 5)
    surface.blit(header_font_2.render('Cannot', True, 'white'), (825, 270))
    surface.blit(header_font_2.render('change', True, 'white'), (825, 300))
    surface.blit(header_font_2.render('game mode', True, 'white'), (825, 330))
    surface.blit(header_font_2.render('while', True, 'white'), (825, 360))
    surface.blit(header_font_2.render('playing!', True, 'white'), (825, 390))

    screen.blit(surface, (0, 0))


def draw_manual():
    global text_surf
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 120), [200, 70, 615, 510], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 70, 615, 510], 5, 5)

    manual_to_menu_btn = Button(245, 115, '<-', False, surface)
    manual_to_menu_btn.draw()

    surface.blit(header_font.render('How to play?', True, 'white'), (350, 90))

    root = 180

    surface.blit(font_for_manual.render('- Type the romaji transcription corresponding to the word on', True, 'white'), (210, root))
    surface.blit(font_for_manual.render('the screen and press enter and the word will disappear if you', True, 'white'), (210, root + 30))
    surface.blit(font_for_manual.render('entered it correctly, otherwise, you lose one heart.', True, 'white'), (210, root + 60))

    surface.blit(font_for_manual.render('- The game mode is customizable: Word lists in Hiragana or', True, 'white'), (210, root + 110))
    surface.blit(font_for_manual.render('Katakana, varying word lengths for learning, and difficulty', True, 'white'), (210, root + 140))
    surface.blit(font_for_manual.render('levels (Easy, Medium, or Hard)', True, 'white'), (210, root + 170))

    surface.blit(font_for_manual.render('- You can change your theme, turn on or off the theme', True, 'white'), (210, root + 220))
    surface.blit(font_for_manual.render('turn on/off music, and have a positive experience.', True, 'white'), (210, root + 250))

    surface.blit(font_for_manual.render('- This game has a leaderboard for both HIRAGANA and KATAKANA', True, 'white'), (210, root + 300))
    surface.blit(font_for_manual.render('You can post your score after game over to compete other players', True, 'white'), (210, root + 330))

    screen.blit(surface, (0, 0))
    return manual_to_menu_btn.clicked


def draw_music_option():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [200, 100, 600, 400], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 100, 600, 400], 5, 5)
    surface.blit(font_for_music_option.render('Volume         Pause Play', True, 'white'), (310, 150))

    music_to_menu_btn = Button(245, 145, '<-', False, surface)
    music_to_menu_btn.draw()

    music_pause_btn = Button(630, 250, 'II', False, surface)
    music_pause_btn.draw()

    music_unpause_btn = Button(730, 250, 'I>', False, surface)
    music_unpause_btn.draw()

    if music_pause_btn.clicked:
        music_choices[0] = True
        music_choices[1] = False
    if music_unpause_btn.clicked:
        music_choices[0] = False
        music_choices[1] = True
    if music_choices[0]:
        pygame.draw.circle(surface, 'yellow', (630, 250), 35, 5)
    elif music_choices[1]:
        pygame.draw.circle(surface, 'yellow', (730, 250), 35, 5)

    volume_up = Button(530, 250, '>', False, surface)
    volume_up.draw()
    volume_down = Button(250, 250, '<', False, surface)
    volume_down.draw()

    pygame.draw.rect(surface, '#6ec6ff', (290, 247, 200, 15), 5, 20)

    current_vol = round(music_channel.get_volume(), 1)
    current_vol *= 10

    pygame.draw.circle(surface, 'black', (300 + (current_vol * 18), 255), 9)

    surface.blit(font_for_music_option.render('Change Song', True, 'white'), (365, 320))

    next_song_btn = ModeButton(620, 390, 'NEXT', False, surface, 'Mode')
    next_song_btn.draw()
    prev_song_btn = ModeButton(230, 390, 'PREV', False, surface, 'Mode')
    prev_song_btn.draw()
    global music_playlist_index
    if next_song_btn.clicked:
        music_playlist_index += 1
        if music_playlist_index == len(music_playlist_object):
            music_playlist_index = 0
    if prev_song_btn.clicked:
        music_playlist_index -= 1
        if music_playlist_index == -1:
            music_playlist_index = len(music_playlist_object) - 1
    surface.blit(banner_font.render(f'MUSIC {music_playlist_index + 1}', True, 'white'), (430, 400))
    screen.blit(surface, (0, 0))
    return music_to_menu_btn.clicked, music_pause_btn.clicked, music_unpause_btn.clicked, volume_up.clicked, volume_down.clicked


def draw_game_over():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [200, 100, 600, 420], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 100, 600, 420], 5, 5)

    game_over_surf = header_font.render('GAME OVER!', True, 'white')
    game_over_rect = game_over_surf.get_rect(midtop=(500, 120))
    surface.blit(game_over_surf, game_over_rect)

    game_over_to_restart_btn = ModeButton(250, 330, 'RESTART', False, surface, 'Game_over')
    game_over_to_restart_btn.draw()

    word_history_btn = ModeButton(250, 410, 'HISTORY', False, surface, 'Game_over')
    word_history_btn.draw()

    back_to_menu_btn = ModeButton(530, 410, 'MENU', False, surface, 'Game_over')
    back_to_menu_btn.draw()

    rank_btn = ModeButton(530, 330, 'ONLINERANK', False, surface, 'Game_over')
    rank_btn.draw()

    if not new_record_found:
        your_score_surf = header_font.render(f'Your score: {save_score}', True, 'white')
        your_score_rect = your_score_surf.get_rect(midtop=(500, 220))
        surface.blit(your_score_surf, your_score_rect)
    elif new_record_found:
        new_record_surf = header_font.render(f'New record: {save_score}', True, 'red')
        new_record_rect = new_record_surf.get_rect(midtop=(500, 220))
        surface.blit(new_record_surf, new_record_rect)

    screen.blit(surface, (0, 0))
    return game_over_to_restart_btn.clicked, back_to_menu_btn.clicked, word_history_btn.clicked, rank_btn.clicked


def draw_are_you_sure():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [200, 200, 600, 250], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 200, 600, 250], 5, 5)
    surface.blit(header_font.render('Are you sure ?', True, 'white'), (330, 220))

    no_btn = ModeButton(250, 330, 'NO', False, surface, 'Game_over')
    no_btn.draw()

    yes_btn = ModeButton(530, 330, 'YES', False, surface, 'Game_over')
    yes_btn.draw()

    screen.blit(surface, (0, 0))
    return yes_btn.clicked, no_btn.clicked


def draw_game_mode():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [200, 100, 600, 460], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [200, 100, 600, 460], 5, 5)

    surface.blit(header_font.render('GAME MODE', True, 'white'), (380, 120))

    game_mode_to_menu_btn = Button(245, 145, '<-', False, surface)
    game_mode_to_menu_btn.draw()

    surface.blit(header_font.render('DIFFICULTY', True, 'white'), (375, 290))

    easy_btn = ModeButton(220, 350, 'EASY', False, surface, 'Mode')
    easy_btn.draw()
    medium_btn = ModeButton(420, 350, 'MEDIUM', False, surface, 'Mode')
    medium_btn.draw()
    hard_btn = ModeButton(620, 350, 'HARD', False, surface, 'Mode')
    hard_btn.draw()

    if mode_choices[0]:
        pygame.draw.rect(surface, 'yellow', (220, 350, 150, 60), 7, 10)
    if mode_choices[1]:
        pygame.draw.rect(surface, 'yellow', (420, 350, 150, 60), 7, 10)
    if mode_choices[2]:
        pygame.draw.rect(surface, 'yellow', (620, 350, 150, 60), 7, 10)

    hira_btn = ModeButton(250, 210, 'HIRAGANA', False, surface, 'Game_over')
    hira_btn.draw()
    kata_btn = ModeButton(520, 210, 'KATAKANA', False, surface, 'Game_over')
    kata_btn.draw()
    if hira_or_kata[0]:
        pygame.draw.rect(surface, 'yellow', (250, 210, 220, 60), 7, 10)
    if hira_or_kata[1]:
        pygame.draw.rect(surface, 'yellow', (520, 210, 220, 60), 7, 10)

    show_theme_btn = ModeButton(220, 470, 'SHOW THEME', False, surface, 'Game_over')
    show_theme_btn.draw()
    global show_theme, random_theme_index
    if show_theme_btn.clicked:
        if show_theme:
            show_theme = False
        else:
            show_theme = True
    if show_theme:
        pygame.draw.rect(surface, 'yellow', (220, 470, 220, 60), 7, 10)

    if random_theme_index < 10:
        surface.blit(banner_font.render(f'THEME {random_theme_index + 1}', True, 'white'), (536, 480))
    else:
        surface.blit(banner_font.render(f'THEME {random_theme_index + 1}', True, 'white'), (527, 480))

    next_theme_btn = Button(750, 500, '>', False, surface)
    next_theme_btn.draw()
    prev_theme_btn = Button(490, 500, '<', False, surface)
    prev_theme_btn.draw()

    if next_theme_btn.clicked:
        random_theme_index += 1
        if random_theme_index == len(theme_list):
            random_theme_index = 0
    if prev_theme_btn.clicked:
        random_theme_index -= 1
        if random_theme_index == -1:
            random_theme_index = len(theme_list) - 1
    screen.blit(surface, (0, 0))
    return (game_mode_to_menu_btn.clicked, easy_btn.clicked, medium_btn.clicked, hard_btn.clicked,
            hira_btn.clicked, kata_btn.clicked)


# các biến phục vụ vẽ history
y_pos_of_miss_part = 0
y_pos_of_hit_part = 0
miss, hit = True, False
miss_surface, hit_surface, height_of_miss_surface, height_of_hit_surface = None, None, None, None
part_of_miss_surf, part_of_hit_surf = None, None
flag_draw_miss_hit_list = False
def draw_history():
    global miss, hit
    global flag_draw_miss_hit_list, y_pos_of_miss_part, y_pos_of_hit_part
    global miss_surface, hit_surface, height_of_miss_surface, height_of_hit_surface
    global part_of_miss_surf, part_of_hit_surf

    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [140, 70, 720, 515], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [140, 70, 720, 515], 5, 5)
    hit_btn = ModeButton(570, 90, 'HIT!', False, surface, 'Mode')
    hit_btn.draw()
    miss_btn = ModeButton(350, 90, 'MISS!', False, surface, 'Mode')
    miss_btn.draw()
    history_to_game_over_btn = Button(185, 115, '<-', False, surface)
    history_to_game_over_btn.draw()
    if hit_btn.clicked:
        miss, hit = False, True
    if hit:
        temp_len_hit = len(hit_list)
        pygame.draw.rect(surface, 'yellow', (570, 90, 150, 60), 7, 10)
        surface.blit(banner_font.render(f'{temp_len_hit}', True, 'black'), (80, 300))
        surface.blit(banner_font.render(f'hits', True, 'black'), (45, 350))
        if temp_len_hit > 2:
            surface.blit(arrow_font.render('↑', True, 'black'), (890, 220))
            surface.blit(banner_font_2.render('SCROLL', True, 'black'), (870, 350))
            surface.blit(arrow_font.render('↓', True, 'black'), (890, 400))
    if miss_btn.clicked:
        miss, hit = True, False
    if miss:
        temp_len_miss = len(miss_list)
        pygame.draw.rect(surface, 'yellow', (350, 90, 150, 60), 7, 10)
        surface.blit(banner_font.render(f'{temp_len_miss}', True, 'black'), (80, 300))
        surface.blit(banner_font.render(f'miss', True, 'black'), (45, 350))
        if temp_len_miss > 2:
            surface.blit(arrow_font.render('↑', True, 'black'), (890, 220))
            surface.blit(banner_font_2.render('SCROLL', True, 'black'), (870, 350))
            surface.blit(arrow_font.render('↓', True, 'black'), (890, 400))

    pygame.draw.line(surface, '#cae63e', (145, 175), (853, 175), 8)

    # vẽ riêng miss surf và hit surf
    if flag_draw_miss_hit_list:
        len_miss_list = len(miss_list)
        len_hit_list = len(hit_list)

        height_of_miss_surface = len_miss_list * 170
        height_of_hit_surface = len_hit_list * 170

        if height_of_miss_surface <= 400:
            height_of_miss_surface = 400
        if height_of_hit_surface <= 400:
            height_of_hit_surface = 400

        miss_surface = pygame.Surface((710, height_of_miss_surface))
        hit_surface = pygame.Surface((710, height_of_hit_surface))
        miss_surface.fill((70, 70, 70))
        hit_surface.fill((70, 70, 70))

        # chắc chắn có miss list, không cần kiểm tra
        for i in range(len_miss_list):
            miss_surface.blit(font2.render(f'{i+1}. {miss_list[i]}', True, 'white'), (20, i*170 + 10))
            miss_surface.blit(font2.render(f'  {to_roma(miss_list[i])}', True, 'white'), (20, i * 170 + 60))
            pygame.draw.line(miss_surface, 'white', (0, i*170 + 170), (853, i*170 + 170), 5)
            pygame.draw.line(miss_surface, 'white', (290, i*170), (290, i*170 + 170), 5)
            meaning_list = split_str_to_list(ja_to_en(miss_list[i]))
            if meaning_list[0]:
                miss_surface.blit(font2.render(f'{meaning_list[0]}', True, 'white'), (310, i * 170))
            if meaning_list[1]:
                miss_surface.blit(font2.render(f'{meaning_list[1]}', True, 'white'), (310, i * 170 + 55))
            if meaning_list[2]:
                miss_surface.blit(font2.render(f'{meaning_list[2]}', True, 'white'), (310, i * 170 + 110))
        if hit_list:
            for i in range(len_hit_list):
                hit_surface.blit(font2.render(f'{i + 1}. {hit_list[i]}', True, 'white'), (20, i * 170 + 10))
                hit_surface.blit(font2.render(f'  {to_roma(hit_list[i])}', True, 'white'), (20, i * 170 + 60))
                pygame.draw.line(hit_surface, 'white', (0, i * 170 + 170), (853, i * 170 + 170), 5)
                pygame.draw.line(hit_surface, 'white', (290, i * 170), (290, i * 170 + 170), 5)
                meaning_list = split_str_to_list(ja_to_en(hit_list[i]))
                if meaning_list[0]:
                    hit_surface.blit(font2.render(f'{meaning_list[0]}', True, 'white'), (310, i * 170))
                if meaning_list[1]:
                    hit_surface.blit(font2.render(f'{meaning_list[1]}', True, 'white'), (310, i * 170 + 55))
                if meaning_list[2]:
                    hit_surface.blit(font2.render(f'{meaning_list[2]}', True, 'white'), (310, i * 170 + 110))
        else:
            hit_surface.blit(font.render('Let practice more!', True, 'white'), (160, 160))

    flag_draw_miss_hit_list = False

    if y_pos_of_miss_part <= 0:
        y_pos_of_miss_part = 0
    if y_pos_of_miss_part >= height_of_miss_surface - 400:
        y_pos_of_miss_part = height_of_miss_surface - 400

    if y_pos_of_hit_part <= 0:
        y_pos_of_hit_part = 0
    if y_pos_of_hit_part >= height_of_hit_surface - 400:
        y_pos_of_hit_part = height_of_hit_surface - 400

    miss_source_rect = pygame.Rect(0, y_pos_of_miss_part, 710, 400)
    part_of_miss_surf = miss_surface.subsurface(miss_source_rect)

    hit_source_rect = pygame.Rect(0, y_pos_of_hit_part, 710, 400)
    part_of_hit_surf = hit_surface.subsurface(hit_source_rect)

    screen.blit(surface, (0, 0))
    if miss:
        screen.blit(part_of_miss_surf, (145, 180))
    if hit:
        screen.blit(part_of_hit_surf, (145, 180))

    return history_to_game_over_btn.clicked


user_name = ''
def draw_check_user_name():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 120), [130, 110, 740, 400], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [130, 110, 740, 400], 5, 5)

    check_to_game_over_btn = ModeButton(147, 425, 'BACK', False, surface, 'Game_over')
    check_to_game_over_btn.draw()

    direct_to_leaderboard_btn = ModeButton(375, 425, 'SCOREBOARD', False, surface, 'Special_mode')
    direct_to_leaderboard_btn.draw()

    check_to_scoreboard_btn = ModeButton(633, 425, 'NEXT', False, surface, 'Game_over')
    check_to_scoreboard_btn.draw()

    user_name_surf = pygame.Surface((400, 50), pygame.SRCALPHA)
    user_name_surf.fill((50, 50, 50, 150))
    user_name_text = font2.render(f'\'{user_name}\'', True, 'yellow')
    user_name_surf.blit(user_name_text, user_name_text.get_rect(midtop=(200, 0)))
    user_name_rect = user_name_surf.get_rect(center=(500, 150))
    surface.blit(user_name_surf, user_name_rect)

    text1 = font2.render('Enter your name (max 20 chars, cannot be empty)', True, 'white')
    surface.blit(text1, text1.get_rect(center=(500, 200)))
    text2 = None
    if hira_or_kata[0]:
        text2 = font2.render(f'You got {save_score} scores in HIRAGANA', True, '#66ffff')
    if hira_or_kata[1]:
        text2 = font2.render(f'You got {save_score} scores in KATAKANA', True, '#cc66ff')
    surface.blit(text2, text2.get_rect(center=(500, 240)))

    text3 = font3.render('Note that you can only post your score once each game over', True, 'white')
    surface.blit(text3, text3.get_rect(center=(500, 300)))
    text4 = font3.render('If you sure, press "NEXT" to public your score', True, 'white')
    surface.blit(text4, text4.get_rect(center=(500, 340)))
    text5 = font3.render('If you only want to see scoreboard, press "SCOREBOARD"', True, 'white')
    surface.blit(text5, text5.get_rect(center=(500, 380)))

    screen.blit(surface, (0, 0))
    return check_to_game_over_btn.clicked, check_to_scoreboard_btn.clicked, direct_to_leaderboard_btn.clicked


hira_scoreboard, kata_scoreboard = True, False
flag_print_info_into_surface = False
y_pos_of_hira_part = 0
y_pos_of_kata_part = 0
hira_surf, kata_surf, height_of_hira_surf, height_of_kata_surf = None, None, None, None
part_of_hira_surf, part_of_kata_surf = None, None
def draw_rank_chart():
    global scoreboard_hiragana_list, connection_error, scoreboard_katakana_list
    global hira_scoreboard, kata_scoreboard, flag_print_info_into_surface, y_pos_of_hira_part, y_pos_of_kata_part
    global hira_surf, kata_surf, height_of_hira_surf, height_of_kata_surf
    global part_of_hira_surf, part_of_kata_surf

    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surface, (0, 0, 0, 100), [140, 70, 720, 515], 0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 200), [140, 70, 720, 515], 5, 5)

    rank_to_game_over_btn = Button(185, 115, '<-', False, surface)
    rank_to_game_over_btn.draw()

    hira_scoreboard_btn = ModeButton(280, 90, 'HIRAGANA', False, surface, 'Game_over')
    hira_scoreboard_btn.draw()
    kata_scoreboard_btn = ModeButton(550, 90, 'KATAKANA', False, surface, 'Game_over')
    kata_scoreboard_btn.draw()

    if hira_scoreboard_btn.clicked:
        hira_scoreboard, kata_scoreboard = True, False
    if kata_scoreboard_btn.clicked:
        hira_scoreboard, kata_scoreboard = False, True
    if hira_scoreboard:
        pygame.draw.rect(surface, 'yellow', (280, 90, 220, 60), 7, 10)
    if kata_scoreboard:
        pygame.draw.rect(surface, 'yellow', (550, 90, 220, 60), 7, 10)

    # nền của top name score
    header_surf = pygame.Surface((710, 70))
    header_surf.fill('#F48681')
    surface.blit(header_surf, (145, 180))

    # 2 đường ngang vàng
    pygame.draw.line(surface, '#ffddcc', (145, 175), (853, 175), 8)
    pygame.draw.line(surface, '#ffddcc', (145, 245), (853, 245), 8)
    # 2 đường dọc trắng
    pygame.draw.line(surface, 'white', (240, 180), (240, 250), 5)
    pygame.draw.line(surface, 'white', (650, 180), (650, 250), 5)

    surface.blit(banner_font.render('TOP', True, 'white'), (155, 190))
    surface.blit(banner_font.render('NAME', True, 'white'), (390, 190))
    surface.blit(banner_font.render('SCORE', True, 'white'), (690, 190))

    if flag_print_info_into_surface:
        hira_len = len(scoreboard_hiragana_list)
        kata_len = len(scoreboard_katakana_list)

        height_of_hira_surf = hira_len * 80
        height_of_kata_surf = kata_len * 80

        if height_of_hira_surf <= 330:
            height_of_hira_surf = 330
        if height_of_kata_surf <= 330:
            height_of_kata_surf = 330

        hira_surf = pygame.Surface((710, height_of_hira_surf))
        kata_surf = pygame.Surface((710, height_of_kata_surf))
        hira_surf.fill((70, 70, 70))
        kata_surf.fill((70, 70, 70))

        if scoreboard_hiragana_list:
            for i in range(hira_len):
                color_top = 'white'
                color_name_score = 'white'
                if i == 0:
                    color_top = '#0091e6'
                    color_name_score = '#5c4c4f'
                    top1_surf = pygame.Surface((710, 80))
                    top1_tag = pygame.image.load('assets/scoreboard_tag/1.png').convert()
                    top1_surf.blit(top1_tag, (0, 0))
                    hira_surf.blit(top1_surf, (0, 0))
                if i == 1:
                    color_top = '#ffcc00'
                    color_name_score = '#3e505c'
                    top2_surf = pygame.Surface((710, 77))
                    top2_tag = pygame.image.load('assets/scoreboard_tag/2.png').convert()
                    top2_surf.blit(top2_tag, (0, 0))
                    hira_surf.blit(top2_surf, (0, 83))
                if i == 2:
                    color_top = '#737373'
                    color_name_score = '#5c4f25'
                    top3_surf = pygame.Surface((710, 77))
                    top3_tag = pygame.image.load('assets/scoreboard_tag/3.png').convert()
                    top3_surf.blit(top3_tag, (0, 0))
                    hira_surf.blit(top3_surf, (0, 163))
                if i > 2:
                    stupid_surf = pygame.Surface((710, 77))
                    stupid_tag = pygame.image.load('assets/scoreboard_tag/stupid.png').convert()
                    stupid_surf.blit(stupid_tag, (0, 0))
                    hira_surf.blit(stupid_surf, (0, 80*i + 3))
                if i != 9:
                    hira_surf.blit(banner_font.render(f'{i+1}', True, color_top), (30, i*80 + 15))
                else:
                    hira_surf.blit(banner_font.render(f'{i + 1}', True, color_top), (13, i * 80 + 15))
                name_surf = font2.render(scoreboard_hiragana_list[i][0], True, color_name_score)
                hira_surf.blit(name_surf, name_surf.get_rect(midtop=(300, i*80 + 15)))
                score_surf = font2.render(str(scoreboard_hiragana_list[i][1]), True, color_name_score)
                hira_surf.blit(score_surf, score_surf.get_rect(midtop=(610, i*80 + 15)))
                # đường ngang
                pygame.draw.line(hira_surf, 'white', (0, i * 80 + 80), (853, i * 80 + 80), 5)
                # 2 đường dọc
                pygame.draw.line(hira_surf, 'white', (505, i * 80), (505, i * 80 + 80), 5)
                pygame.draw.line(hira_surf, 'white', (95, i * 80), (95, i * 80 + 80), 5)
        if scoreboard_katakana_list:
            for i in range(kata_len):
                color_top = 'white'
                color_name_score = 'white'
                if i == 0:
                    color_top = '#0091e6'
                    color_name_score = '#5c4c4f'
                    top1_surf = pygame.Surface((710, 80))
                    top1_tag = pygame.image.load('assets/scoreboard_tag/1.png').convert()
                    top1_surf.blit(top1_tag, (0, 0))
                    kata_surf.blit(top1_surf, (0, 0))
                if i == 1:
                    color_top = '#ffcc00'
                    color_name_score = '#3e505c'
                    top2_surf = pygame.Surface((710, 77))
                    top2_tag = pygame.image.load('assets/scoreboard_tag/2.png').convert()
                    top2_surf.blit(top2_tag, (0, 0))
                    kata_surf.blit(top2_surf, (0, 83))
                if i == 2:
                    color_top = '#737373'
                    color_name_score = '#5c4f25'
                    top3_surf = pygame.Surface((710, 77))
                    top3_tag = pygame.image.load('assets/scoreboard_tag/3.png').convert()
                    top3_surf.blit(top3_tag, (0, 0))
                    kata_surf.blit(top3_surf, (0, 163))
                if i > 2:
                    stupid_surf = pygame.Surface((710, 77))
                    stupid_tag = pygame.image.load('assets/scoreboard_tag/stupid.png').convert()
                    stupid_surf.blit(stupid_tag, (0, 0))
                    kata_surf.blit(stupid_surf, (0, 80*i + 3))
                if i != 9:
                    kata_surf.blit(banner_font.render(f'{i+1}', True, color_top), (30, i*80 + 15))
                else:
                    kata_surf.blit(banner_font.render(f'{i + 1}', True, color_top), (13, i * 80 + 15))
                name_surf = font2.render(scoreboard_katakana_list[i][0], True, color_name_score)
                kata_surf.blit(name_surf, name_surf.get_rect(midtop=(300, i*80 + 15)))
                score_surf = font2.render(str(scoreboard_katakana_list[i][1]), True, color_name_score)
                kata_surf.blit(score_surf, score_surf.get_rect(midtop=(610, i*80 + 15)))
                # đường ngang
                pygame.draw.line(kata_surf, 'white', (0, i * 80 + 80), (853, i * 80 + 80), 5)
                # 2 đường dọc
                pygame.draw.line(kata_surf, 'white', (505, i * 80), (505, i * 80 + 80), 5)
                pygame.draw.line(kata_surf, 'white', (95, i * 80), (95, i * 80 + 80), 5)
    flag_print_info_into_surface = False

    if y_pos_of_hira_part <= 0:
        y_pos_of_hira_part = 0
    if y_pos_of_hira_part >= height_of_hira_surf - 330:
        y_pos_of_hira_part = height_of_hira_surf - 330

    if y_pos_of_kata_part <= 0:
        y_pos_of_kata_part = 0
    if y_pos_of_kata_part >= height_of_kata_surf - 330:
        y_pos_of_kata_part = height_of_kata_surf - 330

    hira_source_rect = pygame.Rect(0, y_pos_of_hira_part, 710, 330)
    part_of_hira_surf = hira_surf.subsurface(hira_source_rect)

    kata_source_rect = pygame.Rect(0, y_pos_of_kata_part, 710, 330)
    part_of_kata_surf = kata_surf.subsurface(kata_source_rect)

    screen.blit(surface, (0, 0))
    if hira_scoreboard:
        screen.blit(part_of_hira_surf, (145, 250))
    if kata_scoreboard:
        screen.blit(part_of_kata_surf, (145, 250))
    return rank_to_game_over_btn.clicked


scoreboard_hiragana_list = []
scoreboard_katakana_list = []
connection_error = False
async def get_scoreboard_list():
    global scoreboard_hiragana_list, connection_error, scoreboard_katakana_list

    scoreboard_hiragana_list.clear()
    fetch = leaderboard_request.WASMFetch()
    try:
        get_hiragana_response = await fetch.pygbag_get("https://scoreunlocked.pythonanywhere.com/leaderboards/get", params={
            'developer': 'minhphuong04',
            'leaderboard': 'japanese-typing-hiragana'})
        hiragana_data = json.loads(get_hiragana_response)
        scoreboard_hiragana_list = hiragana_data['leaderboard']

        get_katakana_response = await fetch.pygbag_get("https://scoreunlocked.pythonanywhere.com/leaderboards/get", params={
           'developer': 'minhphuong04',
           'leaderboard': 'japanese-typing-katakana'})
        katakana_data = json.loads(get_katakana_response)
        scoreboard_katakana_list = katakana_data['leaderboard']

        connection_error = False
    except:
        connection_error = True


async def post_score():
    global user_name, score, connection_error
    if hira_or_kata[0]:
        fetch = leaderboard_request.WASMFetch()
        try:
            await fetch.pygbag_post("https://scoreunlocked.pythonanywhere.com/leaderboards/post/", data={
                'developer': 'minhphuong04',
                'leaderboard': 'japanese-typing-hiragana',
                'name': user_name,
                'score': str(save_score),
                'validation_data': ''})
            connection_error = False
        except:
            connection_error = True
    elif hira_or_kata[1]:
        fetch = leaderboard_request.WASMFetch()
        try:
            await fetch.pygbag_post("https://scoreunlocked.pythonanywhere.com/leaderboards/post/", data={
                'developer': 'minhphuong04',
                'leaderboard': 'japanese-typing-katakana',
                'name': user_name,
                'score': str(save_score),
                'validation_data': ''})
            connection_error = False
        except:
            connection_error = True


def get_speed(len_text):
    if mode_choices[0]:
        if not learn_mode:
            if len_text in [2, 3]:
                return random_lib.choice([1, 1.5, 2])
            if len_text in [4, 5]:
                return random_lib.choice([1, 1.3, 1.5])
            if len_text in [6, 7]:
                return random_lib.choice([0.6, 0.8, 1])
        else:
            if len_text in [2, 3]:
                return random_lib.choice([1, 1.4])
            if len_text in [4, 5]:
                return random_lib.choice([1, 1.2])
            if len_text in [6, 7]:
                return random_lib.choice([0.6, 0.8])
    elif mode_choices[1]:
        if not learn_mode:
            if len_text in [2, 3]:
                return random_lib.choice([1, 2, 3])
            if len_text in [4, 5]:
                return random_lib.choice([1.5, 1.8, 2])
            if len_text in [6, 7]:
                return random_lib.choice([1, 1.3, 1.5])
        else:
            if len_text in [2, 3]:
                return random_lib.choice([1, 2])
            if len_text in [4, 5]:
                return random_lib.choice([1.5, 1.8])
            if len_text in [6, 7]:
                return random_lib.choice([1, 1.3])
    elif mode_choices[2]:
        if not learn_mode:
            if len_text in [2, 3]:
                return random_lib.choice([2, 3, 4, 5])
            if len_text in [4, 5]:
                return random_lib.choice([2, 3, 4])
            if len_text in [6, 7]:
                return random_lib.choice([1, 2, 2.5])
        else:
            if len_text in [2, 3]:
                return random_lib.choice([2, 3, 4])
            if len_text in [4, 5]:
                return random_lib.choice([2, 3])
            if len_text in [6, 7]:
                return random_lib.choice([1, 1.8])


def get_number_of_word_base_on_mode():
    if mode_choices[0]:
        if level <= 2:
            return level
        if level >= 14:
            return 5
        else:
            return 2 + (level - 2) // 4
    if mode_choices[1]:
        if level <= 2:
            return level
        if level >= 14:
            return 6
        else:
            return 2 + (level - 2) // 3
    if mode_choices[2]:
        if level <= 2:
            return level
        if level >= 17:
            return 7
        else:
            return 2 + (level - 2) // 3


def generate_level():
    word_objs = []
    include = []
    if not learn_mode:
        vertical_spacing = (HEIGHT - 150) // get_number_of_word_base_on_mode()
    else:
        vertical_spacing = (HEIGHT - 180) // get_number_of_word_base_on_mode()
    if True not in choices:
        choices[0] = True
    for i in range(len(choices)):
        if choices[i]:
            include.append((len_indexes[i], len_indexes[i + 1]))
    for i in range(get_number_of_word_base_on_mode()):
        ind_sel = random_lib.choice(include)
        index = random_lib.randint(ind_sel[0], ind_sel[1])
        text = wordlist[index].lower()
        len_text = len(text)

        if not learn_mode:
            y_pos = random_lib.randint(30 + (i * vertical_spacing), (i + 1) * vertical_spacing)
        else:
            if i == 0:
                y_pos = random_lib.randint(25 + (i * vertical_spacing), (i + 1) * vertical_spacing)
            else:
                y_pos = random_lib.randint(55 + (i * vertical_spacing), (i + 1) * vertical_spacing)

        if get_number_of_word_base_on_mode() < 4:
            x_pos = random_lib.randint(WIDTH, WIDTH + len_text*50)
        else:
            x_pos = random_lib.randint(WIDTH, WIDTH + len_text*70)

        speed = get_speed(len_text)
        if not learn_mode:
            speed += level * 0.02

        new_word = Word(text, speed, y_pos, x_pos)
        word_objs.append(new_word)
    return word_objs


def check_answer(scor):
    global submit_to_english, combo
    for wrd in word_objects:
        if wrd.text == submit:
            if not learn_mode:
                combo += 1
                bonus = 0
                if combo == 3: bonus = 50
                elif combo == 6: bonus = 100
                elif combo == 10: bonus = 200
                elif combo == 15: bonus = 500
                elif combo == 20: bonus = 1000
                elif combo == 30: bonus = 5000
                else: bonus = 0
                points = wrd.speed * len(wrd.text) * 10 * (len(wrd.text) / 4) + bonus
                scor += int(points)
            word_objects.remove(wrd)
            woosh.play()
            submit_to_english = split_str_to_list(ja_to_en(submit))
            # những từ submit đúng được cho vào hit_list
            hit_list.append(wrd.text)
    return scor


def check_high_score():
    global high_score
    if score > high_score:
        high_score = score


pop_up_start_time = 0
def pop_up(duration):
    global pop_up_start_time, show_cannot_change_mode_while_playing
    show_cannot_change_mode_while_playing = True
    pop_up_start_time = time.time()
    pygame.time.set_timer(pygame.USEREVENT + 1, duration * 1000)


def variable_change(old, new):
    return old != new


show_check_user_name = False
show_history = False
show_rank_chart = False
new_record_found = False
show_theme = True
show_game_mode = False
show_are_you_sure = False
show_cannot_change_mode_while_playing = False
show_menu = True
show_manual = False
show_music = False
show_game_over = False
wordlist = wordlist_hira
wordlist_translated = wordlist_hira_translated
flag_to_load_wordlist = False
run = True
post_score_each_game_over = True

len_indexes = []
length = 1
is_in_menu = True


async def main():
    global score, save_score, theme_list, random_theme_index, level, lives, word_objects, high_score, pz, new_level
    global submit, submit_to_english, active_string, active_string_hiragana, all_words_appeared, hit_list, miss_list
    global choices, music_choices, mode_choices, hira_or_kata, mouse_detected, y_pos_of_miss_part, y_pos_of_hit_part
    global pop_up_start_time, show_history, new_record_found, show_theme, show_game_mode, show_are_you_sure
    global show_cannot_change_mode_while_playing, show_menu, show_manual, show_music, show_game_over
    global run, len_indexes, length, music_channel, music_playlist_object, music_playlist_index
    global blurred_image, theme_image, learn_mode, combo, current_song_playlist_index, flag_draw_miss_hit_list
    global flag_to_load_wordlist, wordlist, wordlist_translated, pause_btn_color, miss, hit
    global combo_signal_list, get_time_signal, word_color, show_rank_chart, history_to_game_over_butt
    global user_name, show_check_user_name, scoreboard_katakana_list, scoreboard_hiragana_list
    global post_score_each_game_over, is_in_menu
    global hira_scoreboard, kata_scoreboard, flag_print_info_into_surface, y_pos_of_hira_part, y_pos_of_kata_part
    global hira_surf, kata_surf, height_of_hira_surf, height_of_kata_surf
    global part_of_hira_surf, part_of_kata_surf

    current_theme_index = random_theme_index
    current_song_playlist_index = music_playlist_index
    delete_counter = 0
    last_delete_time = pygame.time.get_ticks()

    enable_fps = False

    while run:
        # play music
        if not music_channel.get_busy():
            music_playlist_index += 1
            if music_playlist_index == len(music_playlist_object):
                music_playlist_index = 0
            current_song_playlist_index = music_playlist_index
            music_channel.play(music_playlist_object[music_playlist_index])
        elif variable_change(current_song_playlist_index, music_playlist_index):
            current_song_playlist_index = music_playlist_index
            new_music = music_playlist_object[music_playlist_index]
            music_channel.play(new_music)

        # load từ từ bảng hira hoặc kata vào
        if hira_or_kata[0] and flag_to_load_wordlist:
            wordlist = wordlist_hira
            wordlist_translated = wordlist_hira_translated
            flag_to_load_wordlist = False
        if hira_or_kata[1] and flag_to_load_wordlist:
            wordlist = wordlist_kata
            wordlist_translated = wordlist_kata_translated
            flag_to_load_wordlist = False

        len_indexes = []
        length = 1

        # wordlist.sort(key=len)
        for i in range(len(wordlist)):
            if len(wordlist[i]) > length:
                length += 1
                len_indexes.append(i)
        len_indexes.append(len(wordlist))

        # in lên màn hình
        screen.fill('gray')
        timer.tick(fps)

        # draw static background
        if variable_change(current_theme_index, random_theme_index):
            current_theme_index = random_theme_index
            random_theme_index = random_theme_index
            theme_image = pygame.image.load(f'assets/theme/{theme_list[random_theme_index]}').convert()
            blurred_image = theme_image.copy()
            pygame.Surface.blit(blurred_image, theme_image, (0, 0))
            blurred_image.set_alpha(180)
        if show_theme:
            screen.blit(blurred_image, (0, 0))

        pause_butt = draw_screen()

        if combo_signal_list[0] and combo == 3:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(3)
        if combo_signal_list[1] and combo == 6:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(6)
        if combo_signal_list[2] and combo == 10:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(10)
        if combo_signal_list[3] and combo == 15:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(15)
        if combo_signal_list[4] and combo == 20:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(20)
        if combo_signal_list[5] and combo == 30:
            cur_time = pygame.time.get_ticks()
            if cur_time - get_time_signal <= 1000:
                draw_combo(30)

        if pz:
            if show_menu:
                resume_butt, changes, back_menu_butt, manual_butt, music_butt, game_mode_butt, scoreboard_butt = draw_menu()
                is_in_menu = True
                if resume_butt:
                    pz = False
                    show_menu = False
                if back_menu_butt:
                    show_are_you_sure = True
                    show_menu = False
                if game_mode_butt:
                    show_game_mode = True
                    show_menu = False
                if manual_butt:
                    show_menu = False
                    show_manual = True
                if music_butt:
                    show_menu = False
                    show_music = True
                if scoreboard_butt:
                    flag_print_info_into_surface = True
                    await get_scoreboard_list()
                    show_menu = False
                    show_rank_chart = True
                if one_click_accept():
                    choices = changes
            if show_manual:
                manual_to_menu_butt = draw_manual()
                if manual_to_menu_butt:
                    show_manual = False
                    show_menu = True
            if show_music:
                music_to_menu_butt, music_pause_butt, music_unpause_butt, vol_up_butt, vol_down_butt = draw_music_option()
                if music_to_menu_butt:
                    show_music = False
                    show_menu = True
                if music_pause_butt:
                    music_channel.pause()
                if music_unpause_butt:
                    music_channel.unpause()
                cur_vol = music_channel.get_volume()
                if vol_up_butt and cur_vol <= 1:
                    music_channel.set_volume(cur_vol + 0.1)
                if vol_down_butt and cur_vol >= 0:
                    music_channel.set_volume(cur_vol - 0.1)
                if vol_down_butt and cur_vol <= 0.1:
                    music_channel.set_volume(0)

            if show_game_over:
                restart_butt, game_over_to_menu_butt, word_history_butt, check_user_butt = draw_game_over()
                show_menu = False
                active_string = ''
                is_in_menu = False
                if restart_butt:
                    show_game_over = False
                    new_level = True
                    pz = False
                    all_words_appeared = []
                    hit_list = []
                    miss_list = []
                    submit_to_english = ['', '', '']
                    y_pos_of_hit_part = 0
                    y_pos_of_miss_part = 0
                    score = 0
                    post_score_each_game_over = True
                if game_over_to_menu_butt:
                    show_game_over = False
                    show_menu = True
                    all_words_appeared = []
                    hit_list = []
                    miss_list = []
                    submit_to_english = ['', '', '']
                    y_pos_of_hit_part = 0
                    y_pos_of_miss_part = 0
                    score = 0
                    post_score_each_game_over = True
                if word_history_butt:
                    show_game_over = False
                    show_history = True
                    flag_draw_miss_hit_list = True
                if check_user_butt:
                    if post_score_each_game_over:
                        show_game_over = False
                        show_check_user_name = True
                    else:
                        await get_scoreboard_list()
                        show_game_over = False
                        show_rank_chart = True
            if show_are_you_sure:
                yes_butt, no_butt = draw_are_you_sure()
                if yes_butt:
                    level = 1
                    lives = 5
                    score = 0
                    new_level = True
                    active_string = ''
                    word_objects = []
                    all_words_appeared = []
                    hit_list = []
                    miss_list = []
                    show_are_you_sure = False
                    show_menu = True
                    submit_to_english = ['', '', '']
                if no_butt:
                    show_are_you_sure = False
                    show_menu = True
            if show_game_mode:
                game_mode_to_menu_butt, easy_butt, medium_butt, hard_butt, hira_butt, kata_butt = draw_game_mode()
                if not new_level:
                    if easy_butt or medium_butt or hard_butt or hira_butt or kata_butt:
                        pop_up(2)
                    if show_cannot_change_mode_while_playing:
                        draw_cannot_change_mode_while_playing()
                if new_level:
                    if easy_butt:
                        mode_choices[0], mode_choices[1], mode_choices[2] = True, False, False
                    if medium_butt:
                        mode_choices[0], mode_choices[1], mode_choices[2] = False, True, False
                    if hard_butt:
                        mode_choices[0], mode_choices[1], mode_choices[2] = False, False, True
                    if hira_butt:
                        hira_or_kata[0], hira_or_kata[1] = True, False
                        flag_to_load_wordlist = True
                    if kata_butt:
                        hira_or_kata[0], hira_or_kata[1] = False, True
                        flag_to_load_wordlist = True
                if game_mode_to_menu_butt:
                    show_game_mode = False
                    show_menu = True
            if show_history:
                history_to_game_over_butt = draw_history()
                if history_to_game_over_butt:
                    show_history = False
                    show_game_over = True
            if show_check_user_name:
                check_to_game_over_butt, next_to_scoreboard_butt, direct_to_scoreboard_butt = draw_check_user_name()
                if check_to_game_over_butt:
                    show_check_user_name = False
                    show_game_over = True
                if direct_to_scoreboard_butt:
                    flag_print_info_into_surface = True
                    await get_scoreboard_list()
                    show_check_user_name = False
                    show_rank_chart = True
                if next_to_scoreboard_butt:
                    if len(user_name.strip()) > 0:
                        user_name = user_name.strip()
                        flag_print_info_into_surface = True
                        show_check_user_name = False
                        show_rank_chart = True
                        await get_scoreboard_list()
                        await post_score()
                        post_score_each_game_over = False
            if show_rank_chart:
                rank_chart_to_game_over_butt = draw_rank_chart()
                if rank_chart_to_game_over_butt:
                    if not is_in_menu:
                        if post_score_each_game_over:
                            show_rank_chart = False
                            show_check_user_name = True
                        else:
                            show_rank_chart = False
                            show_game_over = True
                    else:
                        show_rank_chart = False
                        show_menu = True
        if not show_game_mode:
            show_cannot_change_mode_while_playing = False
        if new_level and not pz:
            word_objects = generate_level()
            # lấy tất cả những từ đã xuất hiện cho vào all_words_appeared list
            for i in word_objects:
                all_words_appeared.append(i.text)
            new_level = False
        else:
            for w in word_objects:
                w.draw()
                if not pz:
                    w.update()
                if w.x_pos < -(len(w.text) * 50 + 50):
                    word_objects.remove(w)
                    if not learn_mode:
                        lives -= 1
                    combo = 0
                    combo_signal_list = [False] * 6
        if len(word_objects) <= 0 and not pz:
            level += 1
            new_level = True

        if submit != '':
            init = score
            score = check_answer(score)
            submit = ''
            if init == score:
                if not learn_mode:
                    wrong.play()
                combo = 0
                combo_signal_list = [False] * 6
        if combo == 30:
            combo = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                check_high_score()
                run = False
            elif event.type == pygame.USEREVENT + 1:
                show_cannot_change_mode_while_playing = False
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F2:
                    if enable_fps:
                        enable_fps = False
                    else:
                        enable_fps = True

                if not pz:
                    if event.unicode.lower() in letters:
                        if len(to_kana(active_string)) <= 10:
                            active_string += event.unicode
                        click.play()
                    if event.key == pygame.K_BACKSPACE and len(active_string) > 0:
                        active_string = active_string[:-1]
                        current_delete_time = pygame.time.get_ticks()
                        if current_delete_time - last_delete_time > 200:
                            delete_counter = 0
                        else:
                            delete_counter += 1
                        last_delete_time = current_delete_time
                        if delete_counter == 2:
                            active_string = ''
                            delete_counter = 0
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        submit = to_kana(active_string)
                        active_string = ''

                else:
                    if show_check_user_name:
                        if event.unicode:
                            if len(user_name) <= 19:
                                user_name += event.unicode
                        if event.key == pygame.K_BACKSPACE and len(user_name) > 0:
                            user_name = user_name[:-2]
                            current_delete_time = pygame.time.get_ticks()
                            if current_delete_time - last_delete_time > 200:
                                delete_counter = 0
                            else:
                                delete_counter += 1
                            last_delete_time = current_delete_time
                            if delete_counter == 2:
                                user_name = ''
                                delete_counter = 0

                if event.key == pygame.K_ESCAPE:
                    if pz and show_menu:
                        pz = False
                        show_menu = False
                    elif not pz and not show_menu:
                        pz = True
                        show_menu = True
                if event.key == pygame.K_RIGHT:
                    random_theme_index += 1
                    if random_theme_index == len(theme_list):
                        random_theme_index = 0
                if event.key == pygame.K_LEFT:
                    random_theme_index -= 1
                    if random_theme_index == -1:
                        random_theme_index = len(theme_list) - 1
            if event.type == pygame.MOUSEBUTTONDOWN:
                if show_history:
                    if miss:
                        if event.button == 4:
                            y_pos_of_miss_part -= 170
                        elif event.button == 5:
                            y_pos_of_miss_part += 170
                    if hit:
                        if event.button == 4:
                            y_pos_of_hit_part -= 170
                        elif event.button == 5:
                            y_pos_of_hit_part += 170
                if show_rank_chart:
                    if hira_scoreboard:
                        if event.button == 4:
                            y_pos_of_hira_part -= 80
                        elif event.button == 5:
                            y_pos_of_hira_part += 80
                    if kata_scoreboard:
                        if event.button == 4:
                            y_pos_of_kata_part -= 80
                        elif event.button == 5:
                            y_pos_of_kata_part += 80

            if event.type == pygame.MOUSEBUTTONDOWN and pz:
                if event.button == 1:
                    choices = changes

        if pause_butt:
            if not pz:
                pz = True
                show_menu = True

        if lives < 1:
            save_score = score
            if score > high_score:
                new_record_found = True
            else:
                new_record_found = False
            pz = True
            show_game_over = True
            level = 1
            lives = 5
            word_objects = []
            new_level = True
            check_high_score()
            all_words_appeared = del_repetition(all_words_appeared)
            hit_list = del_repetition(hit_list)
            miss_list = [wrd for wrd in all_words_appeared if wrd not in hit_list]

        if enable_fps:
            real_fps = timer.get_fps()
            fps_text = font2.render("{:.1f}".format(real_fps), True, 'black')
            screen.blit(fps_text, (925, 5))

        pygame.display.flip()

        await asyncio.sleep(0)

asyncio.run(main())

