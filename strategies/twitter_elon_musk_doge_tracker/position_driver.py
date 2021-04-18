import logging


class PositionDriver(object):
    """Position driver"""

    def __init__(self, ftx_rest_api):
        """
        Position driver constructor

        :param ftx_rest_api: Instance of FtxRestApi
        :type ftx_rest_api: core.ftx.rest.ftx_rest_api.FtxRestApi
        """
        self.ftx_rest_api = ftx_rest_api
        self.drive_available = False
        logging.debug(f"New position driver created!")

    def open_position(self):
        pass
