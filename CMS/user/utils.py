from string import ascii_letters
from random import sample


def random_string(length=32):
    return ''.join(sample(ascii_letters, length))
