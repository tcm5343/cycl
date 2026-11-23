# Python SDK

Everything importable from the top-level `cycl` package is public API. Modules prefixed with an underscore
(e.g. `cycl._core`, `cycl._utils`) are internal and may change without notice.

## Functions

```{eval-rst}
.. autofunction:: cycl.fetch_exports

.. autofunction:: cycl.build_graph
```

## Models

```{eval-rst}
.. autoclass:: cycl.Stack

.. autoclass:: cycl.Export
```

## Exceptions

```{eval-rst}
.. autoexception:: cycl.CyclError
```

## Examples

### Find cycles

```python
import networkx as nx

from cycl import build_graph, fetch_exports

graph = build_graph(fetch_exports())  # default boto3 credential chain, region and profile

for cycle in nx.simple_cycles(graph):
    print(cycle)
```

### Use a specific profile or region

`fetch_exports` makes many AWS calls, so pass a client configured however you need (profile, region, retries,
assumed role credentials).

```python
import boto3

from cycl import build_graph, fetch_exports

cfn_client = boto3.Session(profile_name='my-profile', region_name='us-west-2').client('cloudformation')
graph = build_graph(fetch_exports(cfn_client=cfn_client))
```

### Explain which exports cause a cycle

Edges are keyed by export name and carry the {class}`~cycl.Export`.

```python
for cycle in nx.simple_cycles(graph):
    print(' -> '.join(cycle))
    for u, v in zip(cycle, cycle[1:] + cycle[:1]):
        for export_name, attrs in graph[u][v].items():
            print(f'  {u} -> {v} via {export_name} = {attrs["export"].value}')
```

### Fetch once, analyze many ways

```python
exports = fetch_exports()  # the expensive part

full = build_graph(exports)
without_shared = build_graph(exports, ignore_nodes=['shared-networking'])
known_ok = build_graph(exports, ignore_edges=[('stack-a', 'stack-b')])
```

### Group stacks into nodes

`node_key_fn` maps each {class}`~cycl.Stack` to a node key. Stacks with the same key become one node, e.g. to find
cycles between environments or applications rather than individual stacks.

```python
graph = build_graph(
    exports,
    node_key_fn=lambda stack: stack.name.split('-')[0],  # 'billing-api' and 'billing-db' -> 'billing'
    remove_selfloops=True,  # dependencies within a group are not cycles between groups
)

graph.nodes['billing']['stacks']   # set of Stack merged into this node
graph.nodes['billing']['exports']  # dict of export name -> Export defined by those stacks
```

### Deployment order

```python
if nx.is_directed_acyclic_graph(graph):
    for generation in nx.topological_generations(graph):
        print(sorted(generation))  # stacks in a generation can be deployed in parallel
```
