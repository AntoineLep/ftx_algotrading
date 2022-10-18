import logging
import time

from core.strategy.strategy import Strategy
from core.ftx.rest.ftx_rest_api import FtxRestApi

# Trading pair to snipe
MARKET_PAIR_TO_SNIPE = "APT/USD"

# USD amount to invest on the coin to be listed
# /!\ Make sure your wallet have more (twice is good) than this amount because due to the high demand,
# the order fill price can be higher than the computed one based on last stock data
AMOUNT_TO_INVEST = 2000

MAX_ASK_PRICE = 50  # If the price is already above MAX_ASK_PRICE, the sniping will be aborted

# First take profit
TP1_TARGET_PERCENTAGE = 500
TP1_SIZE_RATIO = 0.3

# Second take profit
TP2_TARGET_PERCENTAGE = 1200
TP2_SIZE_RATIO = 0.4

# Last take profit
TP3_TARGET_PERCENTAGE = 2000
# TP3_SIZE_RATIO Will be filled with remaining position size

# Stop loss
SL_PERCENTAGE = 20


class ListingSniper(Strategy):
    """Listing Sniper"""

    def __init__(self):
        """The listing sniper strategy constructor"""

        logging.info("ListingSniper run strategy")
        super(ListingSniper, self).__init__()

        self._sniped = False
        self.ftx_rest_api: FtxRestApi = FtxRestApi()

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        if self._sniped:
            return

        try:
            m_response = self.ftx_rest_api.get("markets/" + MARKET_PAIR_TO_SNIPE)
            logging.info(f"FTX API response: {str(m_response)}")

            market_enabled = m_response["enabled"]
            logging.info(f"market enabled: {str(market_enabled)}")

            if market_enabled is False:
                raise Exception(f"Market {MARKET_PAIR_TO_SNIPE} is not yet enabled")

            order_size = (AMOUNT_TO_INVEST / m_response["ask"]) - \
                         (AMOUNT_TO_INVEST / m_response["ask"]) % m_response["sizeIncrement"]

            logging.info(f"Order param: {str(order_size)}")

            if order_size < m_response["minProvideSize"]:
                raise Exception(f"Order computed size {order_size} is less than the minimum size "
                                f"{m_response['minProvideSize']}")

            if m_response["ask"] is not None and m_response["ask"] > MAX_ASK_PRICE:
                self._sniped = True
                logging.info(f"Sniping Aborted (price pumped too much) !")
                return

            opening_order_params = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "buy",
                "price": None,
                "type": "market",
                "size": order_size,
                "ioc": False
            }

            logging.info(f"Opening order param: {str(opening_order_params)}")

            try:
                logging.info(f"Opening position: {str(opening_order_params)}")
                response = self.ftx_rest_api.post("orders", opening_order_params)
                logging.info(f"FTX API response: {str(response)}")

                self._sniped = True
                logging.info(f"Sniping done !")
            except Exception as e:
                logging.error("An error occurred when opening position:")
                logging.error(e)
                raise

            tp1 = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "sell",
                "size": (order_size * TP1_SIZE_RATIO) - (order_size * TP1_SIZE_RATIO) % m_response["sizeIncrement"],
                "type": "takeProfit",
                "reduceOnly": True,
                "triggerPrice": m_response["ask"] + m_response["ask"] * TP1_TARGET_PERCENTAGE / 100,
                "order_price": None,
                "trail_value": None
            }

            tp2 = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "sell",
                "size": (order_size * TP2_SIZE_RATIO) - (order_size * TP2_SIZE_RATIO) % m_response["sizeIncrement"],
                "type": "takeProfit",
                "reduceOnly": True,
                "triggerPrice": m_response["ask"] + m_response["ask"] * TP2_TARGET_PERCENTAGE / 100,
                "order_price": None,
                "trail_value": None
            }

            tp3 = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "sell",
                "size": order_size - tp1["size"] - tp2["size"],
                "type": "takeProfit",
                "reduceOnly": True,
                "triggerPrice": m_response["ask"] + m_response["ask"] * TP3_TARGET_PERCENTAGE / 100,
                "order_price": None,
                "trail_value": None
            }

            sl = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "sell",
                "size": order_size,
                "type": "stop",
                "reduceOnly": True,
                "triggerPrice": m_response["ask"] - m_response["ask"] * SL_PERCENTAGE / 100,
                "order_price": None,
                "trail_value": None
            }

            for trigger_order in [tp1, tp2, tp3, sl]:
                try:
                    logging.info(f"Opening trigger order: {str(trigger_order)}")
                    co_response = self.ftx_rest_api.post("conditional_orders", trigger_order)
                    logging.info(f"FTX API response: {str(co_response)}")
                except Exception as e:
                    logging.error("An error occurred when opening position:")
                    logging.error(e)

                time.sleep(0.25)

        except Exception as e:
            logging.error(e)

    def after_loop(self) -> None:
        time.sleep(10)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("ListingSniper cleanup")
