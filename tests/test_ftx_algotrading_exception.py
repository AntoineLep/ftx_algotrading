import unittest

from exceptions.FtxAlgotradingException import FtxAlgotradingException


class TestFtxAlgotradingException(unittest.TestCase):
    """Test FtxAlgotradingException"""

    class ExceptionRaiser(object):
        """Exception raiser"""

        @staticmethod
        def raise_ftx_algotrading_exception(ex):
            """Raise the exception passed in parameter"""
            raise ex

    def test_ftx_algotrading_exception_raise(self):
        """Test that we can raise an FtxAlgotradingException"""
        self.assertRaises(
            FtxAlgotradingException,
            self.ExceptionRaiser.raise_ftx_algotrading_exception,
            FtxAlgotradingException("Error")
        )
