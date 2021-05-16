import logging


class Strategy(object):
    """Base class for strategies"""

    def __init__(self):
        """Strategy constructor"""

    def run(self) -> None:
        """Run the strategy"""
        try:
            while True:
                self.before_loop()
                self.loop()
                self.after_loop()
        except Exception as e:
            logging.info("An error occurred when running strategy")
            logging.info(e)
            self.cleanup()
            raise

    def before_loop(self) -> None:
        """Method called before the loop"""
        raise NotImplementedError("before_loop method must be override")

    def loop(self) -> None:
        """Method in which is performed the strategy logic"""
        raise NotImplementedError("loop method must be override")

    def after_loop(self) -> None:
        """Method called after the loop"""
        raise NotImplementedError("before_loop method must be override")

    def cleanup(self) -> None:
        """Method called at the end of the strategy execution"""
        raise NotImplementedError("cleanup method must be override")
