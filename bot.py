import os
import random
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["BOT_TOKEN"]

QUESTIONS = [
    ("Have the ability to fly", "Be invisible"),
    ("Never use social media again", "Never watch TV or movies again"),
    ("Always be 10 minutes late", "Always be 20 minutes early"),
    ("Live in the mountains", "Live by the beach"),
    ("Be able to talk to animals", "Speak every human language"),
    ("Have unlimited money", "Have unlimited free time"),
    ("Only eat pizza forever", "Never eat pizza again"),
    ("Travel to the past", "Travel to the future"),
    ("Be famous", "Be rich but unknown"),
    ("Have a rewind button for your life", "Have a pause button for your life"),
    ("Always have to sing instead of speak", "Always have to dance when you walk"),
    ("Live without music", "Live without movies"),
    ("Know how you will die", "Know when you will die"),
    ("Have super strength", "Have super speed"),
    ("Be the smartest person alive", "Be the funniest person alive"),
    ("Live in a treehouse", "Live in a houseboat"),
    ("Never be able to lie", "Always be lied to without knowing"),
    ("Have no homework or work for a year", "Get paid double for a year"),
    ("Always be too hot", "Always be too cold"),
    ("Fight one horse-sized duck", "Fight 100 duck-sized horses"),
    ("Be able to read minds", "Be able to see the future"),
    ("Eat only sweet food forever", "Eat only salty food forever"),
    ("Have a personal chef", "Have a personal driver"),
    ("Visit space", "Explore the deep ocean"),
    ("Lose your phone for a month", "Lose your wallet for a month"),
    ("Be stuck in an elevator for 3 hours", "Be stuck in traffic for 5 hours"),
    ("Have a pet dragon", "Have a pet unicorn"),
    ("Wake up early every day", "Stay up late every night"),
    ("Give up coffee and tea forever", "Give up juice and soda forever"),
    ("Be a superhero", "Be a famous movie star"),
    ("Only whisper", "Only shout"),
    ("Never get sick", "Never feel tired"),
    ("Live 100 years in the past", "Live 100 years in the future"),
    ("Have free flights for life", "Have free food for life"),
    ("Replay one day forever", "Skip ahead 10 years"),
    ("Always speak your mind", "Never speak again"),
    ("Have a tiny house you love", "Have a mansion you hate"),
    ("Never forget anything", "Be able to forget anything you want"),
    ("Have the best sleep every night", "Have the best meal every day"),
    ("Be lost in a jungle", "Be lost in a desert"),
    ("Swim with sharks", "Skydive from a plane"),
    ("Have a boring job you love the pay of", "Have a dream job with low pay"),
    ("Be able to teleport", "Be able to freeze time"),
    ("Always know the time", "Always know the weather"),
    ("Have unlimited data forever", "Have unlimited battery forever"),
    ("Meet your hero", "Meet your future self"),
    ("Have a robot do your chores", "Have a robot cook your meals"),
    ("Only travel by boat", "Only travel by train"),
    ("Be a master at one skill", "Be pretty good at everything"),
    ("Be too early to a party", "Be too late to a party"),
    ("Have eyes in the back of your head", "Have extra-long arms"),
    ("Live in a world with no rules for a day", "Make all the rules for a day"),
    ("Never have to sleep", "Never have to eat"),
    ("Be invisible at will", "Be able to shrink at will"),
    ("Win the lottery", "Find your true passion"),
    ("Have a rewind to fix one mistake", "Have a fast-forward to skip one bad day"),
    ("Always win at board games", "Always win at video games"),
    ("Spend a week alone on an island", "Spend a week in a crowded city"),
    ("Have your dream house", "Have your dream car"),
    ("Be able to breathe underwater", "Be able to survive in space"),
    ("Hear every thought people have about you", "Never know what anyone thinks of you"),
]

TOTAL = len(QUESTIONS)

# In-memory vote tallies shared by everyone using the bot (reset on restart)
VOTES = {i: [0, 0] for i in range(TOTAL)}

WELCOME = (
    "🤷 *Would You Rather?*\n\n"
    "I'll give you two choices, you pick one, and I'll show what everyone "
    "else picked.\n\n"
    f"{TOTAL} dilemmas, with no repeats until you've seen them all. "
    "Tap *Play* to start!"
)


def play_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Play", callback_data="next")]])


def question_keyboard(idx):
    a, b = QUESTIONS[idx]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"🅰️ {a}", callback_data=f"v:{idx}:0")],
            [InlineKeyboardButton(f"🅱️ {b}", callback_data=f"v:{idx}:1")],
        ]
    )


def next_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Next one", callback_data="next")]])


def draw(user_data):
    seen = user_data.setdefault("seen", set())
    reset = False
    pool = [i for i in range(TOTAL) if i not in seen]
    if not pool:
        seen.clear()
        pool = list(range(TOTAL))
        reset = True
    idx = random.choice(pool)
    seen.add(idx)
    return idx, reset


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    context.user_data["seen"] = set()
    await update.message.reply_text(
        WELCOME, parse_mode="Markdown", reply_markup=play_keyboard()
    )


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx, reset = draw(context.user_data)
    a, b = QUESTIONS[idx]
    text = f"🤷 *Would you rather...*\n\n🅰️ {a}\n\n*or*\n\n🅱️ {b}?"
    text += f"\n\n_Question {len(context.user_data['seen'])}/{TOTAL}_"
    if reset:
        text += "\n🔄 _You've seen them all, starting a fresh round!_"
    await query.message.reply_text(
        text, parse_mode="Markdown", reply_markup=question_keyboard(idx)
    )


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, idx, choice = query.data.split(":")
    idx, choice = int(idx), int(choice)

    answered = context.user_data.setdefault("answered", set())
    if idx in answered:
        await query.answer("You already answered this one!")
        return
    answered.add(idx)
    VOTES[idx][choice] += 1
    await query.answer()

    a, b = QUESTIONS[idx]
    va, vb = VOTES[idx]
    total = va + vb
    pa = round(va * 100 / total)
    pb = 100 - pa
    mark_a = "👉 " if choice == 0 else ""
    mark_b = "👉 " if choice == 1 else ""
    text = (
        "📊 *Results*\n\n"
        f"{mark_a}🅰️ {a}: *{pa}%*\n"
        f"{mark_b}🅱️ {b}: *{pb}%*\n\n"
        f"_{total} player(s) answered this one_"
    )
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        text, parse_mode="Markdown", reply_markup=next_keyboard()
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(next_question, pattern="^next$"))
    app.add_handler(CallbackQueryHandler(vote, pattern=r"^v:\d+:[01]$"))
    app.run_polling()


if __name__ == "__main__":
    main()
