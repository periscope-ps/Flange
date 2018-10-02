from unis import Runtime

def reset():
    rt = Runtime('http://localhost:8888')
    for p in rt.ports:
        p.rules = []

    rt.flush()

if __name__ == '__main__':
    reset()
