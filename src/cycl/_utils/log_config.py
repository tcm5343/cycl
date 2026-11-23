import logging


def configure_log(level: int) -> None:
    log_format = '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d: %(message)s'
    logging.basicConfig(level=level, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
