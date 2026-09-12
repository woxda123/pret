from aiogram.types import CallbackQuery
from database import get_player, get_inventory
from keyboards import shop_kb
from i18n import t
from items import ITEMS
from economy import try_buy_item

async def show_shop(call: CallbackQuery):
    lang = get_player(call.from_user.id)[3]
    await call.message.edit_text(t(lang, "shop"), reply_markup=shop_kb(lang), parse_mode="HTML")

async def handle_buy(call: CallbackQuery):
    uid = call.from_user.id
    lang = get_player(uid)[3]
    item_key = call.data.split("_", 1)[1]
    ok, reason = try_buy_item(uid, item_key)
    if not ok:
        await call.answer(t(lang, "no_money"), show_alert=True)
        return
    name = ITEMS[item_key]["name"][lang]
    await call.answer(t(lang, "bought", item=name), show_alert=True)

async def show_inventory(call: CallbackQuery):
    uid = call.from_user.id
    lang = get_player(uid)[3]
    items = get_inventory(uid)
    if not items:
        await call.message.edit_text(t(lang, "inventory_empty"), reply_markup=shop_kb(lang))
        return
    lines = [f"• {ITEMS[i]['name'][lang]}" for i in items if i in ITEMS]
    await call.message.edit_text(t(lang, "inventory", items="\n".join(lines)), reply_markup=shop_kb(lang), parse_mode="HTML")
