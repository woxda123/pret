ROLES = {
    "civilian":     {"name": "👤 Мирный житель", "team": "city",   "emoji": "👤"},
    "detective":    {"name": "🔍 Детектив",      "team": "city",   "emoji": "🔍"},
    "sergeant":     {"name": "👮 Сержант",       "team": "city",   "emoji": "👮"},
    "doctor":       {"name": "💊 Доктор",        "team": "city",   "emoji": "💊"},
    "lucky":        {"name": "🍀 Везунчик",      "team": "city",   "emoji": "🍀"},
    "kamikaze":     {"name": "💣 Камикадзе",     "team": "city",   "emoji": "💣"},
    "mafia":        {"name": "😎 Мафия",         "team": "mafia",  "emoji": "😎"},
    "don":          {"name": "🤵 Дон",           "team": "mafia",  "emoji": "🤵"},
    "maniac":       {"name": "🔪 Маньяк",        "team": "neutral","emoji": "🔪"},
    "suicide":      {"name": "💀 Самоубийца",    "team": "neutral","emoji": "💀"},
    "lover":        {"name": "💋 Любовница",     "team": "city",   "emoji": "💋"},
    "lawyer":       {"name": "💼 Адвокат",       "team": "mafia",  "emoji": "💼"},
    "homeless":     {"name": "🚶 Бомж",          "team": "city",   "emoji": "🚶"},
}

def get_role_distribution(n):
    if n < 4:
        return None
    if n == 4:
        return ["mafia", "detective", "doctor", "civilian"]
    if n == 5:
        return ["mafia", "detective", "doctor", "civilian", "civilian"]
    if n == 6:
        return ["mafia", "detective", "doctor", "lover", "civilian", "civilian"]
    if n == 7:
        return ["don", "mafia", "detective", "doctor", "lover", "civilian", "civilian"]
    if n == 8:
        return ["don", "mafia", "detective", "sergeant", "doctor", "lover", "civilian", "civilian"]
    if n == 9:
        return ["don", "mafia", "mafia", "detective", "sergeant", "doctor", "lover", "civilian", "civilian"]
    if n == 10:
        return ["don", "mafia", "mafia", "maniac", "detective", "sergeant", "doctor", "lover", "civilian", "civilian"]
    if n == 11:
        return ["don", "mafia", "mafia", "maniac", "detective", "sergeant", "doctor", "lover", "lawyer", "civilian", "civilian"]
    if n == 12:
        return ["don", "mafia", "mafia", "maniac", "detective", "sergeant", "doctor", "lover", "lawyer", "homeless", "civilian", "civilian"]
    if n == 13:
        return ["don", "mafia", "mafia", "maniac", "detective", "sergeant", "doctor", "lover", "lawyer", "homeless", "kamikaze", "civilian", "civilian"]
    if n == 14:
        return ["don", "mafia", "mafia", "mafia", "maniac", "detective", "sergeant", "doctor", "lover", "lawyer", "homeless", "kamikaze", "civilian", "civilian"]
    if n >= 15:
        roles = ["don", "mafia", "mafia", "mafia", "maniac", "suicide",
                 "detective", "sergeant", "doctor", "lover", "lawyer",
                 "homeless", "kamikaze", "lucky"]
        while len(roles) < n:
            roles.append("civilian")
        return roles[:n]
    return None
