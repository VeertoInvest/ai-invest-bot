user_favorites = {}

def add_favorite(user_id, ticker):
    user_favorites.setdefault(user_id, set()).add(ticker.upper())

def remove_favorite(user_id, ticker):
    if user_id in user_favorites:
        user_favorites[user_id].discard(ticker.upper())

def get_favorites(user_id):
    return list(user_favorites.get(user_id, []))

def has_favorite(user_id, ticker):
    return ticker.upper() in user_favorites.get(user_id, set())
