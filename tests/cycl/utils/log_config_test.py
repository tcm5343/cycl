import logging

from cycl.utils.log_config import configure_log


def test_logging_format(caplog):
    configure_log(logging.INFO)

    with caplog.at_level(logging.INFO):
        logging.info('Test log message')

    assert len(caplog.records) > 0

    log_message = caplog.text
    assert 'INFO' in log_message
    assert 'log_config_test.py' in log_message
    assert 'Test log message' in log_message
