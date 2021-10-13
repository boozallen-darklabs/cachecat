from cachecat.session import Session 
 
session = Session(1337) 
 
for step, token in session: 
    try: 
        print("Step %i contains: %s” % (step, cache[token])) 
    except KeyError: 
        print("Missing step: %i" % (step)) 
        break 
