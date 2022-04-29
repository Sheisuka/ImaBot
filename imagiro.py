# Импорты
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
import PP
import utility as ut
import json
from typing import Union
import data.db.db as database
import codecs

# Токен бота. Удалять перед комитами
TOKEN = ''

# Индикатор использования русского языка. При значении False все сообщения отправляются на английском
LANG = 'RU'

ASK, WAIT, PROCESS, INFO_FOR_CHANGE, INFO_ALPHA, INFO_RESIZE, ASK_FOR_END, INFO_ROTATE = range(8)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):

        # Клавиатуры
        self.user_info = Union[None, dict]
        self.process_commands = [['/change_color', '/rotate'],
                                 ['/gray_scale'], #convert Добавить
                                 ['/set_alpha', '/resize'],
                                 ['/black_and_white'],
                                 ['/cancel']]
        self.continue_end_commands = [['/yes', '/end']]
        self.con_end_menu = ReplyKeyboardMarkup(self.continue_end_commands, one_time_keyboard=True)
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)
        file = codecs.open('data/json/translations.json', 'r', 'utf_8_sig')
        self.replies = json.load(file)
        file.close()
        database.run_db()

    # Отправляет короткое привествие пользователю
    def start(self, update: Update, context: CallbackContext) -> int:
        self.user, chat_id = update.message.from_user.username, update.message.chat_id
        self.user_info[self.user] = dict()
        self.user_info[self.user]['chat_id'] = chat_id
        logger.info("User %s sent has started a conversation.", self.user)
        if update.message.from_user['language_code'] != 'ru':
            LANG = 'EN'
        self.yesno_keyboard = [['Да', 'Нет']]
        update.message.reply_text(self.replies['greeting'][LANG],
                                  reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        return ASK

    def rotate(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['rotate'][LANG])
        return INFO_ROTATE

    def try_fix_error(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['error_again'][LANG])
        return WAIT

    def gray_scale(self, update: Update, context: CallbackContext):
        update.message.reply_text(self.replies['processing'][LANG])
        result = PP.gray_scale(self.user)
        if result is None:
            logger.info('User %s did grayscale. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['gray_scale_success'][LANG])
            self.ask_end(update, context)
        else:
            logger.info('User %s did grayscale. Fault', self.user, result.__class__.__name__)

    def black_and_white(self, update: Update, context: CallbackContext):
        update.message.reply_text(self.replies['processing'][LANG])
        result = PP.black_and_white(self.user)
        if result is None:
            logger.info('User %s did grayscale. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['gray_scale_success'][LANG])
            self.ask_end(update, context)
        else:
            logger.info('User %s did grayscale. Fault', self.user, result.__class__.__name__)

    def resize(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['resize_info'][LANG])
        return INFO_RESIZE

    def ask_end(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['ask_end'][LANG], reply_markup=self.con_end_menu)
        return ASK_FOR_END

    def get_photo(self, update: Update, context: CallbackContext) -> int:
        """Получение фотографии от пользователя"""
        try:
            photo_file = update.message.photo[-1].get_file()
            photo_file.download(f'data/photos/get/{self.user}.jpg')
            update.message.reply_text(self.replies['processing'][LANG])
            self.user_info[self.user]['last_photo'] = PP.count_unique(f'data/photos/get/{self.user}.jpg',
                                                                      self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption=self.replies['got_photo'][LANG], reply_markup=self.process_menu)
            logger.info("User %s sent a photo. Success", self.user)
            return PROCESS
        except IOError as error:
            logger.info("User %s sent a photo. Fault, Error - %s", self.user, error.__class__.__name__)
            update.message.reply_text(self.replies['error_again'][LANG])
            return WAIT

    def change_color(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['change_color'][LANG])
        return INFO_FOR_CHANGE

    def set_alpha(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(self.replies['set_alpha'][LANG])
        return INFO_ALPHA

    def continue_processing(self, update: Update, context: CallbackContext) -> int:
        """ Меняет местами фото полученное и фото для отправки, возвращает состояние обработки фото"""
        logger.info('User %s continued processing', self.user)
        update.message.reply_text(self.replies['wait_second'][LANG])
        self.user_info[self.user]['last_photo'] = PP.change_filepaths(self.user)
        update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                      photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                      reply_markup=self.process_menu,
                                      caption=self.replies['last_info'][LANG])
        return PROCESS

    def check_rotate(self, update: Update, context: CallbackContext):
        degrees = int(update.message.text)
        result = PP.rotate_image(self.user, degrees)
        if result is None:
            pass

    def check_resize(self, update: Update, context: CallbackContext):
        percents = int(update.message.text)
        result = PP.resize(self.user, percents)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=self.replies['resize_success'][LANG])
            self.ask_end(update, context)
        elif result.__class__ == Exception:
            error = result.__class__.__name__
            logger.info("User %s tried to resize a photo. Fault. %s", self.user, error)
            self.try_fix_error(update, context)
        elif result.__class__ == str:
            update.message.reply_text(result)
            update.message.reply_text(self.replies['resize_troll'][LANG])
            return INFO_RESIZE

    def check_info(self, update: Update, context: CallbackContext):
        color, r, g, b = list(map(int, update.message.text.split()))
        rgb = [r, g, b]
        color = 48 if color > 48 else color
        for pix_i in range(len(rgb)):
            if rgb[pix_i] < 0:
                rgb[pix_i] = 0
            elif rgb[pix_i] > 255:
                rgb[pix_i] = 255
        update.message.reply_text(self.replies['processing'][LANG])
        result = PP.change_color(self.user_info[self.user]['last_photo'][color - 1][1], tuple(rgb), self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=self.replies['change_color_success'][LANG])
            logger.info("User %s changed a color. Success", self.user)
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to change a color. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def check_alpha(self, update: Update, context: CallbackContext):
        color = int(update.message.text.strip())
        color = 1 if color not in range(1, 49) else color
        update.message.reply_text(self.replies['processing'])
        result = PP.alpha_image(self.user_info[self.user]['last_photo'][color - 1][1], self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                          caption=self.replies['set_alpha_success']['jpg'][LANG])
            update.message.bot.send_document(chat_id=self.user_info[self.user]["chat_id"],
                                             document=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                             caption=self.replies['set_alpha_success']['png'][LANG])
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
        update.message.reply_text(self.replies['cancel'][LANG])
        logger.info("User %s left us.", self.user)
        ut.clear_directions(self.user)
        return ConversationHandler.END

    def remove_job_if_exists(self, name: str, context: CallbackContext) -> bool:
        """Remove job with given name. Returns whether job was removed."""
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    def main(self) -> None:
        """Запуск бота"""

        # Создание базы данных
        db_session.global_init('data/db/imagiro.sqlite')

        updater = Updater(TOKEN)

        dispatcher = updater.dispatcher
        ask_end_commands = [CommandHandler('yes', self.continue_processing), CommandHandler('end', self.cancel)]

        conv_handler = ConversationHandler(entry_points=[CommandHandler('start', self.start)],
                                           states={
                                               ASK: [MessageHandler(Filters.regex('Да|да|Yes|yes'), self.ask),
                                                     MessageHandler(Filters.regex('Нет|нет|no|No'), self.cancel)],
                                               WAIT: [MessageHandler(Filters.photo, self.get_photo)],
                                               PROCESS: [CommandHandler('change_color', self.change_color),
                                                         CommandHandler('set_alpha', self.set_alpha),
                                                         CommandHandler('resize', self.resize),
                                                         CommandHandler('gray_scale', self.gray_scale),
                                                         CommandHandler('black_and_white', self.black_and_white),
                                                         CommandHandler('rotate', self.rotate)],
                                               INFO_FOR_CHANGE: [MessageHandler
                                                                 (Filters.regex('^\d{1,2}\s\d{1,3}\s\d{1,3}\s\d{1,3}$'),
                                                                  self.check_info), *ask_end_commands],
                                               # Регулярная строка выше переводится как число из 1 или 2 цифр и
                                               # 3 чисел из 1, 2 или 3 цифр
                                               INFO_ALPHA: [MessageHandler(Filters.regex('^\d{1,2}$'),
                                                                           self.check_alpha), *ask_end_commands],
                                               # Регулярная строка переводится как число из 1 или 2 цифр
                                               # ASK_FOR_END: [CommandHandler('yes', self.continue_processing),
                                               #               CommandHandler('end', self.cancel)]
                                               INFO_RESIZE: [MessageHandler(Filters.regex('^[-+]?\d{1,3}$'),
                                                                            self.check_resize), *ask_end_commands],
                                               INFO_ROTATE: [MessageHandler(Filters.regex('^\d{1,3}$'),
                                                                            self.check_resize), *ask_end_commands]
                                           },
                                           fallbacks=[CommandHandler('cancel', self.cancel)])
        # Добавление хэндлера с состояниями

        dispatcher.add_handler(conv_handler)

        updater.start_polling()

        updater.idle()


if __name__ == '__main__':
    bot = Bot()
    bot.main()
