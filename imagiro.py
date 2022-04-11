# Импорты
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters

# Токен бота. Удалять перед комитами
TOKEN = '5222745741:AAHJws-Ejl09au5E21wXhpKpMRF5ZVI32Gc'

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
        self.process_commands = [['/crop_photo', '/change_color'],
                                 ['/gray_scale', '/convert'],
                                 ['/delete_color', '/resize'],
                                 ['/back']]
        self.process_menu = ReplyKeyboardMarkup(self.process_commands, one_time_keyboard=True)

    # Отправляет короткое привествие пользователю
    def start(self, update: Update, context: CallbackContext) -> int:
        global RU
        if update.message.from_user['language_code'] != 'ru':
            RU = False
        if RU:
            update.message.reply_text(f"Привет {update.message.from_user.username}! "
                                      f"Я Имаджеро. Что привело тебя ко мне? Могу ли я помочь тебе обработать парочку"
                                      f" фото"
                                      f"", reply_markup=self.process_menu)
        else:
            update.message.reply_text(f"Hi {update.message.from_user['username']}! I'm Imagero. Will I help you"
                                      f"with processing some photos?",
                                      reply_markup=self.process_menu)
        print(update.message.text)
        return ASK

    def get_photo(self, update: Update, context: CallbackContext) -> int:
        # Получение фотографии от пользователя
        user = update.message.from_user.username
        photo_file = update.message.photo[-1].get_file()
        photo_file.download(f'photos/{user}_photo.jpg')
        print('success')
        return PROCESS

    def check_help(self, update: Update) -> int:
        print('я тут')
        return WAIT
        # return 0

    def show_menu(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_markup = self.process_menu

    def alarm(self, context: CallbackContext) -> None:
        """Send the alarm message."""
        job = context.job
        context.bot.send_message(job.context, text='Beep!')

    def cancel(self):
        pass

    def remove_job_if_exists(self, name: str, context: CallbackContext) -> bool:
        """Remove job with given name. Returns whether job was removed."""
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    def set_timer(self, update: Update, context: CallbackContext) -> None:
        """Add a job to the queue."""
        chat_id = update.message.chat_id
        try:
            # args[0] should contain the time for the timer in seconds
            due = int(context.args[0])
            if due < 0:
                update.message.reply_text('Sorry we can not go back to future!')
                return

            job_removed = self.remove_job_if_exists(str(chat_id), context)
            context.job_queue.run_once(self.alarm, due, context=chat_id, name=str(chat_id))

            text = 'Timer successfully set!'
            if job_removed:
                text += ' Old one was removed.'
            update.message.reply_text(text)

        except (IndexError, ValueError):
            update.message.reply_text('Usage: /set <seconds>')

    def unset(self, update: Update, context: CallbackContext) -> None:
        """Remove the job if the user changed their mind."""
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(str(chat_id), context)
        text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
        update.message.reply_text(text)

    def main(self) -> None:
        global WAIT, ASK, PROCESS
        # Запуск бота
        updater = Updater(TOKEN)

        dispatcher = updater.dispatcher

        # Добавление обрабатываемых команд
        dispatcher.add_handler(CommandHandler("start", self.start))
        # dispatcher.add_handler(CommandHandler("help", self.start))
        dispatcher.add_handler(CommandHandler("set", self.set_timer))
        # dispatcher.add_handler(CommandHandler("unset", self.unset))

        # Добавление хэндлера с состояниями
        conv_handler = ConversationHandler(entry_points=[CommandHandler('start', self.start)],
                                           states={
                                               WAIT: [MessageHandler(Filters.photo, self.get_photo)],
                                               ASK: [MessageHandler(Filters.regex('да'), self.check_help)],
                                               # PROCESS: [CommandHandler('crop_photo|change_color|gray_scale|'
                                               #                          'convert|delete_color|resize',
                                               #                          self.show_menu)]
                                           },
                                           fallbacks=[CommandHandler('cancel', self.cancel)])

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