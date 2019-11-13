import argparse

from unis import Runtime
from unis.models import Node, Port, Link, OFSwitch

def logical(dpid):
    p1, p2, p3, p4 = [Port({'index': i}) for i in ['143','141','142','144']]
    pc, ps, pr1, pr2 = [Port() for _ in range(4)]
    pc.address = {'type': 'ipv4', 'address': '10.10.1.10'}
    ps.address = {'type': 'ipv4', 'address': '10.10.2.10'}
    pr1.address = {'type': 'ipv4', 'address': '10.10.1.1'}
    pr2.address = {'type': 'ipv4', 'address': '10.10.2.1'}
    pr1.index, pr2.index = '0', '1'

    l_c_sw1 = Link({'directed': False, 'endpoints': [pc, p1]})
    l_sw1_r = Link({'directed': False, 'endpoints': [p2, pr1]})
    l_r_sw2 = Link({'directed': False, 'endpoints': [pr2, p3]})
    l_sw2_s = Link({'directed': False, 'endpoints': [p4, ps]})

    client, server, router = Node({'name': 'client', 'ports': [pc]}), Node({'name': 'server', 'ports': [ps]}), Node({'name': 'router', 'ports': [pr1, pr2]})
    sw1, sw2 = OFSwitch({'name': 'sw_v1', 'dpid': dpid, 'ports': [p1, p2]}), OFSwitch({'name': 'sw_v2', 'dpid': dpid, 'ports': [p3, p4]})

    return [p1, p2, p3, p4, pc, ps, pr1, pr2, l_c_sw1, l_sw1_r, l_r_sw2, l_sw2_s, client, server, router, sw1, sw2]

def physical(dpid):
    # Layer2
    p1, p2, p3, p4 = [Port({'index': i}) for i in ['143','141','142','144']]
    pc, ps, pr1, pr2 = [Port() for _ in range(4)]
    pc.address = {'type': 'ipv4', 'address': '10.10.1.10'}
    ps.address = {'type': 'ipv4', 'address': '10.10.2.10'}
    pr1.address = {'type': 'ipv4', 'address': '10.10.1.1'}
    pr2.address = {'type': 'ipv4', 'address': '10.10.2.1'}
    pr1.index, pr2.index = '0', '1'

    l_c_sw1 = Link({'directed': False, 'endpoints': [pc, p1]})
    l_sw1_r = Link({'directed': False, 'endpoints': [p2, pr1]})
    l_r_sw2 = Link({'directed': False, 'endpoints': [pr2, p3]})
    l_sw2_s = Link({'directed': False, 'endpoints': [p4, ps]})

    client, server, router = Node({'name': 'client', 'ports': [pc]}), Node({'name': 'server', 'ports': [ps]}), Node({'name': 'router', 'ports': [pr1, pr2]})
    sw = OFSwitch({'name': 'sw_v1', 'dpid': dpid, 'ports': [p1, p2, p3, p4]})

    # Layer3
    p3_1, p3_2, p3_3, p3_4 = [Port() for _ in range(4)]
    l_c_r = Link({'directed': False, 'endpoints': [p3_1, p3_2]})
    l_s_r = Link({'directed': False, 'endpoints': [p3_3, p3_4]})
    client.ports.append(p3_1)
    router.ports.append(p3_2)
    router.ports.append(p3_3)
    server.ports.append(p3_4)

    return [p1, p2, p3, p4, pc, ps, pr1, pr2, l_c_sw1, l_sw1_r, l_r_sw2, l_sw2_s, client, server, router, sw, p3_1, p3_2, p3_3, p3_4, l_c_r, l_s_r]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logical', action='store_true')
    parser.add_argument('dpid', metavar='N', type=str)
    args = parser.parse_args()
    rt = Runtime('http://localhost:30100', cache={'preload': ['nodes', 'ports', 'links']})
    
    for n in rt.nodes:
        rt.nodes.remove(n)
    for p in rt.ports:
        rt.ports.remove(p)
    for l in rt.links:
        rt.links.remove(l)

    res = logical(args.dpid) if args.logical else physical(args.dpid)
    for r in res:
        rt.insert(r, commit=True)
    rt.flush()
