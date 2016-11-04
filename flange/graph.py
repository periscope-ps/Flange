#!/usr/bin/env python

"""
Graph representing the network
"""

class Edge:
    def __init__(self, source, des, weight):
        self.source = source
	self.des = des
	self.weight = weight

class Node:
    def __init__(self, node):
        self.id = node
        self.adjacent = {}
	self.edges = []

    def __str__(self):
        return str([x.id for x in self.adjacent])

    def add_edge(self, edge):
	self.edges.append(edge)

    def get_edge(self, node):
	for edge in self.edges:
	    if edge.des == node:
		return edge
	    elif (edge.source == node):
		return edge

    def print_edges(self):
	for edge in self.edges:
	   print "%s ==== %s" %(edge.source.get_id(), edge.des.get_id())

    def add_neighbor(self, neighbor, weight=0):
        self.adjacent[neighbor] = weight

    def get_connections(self):
        return self.adjacent.keys()  

    def get_neighbors(self):
        return [x.id for x in self.adjacent]

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0

    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_node(self, node):
        self.num_vertices = self.num_vertices + 1
        new_node = Node(node)
        self.vert_dict[node] = new_node
        return new_node

    def get_node(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, src, des, cost = 0):
        if src not in self.vert_dict:
            self.add_node(src)
        if des not in self.vert_dict:
            self.add_node(des)

	new_edge = Edge(self.vert_dict[src], self.vert_dict[des], cost)
	self.vert_dict[src].add_edge(new_edge)
	self.vert_dict[des].add_edge(new_edge)
        self.vert_dict[src].add_neighbor(self.vert_dict[des], cost)
        self.vert_dict[des].add_neighbor(self.vert_dict[src], cost)

    def get_vertices(self):
        return self.vert_dict.keys()

    def find_all_paths(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if not self.vert_dict.has_key(start.get_id()):
            return []
        paths = []
        for node in self.vert_dict[start.get_id()].get_connections():
            if node not in path:
                newpaths = self.find_all_paths(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def find_all_paths2(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if not self.vert_dict.has_key(start):
            return []
        paths = []
        for node in self.vert_dict[start].get_neighbors():
            if node not in path:
                newpaths = self.find_all_paths2(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def print_graph (self):
	print "Graph edges with weights :\n"
	for v in self:
            for w in v.get_connections():
            	vid = v.get_id()
           	wid = w.get_id()
            	print '( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w))
	print "--------------------------"

    def print_paths(self):
	print "Graph nodes with neighbours:\n"
    	for v in self:
            print '[node%s] = %s' %(v.get_id(), self.vert_dict[v.get_id()])
	print "-----------------------------"

    def print_edges(self):
	print "Graph Edges:\n"
    	for v in self:
            print 'node = %s edges : ' %(v.get_id())
	    v.print_edges()
	print "-----------------------------"


