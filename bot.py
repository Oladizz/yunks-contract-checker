import json
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from web3 import Web3
from aiohttp import web

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

# --- Health Check ---
async def health_check(request):
    return web.Response(text="OK")

# --- Main Application ---
async def main() -> None:
    """Set up and run the bot."""

    # Health check server
    async def on_startup(app: Application) -> None:
        """Start the health check server."""
        if PRODUCTION:
            health_app = web.Application()
            health_app.router.add_get("/", health_check)
            runner = web.AppRunner(health_app)
            await runner.setup()
            port = int(os.environ.get("PORT", 10000))
            health_check_site = web.TCPSite(runner, "0.0.0.0", port)
            await health_check_site.start()
            app.bot_data["health_check_runner"] = runner

    async def on_shutdown(app: Application) -> None:
        """Stop the health check server."""
        if PRODUCTION:
            runner = app.bot_data.get("health_check_runner")
            if runner:
                await runner.cleanup()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if PRODUCTION:
        port = int(os.environ.get("PORT", 10000))
        webhook_base_url = os.environ.get(
            "WEBHOOK_BASE_URL", "https://yunks-contract-checker.onrender.com"
        )
        webhook_url = f"{webhook_base_url}/{TELEGRAM_BOT_TOKEN}"

        print(
            f"Starting bot in production mode on port {port} with webhook {webhook_url}"
        )
        await application.run_webhook(
            listen="0.0.0.0", port=port, url_path=TELEGRAM_BOT_TOKEN, webhook_url=webhook_url
        )

    else:
        print("Starting bot in development mode with polling.")
        await application.run_polling()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError: # This will be raised if no event loop is set in the current OS thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Check if the loop is already running, if so, schedule the task
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())