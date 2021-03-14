from core.models.identifiedpoint import IdentifiedPoint
from core.enums.colorenum import ColorEnum


class StockDataPoint(IdentifiedPoint):
    """Stock data point"""

    def __init__(self, identifier, time, open_price, high_price, low_price, close_price, volume) -> None:
        """
        Stock data point constructor

        :param identifier: Unique identifier of data point (in timestamp)
        :type identifier: int
        :param time: Time of the data point
        :type time: int
        :param open_price: Open price of the data point
        :type open_price: float
        :param high_price: Highest price of the data point
        :type high_price: float
        :param low_price: Lowest price of the data point
        :type low_price: float
        :param close_price: Close price of the data point
        :type close_price: float
        :param volume: Volume from of the data point
        :type volume: float
        """
        super(StockDataPoint, self).__init__(identifier)
        self.time = time
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume

    def get_color(self) -> ColorEnum:
        """
        Determine the color of the stock data point

        :return: The color of the stock data point
        :rtype: ColorEnum
        """
        return ColorEnum.GREEN if self.open_price < self.close_price else ColorEnum.RED

    def is_hammer_or_hanging_man(self) -> bool:
        """
        Tells if the stock data point is a hammer or an hanging man or not

        :return: True if the stock data point is a hammer or an hanging man, False otherwise
        :rtype: bool
        """
        high_minus_low = (self.high_price - self.low_price)
        if abs(self.open_price - self.close_price) < high_minus_low / 3:
            lowest_of_open_close = self.open_price if self.open_price < self.close_price else self.close_price
            if self.high_price - lowest_of_open_close < high_minus_low / 3:
                return True
        return False

    def is_reversed_hammer_or_falling_star(self) -> bool:
        """
        Tells if the stock data point is a reversed hammer or a falling star or not

        :return: True if the stock data point is a reversed hammer or a falling star, False otherwise
        :rtype: bool
        """
        high_minus_low = (self.high_price - self.low_price)
        if abs(self.open_price - self.close_price) < high_minus_low / 3:
            highest_of_open_close = self.open_price if self.open_price > self.close_price else self.close_price
            if highest_of_open_close - self.low_price < high_minus_low / 3:
                return True
        return False

    def is_a_swallowing(self, previous) -> bool:
        """
        Tells if the stock data point is swallowing the previous stock data point

        :param previous: The previous stock data point
        :type previous: StockDataPoint
        :return: True if the stock data point is swallowing the previous stock data point, False otherwise
        :rtype: bool
        """
        prev_highest_of_open_close = previous.open_price if previous.open_price > previous.close_price \
            else previous.close_price
        prev_lowest_of_open_close = previous.open_price if previous.open_price < previous.close_price \
            else previous.close_price
        highest_of_open_close = self.open_price if self.open_price > self.close_price else self.close_price
        lowest_of_open_close = self.open_price if self.open_price < self.close_price else self.close_price

        return prev_lowest_of_open_close < lowest_of_open_close < highest_of_open_close < prev_highest_of_open_close

    def is_an_harami(self, previous) -> bool:
        """
        Tells if the stock data point is an harami or not

        :param previous: The previous stock data point
        :type previous: StockDataPoint
        :return: True if the stock data point is an harami, False otherwise
        :rtype: bool
        """
        return previous.is_a_swallowing(self)

    def __str__(self):
        return "{identifier: %d, " \
               "open_price: %f, " \
               "high_price: %f, " \
               "low_price: %f, " \
               "close_price: %f, " \
               "volume: %f, " % \
               (self.identifier,
                self.open_price,
                self.high_price,
                self.low_price,
                self.close_price,
                self.volume)
