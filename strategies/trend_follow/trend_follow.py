import logging
import math
import time

from core.enums.order_type_enum import OrderTypeEnum
from core.enums.position_state_enum import PositionStateEnum
from core.enums.side_enum import SideEnum
from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient
from core.models.market_data_dict import MarketDataDict
from core.models.position_config_dict import PositionConfigDict
from core.models.trigger_order_config_dict import TriggerOrderConfigDict
from core.models.wallet_dict import WalletDict
from core.stock.crypto_pair_manager import CryptoPairManager
from core.strategy.strategy import Strategy
from core.trading.position_driver import PositionDriver
from tools.utils import format_ticker_raw_data, format_wallet_raw_data, format_market_raw_data

MARKET = "BTC-PERP"
POSITION_MAX_OPEN_DURATION = 600  # Position max open duration
POSITION_MAX_PRICE = 100  # Position max price

# Open order tp and sl amplitude will be this times less and more than last candle amplitude (high - low)
AMPLITUDE_FACTOR_BASED_ON_LAST_CANDLE = 1

AMPLITUDE_MIN_VALUE = 15  # Minimum value of the amplitude between pos and upper / lower bound of tp / sl

# TODO: update position driver to delay trigger order when main position is a limit one
POSITION_ASK_BID_PRICE_DELTA = 5  # Try to get a maker order by placing an offset price


class TrendFollow(Strategy):
    """High frequency trading"""

    def __init__(self):
        """The High frequency trading strategy constructor"""

        logging.info("HighFrequencyTrading run strategy")
        super(TrendFollow, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.ftx_ws_client: FtxWebsocketClient = FtxWebsocketClient()
        self.ftx_ws_client.connect()

        # Init stock acquisition / or / position driver
        self.btc_manager: CryptoPairManager = CryptoPairManager(MARKET, self.ftx_rest_api)
        self.btc_manager.add_time_frame(15)
        self.btc_manager.start_all_time_frame_acq()
        self.position_driver: PositionDriver = PositionDriver(self.ftx_rest_api, 10)

        # Init loop vars
        self.current_position_side = SideEnum.BUY
        self.last_wallet_usd_value = 0
        self.last_position_successful = True
        self.last_position_state = PositionStateEnum.NOT_OPENED

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        try:
            # Get last ticker price
            ticker_response = self.ftx_ws_client.get_ticker(MARKET)
            ticker_price = format_ticker_raw_data(ticker_response)

            # Check the position driver isn't currently running a position
            if self.position_driver.position_state == PositionStateEnum.OPENED:
                self.last_position_state = PositionStateEnum.OPENED
                return

            # The position driver just finished
            if self.last_position_state == PositionStateEnum.OPENED:
                self.last_position_state = PositionStateEnum.NOT_OPENED

                # Get account available balance
                response = self.ftx_rest_api.get("wallet/balances")
                wallets = [format_wallet_raw_data(wallet) for wallet in response if
                           wallet["coin"] == 'USD']

                # Check that last position was profitable
                self.last_position_successful = wallets[0]["usd_value"] > self.last_wallet_usd_value
                self.last_wallet_usd_value = wallets[0]["usd_value"]

                # Keep or reverse the position side based on last trade
                self.current_position_side = self.current_position_side if self.last_position_successful \
                    else SideEnum.BUY if self.current_position_side is SideEnum.SELL else SideEnum.SELL

            # Get account available balance
            response = self.ftx_rest_api.get("wallet/balances")
            wallets = [format_wallet_raw_data(wallet) for wallet in response if
                       wallet["coin"] == 'USD' and wallet["free"] >= 10]

            # Wallet doesn't contain at least 10 USD
            if len(wallets) != 1:
                logging.info(f"Wallet USD collateral too low")
                return

            wallet: WalletDict = wallets[0]
            position_price = min(math.floor(wallet["free"]), POSITION_MAX_PRICE)

            # Retrieve market data
            logging.info("Retrieving market price")
            response = self.ftx_rest_api.get(f"markets/{MARKET}")
            logging.info(f"FTX API response: {str(response)}")

            market_data: MarketDataDict = format_market_raw_data(response)

            # Ticker ask is not always filled. Use market data in this case
            ask = None
            bid = None

            if ticker_price is None:
                logging.warning(f"Ticker was empty, using stock data instead")
                ask = market_data["ask"]
                bid = market_data["bid"]
            else:
                ask = ticker_price["ask"]
                bid = ticker_price["bid"]

            pair_price = ask if self.current_position_side == SideEnum.BUY else bid

            position_size = position_price / pair_price - position_price / pair_price % market_data["size_increment"]

            # Compute position amplitude
            last_candle = self.btc_manager.get_time_frame(15).stock_data_manager.stock_data_list[-1]
            amplitude = max((last_candle.high_price - last_candle.low_price) / AMPLITUDE_FACTOR_BASED_ON_LAST_CANDLE,
                            AMPLITUDE_MIN_VALUE)

            # TODO
            # Compute a price velocity indicator based on ticker average percentage price variation per second
            # Weight the position amplitude based on last candle with the current velocity indicator

            # Configure position settings

            openings = [{
                "price": None,
                "size": position_size,
                "type": OrderTypeEnum.MARKET
            }]

            u_bound = market_data["ask"] + amplitude  # Upper bound
            l_bound = market_data["ask"] - amplitude  # Lower bound

            tp: TriggerOrderConfigDict = {
                "size": position_size,
                "type": TriggerOrderTypeEnum.TAKE_PROFIT,
                "reduce_only": True,
                "trigger_price": u_bound if self.current_position_side == SideEnum.BUY else l_bound,
                "order_price": None,
                "trail_value": None
            }

            sl: TriggerOrderConfigDict = {
                "size": position_size,
                "type": TriggerOrderTypeEnum.STOP,
                "reduce_only": True,
                "trigger_price": l_bound if self.current_position_side == SideEnum.BUY else u_bound,
                "order_price": None,
                "trail_value": None
            }

            position_config: PositionConfigDict = {
                "openings": openings,
                "trigger_orders": [tp, sl],
                "max_open_duration": POSITION_MAX_OPEN_DURATION
            }

            self.position_driver.open_position("BTC-PERP", self.current_position_side, position_config)
        except Exception as e:
            logging.error(e)

    def after_loop(self) -> None:
        time.sleep(5)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("HighFrequencyTrading cleanup")
