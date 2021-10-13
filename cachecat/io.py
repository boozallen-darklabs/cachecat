"""
Wrapping the :py:class:`Cache <cachecat.cache.Cache>` and
:py:class:`Session <cachecat.session.Session>` interfaces in more familiar
`file-like interfaces <https://docs.python.org/3/library/io.html>`_ simplifies
the user experience and enables more complex buffering techniques which
ultimately improve tunneling capacity.

The following wrappers are currently implemented.

Reading
^^^^^^^

.. autoclass:: cachecat.io.CacheReader

Writing
^^^^^^^

.. autoclass:: cachecat.io.CacheWriter

Buffered Reading and Writing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cachecat.io.CacheIO
    :members:
"""
import threading, io
from .exceptions import AlreadyCachedException, NotCachedException
from .session import Session
from . import log

DEFAULT_CHUNK_SIZE = 1024   # Max URL approx. 2000

class CacheReader(io.RawIOBase):
    """
    A :py:class:`CacheReader <cachecat.io.CacheReader>` will
    iterate over a :py:class:`Session's <cachecat.session.Session>`
    token-space and report any new data as an unseekable readable
    file-like interface, implementing :py:class:`io.RawIOBase <io.RawIOBase>`.

    .. code-block:: python

        # Read all data from a cache session
        with CacheReader(cache, session) as reader:
            print(reader.read())

    Additionally, a :py:class:`CacheReader <cachecat.io.CacheReader>`
    can be wrapped in a :py:class:`BufferedReader <io.BufferedReader>` object
    for more control over the data.

    .. code-block:: python

        # Read the first 100 bytes of data from a cache session
        with io.BufferedReader(CacheReader(cache, session)) as reader:
            print(reader.read(100))
    """
    cache       = None
    session     = None

    def __init__(self, cache, session):
        self.cache = cache
        self.session = session

    def readable(self):
        return True

    def readinto(self, b):
        """
        Base read implementation on which all
        :py:class:`io.RawIOBase <io.RawIOBase>` read* methods depend.
        """
        
        # Try to fetch data from the cache for the current token
        for step, token in self.session:
            log.info("[%i] Reader checking token: %s", step, token)
            try:

                # Read data from the cache
                data = self.cache[token]
                if data:
                    log.info("[%i] Read data: %s", step, data)

                    # Place data into bytearray (if called from io.RawIOBase)
                    if isinstance(b, bytearray):
                        b.clear()
                        b.extend(bytes(data))

                    # Place data into memoryview (if called from io.BufferedReader)
                    elif isinstance(b, memoryview):
                        
                        # If memoryview buffer is too small, postpone read
                        if len(data) > len(b):
                            log.debug("[%i] Memoryview too small for read data - %i < %i", len(b), len(data))
                            self.session.step -= 1
                            return 0

                        l = len(data)
                        b[:l] = data

                    else:
                        raise ValueError(b)

                    return len(data)

            # Read produced unexpected uncached response - reached top of stack
            except NotCachedException as e:
                log.debug("[%i] Not cached", step)
                break

        return 0

class CacheWriter(io.RawIOBase):
    """
    A :py:class:`CacheWriter <cachecat.io.CacheWriter>` will
    iterate over a :py:class:`Session's <cachecat.session.Session>`
    token-space and write data to the cache at the end of the stack
    as an unseekable writeable file-like interface, implementing
    :py:class:`io.RawIOBase <io.RawIOBase>`.

    .. code-block:: python

        # Write some data to the cache session
        with CacheWriter(cache, session) as writer:
            writer.write(b"Hello, world!")
    """
    cache       = None
    session     = None
    chunk_size  = None
    _consumers  = None

    def __init__(self, cache, session, chunk_size=DEFAULT_CHUNK_SIZE):
        self.cache = cache
        self.session = session
        self.chunk_size = chunk_size
        self._consumers = list()

    def writable(self):
        return True

    def write(self, data):
        """
        Base write implementation on which all
        :py:class:`io.RawIOBase <io.RawIOBase>` write* methods depend.
        """

        # Split data into chunks appropriate for url arguments
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i+self.chunk_size]
        
            # Try to write data to the cache for the current token
            for step, token in self.session:
                log.info("[%i] Writer checking token: %s", step, token)
                try:
                    self.cache[token] = chunk
                    log.info("[%i] Wrote data: %s", step, chunk)
                    break

                # Write produced unexpected cached response - buffer any encountered data
                except AlreadyCachedException as e:
                    if e.data:
                        log.info("[%i] Writer encountered cached data: %s", step, e.data)
                        for func in self._consumers:
                            func(e.data)

        return len(data)

    def subscribe(self, func):
        """
        Add a consumer of data the writer encounters while writing.
        """
        if func not in self._consumers:
            self._consumers.append(func)

    def unsubscribe(self, func):
        """
        Remove a consumer of data the writer encounters while writing.
        """
        if func in self._consumers:
            self._consumers.remove(func)

class CacheIO(io.BufferedRWPair):
    """
    A :py:class:`CacheIO <cachecat.io.CacheIO>` object
    will combine a :py:class:`CacheReader <cachecat.io.CacheReader>`
    and :py:class:`CacheWriter <cachecat.io.CacheWriter>` into
    a single buffered I/O stream, enabling communication between
    parties across a public web cache. Implemented as a context manager,
    a :py:class:`CacheIO <cachecat.io.CacheIO>` object can
    also intermittently poll for new data and pass it to a callback
    function, resembling realtime communication between parties across
    a public web cache.

    .. code-block:: python

        # Build STDOUT callback
        def callback(data):
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        
        # Connect STDIN/STDOUT to CacheIO
        with CacheIO(reader, writer, callback) as stream:
            while True:
                data = sys.stdin.buffer.readline()
                if not data:
                    break
                stream.write(data)
    """
    callback        = None
    poll_interval   = None
    _buffer         = None
    _buffer_lock    = None

    def __init__(self, reader, writer, callback=None, poll_interval=1, buffer_size=io.DEFAULT_BUFFER_SIZE):
        super(CacheIO, self).__init__(reader, writer, buffer_size)
        self.callback = callback
        self.poll_interval = poll_interval
        self.event = threading.Event()
        self.thread = threading.Thread(target=self._poll)

        # Subscribe to any reads the writer might do while writing
        self._buffer = list()
        self._buffer_lock = threading.Lock()
        writer.subscribe(self._handle)

    def __enter__(self):
        """Enter polling context"""

        # Start polling thread
        self.event.clear()
        self.thread.start()

        return super(CacheIO, self).__enter__()

    def __exit__(self, type, value, traceback):
        """Exit polling context"""

        # Stop polling thread
        self.event.set()
        self.thread.join()

        return super(CacheIO, self).__exit__(type, value, traceback)
    
    def _handle(self, data):
        """Handle unintentional reads from writer"""

        # Append extra data to buffer
        log.info("Buffering data from writer: %s", data)
        with self._buffer_lock:
            self._buffer.append(data)

    def _poll(self):
        """Intermittently poll the cache for new data"""
        while not self.event.is_set():

            # Read until the end of the stack
            with self._buffer_lock:
                data = b"".join(self._buffer) + self.read()
                self._buffer.clear()

            # If we've reached the end of the stack, flush write buffer and wait
            if not data:
                self.flush()
                self.event.wait(self.poll_interval)

            # Otherwise, notify consumer of any data
            elif self.callback and callable(self.callback):
                self.callback(data)

