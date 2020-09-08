import random
import string


def id_gen(length=20):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join((random.choice(letters_and_digits) for i in range(length)))


def code_gen(length=6):
    return ''.join((random.choice(string.digits) for i in range(length)))
