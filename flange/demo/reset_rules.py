from unis import Runtime
rt = Runtime('http://localhost:8888')
for p in rt.ports:
    p.rules = []

rt.flush()
