"""
The elementary interface for interacting with a vulnerable web cache is
implemented as a python dictionary :py:class:`Cache <cachecat.cache.Cache>`.

.. autoclass:: cachecat.cache.Cache
"""
import requests, re, json, base64
from urllib.parse import urlparse, parse_qsl, urlencode
from html import unescape
from collections.abc import MutableMapping
from .exceptions import AlreadyCachedException, NotCachedException
from . import log

requests.packages.urllib3.disable_warnings(
    category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Safari/605.1.15",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "*/*",
    "Connection": "keep-alive",
    }

class Cache(MutableMapping):
    """
    Some web applications reflect GET request url arguments in cached
    responses, where some arguments are keyed to the cache and others
    are not. This means we can temporarily store data on the
    cache server as a key-value store. This
    :py:class:`Cache <cachecat.cache.Cache>` class implements that
    technique as the backend for a python dictionary.

    .. code-block:: python
        
        # Build a python database backed by a vulnerable public web cache
        cache = Cache("https://webcachetunneling.com/", "q", "p")
        cache["foo"] = b"bar"
        print(cache["foo"])

    """
    url     = None
    key     = None
    slot    = None
    _proxy   = None

    def __init__(self, url, key, slot, proxy=None, **kwargs):
        """
        Create an object representing the target cache.

        :param str url: vulnerable url
        :param str key: cache-keyed url argument for token
        :param str slot: non-cache-keyed url argument for data
        :param str proxy: http proxy to use when making requests
        """
        self.url = urlparse(url)
        self.key = key
        self.slot = slot
        self._proxy = urlparse(proxy) if proxy else None

    @property
    def _proxies(self):
        obj = {}
        if self._proxy:
            obj["http"] = self._proxy.netloc
            obj["https"] = self._proxy.netloc
        return obj

    def __getitem__(self, key):
        """
        Get data from the cache.

        :param str key: unique token identifying data
        :return: data
        :rtype: bytes
        :raises: KeyError, IOError
        """
        # Insert token into url arguments
        d = dict(parse_qsl(self.url.query))
        d[self.key] = key
        u = self.url._replace(query=urlencode(d))

        # Send request
        log.debug("Sending request: %s", u.geturl())
        r = requests.get(u.geturl(), headers=DEFAULT_HEADERS, proxies=self._proxies, verify=0)
        log.debug("Received response: %s", r)
        r.raise_for_status()

        # Confirm response was cached
        if not "HIT" in r.headers.get("X-Cache-Status", "MISS"):
            raise NotCachedException(key)

        # Extract data from cached response
        return self._extract(key, r)

    def __setitem__(self, key, value):
        """
        Put data in the cache.

        :param str key: unique token identifying data
        :param str value: data to store (in bytes)
        :raises: KeyError, IOError
        """
        # Insert token and data into url arguments
        d = dict(parse_qsl(self.url.query))
        d[self.key] = key
        d[self.slot] = base64.urlsafe_b64encode(value)
        u = self.url._replace(query=urlencode(d))

        # Send request
        log.debug("Sending request: %s", u.geturl())
        r = requests.get(u.geturl(), headers=DEFAULT_HEADERS, proxies=self._proxies, verify=0)
        log.debug("Received response: %s", r)
        r.raise_for_status()

        # Confirm response was not cached
        if "HIT" in r.headers.get("X-Cache-Status", "MISS"):
            raise AlreadyCachedException(key, self._extract(key, r))

    def __delitem__(self, key):
        """
        Delete an item from the cache (impossible).

        :param str key: unique token identifying data
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def __iter__(self):
        """
        Iterate over items in the cache (impossible).

        :raises: NotImplementedError
        """
        raise NotImplementedError

    def __len__(self):
        """
        Get the number of items in the cache (impossible).

        :raises: NotImplementedError
        """
        raise NotImplementedError

    def _extract(self, key, response):
        """
        Extract data from a cached response (unique to https://webcachetunneling.com/).

        :param str key: unique token identifying data
        :param requests.models.Response response: cached response
        :return: data
        :rtype: bytes
        """

        # Look for reflected url
        for match in re.finditer("No results for (.*)%s(.*)</code>" % key, response.text):
            log.debug("Matched payload: %s", match)

            # Parse data from reflected url
            a,b = match.span()
            snip = response.text[a+35:b-7]
            try:
                log.debug("Parsing url: %s", snip)
                u = urlparse(snip)
                log.debug("Parsed url: %s", u)
                t = dict(parse_qsl(unescape(u.query)))
                log.debug("Parsed query arguments: %s", t)
                m = t[self.slot]
                log.debug("Parsed message: %s", m)
                return base64.urlsafe_b64decode(m)

            except ValueError as e:
                log.debug("Payload is corrupted: %s", snip)
 
            except KeyError as e:
                log.debug("Payload is missing: %s", e)

