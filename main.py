import requests
import time
import json
from threading import Thread
from colorama import init, Fore, Style
import logging
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

# Configurable API URLs and logging settings
API_URL_GET_POINTS = 'https://www.aeropres.in/api/atom/v1/userreferral/getpoint'
API_URL_KEEP_ALIVE = 'https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive'

# Load configurable timeout from config
TIMEOUT = 5  # default timeout

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(message)s')

def load_config():
    with open('config.json') as config_file:
        config = json.load(config_file)
        global TIMEOUT
        TIMEOUT = config.get('timeout', TIMEOUT)  # Allow configurable timeout
        return config

def load_accounts():
    with open('accounts.json') as accounts_file:
        return json.load(accounts_file)

def load_proxies():
    with open('proxy.json') as proxy_file:
        raw_proxies = json.load(proxy_file)
    return [parse_proxy(proxy) for proxy in raw_proxies if parse_proxy(proxy) is not None]

def parse_proxy(proxy_str):
    try:
        scheme, address = proxy_str.split("://")
        ip, port, username, password = address.split(":")
        return {
            "scheme": scheme,
            "ip": ip,
            "port": int(port),
            "username": username,
            "password": password
        }
    except ValueError:
        logging.error(f"Invalid proxy format: {proxy_str}")
        return None

def check_proxy(proxy):
    proxy_url = f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }
    try:
        response = requests.get("http://ip-api.com/json", proxies=proxies, timeout=TIMEOUT)
        response.raise_for_status()  # Raise error for bad responses
        logging.info(f"Proxy working: {proxy['ip']}:{proxy['port']}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Proxy check failed: {e}")
        return False

def keep_alive(account, proxy=None, retries=3):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': account['authorization'],
        'content-type': 'application/json',
    }
    payload = {
        "username": account['email'],
        "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
        "numberoftabs": 0,
        "_v": "1.0.9"
    }
    proxy_dict = {
        "http": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
        "https": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
    }
    for attempt in range(retries):
        try:
            response = requests.post(API_URL_KEEP_ALIVE, headers=headers, json=payload, proxies=proxy_dict, timeout=TIMEOUT)
            response.raise_for_status()
            logging.info(f"Keep alive recorded for {account['name']} | Proxy = {proxy['ip']}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Keep alive failed on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return False

def process_account(account, proxy):
    while True:
        if keep_alive(account, proxy):
            time.sleep(121)  # Sleep for 121 seconds
        else:
            logging.error(f"Keep alive failed for {account['name']} | Proxy = {proxy['ip']}")

def main():
    load_config()
    accounts = load_accounts()
    proxies = load_proxies()
    
    # Improved logging
    logging.info(f"Total Accounts: {len(accounts)} | Total Proxies: {len(proxies)}")
    
    # Bind proxies to accounts and start threads
    account_proxies = bind_proxy_to_accounts(accounts, proxies)
    
    if len(account_proxies) < len(accounts):
        logging.error("Unable to bind a proxy to every account. Exiting...")
        return

    threads = []
    for account_index, account in enumerate(accounts):
        proxy = account_proxies.get(account_index)
        if proxy:
            thread = Thread(target=process_account, args=(account, proxy))
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    print(Fore.CYAN + "+--------------------------------------------------+")
    print(Fore.CYAN + "| " + Fore.WHITE + "   The Dawn Validator Bot                        " + Fore.CYAN + "|")
    print(Fore.CYAN + "| " + Fore.WHITE + "           v1.0.0                                " + Fore.CYAN + "|")
    print(Fore.CYAN + "| " + Fore.WHITE + "   https://github.com/MrTimonM                   " + Fore.CYAN + "|")
    print(Fore.CYAN + "+--------------------------------------------------+")
    
    choice = input("Enter your choice (1 to start, 2 to exit): ")
    if choice == "1":
        main()
    elif choice == "2":
        print(Fore.YELLOW + "Exiting... Goodbye! :D")
    else:
        print(Fore.RED + "Invalid choice. Exiting...")
