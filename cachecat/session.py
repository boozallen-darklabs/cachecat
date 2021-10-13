"""
To coordinate between multiple :py:class:`Cache <cachecat.cache.Cache>` clients,
a :py:class:`Session <cachecat.session.Session>` iterator implements a stack
interface based on pseudo-random token strings.

.. autoclass:: cachecat.session.Session
    :members: port, step, token
"""
import shortuuid 
from collections.abc import Iterator
from . import log

def int_to_string(number, alphabet, padding=None):
    """
    Convert a number to a string, using the given alphabet.
    The output has the most significant digit first.

    Stolen from shortuuid.
    """
    output = ""
    alpha_len = len(alphabet)
    while number:
        number, digit = divmod(number, alpha_len)
        output += alphabet[digit]
    if padding:
        remainder = max(padding - len(output), 0)
        output = output + alphabet[0] * remainder
    return output[::-1]

class Session(Iterator):
    """
    Due to the nature of a cache, the mere act of checking the cache
    for data itself writes to the cache, disqualifying that entry for
    subsequent checks. To overcome this, a
    :py:class:`Session <cachecat.session.Session>` defines and generates
    a set of predictable tokens which, when queried in a specific order,
    behaves as a type of stack. Through successive queries, each client's
    :py:class:`Session <cachecat.session.Session>` will converge at the
    top of the stack, which will serve as a dynamic reference point for
    new information. For this to work, clients must connect within the
    cache expiration period of each other, which experimentally has been
    about 15 seconds.

    .. code-block:: python

        # Progressively iterate over a Session and report any data in the cache
        for step, token in Session(1337):
            try:
                print("Step %i contains: %s" % (step, cache[token]))
            except KeyError:
                print("Missing step: %i" % (step))
                break
    """

    port        = None
    """Choose a shared, but unique, port to start the stack sequence."""

    step        = None
    """Within a session, the step represents the current location on the stack."""

    max_step  = None
    """At the maximum step value, the step loops back to zero. Hopefully the
    zeroth token no longer exists in the cache and can be reused."""

    def __init__(self, port, step=0, max_step=0xffff):
        self.port = port
        self.step = step
        self.max_step = max_step

    @property
    def token(self):
        """The token is a string representation of the current stack location,
        and should be used as the cache key"""
        _, step = divmod(self.step, self.max_step)
        number = (self.port << self.max_step.bit_length()) + step
        return shortuuid.uuid(int_to_string(number, shortuuid.get_alphabet()))

    def __iter__(self):
        return self

    def __next__(self):
        token = self.token
        step = self.step
        self.step += 1
        return step, token

    def __repr__(self):
        return "<%s port=%i step=%i>" % (self.__class__.__name__, self.port, self.step)

