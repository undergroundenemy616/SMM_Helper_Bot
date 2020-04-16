import io
import json
import os
import time

import requests
from telegram import (Bot, KeyboardButton, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)


import odnoklassniki
import vk_api
from dotenv import load_dotenv

load_dotenv()

vk_name = 'ВКонтакте'
ok_name = "Одноклассники"
vk_groups = {}
ok_groups = {}

vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
vk = vk_session.get_api()

ok = odnoklassniki.Odnoklassniki(os.getenv('CLIENT_KEY'), os.getenv('CLIENT_SECRET'), os.getenv('ACCESS_TOKEN'))


def send_image_to_server_vk(image):
    info = vk.photos.getWallUploadServer()
    result = requests.post(info['upload_url'], files=image).json()
    rs = vk.photos.saveWallPhoto(photo=result['photo'], server=result['server'], hash=result['hash'])
    photo_id = 'photo' + str(rs[0]['owner_id']) + '_' + str(rs[0]['id'])
    return photo_id


def send_image_to_server_ok(image):
    info = ok.photosV2.getUploadUrl()
    result = requests.post(info['upload_url'], files=image).json()
    res = result['photos']
    cond = list(res.values())
    token = cond[0]['token']
    return token


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


def start_conv_handler(bot: Bot, update: Update):
    user = update.effective_user
    name = user.first_name if user else 'аноним'
    bot.send_message(
        chat_id=update._effective_chat,
        reply_text=(f'Привет, {name}, Я твой личный SMM-помощник!'
                    f'\n\nНапиши /help, чтобы узнать чем я могу быть тебе полезен.')
    )


def help_handler(bot: Bot, update: Update):
    update.message.reply_text(
        text=(f'Я умею одновременно публиковать посты в группы социальных сетей, а конкретно в {vk_name} и '
              f'{ok_name}.\n\n1. Введи /add, чтобы я запомнил интересующие тебя группы. \n\n2. Введи /post, чтобы '
              f'я сделал посты в твоих сохраненных группах.\n\n3. Введи /delete, чтобы я забыл ненужные тебе группы.')
    )


