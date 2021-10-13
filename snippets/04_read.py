from cachecat.io import CacheReader 
 
with CacheReader(cache, session) as reader: 
    print(reader.read()) 
