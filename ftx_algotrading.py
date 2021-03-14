import os
import logging
import config.applicationconfig as application_config
from tools.customlogging import init_logger
from core.ftx.ws.ftxwebsocketclient import FtxWebsocketClient

if __name__ == '__main__':
    project_path = os.path.dirname(os.path.realpath(__file__))

    init_logger(
        log_level=application_config.log["level"],
        log_location=os.path.join(project_path, application_config.log["path"]),
        app_name=application_config.name
    )

    logging.info("---------------")
    logging.info("%s V%s" % (application_config.name, application_config.version))
    logging.info("---------------")

    ws_client = FtxWebsocketClient()
    ws_client.connect()

    try:
        strategy = application_config.strategy
        strategy.set_ftx_ws_client(ws_client)
        strategy.run()
    except KeyboardInterrupt:
        logging.info("/!\\ Keyboard interruption: Stopping %s V%s" % (application_config.name,
                                                                      application_config.version))
    finally:
        pass
