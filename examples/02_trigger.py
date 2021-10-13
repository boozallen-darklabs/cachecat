"""
Use a public web cache as a trigger for hidden functionality.

.. code-block::bash

    # To cause the trigger, wait (about a minute) for the cache to expire, then submit this request
    curl -si 'https://webcachetunneling.com/?q=26hqBz7TUL3ikYTGCFBp&p=VGhlIGNyb3cgZmxpZXMgYXQgbWlkbmlnaHQh' | grep -i x-cache
"""
import sys 
from cachecat.cache import Cache

# Prepare trigger condition
key = "26hqBz7TUL3ikYTGCFBp"
trigger = b"The crow flies at midnight!"

# This page reflects unkeyed user-controlled data in cached responses.
# The 'q' parameter is cache-keyed, and the 'p' parameter is not.
cache = Cache("https://webcachetunneling.com/", "q", "p") #, proxy="http://127.0.0.1:8080")

# Check for the trigger condition
try:
    if cache[key] == trigger:
        print("Triggered! This message will now self-destruct!")
        sys.exit(0)
except KeyError as e:
    pass

print("Nothing to see here..")
print("Hint: wait 60 seconds, run the following command, then try again!")
print("> curl -si 'https://webcachetunneling.com/?q=26hqBz7TUL3ikYTGCFBp&p=VGhlIGNyb3cgZmxpZXMgYXQgbWlkbmlnaHQh' | grep -i x-cache")

