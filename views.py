# telegram_bot/views.py

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from .bot import application  # Import the initialized bot application
import logging
import asyncio
import traceback

logger = logging.getLogger(__name__)


@csrf_exempt
async def telegram_webhook(request):
    """Handles incoming webhook requests from Telegram."""
    if request.method == 'POST':
        try:
            logger.debug("Received POST request for Telegram webhook.")

            # Parse the incoming data to create an Update object
            data = json.loads(request.body)
            update = Update.de_json(data, application.bot)
            logger.debug(f"Parsed update: {update}")

            # Process the update with the bot application
            await application.process_update(update)
            logger.info("Update processed successfully.")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)
            logger.error(traceback.format_exc())
            return HttpResponse(content=f"Exception: {str(e)}", status=500)
    else:
        logger.warning("Non-POST request received at the Telegram webhook endpoint.")
        return HttpResponse("This endpoint is for Telegram bot webhook.")
