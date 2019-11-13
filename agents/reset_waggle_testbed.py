from pymongo import MongoClient

import requests,json

try:
    client = MongoClient('localhost', 27017)
    client.drop_database('unis_db')
except: print("Connection to mongodb unavailable")

ports = [{'id': str(i+1), 'selfRef': 'http://unis:30100/ports/{}'.format(i+1),
          '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/port#'} for i in range(5 * 2)]

nodes = [
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'selfRef': 'http://unis:30100/nodes/1',
      'id': '1',
      'name': 'waggle_node_1',
      'usage': 0.2,
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/1'}],
      'cpu_util': 0.3,
      'functions': {
          'create': [],
          'delete': [],
          'active': [{'name': 'traffic_plugin', 'configuration': {}}],
          'modified': []
      }
    },
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'selfRef': 'http://unis:30100/nodes/2',
      'id': '2',
      'name': 'waggle_node_2',
      'usage': 0.7,
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/3'}],
      'functions': {
          'create': [],
          'delete': [],
          'active': [{'name': 'traffic_plugin', 'configuration': {}}],
          'modified': []
     }
    },
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'selfRef': 'http://unis:30100/nodes/3',
      'id': '3',
      'name': 'waggle_node_3',
      'usage': 0.3,
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/5'}],
      'functions': {
          'create': [],
          'delete': [],
          'active': [{'name': 'traffic_plugin', 'configuration': {}}],
          'modified': []
      }
    },
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'selfRef': 'http://unis:30100/nodes/4',
      'id': '4',
      'name': 'waggle_node_4',
      'usage': 0.5,
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/7'}],
      'functions': {
          'create': [],
          'delete': [],
          'active': [{'name': 'traffic_plugin', 'configuration': {}}],
          'modified': []
      }
    },
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'selfRef': 'http://unis:30100/nodes/5',
      'id': '5',
      'name': 'waggle_node_5',
      'usage': 0.5,
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/9'}],
      'functions': {
          'create': [],
          'delete': [],
          'active': [],
          'modified': []
      }
    },
    { 'type': 'waggle_beehive',
      '$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/node#',
      'name': 'waggle_beehive_1',
      'ports': [{'rel': 'full', 'href': 'http://unis:30100/ports/{}'.format(p+1)} for p in range(1, len(ports), 2)],
      'selfRef': 'http://unis:30100/nodes/6',
      'id': '6'
    }
]

links = [{'$schema': 'http://unis.open.sice.indiana.edu/schema/20160630/link#', 'directed': False, 'endpoints': [{'rel': 'full', 'href': 'http://unis:30100/ports/{}'.format(i+1)},
                                                                                                                 {'rel': 'full', 'href': 'http://unis:30100/ports/{}'.format(i+2)}],
          'selfRef': 'http://unis:30100/links/{}'.format(i), 'id': str(i)} for i in range(0, len(ports), 2)]

requests.post('http://localhost:30100/ports', data=json.dumps(ports))
requests.post('http://localhost:30100/nodes', data=json.dumps(nodes))
requests.post('http://localhost:30100/links', data=json.dumps(links))
