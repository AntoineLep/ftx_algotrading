class IdentifiedCandle(object):
    """Identified candle"""

    def __init__(self, identifier: int):
        """
        Identified candle constructor

        :param identifier: Candle identifier
        """
        self.identifier = identifier

    def __str__(self):
        return "{identifier: %d}" % self.identifier

    def __hash__(self):
        return self.identifier
