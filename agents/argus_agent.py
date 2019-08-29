import requests, time, argparse, json

def _start(fn, node):
    print("Starting '{}' on '{}' with\n  {}".format(fn['name'], node['name'], fn['configuration']))
def _stop(fn, node):
    print("Stopping '{}' on '{}'".format(fn['name'], node['name']))

def _check_update(node):
    updated = False
    if 'functions' in node:
        if not 'active' in node['functions']:
            node['functions']['active'] = []
        if 'create' in node['functions'] and node['functions']['create']:
            updated, todo = True, []
            for fn in node['functions']['create']:
                _start(fn, node)
                todo.append(fn)
            for fn in todo:
                node['functions']['create'].remove(fn)
                node['functions']['active'].append(fn)
        if 'delete' in node['functions'] and node['functions']['delete']:
            updated, delete, active = True, [], []
            for fn in node['functions']['delete']:
                _stop(fn, node)
                for f in node['functions']['active']:
                    if f['name'] == fn['name']:
                        active.append(f)
                delete.append(fn)
            [node['function']['active'].remove(f) for f in active]
            [node['function']['delete'].remove(f) for f in delete]
        if 'modified' in node['functions'] and node['functions']['modified']:
            updated, todo = True, []
            for fn in node['functions']['modified']:
                _stop(fn, node)
                _start(fn, node)
                todo.append(fn)
            [node['functions']['modified'].remove(fn) for fn in todo]
    return updated

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--unis', type=str, required=True, help="url of the driving UNIS instance")
    parser.add_argument('-s', '--sample', type=int, default=1, help="Time between polls")
    args = parser.parse_args()

    unis = args.unis
    query = "{}/nodes?ts=gt={}".format(unis, int((time.time() - args.sample) * 1000000))
    while True:
        do_update, nodes = False, {}
        try:
            for v in requests.get(query).json():
                if v['ts'] > nodes.get(v['id'], {}).get('ts', float('-inf')):
                    nodes[v['id']] = v

            for v in nodes.values():
                do_update |= _check_update(v)
                del v['ts']

            if do_update:
                requests.post("{}/nodes".format(unis), data=json.dumps(list(nodes.values())))
                
        except Exception as e: print(e)
        time.sleep(args.sample)