def start_post_handler(bot: Bot, update: Update, user_data: dict):
    user_data['site'] = vk_name
    user_data['vk_groups'] = []
    user_data['ok_groups'] = []
    user_data['vk_tmp'] = []
    user_data['ok_tmp'] = []
    user_data['photos'] = [[], 0]
    user_data['text'] = ''
    user_data['flag'] = ''
    if not list(vk_groups.keys()) and not list(ok_groups.keys()):
        update.message.reply_text(
            text=f"У вас нет групп",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    if list(vk_groups.keys()):
        keyboard = make_keyboard(list(vk_groups.keys()))
        keyboard.append([KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌')])
        reply_markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
        update.message.reply_text(
            text=f"Выбери группы {vk_name}, куда нужно сделать пост. Когда закончишь нажми Готово ✅",
            reply_markup=reply_markup,
        )
        return "post_to_vk"
    elif list(ok_groups.keys()):
        keyboard = make_keyboard(list(ok_groups.keys()))
        keyboard.append([KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌')])
        reply_markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
        update.message.reply_text(
            text=f"Выбери группы {ok_name}, куда нужно сделать пост. Когда закончишь нажми Готово ✅",
            reply_markup=reply_markup,
        )
        return "post_to_ok"


def post_make_post_ok_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.text == 'Готово ✅':
        update.message.reply_text(
            text=f'Напиши текст поста для публикации',
            reply_markup=ReplyKeyboardRemove(),
        )
        return "attachments"
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    elif update.message.text not in list(ok_groups.keys()):
        update.message.reply_text(
            text='Я не понимаю, введи группы с клаиватуры',
        )
        return ConversationHandler.entry_points
    elif update.message.text not in user_data['ok_tmp']:
        user_data['ok_tmp'].append(update.message.text)
        id = ok_groups[update.message.text]
        user_data['ok_groups'].append(id)
        return ConversationHandler.entry_points


def attachments_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        user_data['text'] = update.message.text
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Без фото'),
                ],
                [
                    KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌'),
                ],
            ],
            resize_keyboard=True
        )
        update.message.reply_text(
            text='Приложи фотографию / фотографии к посту',
            reply_markup=reply_markup
        )
        return "final_post_to_vk"


def post_make_post_vk_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.text == 'Готово ✅':
        if list(ok_groups.keys()):
            keyboard = make_keyboard(list(ok_groups.keys()))
            keyboard.append([KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌')])
            reply_markup = ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True
            )
            update.message.reply_text(
                text=f"Выбери группы {ok_name}, куда нужно сделать пост. Когда закончишь нажми Готово",
                reply_markup=reply_markup,
            )
            return "post_to_ok"
        else:
            update.message.reply_text(
                text=f'Напиши текст поста для публикации',
                reply_markup=ReplyKeyboardRemove(),
            )
            return "attachments"
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    elif update.message.text not in list(vk_groups.keys()):
        update.message.reply_text(
            text='Я не понимаю, введи группы с клаиватуры',
        )
        return ConversationHandler.entry_points
    elif update.message.text not in user_data['vk_tmp']:
        user_data['vk_tmp'].append(update.message.text)
        id = vk_groups[update.message.text]
        user_data['vk_groups'].append(id)
        return ConversationHandler.entry_points


def final_post_vk_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.photo:
        if user_data['photos'][1] == 9:
            update.message.reply_text(
                text="К посту можно прикрепить максимум 9 фотографий",
            )
        else:
            file = bot.getFile(update.message.photo[-1].file_id)
            user_data['photos'][0].append(file)
            user_data['photos'][1] += 1
        return ConversationHandler.entry_points

    text = user_data['text']
    user_data['flag'] = update.message.text
    if user_data['vk_groups']:
        if user_data['flag'] == 'Без фото':
            for group_id in user_data['vk_groups']:
                try:
                    vk.wall.post(owner_id=-group_id, message=text)
                except Exception as e:
                    update.message.reply_text(
                        reply_markup=ReplyKeyboardRemove(),
                        text=f"Пост в группу с ID:{group_id} не опубликован. Проблема - {e}",
                    )
                    continue
                update.message.reply_text(
                    reply_markup=ReplyKeyboardRemove(),
                    text=f"Пост в группу с ID:{group_id} успешно опубликован",
                )
        elif user_data['flag'] == 'Отмена ❌':
            update.message.reply_text(
                text='Ок',
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        elif user_data['flag'] == "Готово ✅":
            for group_id in user_data['vk_groups']:
                update.message.reply_text(
                    text="Загрузка поста, ожидайте...",
                    reply_markup=ReplyKeyboardRemove(),
                )
                attachments = []
                for photo in user_data['photos'][0]:
                    img_url = photo.file_path
                    remote_image = requests.get(img_url)
                    photo = io.BytesIO(remote_image.content)
                    photo.name = 'img.png'
                    files = {'photo': photo}
                    attachments.append(send_image_to_server_vk(files))
                try:
                    vk.wall.post(owner_id=-group_id, message=text, attachments=attachments)
                except Exception as e:
                    update.message.reply_text(
                        reply_markup=ReplyKeyboardRemove(),
                        text=f"Пост в группу с ID:{group_id} не опубликован. Проблема - {e}",
                    )
                    continue
                update.message.reply_text(
                    text=f"Пост в группу с ID:{group_id} успешно опубликован",
                )
        else:
            update.message.reply_text(
                text='Я вас не понимаю',
            )
            return ConversationHandler.entry_points
    else:
        update.message.reply_text(
            reply_markup=ReplyKeyboardRemove(),
            text=f"Группы для добавления постов в {vk_name} не были выбраны"
        )
    if user_data['ok_groups']:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Да'), KeyboardButton(text='Отмена ❌'),
                ],
            ],
            resize_keyboard=True
        )
        time.sleep(2)
        update.message.reply_text(
            text=f'С {vk_name} разобрались, в {ok_name} выкладываем?',
            reply_markup=reply_markup
        )
        return "final_post_to_ok"
    else:
        update.message.reply_text(
            reply_markup=ReplyKeyboardRemove(),
            text=f"Группы для добавления постов в {ok_name} не были выбраны"
        )
        return ConversationHandler.END


def final_post_to_ok_handler(bot: Bot, update: Update, user_data: dict):
    text = user_data['text']
    if update.message.text == 'Да':
        if user_data['flag'] == 'Без фото':
            x = {
                "media": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
            attachment = json.dumps(x)
            for group_id in user_data['ok_groups']:
                try:
                    ok.mediatopic.post(type='GROUP_THEME', gid=group_id, attachment=attachment)
                except Exception as e:
                    update.message.reply_text(
                        reply_markup=ReplyKeyboardRemove(),
                        text=f"Пост в группу ID:{group_id} не опубликован. Проблема - {e}",
                    )
                    continue
                update.message.reply_text(
                    text=f"Пост в группу ID:{group_id} успешно опубликован",
                    reply_markup=ReplyKeyboardRemove(),
                )
        elif user_data['flag'] == "Готово ✅":
            for group_id in user_data['ok_groups']:
                update.message.reply_text(
                    text="Загрузка поста, ожидание...",
                    reply_markup=ReplyKeyboardRemove(),
                )
                x = {
                    "media": [
                        {
                            "type": "text",
                            "text": text
                        },
                        {
                            "type": "photo",
                            "list": []
                        }
                    ]
                }
                try:
                    for photo in user_data['photos'][0]:
                        img_url = photo.file_path
                        remote_image = requests.get(img_url)
                        photo = io.BytesIO(remote_image.content)
                        photo.name = 'img.png'
                        files = {'photo': photo}
                        elem = {'id': send_image_to_server_ok(files)}
                        x['media'][1]['list'].append(elem)
                    attachments = json.dumps(x)
                    ok.mediatopic.post(type='GROUP_THEME', gid=group_id, attachment=attachments)
                except Exception as e:
                    update.message.reply_text(
                        reply_markup=ReplyKeyboardRemove(),
                        text=f"Пост в группу ID:{group_id} не опубликован. Проблема - {e}",
                    )
                    continue
                update.message.reply_text(
                    reply_markup=ReplyKeyboardRemove(),
                    text=f"Пост в группу ID:{group_id} успешно опубликован",
                )
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            text='Я вас не понимаю',
        )
        return ConversationHandler.entry_points
    return ConversationHandler.END


def add_start_handler(bot: Bot, update: Update):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=vk_name), KeyboardButton(text=ok_name),
            ],

            [
                KeyboardButton(text='Отмена ❌'),
            ],
        ],
        resize_keyboard=True
    )
    update.message.reply_text(
        "Из какой соцсети мне сохранить группу?",
        reply_markup=reply_markup,
    )
    return "choose_site"


