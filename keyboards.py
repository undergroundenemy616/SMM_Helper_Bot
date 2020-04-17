from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import *


def make_keyboard(groups):
    keyb = []
    i = 0
    while i <= len(groups):
        tmp = []
        j = i
        if len(groups) - i < 3:
            while j < len(groups):
                tmp.append(KeyboardButton(text=groups[j]))
                j = j + 1
        else:
            while j < i + 3:
                tmp.append(KeyboardButton(text=groups[j]))
                j = j + 1
        keyb.append(tmp)
        i = i + 3
    return keyb


CHOOSE_PHOTO_KEYBOARD = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=NO_PHOTO),
                ],
                [
                    KeyboardButton(text=OK), KeyboardButton(text=CANCEL),
                ],
            ],
            resize_keyboard=True
        )

ACCEPT_OR_CANCEL_KEYBOARD = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=YES), KeyboardButton(text=CANCEL),
                ],
            ],
            resize_keyboard=True
        )

CHOOSE_GROUP_KEYBOARD = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=VK_NAME), KeyboardButton(text=OK_NAME),
            ],
            [
                KeyboardButton(text=CANCEL),
            ],
        ],
        resize_keyboard=True
    )

YES_OR_NO_KEYBOARD = [KeyboardButton(text=OK), KeyboardButton(text=CANCEL)]
