# telegram_bot/bot.py

import os
import django
import asyncio
import logging
from telegram.ext import ApplicationBuilder, Application, ContextTypes
from django.conf import settings
from .bot_handler import setup_application  # Import the handler setup function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MCLAPI.settings')
django.setup()  # Initialize Django settings


async def initialize_application() -> Application:
    """Initializes the Telegram bot application asynchronously."""
    try:
        # Build the bot application with the provided token
        application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        logger.info("Telegram bot application built successfully.")

        # Setup handlers
        setup_application(application)
        logger.info("Handlers setup completed.")

        # Register global error handler for catching all exceptions during updates
        application.add_error_handler(handle_error)
        logger.info("Global error handler registered.")

        # Initialize the bot application (necessary for processing updates)
        await application.initialize()
        logger.info("Telegram bot application initialized successfully.")
        return application
    except Exception as e:
        logger.exception("Failed to initialize Telegram bot application.")
        raise


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs and handles any errors in the bot application."""
    logger.error(f"Exception while handling update {update}: {context.error}", exc_info=True)


# Main event loop setup and bot initialization
try:
    # Create a new event loop if the current one is not running or closed
    loop = asyncio.get_event_loop()
    if loop.is_closed() or not loop.is_running():
        logger.info("Creating a new event loop as the current one is closed or not running.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the bot application initialization coroutine
    application = loop.run_until_complete(initialize_application())
    logger.info("Bot application is initialized and running.")
except RuntimeError as e:
    logger.exception("RuntimeError occurred during event loop setup. Attempting to reinitialize.")
    # Reinitialize event loop in case of RuntimeError
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = loop.run_until_complete(initialize_application())
except Exception as e:
    logger.exception("Critical failure during bot initialization.")
