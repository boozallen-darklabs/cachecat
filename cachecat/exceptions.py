
class AlreadyCachedException(KeyError):
    """Used to signify a request was unexpectedly cached"""

    def __init__(self, token, data=None):
        self.token = token
        self.data = data

    def __str__(self):
        return "Token '%s' already cached with data: %s" % (self.token, self.data)

class NotCachedException(KeyError):
    """Used to signify a request was unexpectedly not cached"""

    def __init__(self, token):
        self.token = token

    def __str__(self):
        return "No cache for token '%s'" % self.token

