"""Synthetic graph API cases; no model, corpus, service, or network."""
import math
from mpe_lkg.graph import strongest_path

nodes = [{'id': str(i)} for i in range(1, 5)]
edges = [
    {'from': '1', 'to': '3', 'value': .9},
    {'from': '2', 'to': '3', 'value': .9},
    {'from': '2', 'to': '4', 'value': .9},
    {'from': '1', 'to': '4', 'value': .1},
]
graph = {'nodes': nodes, 'edges': edges}
path, weights, mean = strongest_path(graph, '1', '4')
directed_pairs = {(e['from'], e['to']) for e in edges}
forward = all((a, b) in directed_pairs for a, b in zip(path, path[1:]))
print('path:', path, 'directed_edges_only:', forward)
assert path == ['1', '3', '2', '4'] and not forward

edges2 = [
    {'from': '1', 'to': '4', 'value': .8},
    {'from': '1', 'to': '2', 'value': .9},
    {'from': '2', 'to': '3', 'value': .9},
    {'from': '3', 'to': '4', 'value': .9},
]
path2, weights2, mean2 = strongest_path({'nodes': nodes, 'edges': edges2}, '1', '4')
other_product = .9 ** 3
other_mean = math.prod([.9, .9, .9]) ** (1 / 3)
print('selected:', path2, 'product:', math.prod(weights2), 'mean:', round(mean2, 3))
print('alternative product:', round(other_product, 3), 'mean:', round(other_mean, 3))
assert path2 == ['1', '4'] and other_product < math.prod(weights2) and other_mean > mean2
