import datetime
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
import PP
import utility as ut
import json
from typing import Union
import codecs
from data.data_db import db_session
from data.data_db.users import User
from googletrans import Translator

# Токен бота. Удалять перед комитами
TOKEN = '5222745741:AAHJws-Ejl09au5E21wXhpKpMRF5ZVI32Gc'


ASK, WAIT, PROCESS, INFO_FOR_CHANGE, INFO_ALPHA, INFO_RESIZE, ASK_FOR_END, INFO_ROTATE = range(8)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Bot(Translator):
    def __init__(self):
        super().__init__()
        # Клавиатуры
        self.user_info = Union[dict, None]
        self.process_commands = [['/change_color', '/rotate'],
                                 ['/set_alpha', '/resize'],
                                 ['/black_and_white', '/gray_scale'],
                                 ['/cancel', '/see_stats']]
        self.continue_end_commands = [['/yes', '/cancel']]
        self.con_end_menu = ReplyKeyboardMarkup(self.continue_end_commands, one_time_keyboard=True)
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)

        # Открытие файла с переводом реплик
        file = codecs.open('data/json/translations.json', 'r', 'utf_8_sig')
        self.replies = json.load(file)
        file.close()

        # Подключение к БД
        self.db_sess = db_session.create_session()

    def start(self, update: Update, context: CallbackContext) -> int:
        """Начало диалога, определяет язык, получает информацию и заносит в словарь и БД"""
        self.user, chat_id = update.message.from_user.username, update.message.chat_id
        self.user_info = dict()
        self.user_info[self.user] = dict()
        self.user_info[self.user]['chat_id'] = chat_id
        logger.info("User %s sent has started a conversation.", self.user)
        if update.message.from_user['language_code'] != 'ru':
            self.user_info[self.user]['lang'] = 'en'
        else:
            self.user_info[self.user]['lang'] = 'ru'
        update.message.reply_text(self.replies['greeting'][self.user_info[self.user]['lang']])
        if self.user not in [i[0] for i in self.db_sess.query(User.name).all()]:
            user = User()
            user.name = self.user
            user.created_date = datetime.date.today()
            self.db_sess.add(user)
            logger.info("User %s was added to db", self.user)
            self.db_sess.commit()
        return WAIT

    def rotate(self, update: Update, context: CallbackContext) -> int:
        """Информирует пользователя о том как работать с rotate"""
        update.message.reply_text(self.replies['rotate'][self.user_info[self.user]['lang']])
        return INFO_ROTATE

    def try_fix_error(self, update: Update, context: CallbackContext) -> int:
        """Информирует пользователя об ошибке. Просьба отправить фото ещё раз"""
        update.message.reply_text(self.replies['error_again'][self.user_info[self.user]['lang']])
        return WAIT

    def gray_scale(self, update: Update, context: CallbackContext):
        """Перевод изображения в градации серого"""
        update.message.reply_text(self.replies['processing'][self.user_info[self.user]['lang']])
        result = PP.gray_scale(self.user)
        if result is None:
            logger.info('User %s did grayscale. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['gray_scale_success'][self.user_info[self.user]['lang']])
            self.ask_end(update, context)
        else:
            logger.info('User %s did grayscale. Fault', self.user, result.__class__.__name__)
            self.try_fix_error(update, context)

    def black_and_white(self, update: Update, context: CallbackContext):
        """Перевод изображения в черно-белый режим"""
        update.message.reply_text(self.replies['processing'][self.user_info[self.user]['lang']])
        result = PP.black_and_white(self.user)
        if result is None:
            logger.info('User %s turned the photo to black and white. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['gray_scale_success'][self.user_info[self.user]['lang']])
            self.ask_end(update, context)
        else:
            logger.info('User %s turned the photo to black and white. Fault', self.user, result.__class__.__name__)
            self.try_fix_error(update, context)

    def resize(self, update: Update, context: CallbackContext) -> int:
        """Информирует пользователя о том как работать с resize"""
        update.message.reply_text(self.replies['resize_info'][self.user_info[self.user]['lang']])
        return INFO_RESIZE

    def ask_end(self, update: Update, context: CallbackContext) -> int:
        """Определяет будет ли продолжаться обработка"""
        update.message.reply_text(self.replies['ask_end'][self.user_info[self.user]['lang']],
                                  reply_markup=self.con_end_menu)
        return ASK_FOR_END

    def get_photo(self, update: Update, context: CallbackContext,) -> int:
        """Получение фотографии от пользователя"""
        user = self.db_sess.query(User).filter(User.name == self.user).first()
        user.photos_count += 1
        self.db_sess.commit()
        try:
            photo_file = update.message.photo[-1].get_file()
            photo_file.download(f'data/photos/get/{self.user}.jpg')
            update.message.reply_text(self.replies['processing'][self.user_info[self.user]['lang']])
            self.user_info[self.user]['last_photo'] = PP.count_unique(f'data/photos/get/{self.user}.jpg',
                                                                      self.user, self.translate,
                                                                      self.user_info[self.user]['lang'])
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['got_photo'][self.user_info[self.user]['lang']],
                                          reply_markup=self.process_menu)
            logger.info("User %s sent a photo. Success", self.user)
            return PROCESS
        except IOError as error:
            logger.info("User %s sent a photo. Fault, Error - %s", self.user, error.__class__.__name__)
            self.try_fix_error(update, context)

    def see_stats(self, update: Update, context: CallbackContext) -> int:
        """Отправляет статистику пользователя в виде количества отправленных фото и даты первого сообщения"""
        user = self.db_sess.query(User).filter(User.name == self.user).first()
        count, date = user.photos_count, str(user.created_date).split()[0].replace('-', ' ', 3)
        update.message.reply_text(f'Твоя статистика: \nМы познакомились с тобой {date}, за это время я получил от тебя'
                                  f' {count} фото.')
        self.show_menu(update, context)

    def change_color(self, update: Update, context: CallbackContext) -> int:
        """Информирует пользователя о том как работать с change_color"""
        update.message.reply_text(self.replies['change_color'][self.user_info[self.user]['lang']])
        return INFO_FOR_CHANGE

    def set_alpha(self, update: Update, context: CallbackContext) -> int:
        """Информирует пользователя о том как работать с set_alpha"""
        update.message.reply_text(self.replies['set_alpha'][self.user_info[self.user]['lang']])
        return INFO_ALPHA

    def continue_processing(self, update: Update, context: CallbackContext) -> int:
        """ Меняет местами фото полученное и фото для отправки, возвращает состояние обработки фото"""
        logger.info('User %s continued processing', self.user)
        update.message.reply_text(self.replies['wait_second'][self.user_info[self.user]['lang']])
        self.user_info[self.user]['last_photo'] = PP.change_filepaths(self.user)
        update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                      photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                      reply_markup=self.process_menu,
                                      caption=self.replies['last_info'][self.user_info[self.user]['lang']])
        return PROCESS

    def check_rotate(self, update: Update, context: CallbackContext):
        """Поворачивает фото на выбранное количество градусов против часовой стрелки"""
        degrees = int(update.message.text) % 360
        result = PP.rotate_image(self.user, degrees)
        if result is None:
            logger.info("User %s rotated a photo. Success", self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=self.replies['rotate_success'][self.user_info[self.user]['lang']])
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to rotate a photo. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def check_resize(self, update: Update, context: CallbackContext):
        """Изменяет размер фото на n + 100 прооцентов"""
        percents = int(update.message.text)
        result = PP.resize(self.user, percents)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=self.replies['resize_success'][self.user_info[self.user]['lang']])
            self.ask_end(update, context)
        elif result.__class__ == Exception:
            error = result.__class__.__name__
            logger.info("User %s tried to resize a photo. Fault. %s", self.user, error)
            self.try_fix_error(update, context)
        elif result.__class__ == str:
            update.message.reply_text(result)
            update.message.reply_text(self.replies['resize_troll'][self.user_info[self.user]['lang']])
            return INFO_RESIZE

    def check_info(self, update: Update, context: CallbackContext):
        """Проверяет введенные значения на корректность, изменяет цвет"""
        color, r, g, b = list(map(int, update.message.text.split()))
        rgb = [r, g, b]
        color = 48 if color > 48 else color
        for pix_i in range(len(rgb)):
            if rgb[pix_i] < 0:
                rgb[pix_i] = 0
            elif rgb[pix_i] > 255:
                rgb[pix_i] = 255
        update.message.reply_text(self.replies['processing'][self.user_info[self.user]['lang']])
        result = PP.change_color(self.user_info[self.user]['last_photo'][color - 1][1], tuple(rgb), self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=self.replies['change_color_success'][self.user_info[self.user]['lang']])
            logger.info("User %s changed a color. Success", self.user)
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to change a color. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def check_alpha(self, update: Update, context: CallbackContext):
        """Проверяет введенные значения на корректность, удаляет выбранный цвет"""
        color = int(update.message.text.strip())
        color = 1 if color not in range(1, 49) else color
        update.message.reply_text(self.replies['processing'][self.user_info[self.user]['lang']])
        result = PP.alpha_image(self.user_info[self.user]['last_photo'][color - 1][1], self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                          caption=self.replies['set_alpha_success']['jpg'][self.user_info[self.user]['lang']])
            update.message.bot.send_document(chat_id=self.user_info[self.user]["chat_id"],
                                             document=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                             caption=self.replies['set_alpha_success']['png'][self.user_info[self.user]['lang']])
            logger.info("User %s deleted a color. Success", self.user)
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to delete a color. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def ask(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Отлично! Тогда отправь мне одно фото, которое ты хочешь обработать')
        return WAIT

    def show_menu(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_markup = self.process_menu

    def cancel(self, update: Update, context: CallbackContext):
        update.message.reply_text(self.replies['cancel'][self.user_info[self.user]['lang']])
        logger.info("User %s left us.", self.user)

        # Удаление с диска фото ушедшего пользователя
        ut.clear_directions(self.user)

        return ConversationHandler.END

    def main(self) -> None:
        """Запуск бота"""

        # Создание базы данных

        updater = Updater(TOKEN)

        dispatcher = updater.dispatcher
        ask_end_commands = [CommandHandler('yes', self.continue_processing), CommandHandler('cancel', self.cancel)]

        conv_handler = ConversationHandler(entry_points=[CommandHandler('start', self.start)],
                                           states={
                                               WAIT: [MessageHandler(Filters.photo, self.get_photo)],
                                               PROCESS: [CommandHandler('change_color', self.change_color),
                                                         CommandHandler('set_alpha', self.set_alpha),
                                                         CommandHandler('resize', self.resize),
                                                         CommandHandler('gray_scale', self.gray_scale),
                                                         CommandHandler('black_and_white', self.black_and_white),
                                                         CommandHandler('rotate', self.rotate),
                                                         CommandHandler('see_stats', self.see_stats)],
                                               INFO_FOR_CHANGE: [MessageHandler
                                                                 (Filters.regex('^\d{1,2}\s\d{1,3}\s\d{1,3}\s\d{1,3}$'),
                                                                  self.check_info), *ask_end_commands],
                                               # Регулярная строка выше переводится как число из 1 или 2 цифр и
                                               # 3 чисел из 1, 2 или 3 цифр
                                               INFO_ALPHA: [MessageHandler(Filters.regex('^\d{1,2}$'),
                                                                           self.check_alpha), *ask_end_commands],
                                               # Регулярная строка переводится как число из 1 или 2 цифр
                                               INFO_RESIZE: [MessageHandler(Filters.regex('^[-+]?\d{1,3}$'),
                                                                            self.check_resize), *ask_end_commands],
                                               INFO_ROTATE: [MessageHandler(Filters.regex('^\d{1,3}$'),
                                                                            self.check_rotate), *ask_end_commands],
                                               ASK_FOR_END: [*ask_end_commands]
                                           },
                                           fallbacks=[CommandHandler('cancel', self.cancel)])

        # Добавление хэндлера с состояниями
        dispatcher.add_handler(conv_handler)

        # Начало проверки наличия новых сообщений
        updater.start_polling()

        # Останавливает работу до первого полученного сигнала
        updater.idle()


db_session.global_init("data/db/imagiro.db")
bot = Bot()
bot.main()
