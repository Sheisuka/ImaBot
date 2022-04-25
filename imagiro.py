# Импорты
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
import PP
import utility as ut

# Токен бота. Удалять перед комитами
TOKEN = '5222745741:AAHJws-Ejl09au5E21wXhpKpMRF5ZVI32Gc'

# Индикатор использования русского языка. При значении False все сообщения отправляются на английском
RU = True

ASK, WAIT, PROCESS, INFO_FOR_CHANGE, INFO_ALPHA, INFO_RESIZE, ASK_FOR_END, INFO_ROTATE = range(8)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):
        self.user_info = dict()

        # Клавиатуры
        self.process_commands = [['/change_color', '/rotate'],
                                 ['/gray_scale'], #convert Добавить
                                 ['/set_alpha', '/resize'],
                                 ['/black_and_white'],
                                 ['/cancel']]
        self.continue_end_commands = [['/yes', '/end']]
        self.con_end_menu = ReplyKeyboardMarkup(self.continue_end_commands, one_time_keyboard=True)
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)

    # Отправляет короткое привествие пользователю
    def start(self, update: Update, context: CallbackContext) -> int:
        self.user, chat_id = update.message.from_user.username, update.message.chat_id
        self.user_info[self.user] = dict()
        self.user_info[self.user]['chat_id'] = chat_id
        logger.info("User %s sent has started a conversation.", self.user)
        global RU
        if update.message.from_user['language_code'] != 'ru':
            RU = True
        if RU:
            self.yesno_keyboard = [['Да', 'Нет']]
            update.message.reply_text(f"Привет {self.user}! "
                                      f"Я Имаджеро. Что привело тебя ко мне? Могу ли я помочь тебе обработать парочку"
                                      f" фото?\n"
                                      f"P.S. "
                                      f"Мои алгоритмы группировки цветов всё ещё работают странно",
                                      reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        else:
            self.yesno_keyboard = [['Yes', 'No']]
            update.message.reply_text(f"Hi {self.user}! I'm Imagero. Will I help you"
                                      f" with processing some photos?",
                                      reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        return ASK

    def rotate(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text("Отправь мне одно число - поворот изображения против часовой стрелки в градусах")
        return INFO_ROTATE

    def try_fix_error(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Что-то пошло не так :( \n Отправь мн фото ещё раз')
        return WAIT

    def gray_scale(self, update: Update, context: CallbackContext):
        update.message.reply_text('Обрабатываю....')
        result = PP.gray_scale(self.user)
        if result is None:
            logger.info('User %s did grayscale. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption='Фото успешнено переведено в градации серого')
            self.ask_end(update, context)
        else:
            logger.info('User %s did grayscale. Fault', self.user, result.__class__.__name__)

    def black_and_white(self, update: Update, context: CallbackContext):
        update.message.reply_text('Обрабатываю....')
        result = PP.black_and_white(self.user)
        if result is None:
            logger.info('User %s did grayscale. Success', self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]['chat_id'],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption='Фото успешнено переведено в черно-белые цвета')
            self.ask_end(update, context)
        else:
            logger.info('User %s did grayscale. Fault', self.user, result.__class__.__name__)

    def resize(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Для того, чтобы изменить размер изображения отправь мне количество процентов (от -99'
                                  ' до 500), на которое новое изображение должно быть больше старого. ')
        return INFO_RESIZE

    def ask_end(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Хочешь продолжить обработку этого фото?', reply_markup=self.con_end_menu)
        return ASK_FOR_END

    def get_photo(self, update: Update, context: CallbackContext) -> int:
        """Получение фотографии от пользователя"""
        try:
            photo_file = update.message.photo[-1].get_file()
            photo_file.download(f'data/photos/get/{self.user}.jpg')
            update.message.reply_text('Обрабатываю....')
            self.user_info[self.user]['last_photo'] = PP.count_unique(f'data/photos/get/{self.user}.jpg',
                                                                      self.user)
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'{ut.get_path(self.user, "to_send", "jpg")}', 'rb'),
                                          caption='Я получил твоё фото. Вот информация о нём. '
                                          'Выбери, что мне с ним сделать', reply_markup=self.process_menu)
            logger.info("User %s sent a photo. Success", self.user)
            return PROCESS
        except IOError as error:
            logger.info("User %s sent a photo. Fault, Error - %s", self.user, error.__class__.__name__)
            update.message.reply_text('Что-то пошло не так. Попробуй ещё раз')
            return WAIT

    def change_color(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Для этого отправь мне четыре цифры через пробел. Номер цвета, который нужно заменить'
                                  ' из картинки выше и '
                                  'новый цвет в виде r g b .')
        return INFO_FOR_CHANGE

    def set_alpha(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Для того, чтобы сделать определенный пиксель прозрачным, отправь мне его номер'
                                  ' из картинки с информацией выше.')
        return INFO_ALPHA

    def continue_processing(self, update: Update, context: CallbackContext) -> int:
        """ Меняет местами фото полученное и фото для отправки, возвращает состояние обработки фото"""
        logger.info('User %s continued processing', self.user)
        update.message.reply_text('Подожди секунду....')
        self.user_info[self.user]['last_photo'] = PP.change_filepaths(self.user)
        update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                      photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                      reply_markup=self.process_menu,
                                      caption='Последняя версия информации о твоём фото. '
                                              'Что мне сделать теперь?')
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
                                          caption=f'Размер изображения успешно изменен')
            self.ask_end(update, context)
        elif result.__class__ == Exception:
            error = result.__class__.__name__
            logger.info("User %s tried to resize a photo. Fault. %s", self.user, error)
            self.try_fix_error(update, context)
        elif result.__class__ == str:
            update.message.reply_text(result)
            update.message.reply_text('Введи значение ещё раз. \n Только в этот раз без нулей')
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
        update.message.reply_text('Обрабатываю....')
        result = PP.change_color(self.user_info[self.user]['last_photo'][color - 1][1], tuple(rgb), self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.jpg', 'rb'),
                                          caption=f'Цвет под номером {color} успешно заменен')
            logger.info("User %s changed a color. Success", self.user)
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to change a color. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def check_alpha(self, update: Update, context: CallbackContext):
        color = int(update.message.text.strip())
        color = 1 if color not in range(1, 49) else color
        update.message.reply_text('Обрабатываю....')
        result = PP.alpha_image(self.user_info[self.user]['last_photo'][color - 1][1], self.user)
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info[self.user]["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                          caption=f'Цвет под номером {color} успешно удален. Прилагаю в jpg формате')
            update.message.bot.send_document(chat_id=self.user_info[self.user]["chat_id"],
                                             document=open(f'data/photos/to_send/{self.user}.png', 'rb',),
                                             caption='Ваш файл в формате png.')
            logger.info("User %s deleted a color. Success", self.user)
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to delete a color. Fault. %s", self.user, error)
            self.try_fix_error(update, context)

    def help_colors(self, update: Update, context: CallbackContext):
        update.message.reply_text(f'Краткая информация, необходимая для работы со мной:'
                                  f'Изображение представяляется в виде 3 цифр в формате rgb'
                                  f'Для того, чтобы сообщить мне какой цвет использовать, отправь мне 3 цифры в пределах'
                                  f'0-255. Таблицу соответствия основных цветов и rgb ты можешь увидеть ниже. Тебе '
                                  f'необязательно выбирать цвет именно из таблицы')

    def ask(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Отлично! Тогда отправь мне одно фото, которое ты хочешь обработать')
        return WAIT

    def show_menu(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_markup = self.process_menu

    def cancel(self, update: Update, context: CallbackContext):
        update.message.reply_text('Рад был помочь.')
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
        global WAIT, ASK, PROCESS
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
                                                         CommandHandler['rotate', self.rotate]
                                                         *ask_end_commands],
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
        # Начало поиска полученных сообщений
        updater.start_polling()

        # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
        # SIGABRT. This should be used most of the time, since start_polling() is
        # non-blocking and will stop the bot gracefully.
        updater.idle()


if __name__ == '__main__':
    bot = Bot()
    bot.main()
