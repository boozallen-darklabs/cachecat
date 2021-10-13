from cachecat.cache import Cache

cache = Cache(url, "q", "p")
cache["foo"] = b"bar"
print(cache["foo"])
