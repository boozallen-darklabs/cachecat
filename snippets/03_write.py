from cachecat.io import CacheWriter 
 
with CacheWriter(cache, session) as writer: 
    writer.write(b”Hello, world!”) 
