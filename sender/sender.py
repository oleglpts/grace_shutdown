#!/usr/bin/env python3

import os
import time
import signal
from helpers import connect_to_rabbit, get_logger, is_terminate, set_handlers, get_message as __, LOG_FORMAT


# Entry point

if __name__ == '__main__':
    counter, terminating, logger = 0, False, get_logger('sender', LOG_FORMAT)
    logger.info(__('start process'))
    logger.info(__('connecting to RabbitMQ...'))
    connection = connect_to_rabbit(logger)
    logger.info(__('connected to RabbitMQ'))
    channel = connection.channel()
    channel.queue_declare(queue='test_queue')
    set_handlers([signal.SIGTERM, signal.SIGINT])
    sleep_interval = float(os.getenv('SLEEP_INTERVAL', '1'))
    write_to_file = os.getenv('WRITE_TO_FILE', '0')
    while True:
        if not is_terminate():
            logger.info(__(f"Send message [{counter + 1}]: '{counter + 1}'"))
            channel.basic_publish(exchange='', routing_key='test_queue', body=f"{counter + 1}".encode())
            counter += 1
            if write_to_file == '1':
                with open('sent.txt', 'a') as sent:
                    sent.write(f"{counter}\n")
            time.sleep(sleep_interval)
        else:
            break
    channel.close()
    connection.close()
    logger.info(__('disconnected from RabbitMQ'))
    logger.info(__(f'sent {counter} message(s)'))
    logger.info(__('shutdown process'))
