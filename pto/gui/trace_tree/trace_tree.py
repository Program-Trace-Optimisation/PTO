"""Visualise a trace as a top-down tree using Graphviz.

Usage::

    from pto.gui.trace_tree import trace_tree
    trace_tree(geno)          # render and open
    trace_tree(geno, "out")   # save to out.pdf

    # Compare two traces (e.g., before/after mutation)
    trace_tree_diff(original.geno, mutant.geno)

    # Show crossover contributions from two parents
    trace_tree_crossover(child.geno, parent1.geno, parent2.geno)
"""

import graphviz


# Colors for diff visualization
COLORS = {
    "unchanged": "black",
    "changed": "red",
    "added": "green",
    "removed": "gray",
    "parent1": "blue",
    "parent2": "orange",
    "mixed": "purple",
}


def _build_trie(trace):
    """Build a trie (nested dicts) from slash-separated trace keys.

    Leaves are stored under a special ``_dist`` key.
    """
    root = {}
    for key, dist in trace.items():
        parts = str(key).split("/")
        node = root
        for part in parts:
            node = node.setdefault(part, {})
        node["_dist"] = dist
    return root


_counter = 0


def _next_id():
    global _counter
    _counter += 1
    return f"n{_counter}"


def _format_val(val):
    """Format a value for display."""
    if isinstance(val, float):
        return f"{val:.4g}"
    return str(val)


def _add_nodes(dot, trie, parent_id, depth, levels, leaves, key_to_id=None, path=""):
    """Recursively add nodes and edges to the Digraph."""
    for label, child in trie.items():
        if label == "_dist":
            continue

        node_id = _next_id()
        full_path = f"{path}/{label}" if path else label
        if key_to_id is not None:
            key_to_id[full_path] = node_id

        is_leaf = "_dist" in child and len(child) == 1

        if is_leaf:
            dist = child["_dist"]
            fun_name = dist.fun.__name__
            val = _format_val(dist.val)
            display = f"{fun_name} -> {val}"
            dot.node(node_id, display, shape="box")
            leaves.append(node_id)
        else:
            dot.node(node_id, label, shape="box", style="rounded")
            levels.setdefault(depth, []).append(node_id)

        dot.edge(parent_id, node_id)

        if not is_leaf:
            _add_nodes(dot, child, node_id, depth + 1, levels, leaves, key_to_id, full_path)


def trace_tree(trace, filename=None, view=True):
    """Render a trace dictionary as a top-down tree.

    Parameters
    ----------
    trace : dict
        A genotype trace mapping path keys to ``Dist`` objects.
    filename : str, optional
        Output file path (without extension). If *None* a temporary
        file is used.
    view : bool
        Whether to open the rendered image automatically.

    Returns
    -------
    graphviz.Digraph
        The Digraph object (can be displayed inline in Jupyter).
    """
    global _counter
    _counter = 0

    trie = _build_trie(trace)

    dot = graphviz.Digraph(
        "trace_tree",
        graph_attr={"rankdir": "TB", "ranksep": "0.6", "nodesep": "0.4"},
        node_attr={"fontname": "Helvetica", "fontsize": "11"},
        edge_attr={"arrowsize": "0.6"},
    )

    # Determine the single root or create a synthetic one
    top_keys = [k for k in trie if k != "_dist"]
    if len(top_keys) == 1:
        root_label = top_keys[0]
        root_children = trie[root_label]
    else:
        root_label = "root"
        root_children = trie

    root_id = _next_id()
    dot.node(root_id, root_label, shape="box", style="rounded")

    levels = {0: [root_id]}
    leaves = []
    _add_nodes(dot, root_children, root_id, 1, levels, leaves)

    # Align internal nodes at the same depth
    for depth, node_ids in levels.items():
        with dot.subgraph() as s:
            s.attr(rank="same")
            for nid in node_ids:
                s.node(nid)

    # Force all leaves to the bottom
    with dot.subgraph() as s:
        s.attr(rank="sink")
        for nid in leaves:
            s.node(nid)

    if filename is not None:
        dot.render(filename, view=view, cleanup=True)
    elif view:
        dot.render(view=True, cleanup=True)

    return dot


