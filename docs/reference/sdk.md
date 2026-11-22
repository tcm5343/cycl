# Python SDK

The functions below are the ones the CLI uses.

```{eval-rst}
.. autofunction:: cycl.get_graph_data

.. autofunction:: cycl.build_graph
```

## Example

```python
import networkx as nx

from cycl import build_graph

graph = build_graph()
cycles = list(nx.simple_cycles(graph))
```
