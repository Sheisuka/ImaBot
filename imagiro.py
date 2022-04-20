# Импорты
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
import PP

# Токен бота. Удалять перед комитами
TOKEN = ''

# Индикатор использования русского языка. При значении False все сообщения отправляются на английском
RU = True

ASK, WAIT, PROCESS, INFO_FOR_CHANGE, INFO_ALPHA, ASK_FOR_END = range(6)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):
        self.user_info = dict()
        self.process_commands = [['/crop_photo', '/change_color'],
                                 ['/gray_scale', '/convert'],
                                 ['/set_alpha', '/resize'],
                                 ['/cancel']]
        self.continue_end_commands = [['/yes', '/end']]
        self.con_end_menu = ReplyKeyboardMarkup(self.continue_end_commands, one_time_keyboard=True)
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)

    # Отправляет короткое привествие пользователю
    def start(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user.username
        logger.info("User %s sent has started a conversation.", user)
        global RU
        if update.message.from_user['language_code'] != 'ru':
            RU = True
        if RU:
            self.yesno_keyboard = [['Да', 'Нет']]
            update.message.reply_text(f"Привет {user}! "
                                      f"Я Имаджеро. Что привело тебя ко мне? Могу ли я помочь тебе обработать парочку"
                                      f" фото \n"
                                      f"P.S. "
                                      f"Сейчас я скорее всего сплю, а если нет, то предупреждаю - сейчас я знаю только "
                                      f"две команды /change_color и /set_alpha",
                                      reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        else:
            self.yesno_keyboard = [['Yes', 'No']]
            update.message.reply_text(f"Hi {user}! I'm Imagero. Will I help you"
                                      f" with processing some photos?",
                                      reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        return ASK

    def ask_end(self, update: Update, context: CallbackContext):
        update.message.reply_text('Хочешь продолжить обработку этого фото?', reply_markup=self.con_end_menu)
        return ASK_FOR_END

    def get_photo(self, update: Update, context: CallbackContext) -> int:
        """Получение фотографии от пользователя"""
        try:
            self.user_info['user'], self.user_info['chat_id'] = \
                update.message.from_user.username, update.message.chat_id
            photo_file = update.message.photo[-1].get_file()
            photo_file.download(f'data/photos/get/{self.user_info["user"]}_photo.jpg')
            update.message.reply_text('Обрабатываю....')
            self.user_info['last_photo'] = PP.count_unique(f'data/photos/get/{self.user_info["user"]}_photo.jpg',
                                                           self.user_info["user"])
            update.message.bot.send_photo(chat_id=self.user_info["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user_info["user"]}.jpg', 'rb'),
                                          caption='Я получил твоё фото. Вот информация о нём. '
                                          'Выбери, что мне с ним сделать', reply_markup=self.process_menu)
            logger.info("User %s sent a photo. Success", self.user_info['user'])
            return PROCESS
        except IOError as error:
            logger.info("User %s sent a photo. Fault, Error - %s", self.user_info['user'], error.__class__.__name__)
            update.message.reply_text('Что-то пошло не так. Попробуй ещё раз')

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
        logger.info('User %s continued processing', self.user_info['user'])
        update.message.reply_text('Подожди секунду....')
        self.user_info['last_photo'] = PP.change_filepaths(self.user_info['user'])
        update.message.bot.send_photo(chat_id=self.user_info["chat_id"],
                                      photo=open(f'data/photos/to_send/{self.user_info["user"]}.jpg', 'rb'),
                                      reply_markup=self.process_menu,
                                      caption='Последняя версия твоего фото и информация и о нём. '
                                              'Что мне сделать теперь?')
        return PROCESS

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
        result = PP.change_color(self.user_info['last_photo'][color - 1][1], tuple(rgb), self.user_info['user'])
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user_info["user"]}.jpg', 'rb'),
                                          caption=f'Цвет под номером {color} успешно заменен')
            logger.info("User %s changed a color. Success", self.user_info['user'])
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to change a color. Fault. %s", self.user_info['user'], error)

    def check_alpha(self, update: Update, context: CallbackContext):
        color = int(update.message.text.strip())
        color = 1 if color not in range(1, 49) else color
        update.message.reply_text('Обрабатываю....')
        result = PP.alpha_image(self.user_info['last_photo'][color - 1][1], self.user_info['user'])
        if result is None:
            update.message.bot.send_photo(chat_id=self.user_info["chat_id"],
                                          photo=open(f'data/photos/to_send/{self.user_info["user"]}.png', 'rb',),
                                          caption=f'Цвет под номером {color} успешно удален. Прилагаю в jpg формате')
            update.message.bot.send_document(chat_id=self.user_info["chat_id"],
                                             document=open(f'data/photos/to_send/{self.user_info["user"]}.png', 'rb',),
                                             caption='Ваш файл в формате png.')
            logger.info("User %s deleted a color. Success", self.user_info['user'])
            self.ask_end(update, context)
        else:
            error = result.__class__.__name__
            logger.info("User %s tried to delete a color. Fault. %s", self.user_info['user'], error)

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
        logger.info("User %s left us.", self.user_info['user'])
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

        conv_handler = ConversationHandler(entry_points=[CommandHandler('start', self.start)],
                                           states={
                                               ASK: [MessageHandler(Filters.regex('Да|да|Yes|yes'), self.ask),
                                                     MessageHandler(Filters.regex('Нет|нет|no|No'), self.cancel)],
                                               WAIT: [MessageHandler(Filters.photo, self.get_photo)],
                                               PROCESS: [CommandHandler('change_color', self.change_color),
                                                         CommandHandler('set_alpha', self.set_alpha)],
                                               INFO_FOR_CHANGE: [MessageHandler
                                                                 (Filters.regex('^\d{1,2}\s\d{1,3}\s\d{1,3}\s\d{1,3}$'),
                                                                  self.check_info),
                                                                 CommandHandler('yes', self.continue_processing),
                                                                 CommandHandler('end', self.cancel)],
                                               # Регулярная строка выше переводится как число из 1 или 2 цифр и
                                               # 3 чисел из 1, 2 или 3 цифр
                                               INFO_ALPHA: [MessageHandler(Filters.regex('^\d{1,2}$'),
                                                                           self.check_alpha),
                                                            CommandHandler('yes', self.continue_processing),
                                                            CommandHandler('end', self.cancel)],
                                               # Регулярная строка переводится как число из 1 или 2 цифр
                                               # ASK_FOR_END: [CommandHandler('yes', self.continue_processing),
                                               #               CommandHandler('end', self.cancel)]
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
