#!/usr/bin/env python3

import os
import uuid
import signal
import multiprocessing
from pika.spec import BasicProperties, Basic
from concurrent.futures import ThreadPoolExecutor
from pika.adapters.blocking_connection import BlockingChannel
from helpers import connect_to_rabbit, get_logger, set_handlers, is_terminate, get_message as __, LOG_FORMAT


def terminate():
    """

    On terminating actions

    """
    input_channel.basic_cancel(consumer_tag=consumer_tag)


def request_dispatch(body: bytes):
    """
    Input message dispatch

    :param body: message body
    :type body: bytes
    """
    logger.info(__(f'handle message: \'{body}\''))
    if write_to_file == '1':
        with open('received.txt', 'a') as received:
            received.write(f"{body.decode()}\n")


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
    """

    Message processing

    :param ch: channel
    :type ch: BlockingChannel
    :param method: method
    :type method: Basic.Deliver
    :param properties: properties
    :type properties: BasicProperties
    :param body: message body
    :type body: bytes

    """
    global counter
    if not is_terminate():
        future = pool.submit(request_dispatch, body)
        while not future.done():
            ch.connection.sleep(0.01)
        counter += 1
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.debug(__(f"sent ACK, app id = {properties.FLAG_APP_ID}"))
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        logger.debug(__(f"sent NACK, app_id = {properties.FLAG_APP_ID}"))

# Entry point


if __name__ == '__main__':
    counter, logger = 0, get_logger('receiver', LOG_FORMAT)
    write_to_file, terminating = os.getenv('WRITE_TO_FILE', '0'), False
    consumer_tag = uuid.uuid1().hex
    pool = ThreadPoolExecutor(max_workers=int(os.getenv('WORKERS_COUNT', multiprocessing.cpu_count())))
    logger.info(__('start process'))
    logger.info(__('connecting to RabbitMQ...'))
    connection = connect_to_rabbit(logger)
    input_channel = connection.channel()
    input_channel.queue_declare(queue='test_queue')
    input_channel.basic_qos(prefetch_count=1)
    input_channel.basic_consume('test_queue', callback, consumer_tag=consumer_tag, auto_ack=False)
    logger.info(__('connected to RabbitMQ'))
    set_handlers([signal.SIGTERM, signal.SIGINT], terminate)
    logger.info(__('waiting for messages...'))
    input_channel.start_consuming()
    connection.close()
    logger.info(__('disconnected from RabbitMQ'))
    logger.info(__(f'handled {counter} message(s)'))
    logger.info(__('shutdown process'))