def _compute_diff(trace1, trace2):
    """Compute differences between two traces.

    Returns dict mapping trace keys to status:
    'unchanged', 'changed', 'added', 'removed'
    """
    keys1 = set(trace1.keys())
    keys2 = set(trace2.keys())

    diff = {}
    for key in keys1 | keys2:
        if key in keys1 and key not in keys2:
            diff[key] = "removed"
        elif key not in keys1 and key in keys2:
            diff[key] = "added"
        elif trace1[key].val == trace2[key].val:
            diff[key] = "unchanged"
        else:
            diff[key] = "changed"
    return diff


def _compute_crossover_origin(child_trace, parent1_trace, parent2_trace):
    """Determine which parent each trace entry came from.

    Returns dict mapping trace keys to 'parent1', 'parent2', or 'mixed'.
    """
    origin = {}
    for key, dist in child_trace.items():
        val = dist.val
        p1_val = parent1_trace.get(key, None)
        p2_val = parent2_trace.get(key, None)

        p1_match = p1_val is not None and p1_val.val == val
        p2_match = p2_val is not None and p2_val.val == val

        if p1_match and p2_match:
            origin[key] = "parent1"  # arbitrary when both match
        elif p1_match:
            origin[key] = "parent1"
        elif p2_match:
            origin[key] = "parent2"
        else:
            origin[key] = "mixed"  # new value (e.g., from repair)
    return origin


def _add_nodes_colored(dot, trie, parent_id, depth, levels, leaves,
                       trace, coloring, path=""):
    """Add nodes with coloring based on diff or crossover origin."""
    for label, child in trie.items():
        if label == "_dist":
            continue

        node_id = _next_id()
        full_path = f"{path}/{label}" if path else label
        is_leaf = "_dist" in child and len(child) == 1

        # Determine color for this node
        if is_leaf:
            # Find the original trace key for this leaf
            trace_key = None
            for tk in trace.keys():
                if str(tk) == full_path or str(tk).endswith("/" + label):
                    # Match by checking if the path corresponds
                    parts = str(tk).split("/")
                    if parts[-1] == label.split("/")[-1] if "/" in label else label:
                        trace_key = tk
                        break
            # Simpler approach: reconstruct key from path
            trace_key = full_path
            color = COLORS.get(coloring.get(trace_key, "unchanged"), "black")

            dist = child["_dist"]
            fun_name = dist.fun.__name__
            val = _format_val(dist.val)
            display = f"{fun_name} -> {val}"
            dot.node(node_id, display, shape="box", color=color, fontcolor=color)
            leaves.append(node_id)
        else:
            dot.node(node_id, label, shape="box", style="rounded")
            levels.setdefault(depth, []).append(node_id)

        dot.edge(parent_id, node_id)

        if not is_leaf:
            _add_nodes_colored(dot, child, node_id, depth + 1, levels, leaves,
                               trace, coloring, full_path)


def trace_tree_diff(trace1, trace2, filename=None, view=True, title="Mutation Diff"):
    """Visualize differences between two traces (e.g., before/after mutation).

    Colors:
    - Black: unchanged
    - Red: changed value
    - Green: added (new key)
    - Gray: removed (key no longer present)

    Parameters
    ----------
    trace1 : dict
        Original trace (before mutation).
    trace2 : dict
        Modified trace (after mutation).
    filename : str, optional
        Output file path.
    view : bool
        Whether to open the rendered image.
    title : str
        Title for the graph.

    Returns
    -------
    graphviz.Digraph
        The Digraph object.
    """
    global _counter
    _counter = 0

    diff = _compute_diff(trace1, trace2)
    trie = _build_trie(trace2)

    dot = graphviz.Digraph(
        "trace_tree_diff",
        graph_attr={"rankdir": "TB", "ranksep": "0.6", "nodesep": "0.4",
                    "label": title, "labelloc": "t", "fontsize": "14"},
        node_attr={"fontname": "Helvetica", "fontsize": "11"},
        edge_attr={"arrowsize": "0.6"},
    )

    top_keys = [k for k in trie if k != "_dist"]
    if len(top_keys) == 1:
        root_label = top_keys[0]
        root_children = trie[root_label]
    else:
        root_label = "root"
        root_children = trie

    root_id = _next_id()
    dot.node(root_id, root_label, shape="box", style="rounded")

    levels = {0: [root_id]}
    leaves = []
    _add_nodes_colored(dot, root_children, root_id, 1, levels, leaves,
                       trace2, diff, root_label)

    for depth, node_ids in levels.items():
        with dot.subgraph() as s:
            s.attr(rank="same")
            for nid in node_ids:
                s.node(nid)

    with dot.subgraph() as s:
        s.attr(rank="sink")
        for nid in leaves:
            s.node(nid)

    # Add legend
    with dot.subgraph(name="cluster_legend") as legend:
        legend.attr(label="Legend", style="dashed")
        legend.node("leg_unchanged", "unchanged", shape="box",
                    color=COLORS["unchanged"], fontcolor=COLORS["unchanged"])
        legend.node("leg_changed", "changed", shape="box",
                    color=COLORS["changed"], fontcolor=COLORS["changed"])

    if filename is not None:
        dot.render(filename, view=view, cleanup=True)
    elif view:
        dot.render(view=True, cleanup=True)

    return dot


