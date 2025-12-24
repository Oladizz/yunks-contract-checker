import json
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from web3 import Web3

# --- Configuration ---
TELEGRAM_BOT_TOKEN = "7843191744:AAFTgk1EKhgahjaKuDGtBh-r73ndpCDHeFs"
RPC_URL = "https://base.publicnode.com"
CONTRACT_ADDRESS = "0x3e6A286f005AC829b95DD102328E47A321D4FE4C"
PRODUCTION = os.environ.get("PRODUCTION", "false").lower() == "true"

# -- Load ABI ---
script_dir = os.path.dirname(__file__)
abi_path = os.path.join(script_dir, 'nft_abi.json')
with open(abi_path) as f:
    CONTRACT_ABI = json.load(f)

# --- Web3 Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to the NFT Balance Checker Bot!\n"
        "Just send me a wallet address to check its NFT balance."
    )

async def _check_balance_helper(wallet_address_input: str, update: Update) -> None:
    """Helper function to check NFT balance."""
    print(f"Received wallet address: {wallet_address_input}")
    
    try:
        # Always convert to a checksum address
        wallet_address = Web3.to_checksum_address(wallet_address_input)
        print(f"Checksummed wallet address: {wallet_address}")
    except ValueError:
        await update.message.reply_text("Invalid wallet address. Please provide a valid Ethereum wallet address.")
        return

    try:
        print(f"Checking balance for {wallet_address} on contract {CONTRACT_ADDRESS}")
        balance = contract.functions.balanceOf(wallet_address).call()
        print(f"Balance: {balance}")
        await update.message.reply_text(f"The wallet {wallet_address} holds {balance} NFTs from this collection.")
    except Exception as e:
        print(f"Error calling contract function: {e}")
        await update.message.reply_text("An error occurred while checking the balance. Please check the logs for more details.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages to check for wallet addresses."""
    message_text = update.message.text
    # Simple check if the message looks like a wallet address
    if message_text.startswith("0x") and len(message_text) == 42:
        await _check_balance_helper(message_text, update)
    else:
        await update.message.reply_text("Please send a valid wallet address.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if PRODUCTION:
        port = int(os.environ.get('PORT', 8080))
        webhook_url = f"https://yunks-contract-checker.onrender.com/{TELEGRAM_BOT_TOKEN}"
        print(f"Starting bot in production mode on port {port} with webhook {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=webhook_url
        )
    else:
        print("Starting bot in development mode with polling.")
        application.run_polling()

if __name__ == "__main__":
    main()