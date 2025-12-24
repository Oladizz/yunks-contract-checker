
import json
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from web3 import Web3

# --- Configuration ---
TELEGRAM_BOT_TOKEN = "7843191744:AAFTgk1EKhgahjaKuDGtBh-r73ndpCDHeFs"
RPC_URL = "https://rpc.ankr.com/eth"
CONTRACT_ADDRESS = "0x3e6A286f005AC829b95DD102328E47A321D4FE4C"
with open("nft_balance_bot/nft_abi.json") as f:
    CONTRACT_ABI = json.load(f)

# --- Web3 Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to the NFT Balance Checker Bot!\n"
        "Use /check <wallet_address> to check the NFT balance."
    )

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks the NFT balance for a given wallet address."""
    if not context.args:
        await update.message.reply_text("Please provide a wallet address after the /check command.")
        return

    wallet_address = context.args[0]
    if not w3.is_address(wallet_address):
        await update.message.reply_text("Invalid wallet address.")
        return

    try:
        balance = contract.functions.balanceOf(wallet_address).call()
        await update.message.reply_text(f"The wallet {wallet_address} holds {balance} NFTs from this collection.")
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("An error occurred while checking the balance.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_balance))

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
