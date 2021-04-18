import logging
from strategies.twitter_elon_musk_doge_tracker.enums.probability_enum import ProbabilityEnum
from core.sotck.stock_data_manager import StockDataManager

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

        if external_factor_probability == ProbabilityEnum.PROBABLE:
            return True
        else:
            volume_check_factor_size = 3 if external_factor_probability == ProbabilityEnum.MAYBE_PROBABLE else 5
            if self.stock_data_manager.stock_data_list:
                pass
