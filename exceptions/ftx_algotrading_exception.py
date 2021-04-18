class FtxAlgotradingException(Exception):
    """Generic exception for ftx_algotrading"""

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return "/!\\ FTX ALGOTRADING EXCEPTION: " + self.message
