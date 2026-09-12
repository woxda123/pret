from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from i18n import t
from items import ITEMS

def lobby_kb(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_join"), callback_data="mj")],
        [InlineKeyboardButton(text=t(lang, "btn_start"), callback_data="ms")],
        [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="mc")],
    ])

def target_kb(players_alive, exclude=None, prefix="t", extra_skip=False, lang="ru"):
    buttons = []
    for uid, p in players_alive.items():
        if uid == exclude:
            continue
        buttons.append([InlineKeyboardButton(text=p["name"], callback_data=f"{prefix}_{uid}")])
    if extra_skip:
        buttons.append([InlineKeyboardButton(text=t(lang, "btn_skip"), callback_data=f"{prefix}_skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def vote_kb(players_alive, voter_id, lang="ru"):
    buttons = []
    for uid, p in players_alive.items():
        if uid == voter_id:
            continue
        buttons.append([InlineKeyboardButton(text=p["name"], callback_data=f"v_{uid}")])
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_abstain"), callback_data="v_skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def mafia_kb(players_alive, mafia_ids, lang="ru"):
    buttons = []
    for uid, p in players_alive.items():
        if uid in mafia_ids:
            continue
        buttons.append([InlineKeyboardButton(text=p["name"], callback_data=f"mk_{uid}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def shop_kb(lang="ru"):
    buttons = []
    for key, item in ITEMS.items():
        name = item["name"][lang]
        price_parts = []
        if item["price_cash"]:
            price_parts.append(f"{item['price_cash']}💵")
        if item["price_crystals"]:
            price_parts.append(f"{item['price_crystals']}💎")
        price = " ".join(price_parts)
        buttons.append([InlineKeyboardButton(text=f"{name} — {price}", callback_data=f"buy_{key}")])
    buttons.append([InlineKeyboardButton(text="🎒 Инвентарь" if lang == "ru" else "🎒 Inventar", callback_data="inv")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_kb(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 " + ("Магазин" if lang == "ru" else "Do'kon"), callback_data="shop")],
        [InlineKeyboardButton(text="🎁 " + ("Ежедневный бонус" if lang == "ru" else "Kunlik bonus"), callback_data="daily")],
        [InlineKeyboardButton(text="🏆 " + ("Топ" if lang == "ru" else "Top"), callback_data="top")],
        [InlineKeyboardButton(text="🌐 " + ("Язык" if lang == "ru" else "Til"), callback_data="lang")],
    ])

def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz")],
    ])
