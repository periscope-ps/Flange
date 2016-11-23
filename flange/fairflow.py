#!/usr/bin/env python

"""
Type system for merging rules in Flange
"""

import collections
import operator
import networkx as nx

class app:
    def __init__(self, iD, weight, source_site, destination_site):
        self.Id = iD
        self.weight = weight
        self.source = source_site
        self.destination = destination_site
        self.allow_access = False
        self.demand = 0

    def set_demand (self, demand):
        self.demand = demand

    def print_application (self):
        print("### Application %s Details ###\n" %(self.Id))
        print("Weight assigned = %s" %(self.weight))
        print("Source node = %s" %(self.source))
        print("Destination node = %s" %(self.destination))
        print("Bandwidth required = %s" %(self.demand))
        print("-------------------------------------------------------------------------------------------\n")

class FlowGroup:
    def __init__(self, iD, source, destination):
        self.id = iD
        self.source = source
        self.destination = destination
        self.applist = []
        self.preferred_tunnels = {}
        self.weight = 0
        self.total_demand = 0
        self.demand = 0
        self.allocated = 0

    def add_app (self, app):
        if (app.source == self.source) and (app.destination == self.destination):
            self.applist.append(app)
            self.demand += app.demand
            self.total_demand += app.demand
            self.weight += app.weight
        else:
            print("app %s not added because of source or destination mismatch with FlowGroup (%s -> %s)" %(app.Id, self.source, self.destination))

    def get_applications (self):
        return self.applist

    def print_flowgroup (self):
        util = Utils()
        print("### FlowGroup %s Details ###\n" %(self.id))
        print("Source = %s" %(self.source))
        print("Destination = %s" %(self.destination))
        print("Weight = %s" %(self.weight))
        print("Total Demand = %s" %(self.total_demand))
        print("Allocated = %s" %(self.allocated))
        print("\napplications = %s" %list(map ((lambda x: x.Id), self.applist)))
        print("\nPreferred Tunnels [Allocation Details]:\n")
        util.print_tunnels(self.preferred_tunnels)
        print("-------------------------------------------------------------------------------------------\n")

class Edge:
    def __init__(self, source, des, graph):
        self.source = source
        self.des = des
        self.graph = graph

    def __setattr__(self, name, value):
        if name == "weight":
            self.graph.get_edge_data(self.source, self.des)[name] = value
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        return self.graph.get_edge_data(self.source, self.des)[name] 

class Tunnel:
    def __init__(self, nodes):
        #self.source = source
        #self.destination = destination
        self.nodes = nodes
        self.channels = []
        self.total_bandwidth = 0
        self.available_bandwidth = 0

    def add_channels(self, graph):
        for (src, dst) in zip(self.nodes[:-1], self.nodes[1:]):
            self.channels.append(Edge(src, dst, graph))

    def set_total_bandwidth (self):
        min_total_bandwidth = min(map ((lambda edge: edge.weight), self.channels))

        self.total_bandwidth = min_total_bandwidth
        self.available_bandwidth = min_total_bandwidth

    def request_bandwidth (self, demand):
        min_bandwidth = min(map(lambda edge: edge.weight, self.channels))
        if min_bandwidth != 0:
            if demand >= min_bandwidth:
                self.available_bandwidth = 0
                for edge in self.channels:
                    edge.weight -= min_bandwidth
                return min_bandwidth
            else:
                self.available_bandwidth -= demand
                for edge in self.channels:
                    edge.weight -= demand
                return demand
        else:
            return 0

    def __repr__(self):
        return "{0} ====[{1:.2f}] {2}".format(self.channels[0].source, self.channels[0].weight, self.channels[-1].des)

    def print_tunnel (self):
        print("Tunnel Path :", end="")
        print("%s ====[%s] %s" %(self.channels[0].source, self.channels[0].weight, self.channels[0].des), end="")
        for i in range (1, len(self.channels), 1):
            if (self.channels[i-1].des == self.channels[i].source):
                print("%s ====[%s] %s" %(self.channels[i].source, self.channels[i].weight, self.channels[i].des), end="")
            else:
                print("%s ====[%s] %s" %(self.channels[i].des, self.channels[i].weight, self.channels[i].source), end="")
        print("\nTunnel total bandwidth = %s" %(self.total_bandwidth))
        print("Tunnel available bandwidth = %s" %(min(map ((lambda edge: edge.weight), self.channels))))