def trace_tree_crossover(child_trace, parent1_trace, parent2_trace,
                         filename=None, view=True, title="Crossover"):
    """Visualize which parent contributed each trace entry.

    Colors:
    - Blue: from parent 1
    - Orange: from parent 2
    - Purple: mixed/new (e.g., from repair)

    Parameters
    ----------
    child_trace : dict
        Child trace (after crossover).
    parent1_trace : dict
        First parent trace.
    parent2_trace : dict
        Second parent trace.
    filename : str, optional
        Output file path.
    view : bool
        Whether to open the rendered image.
    title : str
        Title for the graph.

    Returns
    -------
    graphviz.Digraph
        The Digraph object.
    """
    global _counter
    _counter = 0

    origin = _compute_crossover_origin(child_trace, parent1_trace, parent2_trace)
    trie = _build_trie(child_trace)

    dot = graphviz.Digraph(
        "trace_tree_crossover",
        graph_attr={"rankdir": "TB", "ranksep": "0.6", "nodesep": "0.4",
                    "label": title, "labelloc": "t", "fontsize": "14"},
        node_attr={"fontname": "Helvetica", "fontsize": "11"},
        edge_attr={"arrowsize": "0.6"},
    )

    top_keys = [k for k in trie if k != "_dist"]
    if len(top_keys) == 1:
        root_label = top_keys[0]
        root_children = trie[root_label]
    else:
        root_label = "root"
        root_children = trie

    root_id = _next_id()
    dot.node(root_id, root_label, shape="box", style="rounded")

    levels = {0: [root_id]}
    leaves = []
    _add_nodes_colored(dot, root_children, root_id, 1, levels, leaves,
                       child_trace, origin, root_label)

    for depth, node_ids in levels.items():
        with dot.subgraph() as s:
            s.attr(rank="same")
            for nid in node_ids:
                s.node(nid)

    with dot.subgraph() as s:
        s.attr(rank="sink")
        for nid in leaves:
            s.node(nid)

    # Add legend
    with dot.subgraph(name="cluster_legend") as legend:
        legend.attr(label="Legend", style="dashed")
        legend.node("leg_p1", "parent 1", shape="box",
                    color=COLORS["parent1"], fontcolor=COLORS["parent1"])
        legend.node("leg_p2", "parent 2", shape="box",
                    color=COLORS["parent2"], fontcolor=COLORS["parent2"])

    if filename is not None:
        dot.render(filename, view=view, cleanup=True)
    elif view:
        dot.render(view=True, cleanup=True)

    return dot


def compare_phenotypes(sol1, sol2, name1="Original", name2="Modified"):
    """Print a side-by-side comparison of two phenotypes."""
    print(f"{name1}: {sol1.pheno}")
    print(f"{name2}: {sol2.pheno}")
    if sol1.pheno == sol2.pheno:
        print("  (identical)")
    else:
        print("  (different)")


def save_dot(dot, filename):
    """Save a Digraph as a .dot file (without rendering).

    Parameters
    ----------
    dot : graphviz.Digraph
        The Digraph object returned by trace_tree, trace_tree_diff, etc.
    filename : str
        Output file path. '.dot' extension is added if not present.

    Example
    -------
    >>> dot = trace_tree(ind.geno, view=False)
    >>> save_dot(dot, "my_figure")  # saves my_figure.dot
    """
    if not filename.endswith(".dot"):
        filename = filename + ".dot"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(dot.source)
    print(f"Saved: {filename}")
