from typing import List
import sys
import termios
import tty

from arc.color import fg, bg, effects


A = 65
B = 66
C = 67
D = 68
E = 69
F = 70
G = 71
H = 72
I = 73
J = 74
K = 75
L = 76
M = 77
N = 78
O = 79
P = 80
Q = 81
R = 82
S = 83
T = 84
U = 85
V = 86
W = 87
X = 88
Y = 89
Z = 90

a = 97
b = 98
c = 99
d = 100
e = 101
f = 102
g = 103
h = 104
i = 105
j = 106
k = 107
l = 108
m = 109
n = 110
o = 111
p = 112
q = 113
r = 114
s = 115
t = 116
u = 117
v = 118
w = 119
x = 120
y = 121
z = 122

ZERO = 48
ONE = 49
TWO = 50
THREE = 51
FOUR = 52
FIVE = 53
SIX = 54
SEVEN = 55
EIGHT = 56
NINE = 57

NUMBERS = (ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE)

OPENING_BRACKET = 91
BACKSLASH = 92
CLOSING_BRACKET = 93

ESC = 27  # \u001b
UP = (ESC, OPENING_BRACKET, A)
DOWN = (ESC, OPENING_BRACKET, B)
RIGHT = (ESC, OPENING_BRACKET, C)
LEFT = (ESC, OPENING_BRACKET, D)
# Enter is 13 on some systems and 10 on others
ENTER_TUP = (13, 10)


def getch(val: int = 1):
    # I have no idea how this works lol
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(val)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def send(string):
    sys.stdout.write(string)
    sys.stdout.flush()


class Move:
    @classmethod
    def up(cls, val: int):
        send(f"\u001b[{val}A")

    @classmethod
    def down(cls, val: int):
        send(f"\u001b[{val}B")

    @classmethod
    def right(cls, val: int):
        send(f"\u001b[{val}C")

    @classmethod
    def left(cls, val: int):
        send(f"\u001b[{val}D")


class SelectionMenu:
    def __init__(
        self,
        options: List[str],
        format_str="({index}) {string}",
        selected_format_str=fg.RED
        + effects.BOLD
        + "({index}) {string}"
        + effects.CLEAR,
    ):
        self.options: list = options
        self.format_str: str = format_str
        self.selected_format_str: str = selected_format_str

    def render(self):
        selected_index = 0

        clear()
        while True:
            home_pos()
            print(f"Press {fg.YELLOW}q{effects.CLEAR} to quit at any time")
            for index, string in enumerate(self.options):
                if index == selected_index:
                    print(self.selected_format_str.format(index=index, string=string))
                else:
                    print(self.format_str.format(index=index, string=string))

            char = ord(getch())

            if char == q:
                print("Quitting")
                sys.exit(0)

            elif char in NUMBERS:
                value = int(chr(char))
                if value < len(self.options):
                    selected_index = value

            elif char in ENTER_TUP:
                return selected_index, self.options[selected_index]

            elif char == ESC:
                sequence = (char, ord(getch()), ord(getch()))

                if sequence == UP:
                    if selected_index > 0:
                        selected_index -= 1
                elif sequence == DOWN:
                    if selected_index < len(self.options) - 1:
                        selected_index += 1


def getpos():
    send("\033[6n")
    getch(2)
    chars = ""
    while (char := getch()) != "R":
        chars += char

    return tuple(int(val) for val in chars.split(";"))


def pos(row, column):
    send(f"\033[{row};{column}f")


def save_pos():
    send("\u001b[s")


def restore_pos():
    send("\u001b[u")


def clear():
    send("\u001b[2J")


def home_pos():
    send("\u001b[H")
