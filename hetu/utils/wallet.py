"""
Wallet management utilities for Hetutensor SDK.
"""

import os
import json
import getpass
from typing import Optional, List, Dict
from eth_account import Account
from hetu.utils.balance import Balance


def get_wallet_path(config: Optional[dict] = None) -> str:
    """
    Get wallet path from config or use default.
    
    Args:
        config (Optional[dict]): Configuration dictionary.
        
    Returns:
        str: Wallet path.
    """
    raw_path = (config or {}).get("wallet_path", "~/.hetucli/wallets")
    return os.path.expanduser(raw_path)


def load_keystore(address_or_name: str, wallet_path: Optional[str] = None) -> dict:
    """
    Load keystore file by address or name.
    
    Args:
        address_or_name (str): Wallet address or name.
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        dict: Keystore data.
    """
    wallet_path = wallet_path or get_wallet_path()
    
    # Support lookup by wallet name or address
    # First try to find by name, otherwise iterate all files to match address field
    file_path = os.path.join(wallet_path, f"{address_or_name}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    
    # fallback: iterate all files to find by address
    for f in os.listdir(wallet_path):
        if f.endswith(".json"):
            with open(os.path.join(wallet_path, f), "r") as jf:
                data = json.load(jf)
                if data.get("address", "").lower() == address_or_name.lower():
                    return data
    
    raise FileNotFoundError(f"Keystore file not found for: {address_or_name}")


def unlock_wallet(name_or_address: str, wallet_path: Optional[str] = None) -> Account:
    """
    Unlock a wallet from keystore file with interactive password input.
    
    Args:
        name_or_address (str): Wallet name or address.
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        Account: Unlocked wallet account.
    """
    try:
        keystore = load_keystore(name_or_address, wallet_path)
        
        # Interactive password input
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    print(f"⚠️  Password incorrect. Attempt {attempt + 1}/{max_attempts}")
                
                password = getpass.getpass(f"Enter password for wallet '{name_or_address}': ")
                if not password:
                    print("❌ Password cannot be empty")
                    continue
                
                # Try to decrypt
                privkey = Account.decrypt(keystore, password)
                acct = Account.from_key(privkey)
                
                print(f"✅ Wallet unlocked successfully: {acct.address}")
                return acct
                
            except ValueError as e:
                if "Invalid password" in str(e) or "Decryption failed" in str(e):
                    continue  # Try again
                else:
                    raise e  # Re-raise other ValueError exceptions
            except KeyboardInterrupt:
                print("\n🛑 Password input cancelled by user")
                raise KeyboardInterrupt("Password input cancelled")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise e
        
        # If we get here, all attempts failed
        raise ValueError(f"Failed to unlock wallet after {max_attempts} attempts")
        
    except Exception as e:
        raise e


def list_wallets(wallet_path: Optional[str] = None) -> List[Dict]:
    """
    List all wallets in wallet path.
    
    Args:
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        List[Dict]: List of wallet information.
    """
    wallet_path = wallet_path or get_wallet_path()
    
    if not os.path.exists(wallet_path):
        return []
    
    wallets = []
    files = [f for f in os.listdir(wallet_path) if f.endswith(".json")]
    
    for f in files:
        try:
            with open(os.path.join(wallet_path, f), "r") as jf:
                data = json.load(jf)
                name = data.get("name", f.replace('.json', ''))
                address = data.get("address", "")
                wallets.append({
                    "name": name,
                    "address": address,
                    "filename": f
                })
        except Exception as e:
            # Skip corrupted files
            continue
    
    return wallets


def create_wallet(name: str, password: str, wallet_path: Optional[str] = None) -> Dict:
    """
    Create a new wallet and save as keystore file.
    
    Args:
        name (str): Wallet name.
        password (str): Wallet password.
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        Dict: Wallet information.
    """
    wallet_path = wallet_path or get_wallet_path()
    os.makedirs(wallet_path, exist_ok=True)
    
    acct = Account.create()
    keystore = Account.encrypt(acct.key, password)
    keystore["name"] = name
    keystore["address"] = acct.address
    
    keystore_path = os.path.join(wallet_path, f"{name}.json")
    with open(keystore_path, "w") as f:
        json.dump(keystore, f)
    
    return {
        "address": acct.address,
        "keystore_path": keystore_path,
        "name": name
    }


def import_wallet(private_key: str, name: str, password: str, wallet_path: Optional[str] = None) -> Dict:
    """
    Import a private key and save as keystore file.
    
    Args:
        private_key (str): Private key in hex format.
        name (str): Wallet name.
        password (str): Wallet password.
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        Dict: Wallet information.
    """
    wallet_path = wallet_path or get_wallet_path()
    os.makedirs(wallet_path, exist_ok=True)
    
    acct = Account.from_key(private_key)
    keystore = Account.encrypt(acct.key, password)
    keystore["name"] = name
    keystore["address"] = acct.address
    
    keystore_path = os.path.join(wallet_path, f"{name}.json")
    with open(keystore_path, "w") as f:
        json.dump(keystore, f)
    
    return {
        "address": acct.address,
        "keystore_path": keystore_path,
        "name": name
    }


def export_private_key(name_or_address: str, password: str, wallet_path: Optional[str] = None) -> str:
    """
    Export the private key of a wallet.
    
    Args:
        name_or_address (str): Wallet name or address.
        password (str): Wallet password.
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        str: Private key in hex format.
    """
    keystore = load_keystore(name_or_address, wallet_path)
    privkey = Account.decrypt(keystore, password)
    return privkey.hex()


def get_wallet_balance(hetu_client, name_or_address: str, password: Optional[str] = None, wallet_path: Optional[str] = None) -> Balance:
    """
    Get wallet balance by name or address.
    
    Args:
        hetu_client: Hetutensor client instance.
        name_or_address (str): Wallet name or address.
        password (Optional[str]): Wallet password (required if using name).
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        Balance: Wallet balance.
    """
    # If it's an address, use it directly
    if name_or_address.startswith('0x') and len(name_or_address) == 42:
        address = name_or_address
    else:
        # It's a name, need password to unlock
        if not password:
            raise ValueError("Password required when using wallet name")
        
        try:
            account = unlock_wallet(name_or_address, wallet_path)
            address = account.address
        except Exception as e:
            raise e
    
    # Get balance
    return hetu_client.get_balance(address)


def prompt_for_wallet_and_password(wallet_path: Optional[str] = None) -> tuple[Account, str]:
    """
    Prompt user to select a wallet and enter password.
    
    Args:
        wallet_path (Optional[str]): Wallet path.
        
    Returns:
        tuple[Account, str]: (unlocked_account, wallet_name)
    """
    wallets = list_wallets(wallet_path)
    
    if not wallets:
        print("No wallets found. Creating a new wallet...")
        name = input("Enter wallet name: ")
        password = getpass.getpass("Enter password: ")
        wallet_info = create_wallet(name, password, wallet_path)
        account = unlock_wallet(name, wallet_path)
        return account, name
    
    print("Available wallets:")
    for i, wallet in enumerate(wallets):
        print(f"  {i+1}. {wallet['name']}: {wallet['address']}")
    
    while True:
        try:
            choice = input(f"Select wallet (1-{len(wallets)}) or 'new' to create: ")
            if choice.lower() == 'new':
                name = input("Enter wallet name: ")
                password = getpass.getpass("Enter password: ")
                wallet_info = create_wallet(name, password, wallet_path)
                account = unlock_wallet(name, wallet_path)
                return account, name
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(wallets):
                    wallet = wallets[idx]
                    password = getpass.getpass(f"Enter password for {wallet['name']}: ")
                    account = unlock_wallet(wallet['name'], wallet_path)
                    return account, wallet['name']
                else:
                    print("Invalid choice. Please try again.")
        except (ValueError, IndexError):
            print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Failed to unlock wallet: {e}")
            print("Please try again.")
