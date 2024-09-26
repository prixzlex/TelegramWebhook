# telegram_bot/license_bot.py

import datetime
from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
import traceback

# Initialize Django
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MCLAPI.settings')
django.setup()

# Import models
from mscookies.models import License, Domain, Result

# Set up logging
logger = logging.getLogger(__name__)

class LicenseBot:
    # Define state constants for ConversationHandler
    ENTER_LICENSE, LICENSE_VALIDATION, MAIN_MENU, UPDATE_TELEGRAM_ID, UPDATE_BOT_ID, UPDATE_EMAIL, ADD_DOMAIN = range(7)

    def __init__(self, bot_token):
        self.bot_token = bot_token

        # Define available options for the main menu and updates
        self.main_menu_keyboard = [["Enter License Key", "Buy License Key"]]
        self.account_update_keyboard = [["Change Telegram ID", "Change Bot ID", "Change Email Address"]]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /start command and shows the initial options."""
        try:
            await update.message.reply_text(
                "Welcome to the License Manager Bot! Please select an option:",
                reply_markup=ReplyKeyboardMarkup(self.main_menu_keyboard, one_time_keyboard=True)
            )
            logger.info("Start command executed.")
            return self.ENTER_LICENSE
        except Exception as e:
            logger.error(f"Error in start method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    async def enter_license_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompts the user to enter their license key."""
        try:
            await update.message.reply_text("Please enter your license key:")
            return self.LICENSE_VALIDATION
        except Exception as e:
            logger.error(f"Error in enter_license_key method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    async def buy_license_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Provides information for purchasing a license key."""
        try:
            message = (
                "To buy a license key, please send payment to the following address:\n"
                "Crypto Wallet: 0x123456789ABCDEF\n"
                "Price: 0.1 BTC"
            )
            await update.message.reply_text(message)
            return self.ENTER_LICENSE
        except Exception as e:
            logger.error(f"Error in buy_license_key method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    async def validate_license_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Validates the entered license key against the database."""
        license_key = update.message.text.strip()
        logger.debug(f"Validating license key: {license_key}")
        try:
            # Asynchronously fetch the license from the database
            license = await sync_to_async(License.objects.get)(license_key=license_key, valid=True)
            if license.expiration_date < datetime.date.today():
                await update.message.reply_text("Your license key has expired. Please renew your license.")
                return self.ENTER_LICENSE
            else:
                context.user_data['license'] = license
                await update.message.reply_text(
                    "License validated successfully! What would you like to do next?",
                    reply_markup=ReplyKeyboardMarkup(
                        self.account_update_keyboard + [["Add Domain"], ["Done"]],
                        one_time_keyboard=True
                    )
                )
                logger.info(f"License validated for user: {update.message.from_user.username}")
                return self.MAIN_MENU
        except License.DoesNotExist:
            logger.warning(f"Invalid license key: {license_key}")
            await update.message.reply_text(
                "Invalid license key. Please buy a license or try again.\n"
                "Crypto Wallet: 0x123456789ABCDEF\nPrice: 0.1 BTC"
            )
            return self.ENTER_LICENSE
        except Exception as e:
            logger.error(f"Error in validate_license_key method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred while validating the license key. Please try again.")
            return ConversationHandler.END

    async def main_menu_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the selection from the main menu."""
        text = update.message.text
        logger.debug(f"User selected main menu option: {text}")
        try:
            if text == "Change Telegram ID":
                await update.message.reply_text("Please enter your new Telegram ID:")
                return self.UPDATE_TELEGRAM_ID
            elif text == "Change Bot ID":
                await update.message.reply_text("Please enter your new Bot ID:")
                return self.UPDATE_BOT_ID
            elif text == "Change Email Address":
                await update.message.reply_text("Please enter your new Email Address:")
                return self.UPDATE_EMAIL
            elif text == "Add Domain":
                await update.message.reply_text("Please enter the domain name to add:")
                return self.ADD_DOMAIN
            elif text == "Done":
                await update.message.reply_text("Thank you. If you need to update anything else, you can use /start.")
                return ConversationHandler.END
            else:
                await update.message.reply_text("Please select a valid option.")
                return self.MAIN_MENU
        except Exception as e:
            logger.error(f"Error in main_menu_options method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    async def update_telegram_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Updates the Telegram ID associated with the license."""
        new_telegram_id = update.message.text.strip()
        license = context.user_data.get('license')
        try:
            if license:
                results, created = await sync_to_async(Result.objects.get_or_create)(license=license)
                results.telegram_id = new_telegram_id
                await sync_to_async(results.save)()
                await update.message.reply_text("Your Telegram ID has been updated successfully.")
            else:
                await update.message.reply_text("License not found in your session. Please start over with /start.")
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=ReplyKeyboardMarkup(
                    self.account_update_keyboard + [["Add Domain"], ["Done"]],
                    one_time_keyboard=True
                )
            )
            return self.MAIN_MENU
        except Exception as e:
            logger.error(f"Error updating Telegram ID: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return self.MAIN_MENU

    async def update_bot_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Updates the Bot ID associated with the license."""
        new_bot_id = update.message.text.strip()
        license = context.user_data.get('license')
        try:
            if license:
                results, created = await sync_to_async(Result.objects.get_or_create)(license=license)
                results.telegram_bot_id = new_bot_id
                await sync_to_async(results.save)()
                await update.message.reply_text("Your Bot ID has been updated successfully.")
            else:
                await update.message.reply_text("License not found in your session. Please start over with /start.")
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=ReplyKeyboardMarkup(
                    self.account_update_keyboard + [["Add Domain"], ["Done"]],
                    one_time_keyboard=True
                )
            )
            return self.MAIN_MENU
        except Exception as e:
            logger.error(f"Error updating Bot ID: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return self.MAIN_MENU

    async def update_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Updates the email address associated with the license."""
        new_email = update.message.text.strip()
        license = context.user_data.get('license')
        try:
            if license:
                results, created = await sync_to_async(Result.objects.get_or_create)(license=license)
                results.email_address = new_email
                await sync_to_async(results.save)()
                await update.message.reply_text("Your Email Address has been updated successfully.")
            else:
                await update.message.reply_text("License not found in your session. Please start over with /start.")
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=ReplyKeyboardMarkup(
                    self.account_update_keyboard + [["Add Domain"], ["Done"]],
                    one_time_keyboard=True
                )
            )
            return self.MAIN_MENU
        except Exception as e:
            logger.error(f"Error updating Email: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return self.MAIN_MENU

    async def add_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adds a domain to the user's license."""
        domain_name = update.message.text.strip()
        license = context.user_data.get('license')
        try:
            if license:
                domain, created = await sync_to_async(Domain.objects.get_or_create)(
                    license=license, domain_name=domain_name
                )
                if created:
                    await update.message.reply_text(f"Domain '{domain_name}' has been added successfully.")
                else:
                    await update.message.reply_text(f"Domain '{domain_name}' is already associated with your license.")
            else:
                await update.message.reply_text("License not found in your session. Please start over with /start.")
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=ReplyKeyboardMarkup(
                    self.account_update_keyboard + [["Add Domain"], ["Done"]],
                    one_time_keyboard=True
                )
            )
            return self.MAIN_MENU
        except Exception as e:
            logger.error(f"Error adding domain: {e}", exc_info=True)
            await update.message.reply_text("An error occurred. Please try again.")
            return self.MAIN_MENU

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        try:
            await update.message.reply_text("Operation cancelled. You can start again with /start.")
            logger.info("User cancelled the conversation.")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error in cancel method: {e}", exc_info=True)
            await update.message.reply_text("An error occurred while cancelling.")
            return ConversationHandler.END
