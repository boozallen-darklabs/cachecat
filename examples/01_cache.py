"""
Use a simple python dictionary backed by a public web cache.
"""
import sys, random, string
from cachecat.cache import Cache

def random_string(size=10):
    return "".join(random.choice(string.ascii_lowercase) for i in range(size))

# This page reflects unkeyed user-controlled data in cached responses.
# The 'q' parameter is cache-keyed, and the 'p' parameter is not.
cache = Cache("https://webcachetunneling.com/", "q", "p") #, proxy="http://127.0.0.1:8080")

# Try storing some data
key = random_string()
data = b"Hello, world!"
print("Storing data for key '%s': %s" % (key, data))
cache[key] = data

# Now retrieve it!
try:
    check = cache[key]
    assert check == data
    print("Retrieved data from key '%s': %s" % (key, check))
except (KeyError, AssertionError) as e:
    print("Uh oh, it didn't work.. %s" % (key))
    sys.exit()

# What if there's no data..?
key = random_string()
try:
    print("Checking empty key '%s'..." % (key))
    check = cache[key]
except KeyError as e:
    print("%s: %s" % (e.__class__.__name__, e))

