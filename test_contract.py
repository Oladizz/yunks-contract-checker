
import json
from web3 import Web3

# --- Configuration ---
RPC_URL = "https://base.publicnode.com"
CONTRACT_ADDRESS = "0x3e6A286f005AC829b95DD102328E47A321D4FE4C"
TEST_WALLET_ADDRESS = "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae" # A known address for testing

import os

# Load ABI
try:
    script_dir = os.path.dirname(__file__)
    abi_path = os.path.join(script_dir, 'nft_abi.json')
    with open(abi_path) as f:
        CONTRACT_ABI = json.load(f)
except FileNotFoundError:
    print("Error: nft_abi.json not found. Make sure it's in the correct path relative to test_contract.py")
    exit()
except json.JSONDecodeError as e:
    print(f"Error decoding nft_abi.json: {e}")
    exit()

# --- Web3 Setup ---
try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"Error: Not connected to Ethereum node at {RPC_URL}")
        exit()
    print(f"Successfully connected to Ethereum node at {RPC_URL}")
except Exception as e:
    print(f"Error connecting to Web3 provider: {e}")
    exit()

# Contract instance
try:
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    print(f"Successfully loaded contract at {CONTRACT_ADDRESS}")
except Exception as e:
    print(f"Error loading contract: {e}")
    exit()

# --- Test balanceOf function ---
def test_balance_of():
    print(f"\nAttempting to call balanceOf for address: {TEST_WALLET_ADDRESS}")
    checksum_test_wallet_address = Web3.to_checksum_address(TEST_WALLET_ADDRESS)
    try:
        balance = contract.functions.balanceOf(checksum_test_wallet_address).call()
        print(f"Balance of {checksum_test_wallet_address}: {balance}")
    except Exception as e:
        print(f"Error calling balanceOf function: {e}")

if __name__ == "__main__":
    test_balance_of()
