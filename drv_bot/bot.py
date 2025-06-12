import os
import logging
import asyncio
import random

import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from services.gender_service import get_gender

# Apply nest_asyncio to handle event loop issues on all OS
nest_asyncio.apply()

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_API")
GIF_FILE_ID = os.getenv("SHAPUR_GIF_ID")
MALE_STICKER_ID = "CAACAgQAAxkBAAE2GVloRob0YmA4QAK7vRrLguuEWZlQXwACdCoAAiqAEVEvHt9vRgNEaTYE"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.sticker:
        print(f"🎨 Sticker File ID:\n`{message.sticker.file_id}`")
        # Check sticker properties with proper null checks
        if hasattr(message.sticker, 'is_animated') and message.sticker.is_animated:
            print("Type: Animated Sticker")
        elif hasattr(message.sticker, 'is_video') and message.sticker.is_video:
            print("Type: Video Sticker")
        else:
            print("Type: Static Sticker")
        logging.info(f"Sticker file_id: {message.sticker.file_id}")
# --- SRP 1: Extract sender's first name ---
def extract_name_from_forwarded(update: Update) -> str | None:
    message = update.message
    if not message:
        logging.info("Skipped: No message found.")
        return None

    # Check if message is forwarded
    if not message.forward_origin:
        logging.info("Skipped: Not a forwarded message.")
        return None

    # Extract name based on forward origin type
    origin = message.forward_origin
    name = None

    # Check the type of forward origin
    if hasattr(origin, 'sender_user') and origin.sender_user:
        # MessageOriginUser - when user allows linking to their account
        user = origin.sender_user
        full_name = user.first_name or user.username or ""
        name = full_name.split()[0]
    elif hasattr(origin, 'sender_user_name') and origin.sender_user_name:
        # MessageOriginHiddenUser - when user's privacy settings hide their account
        name = origin.sender_user_name.split()[0]

    if name:
        logging.info(f"Forwarded sender name extracted: {name}")
    else:
        logging.info("Could not extract sender name from forwarded message.")

    return name


# --- SRP 2: Format message based on gender ---
def format_void_title(gender: str | None) -> str | None:
    if gender == "female":
        return "دکتر وید دختر @TheDrVoid"
    elif gender == "femboy":
        return "دکتر وید فمبوی  @TheDrVoid "
    return None


# --- SRP 3: Send text + GIF response ---
async def send_void_message(update: Update, context: ContextTypes.DEFAULT_TYPE, title: str):
    try:
        logging.info(f"Sending reply: {title}")
        await update.message.reply_text(title, reply_to_message_id=update.message.message_id)
        await send_gif(update, context)
    except Exception as e:
        logging.error(f"Error sending message: {e}")


# --- SRP 4: Send GIF ---
async def send_gif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_animation(chat_id=update.effective_chat.id, animation=GIF_FILE_ID, reply_to_message_id=update.message.message_id)
        logging.info("GIF sent.")
    except Exception as e:
        logging.error(f"Failed to send GIF: {e}")


# --- SRP 5: Send male sticker ---
async def send_male_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=MALE_STICKER_ID, reply_to_message_id=update.message.message_id )
        logging.info("Male sticker sent.")
    except Exception as e:
        logging.error(f"Failed to send sticker: {e}")


# --- SRP 6: Check for Dr. Void mention ---
def has_dr_void_mention(text: str) -> bool:
    if not text:
        return False
    return "آهای دکتر وید" in text or "دکتر وید!" in text or "@TheDrVoid" in text or "دکتر وید دختر" in text


def has_shapur_mention(text: str):
    if not text:
        return False
    return "شاپور" in text
async def handle_dr_void_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:

        return
    if has_shapur_mention(update.message.text):
        if update.message.from_user.username == "pm_ranj":
            await update.message.reply_text("چاکرم", reply_to_message_id=update.message.message_id)
        elif update.message.from_user.username == "TheDrVoid":
            responses = [
                "راست میگه",
            ]
            response = random.choice(responses)
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
        else:
            responses = [
                "به تو نمیرسه!",
                "گه نخور",
                "سیکیتر",

            ]
            response = random.choice(responses)
            await update.message.reply_text( response, reply_to_message_id=update.message.message_id)
    if has_dr_void_mention(update.message.text):
        logging.info("Dr. Void mention detected, sending GIF")
        await send_gif(update, context)


# --- SRP 8: Main handler for forwarded messages ---
async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = extract_name_from_forwarded(update)
    madarjende_ha = ["sepide","sepideh","amirhosein","amirhossein"]
    if not name:
        await send_male_sticker(update, context)
    elif name.lower() in madarjende_ha:
        await update.message.reply_text("گروه جای اسم این حرومیا نیست", reply_to_message_id=update.message.message_id)
        return

    gender = await get_gender(name)
    print(f"Gender for '{name}': {gender}")
    print(f"Group Chat ID: {update.effective_chat.id}")
    if gender == "male":
        # Send sticker for males
        # await send_male_sticker(update, context)
        await update.message.reply_text("رنجبر پسر @pm_ranj", reply_to_message_id=update.message.message_id)
    else:
        # Handle female/femboy cases
        title = format_void_title(gender)
        if title:
            await send_void_message(update, context, title)
        else:
            await send_gif(update, context)
            logging.info("No response (gender is unknown).")

def is_media_message(update: Update) -> bool:
    """Check if message contains any media"""
    if not update.message:
        return False
    return bool(
        update.message.animation or
        update.message.sticker or
        update.message.photo or
        update.message.video or
        update.message.document
    )

async def send_startup_message(app: ApplicationBuilder):
    chat_id = "-1001710391351"
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text="شاپور بیدار شد!")
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")

async def send_shutdown_message(app: ApplicationBuilder):
    chat_id = "-1001710391351"
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text="فعلا! ما بریم")
    except Exception as e:
        logging.error(f"Failed to send shutdown message: {e}")

# --- SRP 9: Entry point ---
def main():
    logging.info("Bot is starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # media_filter = filters.create(is_media_message) & ~filters.FORWARDED
    # Add handlers
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.FORWARDED, handle_dr_void_mention))
    # app.add_handler(MessageHandler(media_filter, handle_files))
    app.post_init = send_startup_message
    app.post_shutdown = send_shutdown_message
    # Run the bot
    app.run_polling()


if __name__ == "__main__":
    main()