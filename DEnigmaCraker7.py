import os
import sys
import platform
import requests
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip39WordsNum,
)

# Constants
ENV_FILE_NAME = "DEnigmaCracker.env"
WALLETS_FILE_NAME = "wallets_with_balance.txt"

# Global counter for the number of wallets scanned
wallets_scanned = 0

# Get the absolute path of the directory where the script is located
directory = os.path.dirname(os.path.abspath(__file__))
# Initialize directory paths
env_file_path = os.path.join(directory, ENV_FILE_NAME)
wallets_file_path = os.path.join(directory, WALLETS_FILE_NAME)

# Load environment variables from .env file
load_dotenv(env_file_path)

# Environment variable validation
required_env_vars = ["5HDRX437URRRATZJ19X4WCFKB6FSEEADNI"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Function to get log file path based on current timestamp
def get_log_file_path():
    log_directory = os.path.join(directory, "Log")
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(log_directory, f"enigmacracker_{timestamp}.log")

# Configure logging
log_file_path = get_log_file_path()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),  # Log to a file
        logging.StreamHandler(sys.stdout),  # Log to standard output
    ],
)

def update_cmd_title():
    # Update the CMD title with the current number of wallets scanned
    if platform.system() == "Windows":
        os.system(f"title EnigmaCracker.py - Wallets Scanned: {wallets_scanned}")

def generate_bip39_mnemonic():
    # Generate a 12-word BIP39 mnemonic
    return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)

def bip44_eth_wallet_from_seed(seed):
    # Generate an Ethereum wallet from a BIP39 seed.
    seed_bytes = Bip39SeedGenerator(seed).Generate()
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc_ctx = (
        bip44_mst_ctx.Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
    )
    eth_address = bip44_acc_ctx.PublicKey().ToAddress()
    return eth_address

def bip44_btc_seed_to_address(seed):
    # Generate the seed from the mnemonic
    seed_bytes = Bip39SeedGenerator(seed).Generate()
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
    btc_address = bip44_addr_ctx.PublicKey().ToAddress()
    return btc_address

def check_eth_balance(address, etherscan_api_key, retries=3, delay=5):
    api_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={etherscan_api_key}"

    for attempt in range(retries):
        try:
            response = requests.get(api_url)
            data = response.json()
            if data["status"] == "1":
                balance = int(data["result"]) / 1e18
                return balance
            else:
                logging.error("Error getting balance: %s", data["message"])
                return 0
        except Exception as e:
            if attempt < retries - 1:
                logging.error(f"Error checking balance, retrying in {delay} seconds: {str(e)}")
                time.sleep(delay)
            else:
                logging.error("Error checking balance: %s", str(e))
                return 0

def check_btc_balance(address, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={address}")
            data = response.json()
            balance = data[address]["final_balance"]
            return balance / 100000000  # Convert satoshi to bitcoin
        except Exception as e:
            if attempt < retries - 1:
                logging.error(f"Error checking balance, retrying in {delay} seconds: {str(e)}")
                time.sleep(delay)
            else:
                logging.error("Error checking balance: %s", str(e))
                return 0

def write_to_file(seed, btc_address, btc_balance, eth_address, eth_balance):
    with open(wallets_file_path, "a") as f:
        log_message = (
            f"Seed: {seed}\n"
            f"BTC Address: {btc_address}\n"
            f"BTC Balance: {btc_balance} BTC\n"
            f"ETH Address: {eth_address}\n"
            f"ETH Balance: {eth_balance} ETH\n\n"
        )
        f.write(log_message)
        logging.info(f"Written to file: {log_message}")

def main():
    global wallets_scanned
    try:
        while True:
            seed = generate_bip39_mnemonic()
            btc_address = bip44_btc_seed_to_address(seed)
            btc_balance = check_btc_balance(btc_address)

            logging.info(f"Seed: {seed}")
            logging.info(f"BTC address: {btc_address}")
            logging.info(f"BTC balance: {btc_balance} BTC")
            logging.info("")

            eth_address = bip44_eth_wallet_from_seed(seed)
            etherscan_api_key = os.getenv("5HDRX437URRRATZJ19X4WCFKB6FSEEADNI")
            if not etherscan_api_key:
                raise ValueError("The Etherscan API key must be set in the environment variables.")
            eth_balance = check_eth_balance(eth_address, etherscan_api_key)
            logging.info(f"ETH address: {eth_address}")
            logging.info(f"ETH balance: {eth_balance} ETH")

            wallets_scanned += 1
            update_cmd_title()

            if btc_balance > 0 or eth_balance > 0:
                logging.info("(!) Wallet with balance found!")
                write_to_file(seed, btc_address, btc_balance, eth_address, eth_balance)

    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Exiting...")

if __name__ == "__main__":
    main()
