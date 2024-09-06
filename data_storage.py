# data_storage.py
import json

class DataStorage:
    def __init__(self, file_path='subscriptions.json'):
        self.file_path = file_path

    def load(self):
        """Загружает данные из JSON-файла"""
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save(self, data):
        """Сохраняет данные в JSON-файл"""
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)
