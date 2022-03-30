import logging
import math
import time
from typing import Optional

from core.enums.order_type_enum import OrderTypeEnum
from core.enums.side_enum import SideEnum
from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum
from core.models.market_data_dict import MarketDataDict
from core.models.position_config_dict import PositionConfigDict
from core.models.trigger_order_config_dict import TriggerOrderConfigDict
from core.models.wallet_dict import WalletDict
from core.strategy.strategy import Strategy
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.trading.position_driver import PositionDriver
from tools.utils import format_wallet_raw_data, format_market_raw_data


class BestStrategyEver(Strategy):
    """The best strategy ever"""

    def __init__(self):
        """The best strategy ever constructor"""

        logging.info("BestStrategyEver run strategy")
        super(BestStrategyEver, self).__init__()

        self.ftx_ws_client: FtxWebsocketClient = FtxWebsocketClient()
        self.ftx_ws_client.connect()
        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.position_driver: Optional[PositionDriver] = None
        self.opened: bool = False

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        # logging.info(self.ftx_ws_client.get_ticker('DOGE-PERP'))

        # response = self.ftx_rest_api.get(f"markets/DOGE-PERP")
        # logging.info(f"FTX API response: {str(response)}")

        # logging.info("Retrieving orders")
        # response = self.ftx_rest_api.get("orders", {"market": "DOGE-PERP"})
        # logging.info(f"FTX API response: {str(response)}")

        if self.opened:
            return

        pair_to_track = "DOGE-PERP"
        self.position_driver = PositionDriver(self.ftx_rest_api, 30)

        response = self.ftx_rest_api.get("wallet/balances")
        wallets = [format_wallet_raw_data(wallet) for wallet in response if
                   wallet["coin"] == 'USD' and wallet["free"] >= 10]

        if len(wallets) != 1:
            logging.info(f"Market:{pair_to_track}, Can't open a position :/. Wallet USD collateral low")
            return

        wallet: WalletDict = wallets[0]
        position_price = math.floor(wallet["free"]) * 1 / 10

        # Retrieve market data
        logging.info("Retrieving market price")
        response = self.ftx_rest_api.get(f"markets/{pair_to_track}")
        logging.info(f"FTX API response: {str(response)}")

        market_data: MarketDataDict = format_market_raw_data(response)

        position_size = math.floor(position_price / response["ask"]) - \
            math.floor(position_price / response["ask"]) % market_data["sizeIncrement"]

        # Configure position settings

        openings = [{
            "price": None,
            "size": position_size,
            "type": OrderTypeEnum.MARKET
        }]

        trailing_stop: TriggerOrderConfigDict = {
            "size": position_size,
            "type": TriggerOrderTypeEnum.TRAILING_STOP,
            "reduce_only": True,
            "trigger_price": None,
            "order_price": None,
            "trail_value": response["ask"] * 8 / 100 * -1  # 8% trail
        }

        position_config: PositionConfigDict = {
            "openings": openings,
            "trigger_orders": [trailing_stop],
            "max_open_duration": 120
        }

        self.position_driver.open_position(pair_to_track, SideEnum.BUY, position_config)
        self.opened = True

    def after_loop(self) -> None:
        time.sleep(10)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("BestStratEver cleanup")
