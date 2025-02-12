import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue
from openpyxl import Workbook
from datetime import datetime, timedelta

# Set up logging to capture both info and errors
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Excel setup
wb = Workbook()
ws = wb.active
ws.append(['Username', 'Vehicle plate number', 'Date'])

# Initialize sets to track unique usernames and plate numbers
unique_usernames = set()
unique_plate_numbers = set()

# Function to download the photo and save it in a folder by username
async def download_photo(photo_file, username):
    try:
        # Create a folder by username if it does not exist
        user_folder = os.path.join("photos", username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # Get the file object using get_file() method
        file = await photo_file.get_file()
        # Define the file path for the photo
        filename = os.path.join(user_folder, f"photo_{photo_file.file_id}.jpg")

        # Debugging log: Check the photo details
        logger.info(f"Downloading photo for {username} with file_id {photo_file.file_id}")

        # Download the photo content and save it
        await file.download_to_drive(filename)

        logger.info(f"Photo saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error downloading photo for {username}: {e}")
        return None

# Function to handle messages with photos
async def handle_photo(update: Update, context: CallbackContext):
    try:
        # Get the user's username
        username = update.message.from_user.username
        # Get the caption (vehicle plate number)
        caption = update.message.caption if update.message.caption else "No caption"
        # Get the current date
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log the received photo and caption
        logger.info(f"Received photo from {username} with caption: {caption} on {current_date}")

        # Save the data to the Excel file
        ws.append([username, caption, current_date])
        wb.save("captions_data.xlsx")

        # Add to unique sets
        unique_usernames.add(username)
        unique_plate_numbers.add(caption)

        # Get the photo object (largest photo size)
        photo = update.message.photo[-1]
        # Download and save the photo
        await download_photo(photo, username)

        # Send acknowledgment to user
        await update.message.reply_text(f"Photo received!")

    except Exception as e:
        logger.error(f"Error handling photo for {update.message.from_user.username}: {e}")
        await update.message.reply_text(f"Sorry, there was an error processing your photo. Error: {e}")

# Function to handle text messages (optional)
async def handle_text(update: Update, context: CallbackContext):
    await update.message.reply_text("Please send a Vehicle photo with plate number.")

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me a photo with a plate number as a caption.")

# Error handler
async def error_handler(update: Update, context: CallbackContext):
    try:
        raise context.error
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        if update:
            await update.message.reply_text(f"An error occurred: {e}")

# Function to send weekly report to the group
async def send_weekly_report(context: CallbackContext):
    try:
        # Get the group chat ID (replace with your group's chat ID)
        chat_id = "-4264137486"

        # Calculate the number of unique usernames and plate numbers
        unique_usernames_count = len(unique_usernames)
        unique_plate_numbers_count = len(unique_plate_numbers)

        # Prepare the report message
        report_message = (
            f"Weekly Report:\n"
            f"Unique Usernames: {unique_usernames_count}\n"
            f"Unique Plate Numbers: {unique_plate_numbers_count}"
        )

        # Send the message to the Telegram group
        await context.bot.send_message(chat_id=chat_id, text=report_message)

        # Log the sent report
        logger.info(f"Sent weekly report to group: {report_message}")

    except Exception as e:
        logger.error(f"Error sending weekly report: {e}")

# Main function to set up the bot
def main():
    # Set up your bot's token here
    bot_token = "7516113634:AAETwIX7p2YbzGFuE3t5gIt6uh2gJvKCvQY"
    
    # Create the Application and Dispatcher
    application = Application.builder().token(bot_token).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))

    # Register the error handler
    application.add_error_handler(error_handler)

    # Set up the JobQueue for weekly reports (every 7 days)
    job_queue = application.job_queue
    job_queue.run_repeating(send_weekly_report, interval=60, first=timedelta(seconds=10))

    # Start polling (no need for asyncio.run here)
    application.run_polling()

if __name__ == '__main__':
    main()
