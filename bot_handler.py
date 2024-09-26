# telegram_bot/bot_handler.py

from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from .license_bot import LicenseBot
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def setup_application(application):
    """Sets up command and conversation handlers for the bot application."""
    try:
        # Initialize the LicenseBot instance
        bot_instance = LicenseBot(settings.TELEGRAM_BOT_TOKEN)
        logger.info("LicenseBot instance initialized.")

        # Define the conversation handler for different states of interaction
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", bot_instance.start)],
            states={
                bot_instance.ENTER_LICENSE: [
                    MessageHandler(filters.Regex("^Enter License Key$"), bot_instance.enter_license_key),
                    MessageHandler(filters.Regex("^Buy License Key$"), bot_instance.buy_license_key),
                ],
                bot_instance.LICENSE_VALIDATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.validate_license_key),
                ],
                bot_instance.MAIN_MENU: [
                    MessageHandler(
                        filters.Regex("^(Change Telegram ID|Change Bot ID|Change Email Address|Add Domain|Done)$"),
                        bot_instance.main_menu_options,
                    ),
                ],
                bot_instance.UPDATE_TELEGRAM_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.update_telegram_id),
                ],
                bot_instance.UPDATE_BOT_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.update_bot_id),
                ],
                bot_instance.UPDATE_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.update_email),
                ],
                bot_instance.ADD_DOMAIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.add_domain),
                ],
            },
            fallbacks=[CommandHandler("cancel", bot_instance.cancel)],
        )

        # Add the conversation handler to the application
        application.add_handler(conv_handler)
        logger.info("Conversation handler added to the application.")

    except Exception as e:
        logger.exception("Error setting up bot handlers.")
