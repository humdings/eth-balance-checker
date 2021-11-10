import os
from requests import Session
from etherscan.tokens import Tokens
import etherscan.accounts as accounts
import json
import pandas as pd

WEI = 1000000000000000000


def get_eth_balances(addresses, api_key):
    if isinstance(addresses, str):
        addresses = [addresses]
    api = accounts.Account(address=addresses, api_key=api_key)
    eth_balances = api.get_balance_multiple()
    df = pd.DataFrame(eth_balances).set_index('account').astype(int)
    return df / WEI


def get_CMC_listings(start=1, limit=1000, convert='USD', api_key=None):
    if api_key is None:
        api_key = os.environ.get('CMC_API_KEY')
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': str(start),
        'limit': str(limit),
        'convert': convert
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }
    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    return pd.DataFrame(data['data']).set_index('symbol')


ETHERSCAN_API_TOKEN = os.environ.get('ETHERSCAN_API_KEY')
CMC_API_KEY = os.environ.get('CMC_API_KEY')

CONTRACTS = {
    'LPT': '0x58b6a8a3302369daec383334672404ee733ab239',
    'POLY': '0x9992ec3cf6a55b00978cddf2b27bc6882d88d1ec',
    'NMR': '0x1776e1F26f98b1A5dF9cD347953a26dd3Cb46671',
}

ADDRESSES = [
    '0xa5DEFF54b63eF019E94a505dD80090FD3ABaA796',  # Works for donations
]

CONVERT_CURRENCY = 'USD'

balances = pd.DataFrame(columns=CONTRACTS.keys(), index=ADDRESSES)
balances.index.name = 'address'

eth_balances = get_eth_balances(ADDRESSES, ETHERSCAN_API_TOKEN)
balances['ETH'] = eth_balances['balance']

for symbol in CONTRACTS:
    api = Tokens(contract_address=CONTRACTS[symbol], api_key=ETHERSCAN_API_TOKEN)
    for address in ADDRESSES:
        balances.loc[address, symbol] = int(api.get_token_balance(address=address)) / WEI

cmc_data = get_CMC_listings(start=1, limit=1000, convert=CONVERT_CURRENCY, api_key=CMC_API_KEY)
cmc_quotes = cmc_data.quote.apply(lambda q: pd.Series(q[CONVERT_CURRENCY]))

values = balances * cmc_quotes.loc[balances.columns, 'price']
account_info = balances.join(values, rsuffix='_value')

for symbol, price in cmc_quotes.loc[balances.columns, 'price'].items():
    account_info[symbol + '_price'] = price

account_info.to_csv('my_eth_tokens.csv')
print(account_info)