def add_choose_site_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.text == vk_name or update.message.text == ok_name:
        user_data['site'] = update.message.text
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[

                [
                    KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌'),
                ],
            ],
            resize_keyboard=True
        )
        update.message.reply_text(
            text="Введи  идентификатоы или короткие имена сообществ. Как закончишь нажми Готово ✅",
            reply_markup=reply_markup
        )
        return "get_group"
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text="Ок",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            text="Я не понимаю, выбери соцсеть на клавиатуре",
        )
        return ConversationHandler.entry_points


def add_group(site_groups, group_name, group_id, update):
    if group_name != '':
        if group_name == 'DELETED':
            update.message.reply_text(
                text=f"Группа {group_name} удалена, попробуй добавить другую",
            )
        elif group_id in list(site_groups.values()):
            update.message.reply_text(
                text=f"Группа {group_name} уже есть в списке твоих рабочих групп",
            )
        else:
            site_groups[group_name] = group_id
            update.message.reply_text(
                text=f"Группа {group_name} добавлена в список твоих рабочих групп",
            )
    else:
        update.message.reply_text(
            text=f"Группа {group_name}  недоступна, попробуй добавить другую",
        )
    return "get_group"


def add_get_group_handler(bot: Bot, update: Update, user_data: dict):
    if update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text="Ок",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    elif update.message.text == 'Готово ✅':
        update.message.reply_text(
            text="Сохранил",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    id = update.message.text
    try:
        if user_data['site'] == vk_name:
            group = vk.groups.getById(group_id=id)
            add_group(vk_groups, group[0]['name'], group[0]['id'], update)
        elif user_data['site'] == ok_name:
            group = {}
            group['name'] = ok.group.getInfo(uids=id, fields='NAME')[0]['name']
            group['id'] = ok.group.getInfo(uids=id, fields='UID')[0]['uid']
            add_group(ok_groups, group['name'], group['id'], update)
    except Exception as e:
        print(e)
        update.message.reply_text(
            text=f"Некоректный ID, попробуй еще раз",
        )
        return "get_group"


def delete_start_handler(bot: Bot, update: Update):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=vk_name), KeyboardButton(text=ok_name),
            ],
            [
                KeyboardButton(text='Отмена ❌'),
            ],
        ],
        resize_keyboard=True
    )
    update.message.reply_text(
        text="Из какой соцсети мне удалить группу?",
        reply_markup=reply_markup,
    )
    return "delete_group"


