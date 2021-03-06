import logging
import pika
from .properties import Properties

LOGGER = logging.getLogger (__name__)


# accessor = Properties()

class Worker ():
    """This is a worker that can be used to consume messages from queues as
    well as publish messages to exchanges. This will also handle unexpected
    interactions with RabbitMQ such as channel and connection closures.
    If RabbitMQ closes the connection, it will reopen it.
    """
    
    def __init__(self, host, port, user, password, vhost):
        """Create a new instance of the worker class, passing in the credentials
         used to connect to RabbitMQ.
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._vhost = vhost
        
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        
        #
        self._message_count = 0  # Count messages and failed messages.
        self._failed_message_count = 0
        
        self._number_of_messages = 1
        self._message_interval = 1
        self._delivered_messages = 0
        self.published_messages = 0
        
        self.accessor = None
    
    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.
        :rtype: pika.SelectConnection
        """
        LOGGER.info ('Connecting to RabbitMQ..')
        credentials = pika.PlainCredentials (self._user, self._password)
        parameters = pika.ConnectionParameters (self._host, self._port, self._vhost, credentials, socket_timeout=300)
        return pika.SelectConnection (parameters,
                                      self.on_connection_open,
                                      self.on_connection_error,  # !! Handle error opening connection
                                      stop_ioloop_on_close=False)
    
    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        :type unused_connection: pika.SelectConnection
        """
        LOGGER.info ('Connection opened')
        self.add_on_connection_close_callback ()
        self.open_channel ()
    
    def on_connection_error(self, unused_connection, message):
        """This method is called by pika if the connection to RabbitMQ has
        failed to be established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        :type unused_connection: pika.SelectConnection
        """
        LOGGER.error ('Connection failed: %s', message)
    
    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.
        """
        LOGGER.info ('Adding connection close callback')
        self._connection.add_on_close_callback (self.on_connection_closed)
    
    def on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.
        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop ()
        else:
            LOGGER.warning ('Connection closed, reopening in 5 seconds: (%s) %s',
                            reply_code, reply_text)
            self._connection.add_timeout (5, self.reconnect)
    
    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.
        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop ()
        
        if not self._closing:
            # Create a new connection
            self._connection = self.connect ()
            
            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start ()
    
    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.
        """
        LOGGER.info ('Creating a new channel')
        self._connection.channel (on_open_callback=self.on_channel_open)
    
    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.
        Since the channel is now open, we will start consuming
        :param pika.channel.Channel channel: The channel object
        """
        LOGGER.info ('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback ()
        self.start_consuming ()
    
    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        LOGGER.info ('Adding channel close callback')
        self._channel.add_on_close_callback (self.on_channel_closed)
    
    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.
        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed
        """
        LOGGER.warning ('Channel %i was closed: (%s) %s',
                        channel, reply_code, reply_text)
        self._connection.close ()
    
    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        """
        LOGGER.info ('Issuing consumer related RPC commands')
        self.add_on_cancel_callback ()
        
        # setting prefetch count
        self._channel.basic_qos (prefetch_count=1)
        
        self._consumer_tag = self._channel.basic_consume (self.on_message,
                                                          self.accessor.queue)
    
    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.
        """
        LOGGER.info ('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback (self.on_consumer_cancelled)
    
    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.
        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        LOGGER.info ('Consumer was cancelled remotely, shutting down: %r',
                     method_frame)
        if self._channel:
            self._channel.close ()
    
    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.
        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body
        """

        # num = self._on_consume_callback(unused_channel, basic_deliver, properties, body)
        # num = self.accessor.on_consume_callback(unused_channel, basic_deliver, properties, body)
        LOGGER.info ('calling on_consume_callback...')
        self._msg = self.accessor.on_consume_callback (unused_channel, basic_deliver, properties, body)
        LOGGER.info ('Done with on_consume_callback...')

        # Also, publish to a exchange
        if self.accessor.is_publish and (self._msg != 0 and self._msg is not None):
            self._channel.confirm_delivery (self.on_delivery_confirmation)
            self.schedule_next_message ()
        
        self._message_count = self._message_count + 1
        
        if self._msg == 0:
            self._failed_message_count = self._failed_message_count + 1
            LOGGER.info ('Processed %d messages. %d failed messages', self._message_count, self._failed_message_count)
        # if self.accessor.message_count_limit > 0 and self._message_count >= self.accessor.message_count_limit :
        #    LOGGER.info('Processed limit of %d messages. %d failed messages', self._message_count, self._failed_message_count)
        #    self.stop()
    
    ####
    def on_delivery_confirmation(self, method_frame):
        """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
        command, passing in either a Basic.Ack or Basic.Nack frame with
        the delivery tag of the message that was published.
        """
        confirmation_type = method_frame.method.NAME.split ('.')[1].lower ()
        self._delivered_messages += 1
        LOGGER.info ("\n"
                     "==========================================")
        LOGGER.info (method_frame)
        LOGGER.info ("An %s has been received!!!" % confirmation_type)
        LOGGER.info ("Published %i messages and received delivery confirmation for %i messages" % (
        self.published_messages, self._delivered_messages))
        self._p_res = self.accessor.on_publish_callback ()
    
    def publish_message(self):
        LOGGER.info ('publishing now...')
        self._channel.basic_publish (exchange=self.accessor.exchange,
                                     routing_key=self.accessor.routing_key,
                                     body=self._msg,
                                     properties=pika.BasicProperties (content_type='text/plain',
                                                                      delivery_mode=2))
        self._number_of_messages -= 1
        self.published_messages += 1
        
        if self._number_of_messages >= 1:
            self.schedule_next_message ()
        # else:
        # self._connection.close()
    
    def schedule_next_message(self):
        self._connection.add_timeout (self._message_interval, self.publish_message)
    
    ####
    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.
        :param int delivery_tag: The delivery tag from the Basic.Deliver frame
        """
        LOGGER.info ('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack (delivery_tag)
    
    def reject_message(self, delivery_tag):
        """
        Reject the message by sending a Basic.Reject
        """
        LOGGER.info ('Rejecting message %s', delivery_tag)
        self._channel.basic_reject (delivery_tag, requeue=False)
    
    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self._channel:
            LOGGER.info ('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel (self.on_cancelok, self._consumer_tag)
    
    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        :param pika.frame.Method unused_frame: The Basic.CancelOk frame
        """
        LOGGER.info ('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel ()
    
    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.
        """
        LOGGER.info ('Closing the channel')
        self._channel.close ()
    
    def process(self, obj):
        """Run the  consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.
        """
        if not isinstance (obj, Properties):
            raise ValueError ("parameter should be an instance of type 'Properties'")
        self.accessor = obj
        self._connection = self.connect ()
        self._connection.ioloop.start ()
    
    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """
        LOGGER.info ('Stopping')
        LOGGER.info ('Processed %d messages. %d failed messages', self._message_count, self._failed_message_count)
        self._closing = True
        self.stop_consuming ()
        self._connection.ioloop.start ()
        LOGGER.info ('Stopped')
    
    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        LOGGER.info ('Closing connection')
        self._connection.close ()
