import logging

from core.sotck.stock_data_manager import StockDataManager
from strategies.twitter_elon_musk_doge_tracker.enums.probability_enum import ProbabilityEnum


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
        volume_check_depth = 20

        if external_factor_probability == ProbabilityEnum.PROBABLE:
            logging.info("The decision maker is confident concerning the future of DOGE. Decision made !")
            return True
        else:
            volume_check_factor_size = 3 if external_factor_probability == ProbabilityEnum.MAYBE_PROBABLE else 5

            logging.info("The decision maker needs to verify with volumes.")

            if len(self.stock_data_manager.stock_data_list) > volume_check_depth:
                # Check last volume is volume_check_factor_size times more than the average 20 data points
                sum_volume = sum([d.volume for d in self.stock_data_manager.stock_data_list[-volume_check_depth:]])
                avg_volume = sum_volume / volume_check_depth
                last_data_point = self.stock_data_manager.stock_data_list[-1]

                logging.info(f"Volume ratio is {last_data_point.volume / avg_volume} out of {volume_check_factor_size}")

                volumes_factor_reached = last_data_point.volume / avg_volume > volume_check_factor_size and \
                    last_data_point.open_price < last_data_point.close_price

                if volumes_factor_reached:
                    logging.info(
                        f"Last volume is at least {volume_check_factor_size} times more than the average 20 data "
                        f"points. Decision made !")

                return volumes_factor_reached
            else:
                logging.info("The decision maker is still uncertain about the future of DOGE")
                return False
