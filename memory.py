# memory.py
from collections import defaultdict

# Хранилище избранных тикеров пользователей
favorites = defaultdict(set)

def add_favorite_ticker(user_id, ticker):
    favorites[user_id].add(ticker)

def remove_favorite_ticker(user_id, ticker):
    favorites[user_id].discard(ticker)

def get_favorites(user_id=None):
    if user_id:
        return list(favorites.get(user_id, []))
    return favorites
