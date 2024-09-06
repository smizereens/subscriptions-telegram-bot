# main.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, \
    filters, CallbackQueryHandler
from subscription_manager import SubscriptionManager
from notification_manager import NotificationManager
from data_storage import DataStorage

data_storage = DataStorage()

subscription_manager = SubscriptionManager(data_storage)
notification_manager = NotificationManager(subscription_manager)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Добро пожаловать в бота для управления подписками! Введите /help, чтобы увидеть доступные команды.")

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
    Available commands:
    /add_subscription - Добавить новую подписку
    /view_subscriptions - Посмотреть ваши подписки
    /remove_subscription - Удалить подписку
    /edit_subscription - Изменить подписку
    /help - Показать это сообщение
    """
    await update.message.reply_text(help_text)

def main() -> None:
    application = ApplicationBuilder().token("7316469051:AAHtKtJJiSRGEBzZkltr1NSaQv_UUHK66H0").build()

    notification_manager.schedule_payment_notifications(application.job_queue)

    add_subscription_handler = ConversationHandler(
        entry_points=[CommandHandler('add_subscription', subscription_manager.start_add_subscription)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_manager.save_subscription_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_manager.save_subscription_cost)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_manager.save_subscription_date)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_manager.save_subscription_period)],
        },
        fallbacks=[]
    )

    remove_subscription_handler = ConversationHandler(
        entry_points=[CommandHandler('remove_subscription', subscription_manager.start_remove_subscription)],
        states={
            1: [    CallbackQueryHandler(subscription_manager.confirm_remove_subscription)],
        },
        fallbacks=[],
    )

    edit_subscription_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_subscription', subscription_manager.start_edit_subscription)],
        states={
            1: [CallbackQueryHandler(subscription_manager.choose_edit_field)],
            2: [CallbackQueryHandler(subscription_manager.save_edit_field)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, subscription_manager.apply_edit)],
        },
        fallbacks=[]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(add_subscription_handler)
    application.add_handler(remove_subscription_handler)
    application.add_handler(edit_subscription_handler)
    application.add_handler(CommandHandler("view_subscriptions", subscription_manager.view_subscriptions))

    application.run_polling()

if __name__ == "__main__":
    main()
