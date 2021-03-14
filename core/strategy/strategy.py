class Strategy(object):
    """Base class for strategies"""

    def __init__(self):
        """Strategy constructor"""
        self._crypto_pair_manager_list = None
        self._lock = None
        self._k = None
        self._call_rate_manager = None

    def run(self) -> None:
        """Run the strategy"""
        try:
            self.startup()
            self.run_strategy()
        except Exception:
            self.cleanup()
            raise

        self.cleanup()

    def startup(self) -> None:
        """Method called at the beginning of the strategy execution"""
        raise NotImplementedError("startup method must be override")

    def run_strategy(self) -> None:
        """Method in which is performed the strategy logic"""
        raise NotImplementedError("run_strategy method must be override")

    def cleanup(self) -> None:
        """Method called at the end of the strategy execution"""
        raise NotImplementedError("cleanup method must be override")
