from unis import Runtime

def reset(rt):
    for p in rt.ports:
        p.rules = []

    rt.flush()

if __name__ == '__main__':
    rt = Runtime('http://localhost:8888')
    reset(rt)
