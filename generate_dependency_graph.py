#!/usr/bin/python

import igraph as ig
import os

def generate(builddir, excludes):
    map_path_v = {}

    depgraph = ig.Graph(directed=True) # edges from target to prerequisite

    # sp.run(["ls", builddir])


    def get_or_add_vertex(graph, vertex_id_map, name):
        vid = vertex_id_map.get(name)
        if vid is None:
            vid = len(graph.vs)
            vertex_id_map[name] = vid
            graph.add_vertices(1)
            graph.vs[vid]["path"] = name
        return vid

    edges = []

    # read cmake dependency information
    for root, _, files in os.walk(builddir):
        for f in files:
            if f == "depend.internal":
                path = os.path.join(root, f)

                with open(path, "r") as fh:
                    target_id = -1
                    for line in fh:
                        if (not line.strip()) or line.strip().startswith("#"):
                            continue

                        path = line.strip()
                        prefix = os.path.join(builddir, "")
                        if path.startswith(prefix): path = path[len(prefix):]
                        if not line.startswith(" "):
                            path = os.path.join("build", line.strip())

                        # exclude certain patterns
                        excluded = False
                        for r in excludes:
                            if r.search(path):
                                excluded = True
                                break

                        if line.startswith(" "):
                            # prerequisites of excluded targets are excluded as well
                            if (not excluded) and target_id != -1:
                                prereq_id = get_or_add_vertex(depgraph, map_path_v, path)
                                edges.append((target_id, prereq_id))
                        else:
                            if excluded:
                                target_id = -1
                            else:
                                target_id = get_or_add_vertex(depgraph, map_path_v, path)

    depgraph.add_edges(edges)

    return depgraph


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("builddir")
    args = parser.parse_args()

    depgraph = generate(args.builddir, [])

    print("# laying out graph")
    layout = depgraph.layout("kamada_kawai")

    print("# plotting graph")
    ig.plot(depgraph, "depgraph.pdf", layout=layout)

