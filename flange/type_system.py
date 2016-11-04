#!/usr/bin/env python

"""
Type system for merging rules in Flange
"""

import collections
import operator

from graph import Graph
from graph import Node

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
        print("Source node = %s" %(self.source.get_id()))
        print("Destination node = %s" %(self.destination.get_id()))
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
        print("Source = %s" %(self.source.get_id()))
        print("Destination = %s" %(self.destination.get_id()))
        print("Weight = %s" %(self.weight))
        print("Total Demand = %s" %(self.total_demand))
        print("Allocated = %s" %(self.allocated))
        print("\napplications = %s" %(map ((lambda x: x.Id), self.applist)))
        print("\nPreferred Tunnels [Allocation Details]:\n")
        util.print_tunnels(self.preferred_tunnels)
        print("-------------------------------------------------------------------------------------------\n")

class Tunnel:
    def __init__(self, nodes):
        #self.source = source
        #self.destination = destination
        self.nodes = nodes
        self.channels = []
        self.total_bandwidth = 0
        self.available_bandwidth = 0

    def add_channels(self):
        for i in range (0, len(self.nodes), 1):
            if i != (len(self.nodes) - 1):
                e = self.nodes[i].get_edge(self.nodes[i+1])
                if e:
                    self.channels.append(e)

    def set_total_bandwidth (self):
        min_total_bandwidth = min(map ((lambda edge: edge.weight), self.channels))

        self.total_bandwidth = min_total_bandwidth
        self.available_bandwidth = min_total_bandwidth

    def request_bandwidth (self, demand):
        min_bandwidth = min(map ((lambda edge: edge.weight), self.channels))
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

    def print_tunnel (self):
        print("Tunnel Path :")
        print("%s ====[%s] %s" %(self.channels[0].source.get_id(), self.channels[0].weight, self.channels[0].des.get_id()))
        for i in range (1, len(self.channels), 1):
            if (self.channels[i-1].des == self.channels[i].source):
                print("%s ====[%s] %s" %(self.channels[i].source.get_id(), self.channels[i].weight, self.channels[i].des.get_id()))
            else:
                print("%s ====[%s] %s" %(self.channels[i].des.get_id(), self.channels[i].weight, self.channels[i].source.get_id()))
                print("\nTunnel total bandwidth = %s" %(self.total_bandwidth))
                print("Tunnel available bandwidth = %s" %(min(map ((lambda edge: edge.weight), self.channels))))

class Utils:
    def assign_tunnels (self, flowG):
        paths = g.find_all_paths(flowG.source, flowG.destination)
        FG_Tunnels = {}    

        for tunnel in paths:
            t = Tunnel(tunnel)
            t.add_channels()
            t.set_total_bandwidth()
            FG_Tunnels[t] = len(tunnel)

        flowG.preferred_tunnels = collections.OrderedDict(sorted(FG_Tunnels.items(), key=operator.itemgetter(1)))
        tup = flowG.preferred_tunnels.items()
        for t in tup:
            flowG.preferred_tunnels[t[0]] = 0	#setting length value to zero for later use (to store allocated bandwidth from this tunnel) 

    def print_tunnels (self, FG_tunnel):
        tup = FG_tunnel.items()
        for t in tup:
            t[0].print_tunnel()
            print("Tunnel allocated bandwidth: %s\n" %(t[1]))

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
    g = Graph()

    nodeA = g.add_node('A')
    nodeB = g.add_node('B')
    nodeC = g.add_node('C')
    nodeD = g.add_node('D')
    nodeE = g.add_node('E')
    nodeF = g.add_node('F')

    g.add_edge('A', 'B', 7)  
    g.add_edge('A', 'C', 9)
    g.add_edge('A', 'F', 14)  
    g.add_edge('B', 'C', 10)
    g.add_edge('B', 'D', 15)
    g.add_edge('C', 'D', 11)
    g.add_edge('C', 'F', 6)
    g.add_edge('D', 'E', 6)
    g.add_edge('E', 'F', 9)

    #g.print_graph()
    #g.print_paths()

    app1 = app("app1", 10, nodeA, nodeB)
    app2 = app("app2", 1, nodeA, nodeB)
    app3 = app("app3", 0.5, nodeA, nodeC)

    app1.set_demand(15)
    app2.set_demand(5)
    app3.set_demand(10)

    app1.print_application()
    app2.print_application()
    app3.print_application()

    FG1 = FlowGroup("fg1", nodeA, nodeB)
    FG2 = FlowGroup("fg2", nodeA, nodeC)

    FG1.add_app(app1)
    FG1.add_app(app2)
    FG2.add_app(app3)

    util.assign_tunnels(FG1)
    util.assign_tunnels(FG2)

    b4_fairflow = B4_Max_Min_Fairshare()
    b4_fairflow.generate_TunnelGroup([FG1, FG2])

'''
nodeA = g.add_node('A')
nodeB = g.add_node('B')
nodeC = g.add_node('C')
nodeD = g.add_node('D')

    g.add_edge('A', 'B', 10)  
    g.add_edge('A', 'C', 10)
    g.add_edge('A', 'D', 5)  
    g.add_edge('B', 'C', 10)
    g.add_edge('C', 'D', 5)

'''

