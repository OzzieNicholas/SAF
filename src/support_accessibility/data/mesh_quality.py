"""Deterministic diagnostics for the raw meshes retained by SAF cohorts.

The functions in this module are descriptive only.  They do not repair a mesh,
change ingest eligibility, or alter the frozen accessibility label semantics.
"""


def _validated_arrays(vertices, faces):
    import numpy as np

    V = np.asarray(vertices, dtype=float)
    F = np.asarray(faces)
    if V.ndim != 2 or V.shape[1] != 3:
        raise ValueError("vertices must have shape (N, 3)")
    if F.ndim != 2 or F.shape[1] != 3:
        raise ValueError("faces must have shape (M, 3)")
    if not np.isfinite(V).all():
        raise ValueError("vertices must be finite")
    if not np.issubdtype(F.dtype, np.integer):
        raise ValueError("faces must contain integer indices")
    F = np.asarray(F, dtype=np.int64)
    if F.size and (int(F.min()) < 0 or int(F.max()) >= V.shape[0]):
        raise ValueError("face index out of range")
    return V, F


class _UnionFind:
    def __init__(self, n):
        self.parent = list(range(int(n)))

    def find(self, node):
        node = int(node)
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left, right):
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def summarize_mesh_quality(vertices, faces):
    """Return topology and triangle-quality diagnostics as JSON-safe scalars.

    Exact duplicate vertices are merged before topology checks because binary
    STL commonly repeats all three vertices per triangle.  Degenerate faces
    are reported but excluded from edges and connected components: they have no
    surface measure and cannot form a meaningful topological edge.
    """
    import numpy as np

    V, F = _validated_arrays(vertices, faces)
    n_vertices_raw, n_faces = int(V.shape[0]), int(F.shape[0])
    if n_vertices_raw:
        V_merged, inverse = np.unique(V, axis=0, return_inverse=True)
        merged_faces = inverse[F] if n_faces else np.empty((0, 3), dtype=np.int64)
    else:
        V_merged = V
        merged_faces = np.empty((0, 3), dtype=np.int64)

    if n_faces:
        tri = V_merged[merged_faces]
        doubled_area = np.linalg.norm(
            np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1
        )
        diagonal = float(np.linalg.norm(V_merged.max(axis=0) - V_merged.min(axis=0)))
        tolerance = np.finfo(float).eps * diagonal * diagonal
        repeated_vertex = (
            (merged_faces[:, 0] == merged_faces[:, 1])
            | (merged_faces[:, 1] == merged_faces[:, 2])
            | (merged_faces[:, 0] == merged_faces[:, 2])
        )
        degenerate = repeated_vertex | (doubled_area <= tolerance)
    else:
        degenerate = np.zeros(0, dtype=bool)

    valid_faces = merged_faces[~degenerate]
    n_degenerate = int(degenerate.sum())
    n_valid = int(valid_faces.shape[0])

    if n_valid:
        canonical_faces = np.sort(valid_faces, axis=1)
        n_duplicate = n_valid - int(np.unique(canonical_faces, axis=0).shape[0])
        edges = np.concatenate(
            (valid_faces[:, (0, 1)], valid_faces[:, (1, 2)], valid_faces[:, (2, 0)]), axis=0
        )
        canonical_edges = np.sort(edges, axis=1)
        _unique_edges, edge_counts = np.unique(canonical_edges, axis=0, return_counts=True)
        n_boundary = int((edge_counts == 1).sum())
        n_non_manifold = int((edge_counts > 2).sum())

        components = _UnionFind(V_merged.shape[0])
        for a, b, c in valid_faces:
            components.union(a, b)
            components.union(a, c)
        used_vertices = np.unique(valid_faces)
        n_components = len({components.find(vertex) for vertex in used_vertices})
    else:
        n_duplicate = 0
        n_boundary = 0
        n_non_manifold = 0
        n_components = 0

    return {
        "n_vertices_raw": n_vertices_raw,
        "n_vertices_merged": int(V_merged.shape[0]),
        "n_faces": n_faces,
        "n_valid_faces": n_valid,
        "n_degenerate_faces": n_degenerate,
        "degenerate_face_fraction": float(n_degenerate / n_faces) if n_faces else 0.0,
        "n_duplicate_faces": int(n_duplicate),
        "n_boundary_edges": n_boundary,
        "n_non_manifold_edges": n_non_manifold,
        "n_components": int(n_components),
        "is_watertight": bool(n_valid and n_boundary == 0 and n_non_manifold == 0),
    }
