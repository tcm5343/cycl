cycl check
================================

.. argparse::
    :module: cycl.cli
    :func: create_parser
    :prog: cycl
    :path: check
    
    --ignore-nodes : @after
        .. math::

            \forall v \in V(G), \quad v \notin V_{\text{ignored}}

    --ignore-edge : @after
        .. math::

            \forall (u, v) \in E(G), \quad (u, v) \notin E_{\text{ignored}}
