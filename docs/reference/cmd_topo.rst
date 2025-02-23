cycl topo
================================

.. argparse::
    :module: cycl.cli
    :func: create_parser
    :prog: cycl
    :path: topo
    
    --ignore-nodes : @after
        .. math::

            \forall v \in G, \quad v \notin V_{\text{ignored}}

    --ignore-edge : @after
        .. math::

            \forall (u, v) \in E(G), \quad (u, v) \notin E_{\text{ignored}}
