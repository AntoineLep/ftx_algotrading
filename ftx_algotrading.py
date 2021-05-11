import os
import logging
import config.application_config as application_config
from tools.custom_logging import init_logger

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

    try:
        strategy = application_config.strategy
        strategy.run()
    except KeyboardInterrupt:
        logging.info("/!\\ Keyboard interruption: Stopping %s V%s" % (application_config.name,
                                                                      application_config.version))
    finally:
        pass
