class Strategy(object):
    """Base class for strategies"""

    def __init__(self):
        """Strategy constructor"""

        self.ftx_ws_client = None
        """
        The ftx web socket client
        :type: core.ws.ftxwebsocketclient.FtxWebsocketClient
        """

    def set_ftx_ws_client(self, ftx_ws_client) -> None:
        """
        Set the ftx web socket client
        :param ftx_ws_client: The ftx web socket client
        """
        self.ftx_ws_client = ftx_ws_client

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
