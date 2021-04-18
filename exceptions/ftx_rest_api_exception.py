class FtxRestApiException(Exception):
    """Generic exception for ftx_rest_api"""

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return "/!\\ FTX REST API EXCEPTION: " + self.message
