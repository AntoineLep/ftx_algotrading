import os
import logging
import config.application_config as application_config
from tools.custom_logging import init_logger

if __name__ == '__main__':
    project_path = os.path.dirname(os.path.realpath(__file__))
    project_name = "ftx_algotrading"
    project_version = "1.0"

    init_logger(
        log_level=application_config.log["level"],
        log_location=os.path.join(project_path, application_config.log["path"]),
        app_name=project_name
    )

    logging.info("---------------")
    logging.info(f"{project_name}, {project_version}")
    logging.info("---------------")

    strategy = application_config.strategy

    try:
        strategy.run()
    except KeyboardInterrupt:
        strategy.cleanup()
        logging.info(f"/!\\ Keyboard interruption: Stopping {project_name} V{project_version}")
    finally:
        pass
