import logging
from lib.rabbitmq_worker import Worker
from lib.properties import Properties
from utils.yml import YAML

#import pdb;pdb.set_trace()
yml = YAML ("prod_cons_config.yml", "test_app_pas")
config = yml.get_config()

prop_obj = Properties()
worker = Worker(config['host'], config['port'], config['userName'], config['password'], config['virtualHost'])


# 'on_consume' method would be called on successful consumption of the message
# Ack/reject message
def on_consume(unused_channel, basic_deliver, properties, body):
    print(properties)
    print(body)
    #worker.acknowledge_message (basic_deliver.delivery_tag)
    # LOGGER.info('send reject ..')
    # worker.reject_message(basic_deliver.delivery_tag)

    return 0  # return 0 in case there is an exception while processing the message or
    # if we have intentionally rejected the message ;)
    # otherwise, return a message which needs to be published to an another exchange


# 'on_publish' function would be called after the successful publish
def on_publish():
    print("on publishing return")


def main():

    prop_obj.on_consume_callback = lambda unused_channel, basic_deliver, properties, body: on_consume (unused_channel,
                                                                                                       basic_deliver,
                                                                                                       properties, body)
    prop_obj.on_publish_callback = lambda: on_publish ()
    prop_obj.exchange = config['exchangeName']
    prop_obj.routing_key = 'routing key'
    prop_obj.queue = config['queueName']
    prop_obj.is_publish = False  # tells whether to publish to an another exchange after processing
    try:
        worker.process (prop_obj)
    except KeyboardInterrupt:
        worker.stop ()


if __name__ == '__main__':
    main ()
