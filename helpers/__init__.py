import os
import sys
import json
import types
import signal
import logging
import traceback
from signal import Signals
from logging import Logger
from typing import Callable
from time import strftime, localtime
from pika import BlockingConnection, ConnectionParameters, PlainCredentials

TERMINATE = False
on_terminate: Callable[[], None] = lambda: None
LOG_FORMAT = u'{"source": "%(name)s", "log_level": "%(levelname)s", "timestamp": "%(asctime)s",' \
             u'"message": %(message)s}'


def get_logger(name: str, logger_format: str, hide: tuple = (), logger_level: int = logging.INFO) -> Logger:
    """
    Return logger

    :param name: logger name
    :type name: str
    :param logger_format: logger format
    :type logger_format: str
    :param hide: loggers that should output error messages only
    :type hide: tuple
    :param logger_level: logger level
    :type logger_level: int
    :return: logger
    :rtype: Logger
    """
    time_zone = strftime("%z", localtime())
    logging.basicConfig(stream=sys.stdout, level=logger_level, format=logger_format)
    logging.Formatter.default_msec_format = '%s.%03d' + time_zone
    logging.Formatter.default_time_format = '%Y-%m-%dT%H:%M:%S'
    for log in hide:
        logging.getLogger(log).setLevel(logging.ERROR)
    return logging.getLogger(name)


def get_message(message: str, report: dict = None, error_code: str = None,
                error_name: str = None, trace: str = None) -> str:
    """

    Formatting message for logging

    :param: message: message
    :type message: str
    :param report: user parameters for logging
    :type report: dict
    :param error_code: error code
    :type error_code: str
    :param error_name: error message
    :type error_name: str
    :param trace: traceback
    :type trace: str
    :return: formatted log entry
    :rtype: str

    """
    message = {"message": message}
    if error_code:
        message['error'] = {'code': error_code, 'name': error_name}
    if trace:
        message['error']['trace'] = trace
    if report:
        message['report'] = report
    return json.dumps(message, sort_keys=True)


def terminate(signum: int, frame: types.FrameType) -> None:
    """
    Processed signals handling

    :param signum: system signal
    :type signum: int
    :param frame: terminating frame
    :type frame: types.FrameType
    """
    global TERMINATE
    try:
        signal_name = Signals(signum).name
    except ValueError:
        signal_name = signum
    logger.info(get_message(f"received signal {signal_name} ({signal.strsignal(signum)}), terminating"))
    tb = traceback.format_stack(frame)[0].replace('\n', ';')
    logger.info(get_message(f"terminating traceback: {tb}"))
    TERMINATE = True
    on_terminate()


def set_handlers(signals: list, handler: Callable[[], None] = lambda: None) -> None:
    """
    Setting signal handlers

    :param signals: processed signals
    :type signals: list
    :param handler: signals handler
    :type handler: Callable[[], None]
    """
    global TERMINATE, on_terminate
    on_terminate = handler
    for sign in signals:
        signal.signal(sign, terminate)


def is_terminate() -> bool:
    """
    Termination flag value

    :return: termination flag value
    :rtype: bool
    """
    return TERMINATE


def connect_to_rabbit(log: Logger) -> BlockingConnection:
    """
    Connection to RabbitMQ

    :param log: logger
    :type log: Logger
    :return: RabbitMQ connection
    :rtype: BlockingConnection
    """
    error, conn, err_count = True, None, 0
    while error:
        try:
            conn = BlockingConnection(
                ConnectionParameters(os.getenv('RABBITMQ_SERVICE_HOST', 'localhost'),
                                     port=int(os.getenv('RABBITMQ_SERVICE_PORT', '5672')),
                                     credentials=PlainCredentials(
                                         os.getenv('RABBITMQ_USERNAME', 'rabbitmq'),
                                         os.getenv('RABBITMQ_PASSWORD', 'rabbitmq'))))
            error = False
        except Exception as e:
            if err_count / 10 * 10 == err_count:
                log.critical(f"Rabbit connection error[{err_count}] {str(e)}")
            error = True
            err_count += 1
    return conn


logger = get_logger('helper', LOG_FORMAT)
