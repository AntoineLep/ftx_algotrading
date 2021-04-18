import logging


class OrderDecisionMaker(object):
    """Order decision maker"""

    def __init__(self, stock_data_manager):
        """
        Order decision maker constructor

        :param stock_data_manager: Instance of StockDataManager
        :type stock_data_manager: core.stock.stock_data_manager.StockDataManager
        """
        self.stock_data_manager = stock_data_manager
        logging.debug(f"New order decision maker created!")

    def decide(self):
        """
        Decide if yes or no, a position has to be made

        :return: A boolean value to tells if yes or no a position has to be made
        :rtype: bool
        """
        pass
