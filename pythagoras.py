#!/usr/bin/env python3
import csv
import math
import os
import sys
from time import time

from colorama import Fore, Style, init
from pyfiglet import figlet_format
from readchar import readchar

from pythagoras.polyphonic_player import PolyphonicPlayer

dir_path = os.path.dirname(sys.argv[0])
FILENAME = os.path.join(dir_path, 'ratios.csv')
BASE_FREQ = int(sys.argv[1]) if len(sys.argv) > 1 else 10

template = '\n{1:>6}{2:>6}{3:>6}{4:>6}{5:>6}{6:>6}{7:>6}{8:>6}{9:>6}{0:>6}    '
help_msg = f'''
choose slot by pressing a number key
slots: {template.format(*'0123456789')}

after that type a number from 01 to 99
for example, typing 45, means {45 * BASE_FREQ} Hz will be played from this slot,
typing 08, means {8 * BASE_FREQ} Hz will be played
type 00 to delete sound in this slot

if you like some chord, press r to record it (it will be placed in ratios.csv file)
pressing e will save the chord progression from the previous to this chord

for some ideas of things to try, read:
https://github.com/fsondej/pythagoras/blob/master/check_it_out.md

press q to quit
'''

# credit: stackoverflow.com/questions/10702942/note-synthesis-harmonics-violin-piano-guitar-bass-frequencies-midi


# def set_ratios(self, *ratios):
#     self.ratios = list(ratios)


def get_digit(char):
    keymap = {
        'a': '1',
        's': '2',
        'd': '3',
        'f': '4',
        'v': '5',
        'n': '6',
        'j': '7',
        'k': '8',
        'l': '9',
        ';': '0',
    }
    if char == 'q':
        raise KeyboardInterrupt
    if char in keymap:
        char = keymap[char]
    digit = int(char)   # may throw ValueError
    return digit


def color_number(n):
    color_map = {
        2: Fore.RED,
        3: Fore.GREEN,
        4: Fore.RED,
        5: Fore.BLUE,
        6: Fore.YELLOW,
        8: Fore.RED,
        9: Fore.GREEN,
        10: Fore.MAGENTA,
        12: Fore.YELLOW,
        15: Fore.CYAN
    }
    color = ''
    if n in color_map:
        color += color_map[n]
    return color + str(n) + Style.RESET_ALL


def decompose(n, length=6):
    if n == 0:
        return ''
    i = math.floor(math.sqrt(n))
    while True:
        if n % i == 0:
            j = n // i
            # pan is needed because colored text isn't formatted correctly
            real_len = len(f'{i}*{j}')
            pan = ' ' * (6 - real_len)
            return f'{pan}{color_number(i)}*{color_number(j)}'
        i -= 1


def control(player, verbose=True):
    with open(FILENAME, 'a') as csvfile:
        writer = csv.writer(csvfile)
        while True:
            command = readchar()
            if command == 'h':
                print(help_msg)
                continue
            elif command == 'r':
                writer.writerow([time(), 'node'] + player.ratios)
                print('chord saved', end='  ', flush=True)
                continue
            elif command == 'e':
                writer.writerow([time(), 'edge'] + player.ratios)
                print('chords saved', end='  ', flush=True)
                continue

            try:
                index = get_digit(command)
                # draw index indicator
                placeholder = [''] * 10
                placeholder[index] = '||'
                print(template.format(*placeholder), end='', flush=True)
                # read frequency value
                digit1 = get_digit(readchar())
                digit2 = get_digit(readchar())
            except ValueError:
                print('wrong key', end=' ', flush=True)
                continue
            except KeyboardInterrupt:
                return

            new_ratio = digit1 * 10 + digit2
            player.ratios[index] = new_ratio
            nums_to_display = [n if n != 0 else '' for n in player.ratios]
            print(template.format(*nums_to_display), end='', flush=True)
            if verbose:
                factors = (decompose(num) for num in player.ratios)
                print(template.format(*factors), end='', flush=True)

            writer.writerow([time(), 'auto'] + player.ratios)


if __name__ == '__main__':
    # if len(sys.argv) > 1:
    #     base_freq = float(sys.argv[1])
    # else:
    #     base_freq = 5
    init()
    player = PolyphonicPlayer(base_freq=BASE_FREQ)
    player.start()
    player.ratios = [0] * 10
    print(figlet_format('Pythagoras', font='graffiti'))
    print('press h for help')
    control(player)
    player.kill()
    player.join()
