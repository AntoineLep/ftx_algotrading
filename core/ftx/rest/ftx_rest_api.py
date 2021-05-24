import hmac
import logging
import threading
import time
import urllib.parse
from typing import Optional, Dict, Any

from requests import Request, Session, Response

import config.private.ftx_config as ftx_config
from exceptions.ftx_rest_api_exception import FtxRestApiException

api = {
    'public': {
        'get': [
            'coins',
            'markets',
            'markets/{market_name}',
            'markets/{market_name}/orderbook',  # ?depth={depth}
            'markets/{market_name}/trades',  # ?limit={limit}&start_time={start_time}&end_time={end_time}
            'markets/{market_name}/candles',
            # ?resolution={resolution}&limit={limit}&start_time={start_time}&end_time={end_time}
            # futures
            'futures',
            'futures/{future_name}',
            'futures/{future_name}/stats',
            'funding_rates',
            'indexes/{index_name}/weights',
            'expired_futures',
            'indexes/{market_name}/candles',
            # ?resolution={resolution}&limit={limit}&start_time={start_time}&end_time={end_time}
            # leverage tokens
            'lt/tokens',
            'lt/{token_name}',
            # options
            'options/requests',
            'options/trades',
            'stats/24h_options_volume',
            'options/historical_volumes/BTC',
            'options/open_interest/BTC',
            'options/historical_open_interest/BTC',
        ],
    },
    'private': {
        'get': [
            'account',
            'positions',
            'wallet/coins',
            'wallet/balances',
            'wallet/all_balances',
            'wallet/deposit_address/{coin}',  # ?method={method}
            'wallet/deposits',
            'wallet/withdrawals',
            'wallet/withdrawal_fee',
            'wallet/airdrops',
            'wallet/saved_addresses',
            'orders',  # ?market={market}
            'orders/history',  # ?market={market}
            'orders/{order_id}',
            'orders/by_client_id/{client_order_id}',
            'conditional_orders',  # ?market={market}
            'conditional_orders/{conditional_order_id}/triggers',
            'conditional_orders/history',  # ?market={market}
            'spot_margin/borrow_rates',
            'spot_margin/lending_rates',
            'spot_margin/borrow_summary',
            'spot_margin/market_info',  # ?market={market}
            'spot_margin/borrow_history',
            'spot_margin/lending_history',
            'spot_margin/offers',
            'spot_margin/lending_info',
            'fills',  # ?market={market}
            'funding_payments',
            # leverage tokens
            'lt/balances',
            'lt/creations',
            'lt/redemptions',
            # subaccounts
            'subaccounts',
            'subaccounts/{nickname}/balances',
            # otc
            'otc/quotes/{quoteId}',
            # options
            'options/my_requests',
            'options/requests/{request_id}/quotes',
            'options/my_quotes',
            'options/account_info',
            'options/positions',
            'options/fills',
            # staking
            'staking/stakes',
            'staking/unstake_requests',
            'staking/balances',
            'staking/staking_rewards',
        ],
        'post': [
            'account/leverage',
            'wallet/withdrawals',
            'wallet/saved_addresses',
            'orders',
            'conditional_orders',
            'orders/{order_id}/modify',
            'orders/by_client_id/{client_order_id}/modify',
            'conditional_orders/{order_id}/modify',
            # spot margin
            'spot_margin/offers',
            # leverage tokens
            'lt/{token_name}/create',
            'lt/{token_name}/redeem',
            # subaccounts
            'subaccounts',
            'subaccounts/update_name',
            'subaccounts/transfer',
            # otc
            'otc/quotes/{quote_id}/accept',
            'otc/quotes',
            # options
            'options/requests',
            'options/requests/{request_id}/quotes',
            'options/quotes/{quote_id}/accept',
            # staking
            'staking/unstake_requests',
            'srm_stakes/stakes',
        ],
        'delete': [
            'wallet/saved_addresses/{saved_address_id}',
            'orders/{order_id}',
            'orders/by_client_id/{client_order_id}',
            'orders',
            'conditional_orders/{order_id}',
            # subaccounts
            'subaccounts',
            # options
            'options/requests/{request_id}',
            'options/quotes/{quote_id}',
            # staking
            'staking/unstake_requests/{request_id}',
        ],
    }
}


class FtxRestApi(object):
    _ENDPOINT = ftx_config.rest_endpoint
    _LOCK: threading.Lock = threading.Lock()

    def __init__(self):
        self._session = Session()
        self._api_key = ftx_config.api['key']
        self._api_secret = ftx_config.api['secret']
        self._api_sub_account = ftx_config.api['sub_account']

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        with FtxRestApi._LOCK:
            request = Request(method, FtxRestApi._ENDPOINT + path, **kwargs)
            if self._api_key:
                self._sign_request(request)
            response = self._session.send(request.prepare())

            return FtxRestApi._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._api_sub_account:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._api_sub_account)

    @staticmethod
    def _process_response(response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise FtxRestApiException(data['error'])
            return data['result']
