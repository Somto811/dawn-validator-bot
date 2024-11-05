import json
import requests
from threading import Thread

API_URL_GET_POINTS = "YOUR_API_URL_GET_POINTS"
API_URL_KEEP_ALIVE = "YOUR_API_URL_KEEP_ALIVE"

def load_config():
    with open('config.json') as config_file:
        config = json.load(config_file)
    return config

def load_accounts():
    # Your implementation to load accounts
    pass

def load_proxies():
    # Your implementation to load proxies
    pass

def bind_proxy_to_accounts(accounts, proxies):
    # Your implementation for binding proxies to accounts
    pass

def get_points(account, proxy=None, timeout=10):
    headers = {
        'accept': '*/*',
        'authorization': account['authorization'],
        # other headers...
    }
    proxy_dict = {
        "http": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
        "https": f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
    }
    response = requests.get(API_URL_GET_POINTS, headers=headers, proxies=proxy_dict, verify=False, timeout=timeout)
    # Process the response...

def keep_alive(account, proxy=None, retries=3, timeout=10):
    headers = {
        'accept': '*/*',
        'authorization': account['authorization'],
        # other headers...
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
        response = requests.post(API_URL_KEEP_ALIVE, headers=headers, json=payload, proxies=proxy_dict, verify=False, timeout=timeout)
        # Process the response...

def process_account(account, proxy, timeout):
    get_points(account, proxy, timeout)
    keep_alive(account, proxy, timeout=timeout)

def main():
    config = load_config()
    accounts = load_accounts()
    proxies = load_proxies()
    timeout = config.get("timeout", 10)  # Get the timeout value

    account_proxies = bind_proxy_to_accounts(accounts, proxies)

    # Start threads for processing each account
    for account_index, account in enumerate(accounts):
        proxy = account_proxies.get(account_index)
        if proxy:
            thread = Thread(target=process_account, args=(account, proxy, timeout))
            thread.start()

if __name__ == "__main__":
    main()
