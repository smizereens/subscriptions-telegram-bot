import datetime

class NotificationManager:
    def __init__(self, subscription_manager):
        self.subscription_manager = subscription_manager

    async def check_payment_dates(self, context):
        """Проверяет даты оформления подписок и отправляет уведомления за минуту до времени оформления"""
        now = datetime.datetime.now()
        for user_id, subscriptions in self.subscription_manager.subscriptions.items():
            for sub in subscriptions:
                try:
                    subscription_time = datetime.datetime.strptime(sub['date'], '%d-%m-%Y')
                    subscription_time = subscription_time.replace(
                        hour=int(sub['time'].split(':')[0]),
                        minute=int(sub['time'].split(':')[1])
                    )
                except ValueError:
                    continue

                delta_minutes = (subscription_time - now).total_seconds() / 60
                if 0 <= delta_minutes <= 1:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Напоминание: время оформления подписки '{sub['name']}' приближается! {sub['date']} в {sub['time']}"
                    )

    def schedule_payment_notifications(self, job_queue):
        """Запускает планировщик для проверки подписок каждую минуту"""
        job_queue.run_repeating(self.check_payment_dates, interval=60, first=0)