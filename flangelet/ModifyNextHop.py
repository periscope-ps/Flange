from unis.models import Node,Service,Port,Link,Path
from unis import Runtime
from flange import compiler
import json
import argparse


#Method to get the order in which the next hop attributes updates are to be applied
def get_update_order(netpath):
    total_changes = []
    for i in range(0, len(netpath)):
        path = json.loads(netpath[i])
        hops = path['hops']
        update_order = []
        for i in range(0, len(hops)):
            if 'node' in hops[i]['$schema']:
                update_order.append(hops[i]['id'])
        total_changes.append(update_order)
    return total_changes

#Retrieves the latest timestamp of each service
def get_latest_node_timestamp(update):
    node_id = {}
    for service in rt.services:
        if service.id in update:
            if service.id not in node_id:
                node_id[service.id] = service.ts
            else:
                if node_id[service.id] < service.ts:
                    node_id[service.id] = service.ts
        else:
            pass
    return node_id

#Utility to perform the update
def perform_update(path_update_order):
    for update in path_update_order:                 #list which contains a multiple update lists
        update_node = []
        update_hop = []
        latest_services = get_latest_node_timestamp(update)
        for i in range (0, len(update)):             #list which contains the order of update for a path
            for node in rt.services:                 #iterating over the services to match on tha node id
                if update[i] == node.id and latest_services[node.id] == node.ts:
                    update_node.append(node.id)
                    update_hop.append(node.selfRef)
        latest_nodes = get_latest_node_timestamp(update)
        for i in range(0, len(update_node)-1):
            for service in rt.services:
                #Checks for the service id and latest timestamp of the given service
                if update_node[i] == service.id and latest_nodes[service.id] == service.ts:		
                    service.default_next_hop = update_hop[i+1]		#updates the next hop attribute
                    print('Updated next hop of  ',service.selfRef,  ' to  ',  update_hop[i+1])

if __name__ == "__main__":
    #Argparser when the file is invoked from command line
    parser = argparse.ArgumentParser(description='Flangelet to modify the next hop attribute of the service')
    parser.add_argument('-s','--source', help='Source node in the topology', required=True)
    parser.add_argument('-d','--dest', help='Destination node in the topology', required=True)
    parser.add_argument('-r','--runtime', help='UNIS runtime URL', required = True)
    args = vars(parser.parse_args())
    
    runtime_url = args['runtime']
    rt = Runtime(runtime_url)        
    foundSource = False
    foundDest = False
    
    #Validating the source and destination services if they are present in the runtime resources
    for service in rt.services:
    		if args['source'] ==  service.id:
    			source = args['source']
    			foundSource = True
    		if args['dest'] == service.id:
    			dest = args['dest']
    			foundDest = True

    if not foundSource:
    	raise Exception('The source node isn''t present in the topology')
    if not foundDest:
    	raise Exception('The source node isn''t present in the topology')
    
    #Flangelet to compute the netpath for a given source and destination in the topology
    netpath =  compiler.flange("exists { x |  x.id == "+source+" } ~> { x |  x.id == "+dest+" }",
                               db=runtime_url)
    path_update_order = []
    path_update_order = get_update_order(netpath)
    perform_update(path_update_order=path_update_order)
