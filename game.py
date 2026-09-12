import asyncio
import random
from aiogram import Bot
from config import NIGHT_DURATION, DAY_DISCUSSION, VOTE_DURATION
from roles import ROLES, get_role_distribution
from storage import get_game, end_game
from keyboards import target_kb, vote_kb, mafia_kb
from economy import grant_win_rewards, grant_lose_rewards
from database import inc_game, get_inventory
from i18n import t

async def start_game(bot: Bot, chat_id: int):
    game = get_game(chat_id)
    if not game:
        return

    player_ids = list(game["players"].keys())
    roles = get_role_distribution(len(player_ids))
    if not roles:
        await bot.send_message(chat_id, "❌ Недостаточно игроков.")
        return

    random.shuffle(roles)
    for uid, role in zip(player_ids, roles):
        game["players"][uid]["role"] = role
        team_key = "team_" + ROLES[role]["team"]
        try:
            await bot.send_message(
                uid,
                t("ru", "your_role",
                  role=ROLES[role]["name"],
                  team=t("ru", team_key)),
                parse_mode="HTML"
            )
        except Exception:
            await bot.send_message(
                chat_id,
                t("ru", "dm_fail", name=game["players"][uid]["name"]),
                parse_mode="HTML"
            )
            return

    game["phase"] = "night"
    game["day"] = 1
    await bot.send_message(chat_id, t("ru", "game_started"), parse_mode="HTML")
    await asyncio.sleep(3)
    await night_phase(bot, chat_id)


async def night_phase(bot: Bot, chat_id: int):
    game = get_game(chat_id)
    if not game:
        return
    game["night_actions"] = {}
    game["phase"] = "night"

    alive = {uid: p for uid, p in game["players"].items() if p["alive"]}
    mafia_ids = [uid for uid, p in alive.items() if p["role"] in ("mafia", "don")]

    if mafia_ids:
        for uid in mafia_ids:
            try:
                await bot.send_message(
                    uid,
                    f"🔫 <b>Мафия, выбирай жертву.</b>\n\nТы — {ROLES[game['players'][uid]['role']]['name']}.",
                    parse_mode="HTML",
                    reply_markup=mafia_kb(alive, mafia_ids)
                )
            except Exception:
                pass

    for uid, p in alive.items():
        if p["role"] == "detective":
            try:
                await bot.send_message(
                    uid,
                    "🔍 <b>Детектив, кого проверяем сегодня?</b>",
                    parse_mode="HTML",
                    reply_markup=target_kb(alive, exclude=uid, prefix="dc")
                )
            except Exception:
                pass

    for uid, p in alive.items():
        if p["role"] == "doctor":
            try:
                await bot.send_message(
                    uid,
                    "💊 <b>Доктор, кого лечим?</b>\n\n<i>Можешь спасти себя, но только один раз за игру.</i>",
                    parse_mode="HTML",
                    reply_markup=target_kb(alive, prefix="dr")
                )
            except Exception:
                pass

    for uid, p in alive.items():
        if p["role"] == "maniac":
            try:
                await bot.send_message(
                    uid,
                    "🔪 <b>Маньяк, выбирай жертву.</b>",
                    parse_mode="HTML",
                    reply_markup=target_kb(alive, exclude=uid, prefix="mn")
                )
            except Exception:
                pass

    for uid, p in alive.items():
        if p["role"] == "lover":
            try:
                await bot.send_message(
                    uid,
                    "💋 <b>Любовница, кого отвлечь этой ночью?</b>",
                    parse_mode="HTML",
                    reply_markup=target_kb(alive, exclude=uid, prefix="lv")
                )
            except Exception:
                pass

    for uid, p in alive.items():
        if p["role"] == "lawyer":
            try:
                await bot.send_message(
                    uid,
                    "💼 <b>Адвокат, выбери клиента на сегодня.</b>",
                    parse_mode="HTML",
                    reply_markup=target_kb(alive, exclude=uid, prefix="lw")
                )
            except Exception:
                pass

    await asyncio.sleep(NIGHT_DURATION)
    await resolve_night(bot, chat_id)


async def resolve_night(bot: Bot, chat_id: int):
    game = get_game(chat_id)
    if not game:
        return

    actions = game["night_actions"]
    killed = set()

    lover_target = actions.get("lover_target")
    mafia_target = actions.get("mafia_target")
    maniac_target = actions.get("maniac_target")
    doctor_target = actions.get("doctor_target")

    if mafia_target and mafia_target != lover_target:
        killed.add(mafia_target)
    if maniac_target and maniac_target != lover_target:
        killed.add(maniac_target)
    if doctor_target:
        killed.discard(doctor_target)

    for uid in list(killed):
        if uid in game["players"] and game["players"][uid]["role"] == "lucky":
            if random.random() < 0.5:
                killed.discard(uid)

    dead_names = []
    for uid in killed:
        if uid in game["players"]:
            game["players"][uid]["alive"] = False
            dead_names.append(game["players"][uid]["name"])

    if not game["sergeant_promoted"]:
        detective_alive = any(p["role"] == "detective" and p["alive"] for p in game["players"].values())
        if not detective_alive:
            for uid, p in game["players"].items():
                if p["role"] == "sergeant" and p["alive"]:
                    p["role"] = "detective"
                    game["sergeant_promoted"] = True
                    try:
                        await bot.send_message(uid, "👮 <b>Детектив погиб. Ты теперь Детектив!</b>", parse_mode="HTML")
                    except Exception:
                        pass
                    break

    game["phase"] = "day"
    game["day"] += 1

    if check_win(bot, chat_id):
        return

    if dead_names:
        deaths = t("ru", "deaths_some", names=", ".join(dead_names))
    else:
        deaths = t("ru", "deaths_none")

    await bot.send_message(
        chat_id,
        t("ru", "day_start", day=game["day"], deaths=deaths, sec=DAY_DISCUSSION),
        parse_mode="HTML"
    )
    await asyncio.sleep(DAY_DISCUSSION)
    await voting_phase(bot, chat_id)


