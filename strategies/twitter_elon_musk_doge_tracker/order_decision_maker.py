import logging

from core.enums.color_enum import ColorEnum
from core.stock.stock_data_manager import StockDataManager
from strategies.twitter_elon_musk_doge_tracker.enums.probability_enum import ProbabilityEnum

PROBABLE_VOLUME_FACTOR_TRIGGER = 4
MAYBE_PROBABLE_VOLUME_FACTOR_TRIGGER = 5
UNKNOWN_PROBABILITY_VOLUME_FACTOR_TRIGGER = 6
NOT_PROBABLE_VOLUME_FACTOR_TRIGGER = 60


class OrderDecisionMaker(object):
    """Order decision maker"""

    def __init__(self, stock_data_manager: StockDataManager):
        """
        Order decision maker constructor

        :param stock_data_manager: Instance of the stock data manager to use
        """
        self.stock_data_manager: StockDataManager = stock_data_manager

    def decide(self, external_factor_probability: ProbabilityEnum) -> bool:
        """
        Decide if yes or no, a position has to be made

        :param: external_factor_probability: External factor probability
        :return: A boolean value to tells if yes or no a position has to be made
        """
        return False
        volume_check_depth = 50

        if external_factor_probability == ProbabilityEnum.NO_DOUBT:
            logging.info("The decision maker is confident concerning the future of DOGE. Decision made !")
            return True
        else:
            volume_check_factor_size = PROBABLE_VOLUME_FACTOR_TRIGGER \
                if external_factor_probability == ProbabilityEnum.PROBABLE \
                else MAYBE_PROBABLE_VOLUME_FACTOR_TRIGGER \
                if external_factor_probability == ProbabilityEnum.MAYBE_PROBABLE \
                else NOT_PROBABLE_VOLUME_FACTOR_TRIGGER \
                if external_factor_probability == ProbabilityEnum.NOT_PROBABLE \
                else UNKNOWN_PROBABILITY_VOLUME_FACTOR_TRIGGER

            logging.info("The decision maker needs to verify with volumes.")

            if len(self.stock_data_manager.stock_data_list) > volume_check_depth:
                # Check last volume is volume_check_factor_size times more than the average 20 data candles
                sum_volume = sum([d.volume for d in self.stock_data_manager.stock_data_list[-volume_check_depth:]])
                avg_volume = sum_volume / volume_check_depth
                last_data_candle = self.stock_data_manager.stock_data_list[-1]

                logging.info(f"Volume ratio is {last_data_candle.volume / avg_volume} out of "
                             f"{volume_check_factor_size}. Trend is "
                             f"{'upward' if last_data_candle.get_color() == ColorEnum.GREEN else 'downward'}")

                volumes_factor_reached = last_data_candle.volume / avg_volume > volume_check_factor_size and \
                    last_data_candle.get_color() == ColorEnum.GREEN

                if volumes_factor_reached:
                    logging.info(
                        f"Last volume is at least {volume_check_factor_size} times more than the average 20 data "
                        f"points and the last data candle is green. Decision made !")

                return volumes_factor_reached
            else:
                logging.info("The decision maker is still uncertain about the future of DOGE")
                return False
