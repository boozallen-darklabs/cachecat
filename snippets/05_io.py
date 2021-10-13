from cachecat.io import CacheReader, CacheWriter, CacheIO 
import sys 
 
reader = CacheReader(cache, session) 
writer = CacheWriter(cache, session) 
 
def callback(data): 
    sys.stdout.buffer.write(data) 
    sys.stdout.buffer.flush() 
 
with CacheIO(reader, writer, callback) as stream: 
    while True: 
        data = sys.stdin.buffer.readline() 
        if not data: 
            break 
        stream.write(data)
