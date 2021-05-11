from core.enums.color_enum import ColorEnum
from core.models.identified_candle import IdentifiedCandle


class Candle(IdentifiedCandle):
    """Candle"""

    def __init__(self, identifier: int, time: int, open_price: float, high_price: float, low_price: float,
                 close_price: float, volume: float) -> None:
        """
        Candle constructor

        :param identifier: Unique identifier of data candle (in timestamp)
        :param time: Time of the data candle
        :param open_price: Open price of the candle
        :param high_price: Highest price of the candle
        :param low_price: Lowest price of the candle
        :param close_price: Close price of the candle
        :param volume: Volume from of the candle
        """
        super(Candle, self).__init__(identifier)
        self.time = time
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume

    def get_color(self) -> ColorEnum:
        """
        Determine the color of the candle

        :return: The color of the candle
        :rtype: ColorEnum
        """
        return ColorEnum.GREEN if self.open_price < self.close_price else ColorEnum.RED

    def is_hammer_or_hanging_man(self) -> bool:
        """
        Tells if the candle is a hammer or an hanging man or not

        :return: True if the candle is a hammer or an hanging man, False otherwise
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
        Tells if the candle is a reversed hammer or a falling star or not

        :return: True if the candle is a reversed hammer or a falling star, False otherwise
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
        Tells if thecandle is swallowing the previous candle

        :param previous: The previous candle
        :return: True if the candle is swallowing the previous candle, False otherwise
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
        Tells if the candle is an harami or not

        :param previous: The previous candle
        :return: True if the candle is an harami, False otherwise
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
