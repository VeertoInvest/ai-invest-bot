# memory.py
from collections import defaultdict

# Память для хранения избранных тикеров пользователей
user_favorites = defaultdict(set)

def add_favorite_ticker(user_id: int, ticker: str):
    """Добавить тикер в избранное пользователя"""
    user_favorites[user_id].add(ticker.upper())

def remove_favorite_ticker(user_id: int, ticker: str):
    """Удалить тикер из избранного пользователя"""
    user_favorites[user_id].discard(ticker.upper())

def get_favorites(user_id: int):
    """Получить список избранных тикеров пользователя"""
    return list(user_favorites[user_id])
