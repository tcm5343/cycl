# Python SDK

Everything importable from the top-level `cycl` package is public API. Modules prefixed with an underscore
(e.g. `cycl._fetch`, `cycl._utils`) are internal and may change without notice.

## Functions

```{eval-rst}
.. autofunction:: cycl.fetch_exports

.. autofunction:: cycl.build_graph

.. autofunction:: cycl.merge_graphs
```

## Models

```{eval-rst}
.. autoclass:: cycl.Stack

.. autoclass:: cycl.Export
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
assumed role credentials). A client you pass in is used as is, so give it a retry configuration to avoid
throttling on accounts with many exports (the client cycl creates by default uses the one below).

```python
import boto3
from botocore.config import Config

from cycl import build_graph, fetch_exports

cfn_client = boto3.Session(profile_name='my-profile', region_name='us-west-2').client(
    'cloudformation',
    config=Config(retries={'max_attempts': 10, 'mode': 'adaptive'}),
)
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

### Group stacks by tag

Fetch with `describe_stacks=True` to fill in each {class}`~cycl.Stack`'s `tags` (one extra paginated
`DescribeStacks` call, and the `cloudformation:DescribeStacks` permission). Nodes can then be any grouping you tag
stacks with, such as the repository that deploys them.

```python
graph = build_graph(
    fetch_exports(describe_stacks=True),
    node_key_fn=lambda stack: stack.tags.get('github-repo', stack.name),  # untagged stacks stay on their own
    remove_selfloops=True,
)
```

### Merge accounts and regions

{func}`~cycl.merge_graphs` combines graphs from several accounts or regions into one. Nodes with the same key are
merged, so pick a `node_key_fn` that means the same thing everywhere.

Grouping by a tag finds cycles between repositories across all of their deployments. This is a real ordering
problem if a repository is released to every account together, but not if each account is deployed on its own:

```python
import boto3
import networkx as nx
from botocore.config import Config

from cycl import build_graph, fetch_exports, merge_graphs

retries = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
targets = {
    ('dev', 'us-east-1'): boto3.Session(profile_name='dev', region_name='us-east-1'),
    ('prod', 'us-east-1'): boto3.Session(profile_name='prod', region_name='us-east-1'),
    ('prod', 'us-west-2'): boto3.Session(profile_name='prod', region_name='us-west-2'),
}

graphs = {
    source: build_graph(
        fetch_exports(cfn_client=session.client('cloudformation', config=retries), describe_stacks=True),
        node_key_fn=lambda stack: stack.tags.get('github-repo', stack.name),
        remove_selfloops=True,
    )
    for source, session in targets.items()
}
merged = merge_graphs(graphs)

for cycle in nx.simple_cycles(merged):
    print(' -> '.join(cycle))
    for u, v in zip(cycle, cycle[1:] + cycle[:1]):
        for (source, export_name), attrs in merged[u][v].items():  # edges are keyed by (source, export name)
            print(f'  {u} -> {v} via {export_name} in {source}')
```

To keep each source apart instead, for example to see every stack in one graph, include the source in the key.
Without `describe_stacks`, a stack which only imports has no `id`, so in a merged graph such stacks with the same
name in different sources are equal and kept once in a node's `stacks`. Fetch with `describe_stacks=True` to keep them
apart, and to tell from each node's `stacks` which accounts it spans, since `Stack.id` is the stack ARN.

```python
graphs = {
    source: build_graph(fetch_exports(cfn_client=session.client('cloudformation', config=retries)),
                        node_key_fn=lambda stack, source=source: (*source, stack.name))
    for source, session in targets.items()
}
merged = merge_graphs(graphs)  # no cycles across sources, since exports cannot be imported across them
```

### Deployment order

```python
if nx.is_directed_acyclic_graph(graph):
    for generation in nx.topological_generations(graph):
        print(sorted(generation))  # stacks in a generation can be deployed in parallel
```
