import requests
import time
import json
from threading import Thread
from colorama import init, Fore
import logging
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

API_URL_GET_POINTS = 'https://www.aeropres.in/api/atom/v1/userreferral/getpoint'
API_URL_KEEP_ALIVE = 'https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)

def load_accounts():
    with open('accounts.json') as accounts_file:
        return json.load(accounts_file)

def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

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
        logging.error(f"{get_timestamp()} | ERROR | Invalid proxy format: {proxy_str}")
        return None

def load_proxies():
    with open('proxy.json') as proxy_file:
        raw_proxies = json.load(proxy_file)
    proxies = [parse_proxy(proxy) for proxy in raw_proxies if parse_proxy(proxy) is not None]
    return proxies

def check_proxy(proxy):
    try:
        proxy_url = f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        response = requests.get("http://ip-api.com/json", proxies=proxies, timeout=5)
        if response.status_code == 200:
            logging.info(f"{get_timestamp()} | {Fore.GREEN}SUCCESS{Fore.RESET} | Proxy working: {Fore.BLUE} {proxy['ip']}:{proxy['port']} {Fore.RESET}")
            return True
        else:
            logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | Proxy test failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | Proxy check failed: {e}")
        return False

def bind_proxy_to_accounts(accounts, raw_proxies):
    account_proxies = {}
    available_proxies = raw_proxies.copy()
    for account_index, account in enumerate(accounts):
        for proxy in available_proxies:
            logging.info(f"{get_timestamp()} | {Fore.YELLOW} INFO {Fore.RESET} | Testing Proxy: {proxy['ip']}:{proxy['port']} for [{account['name']}]...")
            if check_proxy(proxy):
                logging.info(f"{get_timestamp()} | {Fore.YELLOW} INFO {Fore.RESET} | Proxy [{proxy['ip']}, {proxy['port']}] bound to [{account['name']}]")
                account_proxies[account_index] = proxy
                available_proxies.remove(proxy)
                break
            else:
                logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | Proxy [{proxy['ip']}:{proxy['port']}] not working, trying next...")
        if account_index not in account_proxies:
            logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | Could not bind a working proxy to [{account['name']}]")
    return account_proxies

def get_points(account, proxy=None):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': account['authorization'],
        'content-type': 'application/json',
        'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    proxy_dict = {
        "http": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
        "https": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
    }
    response = requests.get(API_URL_GET_POINTS, headers=headers, proxies=proxy_dict, verify=False)
    if response.ok:
        data = response.json()
        points = data.get('data', {}).get('rewardPoint', {}).get('points', 'N/A')
        logging.info(f"{get_timestamp()} | {Fore.YELLOW} INFO {Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Points: {Fore.BLUE} {points} {Fore.RESET}")
        return points
    else:
        logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Failed to retrieve points.")
        return None

def keep_alive(account, proxy=None, retries=3):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': account['authorization'],
        'content-type': 'application/json',
        'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
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
        response = requests.post(API_URL_KEEP_ALIVE, headers=headers, json=payload, proxies=proxy_dict, verify=False)
        if response.ok and response.json().get('success'):
            logging.info(f"{get_timestamp()} | {Fore.GREEN}SUCCESS{Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Keep alive recorded")
            return True
        else:
            logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Keep alive failed on attempt {attempt + 1}. Response Code: {response.status_code if response else '502 Bad Gateway'}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return False

def process_account(account, proxy):
    get_points(account, proxy)
    while True:
        if keep_alive(account, proxy):
            logging.info(f"{get_timestamp()} | {Fore.YELLOW} INFO {Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Sleeping for 121 seconds...")
            time.sleep(121)
        else:
            logging.error(f"{get_timestamp()} | {Fore.RED}ERROR{Fore.RESET} | {account['name']} | Proxy = {proxy['ip']} | Keep alive failed, retrying...")

def main():
    config = load_config()
    accounts = load_accounts()
    if accounts is None:
        logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | No accounts loaded. Exiting...")
        return
    
    proxies = load_proxies()
    account_proxies = bind_proxy_to_accounts(accounts, proxies)
    if len(account_proxies) < len(accounts):
        logging.error(f"{get_timestamp()} | {Fore.RED}FAIL{Fore.RESET} | Unable to bind a proxy to every account. Exiting...")
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
    print(Fore.CYAN + "| " + Fore.WHITE + "   https://github.com/Somto811                   " + Fore.CYAN + "|")
    print(Fore
