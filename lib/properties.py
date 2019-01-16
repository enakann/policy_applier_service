class Properties(object):
    """
    A class in which getter setter methods are defined
    """
    def __init__(self):
            self._exchange = None
            self._routing_key = None
            self._queue = None
            self._on_consume_callback = None   # Use a callback to process the message.
            self._on_publish_callback = None   # Use a callback to do operations upon successful publish
            #self._message_count_limit = 0      # Stop reading messages after reading this many.
            self._is_publish = False           # Enable both consume and consume-publish feature

    @property
    def exchange(self):
        return self._exchange

    @exchange.setter
    def exchange(self, exchange):
        self._exchange = exchange

    @property
    def routing_key(self):
        return self._routing_key

    @routing_key.setter
    def routing_key(self,routing_key):
        self._routing_key = routing_key

    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, queue):
        self._queue = queue

    @property
    def is_publish(self):
        return self._is_publish

    @is_publish.setter
    def is_publish(self, is_publish):
        self._is_publish = is_publish

    #@property
    #def message_count_limit(self):
    #    return self._message_count_limit

    #@message_count_limit.setter
    #def message_count_limit(self, message_count_limit) :
    #    self._message_count_limit = message_count_limit

    @property
    def on_consume_callback(self):
        return self._on_consume_callback

    @on_consume_callback.setter
    def on_consume_callback(self, on_consume_callback):
        self._on_consume_callback = self._isfunc(on_consume_callback)

    @property
    def on_publish_callback(self):
        return self._on_publish_callback

    @on_publish_callback.setter
    def on_publish_callback(self, on_publish_callback):
        self._on_publish_callback = self._isfunc(on_publish_callback)

    def _isfunc(self, func):
        if not callable(func):
            func_name = func.__name__ if hasattr(func,'__name__') else func
            raise ValueError("'{}' must be a callable function".format(func_name))
        return func