class Utils:

    def __init__ (self):
        self.fg_id = 0
        self.flowgroups = []

    def assign_flowgroup (self, graph, applist):
        for app in applist:
            flwg_assigned = False
            for flwg in self.flowgroups:
                if (flwg.source == app.source) and (flwg.destination == app.destination):
                    flwg.add_app(app)
                    flwg_assigned = True
                    break
            if not flwg_assigned:
                flwg_id = self.fg_id + 1
                self.fg_id += 1
                new_flwg = FlowGroup("FLWG" + str(flwg_id), app.source, app.destination)
                new_flwg.add_app(app)
                self.flowgroups.append(new_flwg)

        for flwg in self.flowgroups:
            self.assign_tunnels(graph, flwg)

    def get_flowgroups (self):
        return self.flowgroups

    def assign_tunnels (self, graph, flowG):
        paths = nx.all_simple_paths(graph, flowG.source, flowG.destination)
        FG_Tunnels = {}    

        for tunnel in paths:
            t = Tunnel(tunnel)
            t.add_channels(graph)
            t.set_total_bandwidth()
            FG_Tunnels[t] = len(tunnel)

        presort = sorted(FG_Tunnels.items(), key=lambda e: str(e[0]))
        flowG.preferred_tunnels = collections.OrderedDict(sorted(presort, key=operator.itemgetter(1)))
        tup = flowG.preferred_tunnels.items()
        for t in tup:
            flowG.preferred_tunnels[t[0]] = 0	#setting length value to zero for later use (to store allocated bandwidth from this tunnel) 

    def print_flowgroups (self):
        for flwg in self.flowgroups:
            print("Flow Group : id = %s, source = %s, destination = %s" %(flwg.id, flwg.source, flwg.destination))

    def print_tunnels (self, FG_tunnel):
        for (tunnel, allocation) in FG_tunnel.items():
            tunnel.print_tunnel()
            print("Tunnel allocated bandwidth: %s\n" %(allocation))

class B4_Max_Min_Fairshare:
    def __init__(self):
        self.fairshare = 0

    def generate_TunnelGroup (self, FGlist):
        FGlist.sort(key = lambda x: x.demand)

        while (True):
            self.fairshare += 0.1

            for flwG in FGlist:
                if flwG.demand > 0:
                    request_bw = flwG.weight * self.fairshare

                    if request_bw > flwG.demand:
                        request_bw = flwG.demand

                    tup = flwG.preferred_tunnels.items()

                    for t in tup:
                        allocated_bw = t[0].request_bandwidth(request_bw)
                        flwG.demand -= allocated_bw
                        flwG.preferred_tunnels[t[0]] += allocated_bw
                        flwG.allocated += allocated_bw
                        if allocated_bw == request_bw:
                            break
                        else:
                            request_bw -= allocated_bw

            demands_satisfied = 1
            bottleneck = 1

            for flwG in FGlist:
                if flwG.demand != 0:
                    demands_satisfied = 0

                tup = flwG.preferred_tunnels.items()
                for t in tup:
                    if (min(map ((lambda edge: edge.weight), t[0].channels))) != 0:
                        bottleneck = 0

            if (demands_satisfied == 1) or (bottleneck == 1):
                print("\n!!! B4_Max_Min_Fairshare Algorithm Terminated - Either Flow Graph demands satisfied or Bottleneck occured !!!\n")
                break

            if (self.fairshare > 1000):
                print("\n!!! B4_Max_Min_Fairshare Algorithm - Either Infinite Loop or High Bandwidth Channels !!!\n")
                break

        for flwG in FGlist:
            flwG.print_flowgroup()

        return


if __name__ == '__main__':
    util = Utils()
    g = nx.Graph()

    nodeA = g.add_node('A')
    nodeB = g.add_node('B')
    nodeC = g.add_node('C')
    nodeD = g.add_node('D')
    nodeE = g.add_node('E')
    nodeF = g.add_node('F')

    g.add_edge('A', 'B', weight=7)  
    g.add_edge('A', 'C', weight=9)
    g.add_edge('A', 'F', weight=14)  
    g.add_edge('B', 'C', weight=10)
    g.add_edge('B', 'D', weight=15)
    g.add_edge('C', 'D', weight=11)
    g.add_edge('C', 'F', weight=6)
    g.add_edge('D', 'E', weight=6)
    g.add_edge('E', 'F', weight=9)

#    nodeA = g.add_node('A')
#    nodeB = g.add_node('B')
#    nodeC = g.add_node('C')
#    nodeD = g.add_node('D')
#
#    g.add_edge('A', 'B', weight=10)  
#    g.add_edge('A', 'C', weight=10)
#    g.add_edge('A', 'D', weight=5)  
#    g.add_edge('B', 'C', weight=10)
#    g.add_edge('C', 'D', weight=5)

    app1 = app("app1", 10, 'A', 'B')
    app2 = app("app2", 1, 'A', 'B')
    app3 = app("app3", 0.5, 'A', 'C')

    app1.set_demand(15)
    app2.set_demand(5)
    app3.set_demand(10)

    app1.print_application()
    app2.print_application()
    app3.print_application()

    applist = [app1, app2, app3]

    util.assign_flowgroup(g, applist)
    fg_list = util.get_flowgroups()

    b4_fairflow = B4_Max_Min_Fairshare()
    b4_fairflow.generate_TunnelGroup(fg_list)

