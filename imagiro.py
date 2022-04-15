# Импорты
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters, \
    DictPersistence
import PP

# Токен бота. Удалять перед комитами
TOKEN = ''

# Индикатор использования русского языка. При значении False все сообщения отправляются на английском
RU = True

ASK, WAIT, PROCESS = range(3)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):
        self.user_dict = DictPersistence()
        self.process_commands = [['/crop_photo', '/change_color'],
                                 ['/gray_scale', '/convert'],
                                 ['/delete_color', '/resize'],
                                 ['/back']]
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)

    # Отправляет короткое привествие пользователю
    def start(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user.username
        logger.info("User %s sent has started a conversation.", user)
        global RU
        if update.message.from_user['language_code'] != 'ru':
            RU = False
        if RU:
            self.yesno_keyboard = [['Да', 'Нет']]
            update.message.reply_text(f"Привет {user}! "
                                      f"Я Имаджеро. Что привело тебя ко мне? Могу ли я помочь тебе обработать парочку"
                                      f" фото"
                                      f"", reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        else:
            self.yesno_keyboard = [['Yes', 'No']]
            update.message.reply_text(f"Hi {user}! I'm Imagero. Will I help you"
                                      f"with processing some photos?",
                                      reply_markup=ReplyKeyboardMarkup(self.yesno_keyboard, one_time_keyboard=True))
        return ASK

    def get_photo(self, update: Update, context: CallbackContext) -> int:
        # Получение фотографии от пользователя
        try:
            user = update.message.from_user.username
            photo_file = update.message.photo[-1].get_file()
            photo_file.download(f'photos/{user}_photo.jpg')
            update.message.reply_text('Я получил твоё фото. Выбери, что мне с ним сделать',
                                      reply_markup=self.process_menu)
            return PROCESS
        except:
            update.message.reply_text('Что-то пошло не так. Попробуй ещё раз')

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
        logger.info("User %s left us.", update.message.from_user.username)
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
                                               ASK: [MessageHandler(Filters.regex('да'), self.ask),
                                                     MessageHandler(Filters.regex('нет'), self.cancel)],
                                               WAIT: [MessageHandler(Filters.photo, self.get_photo)],
                                               # PROCESS: [CommandHandler('crop_photo|change_color|gray_scale|'
                                               #                          'convert|delete_color|resize',
                                               #                          self.show_menu)]
                                               PROCESS: [CommandHandler('crop_photo', self.cancel)],
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
