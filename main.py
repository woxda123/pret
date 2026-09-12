import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, MIN_PLAYERS
from storage import get_game, create_game, end_game, games
from keyboards import lobby_kb, lang_kb, shop_kb
from game import start_game
from database import init_db, ensure_player, get_player, set_lang
from i18n import t
from profile import show_profile, handle_daily, show_top
from shop import show_shop, handle_buy, show_inventory

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def lang_of(uid):
    p = get_player(uid)
    return p[3] if p else "ru"

def _chat_id_of(user_id):
    for chat_id, game in games.items():
        if user_id in game["players"]:
            return chat_id
    return None

@dp.message(Command("start"))
async def cmd_start(message: Message):
    ensure_player(message.from_user.id, message.from_user.username, message.from_user.first_name)
    lang = lang_of(message.from_user.id)
    await message.answer(t(lang, "welcome"))

@dp.message(Command("lang"))
async def cmd_lang(message: Message):
    await message.answer("🌐 Выбери язык / Tilni tanlang:", reply_markup=lang_kb())

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_cb(call: CallbackQuery):
    lang = call.data.split("_")[1]
    set_lang(call.from_user.id, lang)
    await call.message.edit_text(t(lang, "welcome"))
    await call.answer("OK")

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    ensure_player(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await show_profile(message, message.from_user.id)

@dp.message(Command("shop"))
async def cmd_shop(message: Message):
    lang = lang_of(message.from_user.id)
    await message.answer(t(lang, "shop"), reply_markup=shop_kb(lang))

@dp.message(Command("game"))
async def cmd_game(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(t(lang_of(message.from_user.id), "only_group"))
        return
    chat_id = message.chat.id
    if get_game(chat_id):
        await message.answer(t(lang_of(message.from_user.id), "game_exists"))
        return
    create_game(chat_id)
    await message.answer(t("ru", "lobby", n=0), reply_markup=lobby_kb("ru"))

@dp.callback_query(F.data == "mj")
async def join(call: CallbackQuery):
    game = get_game(call.message.chat.id)
    if not game or game["phase"] != "lobby":
        await call.answer("—", show_alert=True)
        return
    uid = call.from_user.id
    if uid in game["players"]:
        await call.answer(t(lang_of(uid), "already_joined"), show_alert=True)
        return
    ensure_player(uid, call.from_user.username, call.from_user.full_name)
    game["players"][uid] = {
        "name": call.from_user.full_name,
        "username": call.from_user.username or "",
        "role": None,
        "alive": True,
        "healed_self": False,
    }
    await call.message.edit_text(t("ru", "lobby", n=len(game["players"])), reply_markup=lobby_kb("ru"))
    await call.answer(t(lang_of(uid), "joined"))

@dp.callback_query(F.data == "ms")
async def start(call: CallbackQuery):
    game = get_game(call.message.chat.id)
    if not game or game["phase"] != "lobby":
        await call.answer("—", show_alert=True)
        return
    if len(game["players"]) < MIN_PLAYERS:
        await call.answer(t("ru", "not_enough", n=MIN_PLAYERS), show_alert=True)
        return
    await call.message.edit_text(t("ru", "game_started"))
    await call.answer()
    await start_game(bot, call.message.chat.id)

@dp.callback_query(F.data == "mc")
async def cancel(call: CallbackQuery):
    end_game(call.message.chat.id)
    await call.message.edit_text(t("ru", "cancelled"))
    await call.answer()

@dp.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery):
    await show_profile(call, call.from_user.id)

@dp.callback_query(F.data == "daily")
async def cb_daily(call: CallbackQuery):
    await handle_daily(call)

@dp.callback_query(F.data == "top")
async def cb_top(call: CallbackQuery):
    await show_top(call)

@dp.callback_query(F.data == "lang")
async def cb_lang(call: CallbackQuery):
    await call.message.edit_text("🌐 Выбери язык / Tilni tanlang:", reply_markup=lang_kb())

@dp.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    await show_shop(call)

@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(call: CallbackQuery):
    await handle_buy(call)

@dp.callback_query(F.data == "inv")
async def cb_inv(call: CallbackQuery):
    await show_inventory(call)

@dp.callback_query(F.data.startswith("mk_"))
async def mafia_kill(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        game["night_actions"]["mafia_target"] = int(tgt)
    await call.message.edit_text("🔫 Выбор принят.")
    await call.answer()

@dp.callback_query(F.data.startswith("dc_"))
async def detective(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        uid = int(tgt)
        p = game["players"][uid]
        if game["night_actions"].get("lawyer_target") == uid:
            is_mafia = False
        else:
            is_mafia = p["role"] in ("mafia", "don", "lawyer")
        if "mask" in get_inventory(uid):
            is_mafia = False
        result = "🔫 МАФИЯ" if is_mafia else "👤 Мирный"
        await call.message.edit_text(f"🔍 <b>Проверка:</b> {p['name']} — {result}")
    await call.answer()

@dp.callback_query(F.data.startswith("dr_"))
async def doctor(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        uid = int(tgt)
        p = game["players"][uid]
        if uid == call.from_user.id and p["healed_self"]:
            await call.answer("Ты уже спасал себя.", show_alert=True)
            return
        game["night_actions"]["doctor_target"] = uid
        if uid == call.from_user.id:
            p["healed_self"] = True
    await call.message.edit_text("💊 Выбор принят.")
    await call.answer()

@dp.callback_query(F.data.startswith("mn_"))
async def maniac(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        game["night_actions"]["maniac_target"] = int(tgt)
    await call.message.edit_text("🔪 Выбор принят.")
    await call.answer()

@dp.callback_query(F.data.startswith("lv_"))
async def lover(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        game["night_actions"]["lover_target"] = int(tgt)
    await call.message.edit_text("💋 Выбор принят.")
    await call.answer()

@dp.callback_query(F.data.startswith("lw_"))
async def lawyer(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    tgt = call.data.split("_")[1]
    if tgt != "skip":
        game["night_actions"]["lawyer_target"] = int(tgt)
    await call.message.edit_text("💼 Клиент выбран.")
    await call.answer()

@dp.callback_query(F.data.startswith("v_"))
async def vote(call: CallbackQuery):
    chat_id = _chat_id_of(call.from_user.id)
    if not chat_id: return
    game = get_game(chat_id)
    if game["phase"] != "vote":
        await call.answer("—", show_alert=True)
        return
    tgt = call.data.split("_")[1]
    game["votes"][call.from_user.id] = "skip" if tgt == "skip" else int(tgt)
    await call.message.edit_text("🗳 Голос учтён.")
    await call.answer()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
