import os
import logging
import config.applicationconfig as application_config
from tools.customlogging import init_logger

if __name__ == '__main__':
    init_logger(
        log_level=application_config.log["level"],
        log_location=os.path.join(application_config.path, application_config.log["path"]),
        app_name=application_config.name
    )

    logging.info("---------------")
    logging.info("%s V%s" % (application_config.name, application_config.version))
    logging.info("---------------")