async def voting_phase(bot: Bot, chat_id: int):
    game = get_game(chat_id)
    if not game:
        return
    game["votes"] = {}
    game["phase"] = "vote"

    alive = {uid: p for uid, p in game["players"].items() if p["alive"]}
    for uid in alive:
        try:
            await bot.send_message(
                uid,
                "🗳 <b>Голосование. Кого казним?</b>",
                parse_mode="HTML",
                reply_markup=vote_kb(alive, voter_id=uid)
            )
        except Exception:
            pass

    await bot.send_message(
        chat_id,
        t("ru", "vote_start"),
        parse_mode="HTML"
    )
    await asyncio.sleep(VOTE_DURATION)
    await resolve_voting(bot, chat_id)


async def resolve_voting(bot: Bot, chat_id: int):
    game = get_game(chat_id)
    if not game:
        return

    votes = game["votes"]
    vote_counts = {}
    for target in votes.values():
        if target != "skip":
            vote_counts[target] = vote_counts.get(target, 0) + 1

    lynched = None
    if vote_counts:
        max_v = max(vote_counts.values())
        candidates = [uid for uid, c in vote_counts.items() if c == max_v]
        if len(candidates) == 1:
            lynched = candidates[0]

    result_text = t("ru", "vote_none")
    extra = ""
    if lynched is not None:
        p = game["players"][lynched]

        if "shield_vote" in get_inventory(lynched):
            from database import consume_item
            consume_item(lynched, "shield_vote")
            result_text = f"🛡 <b>{p['name']}</b> защищён и не казнён!"
        else:
            result_text = t("ru", "vote_lynched", name=p["name"])

            if p["role"] == "kamikaze":
                others = [uid for uid, pl in game["players"].items() if pl["alive"] and uid != lynched]
                if others:
                    victim = random.choice(others)
                    game["players"][victim]["alive"] = False
                    extra = t("ru", "kamikaze_extra", name=game["players"][victim]["name"])

            if p["role"] == "suicide":
                game["players"][lynched]["alive"] = False
                await bot.send_message(chat_id, t("ru", "vote_result", result=result_text), parse_mode="HTML")
                await _end(bot, chat_id, t("ru", "win_suicide"))
                return

            game["players"][lynched]["alive"] = False

    await bot.send_message(
        chat_id,
        t("ru", "vote_result", result=result_text + extra),
        parse_mode="HTML"
    )

    if check_win(bot, chat_id):
        return

    await asyncio.sleep(3)
    await bot.send_message(chat_id, t("ru", "night_start"), parse_mode="HTML")
    await asyncio.sleep(2)
    await night_phase(bot, chat_id)


def check_win(bot: Bot, chat_id: int) -> bool:
    game = get_game(chat_id)
    if not game:
        return True

    alive = [p for p in game["players"].values() if p["alive"]]
    mafia_alive = [p for p in alive if p["role"] in ("mafia", "don", "lawyer")]
    maniac_alive = [p for p in alive if p["role"] == "maniac"]
    total = len(alive)

    if len(mafia_alive) == 0 and len(maniac_alive) == 0:
        asyncio.create_task(_end(bot, chat_id, t("ru", "win_city")))
        return True
    if len(mafia_alive) >= total - len(mafia_alive) and len(maniac_alive) == 0:
        asyncio.create_task(_end(bot, chat_id, t("ru", "win_mafia")))
        return True
    if maniac_alive and total == 1:
        asyncio.create_task(_end(bot, chat_id, t("ru", "win_maniac")))
        return True
    return False


async def _end(bot: Bot, chat_id: int, text: str):
    game = get_game(chat_id)
    if not game:
        return
    roles_text = "\n".join(
        f"• {p['name']} — {ROLES[p['role']]['name']} {'💀' if not p['alive'] else ''}"
        for p in game["players"].values()
    )
    await bot.send_message(
        chat_id,
        f"{text}\n\n{t('ru', 'all_roles', roles=roles_text)}",
        parse_mode="HTML"
    )
    winners = []
    for uid, p in game["players"].items():
        win = False
        if "Мафия победила" in text:
            win = p["role"] in ("mafia", "don", "lawyer")
        elif "Мирные" in text:
            win = p["role"] not in ("mafia", "don", "lawyer", "maniac")
        elif "Маньяк" in text:
            win = p["role"] == "maniac"
        inc_game(uid, win=win)
        if win:
            winners.append(uid)
        else:
            grant_lose_rewards([uid])
    if winners:
        grant_win_rewards(winners)
    end_game(chat_id)
