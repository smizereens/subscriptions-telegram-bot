import datetime
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data_storage import DataStorage

class SubscriptionManager:
    def __init__(self, data_storage: DataStorage):
        self.data_storage = data_storage
        self.subscriptions = self.data_storage.load()

    def get_user_subscriptions(self, user_id):
        """Возвращает подписки для конкретного пользователя"""
        self.subscriptions = self.data_storage.load()
        return self.subscriptions.get(str(user_id), [])

    def update_user_subscriptions(self, user_id, new_subscriptions):
        """Обновляет подписки пользователя и сохраняет их"""
        self.subscriptions[str(user_id)] = new_subscriptions
        self.data_storage.save(self.subscriptions)

    async def start_add_subscription(self, update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("Введите название подписки:")
        return 1

    async def save_subscription_name(self, update: Update, context: CallbackContext) -> int:
        context.user_data['subscription_name'] = update.message.text
        await update.message.reply_text("Введите стоимость подписки:")
        return 2

    async def save_subscription_cost(self, update: Update, context: CallbackContext) -> int:
        context.user_data['subscription_cost'] = update.message.text
        await update.message.reply_text("Введите дату следующего платежа (в формате ДД-ММ-ГГГГ):")
        return 3

    async def save_subscription_date(self, update: Update, context: CallbackContext) -> int:
        datetime.datetime.strptime(update.message.text, '%d-%m-%Y')
        context.user_data['subscription_date'] = update.message.text
        await update.message.reply_text("Введите время оформления подписки (например, 14:30):")
        return 4

    async def save_subscription_period(self, update: Update, context: CallbackContext) -> int:
        context.user_data['subscription_period'] = update.message.text

        # Сохраняем подписку
        user_id = update.message.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)

        user_subscriptions.append({
            'name': context.user_data['subscription_name'],
            'cost': context.user_data['subscription_cost'],
            'date': context.user_data['subscription_date'],
            'time': context.user_data['subscription_period']
        })

        self.update_user_subscriptions(user_id, user_subscriptions)

        await update.message.reply_text(f"Подписка '{context.user_data['subscription_name']}' успешно добавлена!")
        return ConversationHandler.END

    async def view_subscriptions(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)

        if not user_subscriptions:
            await update.message.reply_text("У вас нет активных подписок.")
        else:
            message = "Ваши подписки:\n"
            for i, sub in enumerate(user_subscriptions, start=1):
                message += f"\n{i}. Название: {sub['name']}\nСтоимость: {sub['cost']}\nДата следующего платежа: {sub['date']}\nВремя платежа: {sub['time']}\n"
            await update.message.reply_text(message)

    async def start_remove_subscription(self, update: Update, context: CallbackContext) -> int:
        user_id = update.message.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)

        if not user_subscriptions:
            await update.message.reply_text("У вас нет активных подписок.")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(sub['name'], callback_data=str(i))]
            for i, sub in enumerate(user_subscriptions)
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите подписку для удаления:", reply_markup=reply_markup)
        return 1

    async def confirm_remove_subscription(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)
        sub_index = int(query.data)

        subscription_name = user_subscriptions[sub_index]['name']
        del user_subscriptions[sub_index]

        self.update_user_subscriptions(user_id, user_subscriptions)

        await query.edit_message_text(text=f"Подписка '{subscription_name}' успешно удалена.")
        return ConversationHandler.END

    async def start_edit_subscription(self, update: Update, context: CallbackContext) -> int:
        user_id = update.message.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)

        if not user_subscriptions:
            await update.message.reply_text("У вас нет активных подписок.")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(sub['name'], callback_data=str(i))]
            for i, sub in enumerate(user_subscriptions)
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите подписку для редактирования:", reply_markup=reply_markup)
        return 1

    async def choose_edit_field(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        sub_index = int(query.data)
        context.user_data['edit_index'] = sub_index

        keyboard = [
            [InlineKeyboardButton("Название", callback_data='name')],
            [InlineKeyboardButton("Стоимость", callback_data='cost')],
            [InlineKeyboardButton("Дата", callback_data='date')],
            [InlineKeyboardButton("Время платежа", callback_data='time')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Что вы хотите изменить?", reply_markup=reply_markup)
        return 2

    async def save_edit_field(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()

        field = query.data
        context.user_data['edit_field'] = field

        await query.edit_message_text(text=f"Введите новое значение для поля '{field}':")
        return 3

    async def apply_edit(self, update: Update, context: CallbackContext) -> int:
        user_id = update.message.from_user.id
        user_subscriptions = self.get_user_subscriptions(user_id)
        sub_index = context.user_data['edit_index']
        field = context.user_data['edit_field']
        new_value = update.message.text

        user_subscriptions[sub_index][field] = new_value

        self.update_user_subscriptions(user_id, user_subscriptions)

        await update.message.reply_text(f"Подписка '{user_subscriptions[sub_index]['name']}' успешно обновлена!")
        return ConversationHandler.END