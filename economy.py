from database import (
    get_player, add_cash, add_crystals, spend, add_item,
    get_inventory, consume_item, claim_daily
)
from items import ITEMS

def try_buy_item(user_id, item_key):
    if item_key not in ITEMS:
        return False, "no_item"
    item = ITEMS[item_key]
    ok = spend(user_id, cash=item["price_cash"], crystals=item["price_crystals"])
    if not ok:
        return False, "no_money"
    add_item(user_id, item_key)
    return True, "bought"

def grant_win_rewards(user_ids):
    for uid in user_ids:
        add_cash(uid, 300)
        add_crystals(uid, 2)

def grant_lose_rewards(user_ids):
    for uid in user_ids:
        add_cash(uid, 50)
