"""
Upload to and download from a public web cache.
"""
import os, sys, random
from cachecat.cache import Cache
from cachecat.session import Session
from cachecat.io import CacheReader, CacheWriter

def chunk(data, size=24):
    for i in range(0, len(data), size):
        yield data[i:i+size]

content = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

# This page reflects unkeyed user-controlled data in cached responses.
# The 'q' parameter is cache-keyed, and the 'p' parameter is not.
cache = Cache("https://webcachetunneling.com/", "q", "p") #, proxy="http://127.0.0.1:8080")

if len(sys.argv) > 1:

    # The 'port' is essentially the 'location' of the file
    port = int(sys.argv[1])
    print("Downloading from port: %i" % port)

    # A Session establishes the key-space under which the file will be stored
    session = Session(port)

    # We'll download all data that is available under this session
    content = b""
    with CacheReader(cache, session) as reader:
        print("Downloading..")
        content = reader.read()
    print("Downloaded %i bytes: %s" % (len(content), content))

else:
    
    # The 'port' is essentially the 'location' of the file
    port = random.randint(0, 0xFFFF)
    print("Uploading to port: %i" % port)

    # A Session establishes the key-space under which the file will be stored
    session = Session(port)

    # We'll upload the data in 32-byte chunks
    with CacheWriter(cache, session, chunk_size=32) as writer:
        print("Uploading %i bytes.." % len(content))
        writer.write(content)
    print("Done! Use '%s %i' to download." % (sys.argv[0], port))
