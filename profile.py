from aiogram.types import CallbackQuery, Message
from database import get_player, top_players, claim_daily
from keyboards import profile_kb
from i18n import t

async def show_profile(target, user_id):
    p = get_player(user_id)
    if not p:
        return
    _, username, first_name, lang, cash, crystals, wins, games, streak, _ = p
    wr = int((wins / games * 100) if games else 0)
    name = first_name or "Player"
    text = t(lang, "profile", name=name, cash=cash, crystals=crystals,
             wins=wins, games=games, wr=wr, streak=streak)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=profile_kb(lang), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=profile_kb(lang), parse_mode="HTML")

async def handle_daily(call: CallbackQuery):
    uid = call.from_user.id
    lang = get_player(uid)[3]
    ok = claim_daily(uid)
    if ok:
        await call.message.answer(t(lang, "daily_ok", cash=500, crystals=1), parse_mode="HTML")
    else:
        await call.answer(t(lang, "daily_used"), show_alert=True)

async def show_top(call: CallbackQuery):
    uid = call.from_user.id
    lang = get_player(uid)[3]
    rows = top_players()
    lines = []
    for i, (name, uname, wins, games) in enumerate(rows, 1):
        medal = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"{i}."
        lines.append(f"{medal} <b>{name or uname or 'Игрок'}</b> — {wins} 🏆 / {games} 🎮")
    await call.message.edit_text(t(lang, "top", list="\n".join(lines) or "—"), parse_mode="HTML")