def get_delete_interface(groups, update):
    keyboard = make_keyboard(list(groups.keys()))
    keyboard.append([KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌')])
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
    update.message.reply_text(
        text='После удаления ненужных групп нажми Готово ✅',
        reply_markup=reply_markup,
    )


def delete_groups_handler(bot: Bot, update: Update):
    if update.message.text == vk_name:
        if not list(vk_groups.keys()):
            update.message.reply_text(
                text=f'У тебя нет рабочих групп в {vk_name}',
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        else:
            get_delete_interface(vk_groups, update)
        return "vk_delete"
    elif update.message.text == ok_name:
        if not list(vk_groups.keys()):
            update.message.reply_text(
                text=f'У тебя нет рабочих групп в {ok_name}',
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        else:
            get_delete_interface(ok_groups, update)
        return "fb_delete"
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            text='Я не понимаю, используй клавиатуру'
        )
        return ConversationHandler.entry_points


def tmpl_group_delete(groups, update):
    if update.message.text == "Готово ✅":
        update.message.reply_text(
            text='Я запомнил изменения',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    if not list(groups.keys()):
        update.message.reply_text(
            text='Группы полностью удалены',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    elif update.message.text in list(groups.keys()):
        group_name = update.message.text
        d = groups.pop(group_name)
        keyboard = make_keyboard(list(groups.keys()))
        keyboard.append([KeyboardButton(text='Готово ✅'), KeyboardButton(text='Отмена ❌')])
        reply_markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
        update.message.reply_text(
            text=f'Я забыл группу {group_name}',
            reply_markup=reply_markup,
        )
        return ConversationHandler.entry_points
    elif update.message.text == 'Отмена ❌':
        update.message.reply_text(
            text='Ок',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            text='Я не понимаю, используй клавиатуру'
        )
        return ConversationHandler.entry_points


def fb_delete_groups_handler(bot: Bot, update: Update):
    tmpl_group_delete(ok_groups, update)
    return ConversationHandler.END


def vk_delete_groups_handler(bot: Bot, update: Update):
    tmpl_group_delete(vk_groups, update)
    return ConversationHandler.END


def main():
    bot = Bot(
        token=os.getenv('TELEGRAM_TOKEN')
    )
    updater = Updater(
        bot=bot
    )
    print(updater.bot.get_me())
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('add', add_start_handler),
            CommandHandler('delete', delete_start_handler),
            CommandHandler('post', start_post_handler, pass_user_data=True),
        ],
        states={
            "choose_site": [
                MessageHandler(Filters.text, add_choose_site_handler, pass_user_data=True),
            ],
            "get_group": [
                MessageHandler(Filters.text, add_get_group_handler, pass_user_data=True),
            ],
            "final_post_to_vk": [
                MessageHandler(Filters.photo | Filters.text, final_post_vk_handler, pass_user_data=True)
            ],
            "post_to_vk": [
                MessageHandler(Filters.text, post_make_post_vk_handler, pass_user_data=True)
            ],
            "attachments": [
                MessageHandler(Filters.text, attachments_handler, pass_user_data=True)
            ],
            "post_to_ok": [
                MessageHandler(Filters.text, post_make_post_ok_handler, pass_user_data=True)
            ],
            "final_post_to_ok": [
                MessageHandler(Filters.photo | Filters.text, final_post_to_ok_handler, pass_user_data=True)
            ],
            "delete_group": [
                MessageHandler(Filters.text, delete_groups_handler)
            ],
            "fb_delete": [
                MessageHandler(Filters.text, fb_delete_groups_handler)
            ],
            "vk_delete": [
                MessageHandler(Filters.text, vk_delete_groups_handler)
            ],
        },
        fallbacks=[
        ],
    )
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CommandHandler('start', start_conv_handler))
    updater.dispatcher.add_handler(CommandHandler('help', help_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
