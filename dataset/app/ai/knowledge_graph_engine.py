"""
knowledge_graph_engine.py
Phase 5.5 — Enterprise Knowledge Graph Engine

Pure Python, deterministic, no external graph libraries.
All edges verified against database fields only.
No ML, no embeddings, no hallucinations.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Deque
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# NODE TYPES
# ─────────────────────────────────────────────────────────────────────────────

NODE_TYPES = frozenset([
    "FIR", "Accused", "Victim", "Witness", "Vehicle", "Weapon",
    "Phone", "Address", "Crime", "Station", "District",
    "Officer", "Evidence", "Organization"
])

# ─────────────────────────────────────────────────────────────────────────────
# EDGE RELATIONSHIP TYPES
# ─────────────────────────────────────────────────────────────────────────────

EDGE_TYPES = frozenset([
    "Appeared In",       # Accused/Victim appeared in a FIR
    "Associated With",   # Two entities share a common link
    "Lives At",          # Accused/Victim lives at Address
    "Uses",              # Accused uses Phone/Vehicle
    "Owns",              # Accused owns Vehicle/Weapon
    "Connected To",      # Entity connected to another entity via shared FIR
    "Investigated By",   # FIR investigated by Officer
    "Recovered From",    # Weapon/Evidence recovered from Accused
    "Occurred At",       # Crime occurred at Address/Station/District
])

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GraphNode:
    """
    A typed node in the investigation knowledge graph.
    """
    node_id: str
    node_type: str          # One of NODE_TYPES
    label: str              # Human-readable name
    attributes: Dict[str, Any] = field(default_factory=dict)
    source_fir_ids: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "attributes": self.attributes,
            "source_fir_ids": self.source_fir_ids,
            "source_fields": self.source_fields,
        }


@dataclass
class GraphEdge:
    """
    A typed, verified directed edge in the investigation knowledge graph.
    Every edge must carry a reason chain and evidence score.
    """
    source_id: str
    target_id: str
    relationship: str       # One of EDGE_TYPES
    confidence: float       # 0.0 – 1.0
    evidence_score: int     # 0 – 100
    supporting_fir_ids: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)
    reason_chain: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "evidence_score": self.evidence_score,
            "supporting_fir_ids": self.supporting_fir_ids,
            "source_fields": self.source_fields,
            "reason_chain": self.reason_chain,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE GRAPH (PURE PYTHON ADJACENCY LIST)
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeGraph:
    """
    Pure Python adjacency-list graph.
    No external graph library dependencies.
    All traversal algorithms implemented from scratch.
    """

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        # Undirected adjacency: node_id → set of neighbour node_ids
        self._adj: Dict[str, Set[str]] = {}
        # Edge lookup: (source, target) → List[GraphEdge]
        self._edge_map: Dict[Tuple[str, str], List[GraphEdge]] = {}

    # ── Node Management ───────────────────────────────────────────────────────

    def add_node(self, node: GraphNode) -> None:
        """Idempotent node insertion — merges source_fir_ids on collision."""
        if node.node_id in self._nodes:
            existing = self._nodes[node.node_id]
            for fid in node.source_fir_ids:
                if fid not in existing.source_fir_ids:
                    existing.source_fir_ids.append(fid)
        else:
            self._nodes[node.node_id] = node
            self._adj[node.node_id] = set()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def node_count(self) -> int:
        return len(self._nodes)

    def all_nodes(self) -> List[GraphNode]:
        return list(self._nodes.values())

    # ── Edge Management ───────────────────────────────────────────────────────

    def add_edge(self, edge: GraphEdge) -> None:
        """
        Add a verified edge. Only edges with evidence_score > 0 are accepted.
        Safety gate: rejects edges without supporting FIR IDs.
        """
        if edge.evidence_score <= 0:
            return
        if not edge.supporting_fir_ids:
            return
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            return

        self._edges.append(edge)
        # Undirected adjacency
        self._adj[edge.source_id].add(edge.target_id)
        self._adj[edge.target_id].add(edge.source_id)
        # Edge map (both directions)
        key_fwd = (edge.source_id, edge.target_id)
        key_rev = (edge.target_id, edge.source_id)
        self._edge_map.setdefault(key_fwd, []).append(edge)
        self._edge_map.setdefault(key_rev, []).append(edge)

    def edge_count(self) -> int:
        return len(self._edges)

    def all_edges(self) -> List[GraphEdge]:
        return list(self._edges)

    def get_edges_between(self, node_a: str, node_b: str) -> List[GraphEdge]:
        return self._edge_map.get((node_a, node_b), [])

    # ── Traversal: FindNeighbors ──────────────────────────────────────────────

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """Return all 1-hop neighbours of a node."""
        neighbor_ids = self._adj.get(node_id, set())
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def get_neighbors_by_type(self, node_id: str, node_type: str) -> List[GraphNode]:
        """Return 1-hop neighbours filtered by type."""
        return [n for n in self.get_neighbors(node_id) if n.node_type == node_type]

    # ── Traversal: ShortestPath (BFS) ─────────────────────────────────────────

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        BFS shortest path between source and target.
        Returns list of node_ids or None if no path exists.
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        if source_id == target_id:
            return [source_id]

        visited: Set[str] = {source_id}
        queue: Deque[List[str]] = deque([[source_id]])

        while queue:
            path = queue.popleft()
            current = path[-1]
            for neighbor in self._adj.get(current, set()):
                if neighbor == target_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def find_all_paths(self, source_id: str, target_id: str, max_depth: int = 4) -> List[List[str]]:
        """
        Find all simple paths up to max_depth hops (capped for performance).
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return []

        results: List[List[str]] = []
        queue: Deque[List[str]] = deque([[source_id]])

        while queue:
            path = queue.popleft()
            if len(path) > max_depth + 1:
                continue
            current = path[-1]
            if current == target_id and len(path) > 1:
                results.append(path)
                continue
            for neighbor in self._adj.get(current, set()):
                if neighbor not in path:
                    queue.append(path + [neighbor])

        return results

    # ── Traversal: ConnectedComponents (Iterative DFS) ───────────────────────

    def find_connected_components(self) -> List[List[str]]:
        """
        Iterative DFS to find all connected components.
        Returns list of components, each being a list of node_ids.
        """
        visited: Set[str] = set()
        components: List[List[str]] = []

        for node_id in self._nodes:
            if node_id not in visited:
                component: List[str] = []
                stack: List[str] = [node_id]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    component.append(current)
                    for neighbor in self._adj.get(current, set()):
                        if neighbor not in visited:
                            stack.append(neighbor)
                components.append(component)

        return components

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_report(self) -> Dict[str, Any]:
        """Serialize the graph to a dict report."""
        components = self.find_connected_components()
        return {
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "nodes": [n.to_dict() for n in self.all_nodes()],
            "edges": [e.to_dict() for e in self.all_edges()],
            "connected_components": components,
            "component_count": len(components),
        }


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE GRAPH ENGINE (BUILDER + QUERY LAYER)
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeGraphEngine:
    """
    Enterprise Knowledge Graph Engine.
    Builds a deterministic, evidence-backed investigation graph
    from database query results and exposes graph query operations.
    """

    MIN_RECORDS = 2  # Safety gate: require at least 2 records to build meaningful graph

    @classmethod
    def build_graph(cls, context: Any) -> Tuple["KnowledgeGraph", Dict[str, Any]]:
        """
        Main builder. Extracts nodes and edges from context.search_result.
        Returns (graph, report_dict).
        """
        results = context.search_result or []

        graph = KnowledgeGraph()

        if len(results) < cls.MIN_RECORDS:
            return graph, cls._empty_report("Insufficient records to build knowledge graph.")

        timestamp = datetime.now(timezone.utc).isoformat()

        # ── Pass 1: Extract all nodes ─────────────────────────────────────────
        for row in results:
            cls._extract_nodes(graph, row, timestamp)

        # ── Pass 2: Build edges from each FIR ────────────────────────────────
        for row in results:
            cls._build_fir_edges(graph, row, timestamp)

        # ── Pass 3: Cross-FIR correlation edges ──────────────────────────────
        cls._build_correlation_edges(graph, results, timestamp)

        # ── Build Report ──────────────────────────────────────────────────────
        base_report = graph.to_report()
        extended = cls._build_extended_report(graph, results)
        report = {**base_report, **extended}

        return graph, report

    # ── Node Extraction ───────────────────────────────────────────────────────

    @classmethod
    def _extract_nodes(cls, graph: KnowledgeGraph, row: Dict, timestamp: str) -> None:
        crime_no = (row.get("crime_no") or row.get("case_no") or
                    row.get("fir_no") or "UNKNOWN")
        fir_id = f"FIR:{crime_no}"

        # FIR node
        graph.add_node(GraphNode(
            node_id=fir_id,
            node_type="FIR",
            label=f"FIR {crime_no}",
            attributes={
                "crime_no": crime_no,
                "category": row.get("crime_category") or row.get("crime_head") or "",
                "date": str(row.get("crime_registered_date") or ""),
                "district": row.get("district_name") or "",
                "station": row.get("police_station_name") or "",
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
            },
            source_fir_ids=[crime_no],
            source_fields=["crime_no"],
        ))

        # Accused nodes
        for acc in cls._extract_name_list(row, "accused_name", "accused_names"):
            node_id = f"Accused:{acc.strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Accused",
                label=acc.strip(),
                source_fir_ids=[crime_no],
                source_fields=["accused_name"],
            ))

        # Victim nodes
        for vic in cls._extract_name_list(row, "victim_name", "victim_names"):
            node_id = f"Victim:{vic.strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Victim",
                label=vic.strip(),
                source_fir_ids=[crime_no],
                source_fields=["victim_name"],
            ))

        # Witness nodes
        witness = row.get("witness_name") or row.get("witness")
        if witness:
            node_id = f"Witness:{str(witness).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Witness",
                label=str(witness).strip(),
                source_fir_ids=[crime_no],
                source_fields=["witness_name"],
            ))

        # Vehicle nodes
        vehicle = row.get("vehicle") or row.get("vehicle_number")
        if vehicle:
            node_id = f"Vehicle:{str(vehicle).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Vehicle",
                label=str(vehicle).strip(),
                source_fir_ids=[crime_no],
                source_fields=["vehicle_number"],
            ))

        # Weapon nodes
        weapon = row.get("weapon")
        if weapon:
            node_id = f"Weapon:{str(weapon).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Weapon",
                label=str(weapon).strip(),
                source_fir_ids=[crime_no],
                source_fields=["weapon"],
            ))

        # Phone nodes
        phone = row.get("phone_number") or row.get("mobile_number")
        if phone:
            node_id = f"Phone:{str(phone).strip()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Phone",
                label=str(phone).strip(),
                source_fir_ids=[crime_no],
                source_fields=["phone_number"],
            ))

        # Address nodes
        address = row.get("address") or row.get("accused_address")
        if address:
            node_id = f"Address:{str(address).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Address",
                label=str(address).strip(),
                source_fir_ids=[crime_no],
                source_fields=["address"],
            ))

        # Station nodes
        station = row.get("police_station_name")
        if station:
            node_id = f"Station:{str(station).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Station",
                label=str(station).strip(),
                source_fir_ids=[crime_no],
                source_fields=["police_station_name"],
            ))

        # District nodes
        district = row.get("district_name")
        if district:
            node_id = f"District:{str(district).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="District",
                label=str(district).strip(),
                source_fir_ids=[crime_no],
                source_fields=["district_name"],
            ))

        # Officer nodes
        officer = row.get("officer_name") or row.get("io_name")
        if officer:
            node_id = f"Officer:{str(officer).strip().lower()}"
            graph.add_node(GraphNode(
                node_id=node_id,
                node_type="Officer",
                label=str(officer).strip(),
                source_fir_ids=[crime_no],
                source_fields=["officer_name"],
            ))

    # ── FIR-level Edge Building ───────────────────────────────────────────────

    @classmethod
    def _build_fir_edges(cls, graph: KnowledgeGraph, row: Dict, timestamp: str) -> None:
        crime_no = (row.get("crime_no") or row.get("case_no") or
                    row.get("fir_no") or "UNKNOWN")
        fir_id = f"FIR:{crime_no}"

        # Accused → Appeared In → FIR
        for acc in cls._extract_name_list(row, "accused_name", "accused_names"):
            acc_id = f"Accused:{acc.strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=acc_id, target_id=fir_id,
                relationship="Appeared In",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["accused_name"],
                reason_chain=[f"Accused '{acc.strip()}' directly listed in FIR {crime_no}"],
                timestamp=timestamp,
            ))

        # Victim → Appeared In → FIR
        for vic in cls._extract_name_list(row, "victim_name", "victim_names"):
            vic_id = f"Victim:{vic.strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=vic_id, target_id=fir_id,
                relationship="Appeared In",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["victim_name"],
                reason_chain=[f"Victim '{vic.strip()}' directly listed in FIR {crime_no}"],
                timestamp=timestamp,
            ))

        # Vehicle → Associated With → FIR
        vehicle = row.get("vehicle") or row.get("vehicle_number")
        if vehicle:
            veh_id = f"Vehicle:{str(vehicle).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=veh_id, target_id=fir_id,
                relationship="Associated With",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["vehicle_number"],
                reason_chain=[f"Vehicle '{str(vehicle).strip()}' recorded in FIR {crime_no}"],
                timestamp=timestamp,
            ))

        # Weapon → Recovered From / Associated With → FIR
        weapon = row.get("weapon")
        if weapon:
            wp_id = f"Weapon:{str(weapon).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=wp_id, target_id=fir_id,
                relationship="Recovered From",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["weapon"],
                reason_chain=[f"Weapon '{str(weapon).strip()}' recorded in FIR {crime_no}"],
                timestamp=timestamp,
            ))

        # Phone → Uses → (Accused) via FIR
        phone = row.get("phone_number") or row.get("mobile_number")
        if phone:
            ph_id = f"Phone:{str(phone).strip()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=ph_id, target_id=fir_id,
                relationship="Associated With",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["phone_number"],
                reason_chain=[f"Phone '{str(phone).strip()}' recorded in FIR {crime_no}"],
                timestamp=timestamp,
            ))

        # Station → Occurred At → FIR
        station = row.get("police_station_name")
        if station:
            st_id = f"Station:{str(station).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=fir_id, target_id=st_id,
                relationship="Occurred At",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["police_station_name"],
                reason_chain=[f"FIR {crime_no} registered at station '{str(station).strip()}'"],
                timestamp=timestamp,
            ))

        # District → Occurred At → FIR
        district = row.get("district_name")
        if district:
            dist_id = f"District:{str(district).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=fir_id, target_id=dist_id,
                relationship="Occurred At",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["district_name"],
                reason_chain=[f"FIR {crime_no} registered in district '{str(district).strip()}'"],
                timestamp=timestamp,
            ))

        # Officer → Investigated By → FIR
        officer = row.get("officer_name") or row.get("io_name")
        if officer:
            off_id = f"Officer:{str(officer).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=fir_id, target_id=off_id,
                relationship="Investigated By",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["officer_name"],
                reason_chain=[f"FIR {crime_no} investigated by '{str(officer).strip()}'"],
                timestamp=timestamp,
            ))

        # Address → Lives At → (Accused)
        address = row.get("address") or row.get("accused_address")
        for acc in cls._extract_name_list(row, "accused_name", "accused_names"):
            if address:
                addr_id = f"Address:{str(address).strip().lower()}"
                acc_id = f"Accused:{acc.strip().lower()}"
                cls._add_edge_safe(graph, GraphEdge(
                    source_id=acc_id, target_id=addr_id,
                    relationship="Lives At",
                    confidence=1.0, evidence_score=100,
                    supporting_fir_ids=[crime_no],
                    source_fields=["address", "accused_name"],
                    reason_chain=[f"Accused '{acc.strip()}' address recorded as '{str(address).strip()}' in FIR {crime_no}"],
                    timestamp=timestamp,
                ))

        # Station → Connected To → District
        if station and district:
            st_id = f"Station:{str(station).strip().lower()}"
            dist_id = f"District:{str(district).strip().lower()}"
            cls._add_edge_safe(graph, GraphEdge(
                source_id=st_id, target_id=dist_id,
                relationship="Connected To",
                confidence=1.0, evidence_score=100,
                supporting_fir_ids=[crime_no],
                source_fields=["police_station_name", "district_name"],
                reason_chain=[f"Station '{str(station).strip()}' belongs to district '{str(district).strip()}' per FIR {crime_no}"],
                timestamp=timestamp,
            ))

    # ── Cross-FIR Correlation Edges ───────────────────────────────────────────

    @classmethod
    def _build_correlation_edges(cls, graph: KnowledgeGraph, results: List[Dict], timestamp: str) -> None:
        """
        Build cross-FIR edges for shared entities (accused, vehicle, weapon, phone).
        Enforces strict evidence requirement: only actual field matches, no inference.
        """
        # Index entities → list of FIR IDs
        accused_index: Dict[str, List[str]] = {}
        victim_index: Dict[str, List[str]] = {}
        vehicle_index: Dict[str, List[str]] = {}
        weapon_index: Dict[str, List[str]] = {}
        phone_index: Dict[str, List[str]] = {}
        station_index: Dict[str, List[str]] = {}
        district_index: Dict[str, List[str]] = {}

        for row in results:
            crime_no = (row.get("crime_no") or row.get("case_no") or
                        row.get("fir_no") or "UNKNOWN")

            for acc in cls._extract_name_list(row, "accused_name", "accused_names"):
                key = acc.strip().lower()
                accused_index.setdefault(key, []).append(crime_no)

            for vic in cls._extract_name_list(row, "victim_name", "victim_names"):
                key = vic.strip().lower()
                victim_index.setdefault(key, []).append(crime_no)

            veh = (row.get("vehicle") or row.get("vehicle_number") or "")
            if veh:
                vehicle_index.setdefault(str(veh).strip().lower(), []).append(crime_no)

            wpn = row.get("weapon") or ""
            if wpn:
                weapon_index.setdefault(str(wpn).strip().lower(), []).append(crime_no)

            ph = str(row.get("phone_number") or row.get("mobile_number") or "").strip()
            if ph:
                phone_index.setdefault(ph, []).append(crime_no)

            st = row.get("police_station_name") or ""
            if st:
                station_index.setdefault(str(st).strip().lower(), []).append(crime_no)

            dist = row.get("district_name") or ""
            if dist:
                district_index.setdefault(str(dist).strip().lower(), []).append(crime_no)

        # Build cross-FIR "Connected To" edges for entities seen in ≥2 FIRs
        def _build_cross_fir(index: Dict[str, List[str]], prefix: str,
                              relationship: str, field_name: str) -> None:
            for key, fir_list in index.items():
                unique_firs = list(dict.fromkeys(fir_list))  # deduplicate preserving order
                if len(unique_firs) < 2:
                    continue
                node_id = f"{prefix}:{key}"
                if node_id not in graph._nodes:
                    continue
                # Connect all pairs of FIRs through this entity
                for i in range(len(unique_firs)):
                    for j in range(i + 1, len(unique_firs)):
                        fir_a = f"FIR:{unique_firs[i]}"
                        fir_b = f"FIR:{unique_firs[j]}"
                        if fir_a not in graph._nodes or fir_b not in graph._nodes:
                            continue
                        entity_label = graph._nodes[node_id].label
                        graph.add_edge(GraphEdge(
                            source_id=fir_a, target_id=fir_b,
                            relationship=relationship,
                            confidence=0.95,
                            evidence_score=90,
                            supporting_fir_ids=[unique_firs[i], unique_firs[j]],
                            source_fields=[field_name],
                            reason_chain=[
                                f"Both FIRs share {prefix.lower()} '{entity_label}' "
                                f"(verified from field '{field_name}')"
                            ],
                            timestamp=timestamp,
                        ))

        _build_cross_fir(accused_index, "Accused", "Associated With", "accused_name")
        _build_cross_fir(victim_index, "Victim", "Associated With", "victim_name")
        _build_cross_fir(vehicle_index, "Vehicle", "Associated With", "vehicle_number")
        _build_cross_fir(weapon_index, "Weapon", "Associated With", "weapon")
        _build_cross_fir(phone_index, "Phone", "Associated With", "phone_number")

    # ── Graph Query Operations ────────────────────────────────────────────────

    @classmethod
    def find_neighbors(cls, graph: KnowledgeGraph, node_id: str) -> Dict[str, Any]:
        """Show all connections of a node."""
        node = graph.get_node(node_id)
        if not node:
            return {"node_id": node_id, "found": False, "neighbors": [],
                    "message": "No verified graph relationship found."}
        neighbors = graph.get_neighbors(node_id)
        return {
            "node_id": node_id,
            "node_label": node.label,
            "node_type": node.node_type,
            "found": True,
            "neighbor_count": len(neighbors),
            "neighbors": [n.to_dict() for n in neighbors],
        }

    @classmethod
    def shortest_path(cls, graph: KnowledgeGraph, source_id: str, target_id: str) -> Dict[str, Any]:
        """Find shortest path between two nodes."""
        path = graph.find_shortest_path(source_id, target_id)
        if not path:
            return {
                "source": source_id, "target": target_id,
                "path": [], "hops": -1,
                "message": "No verified graph relationship found.",
            }
        # Build path with edge details
        path_detail = []
        for i in range(len(path) - 1):
            edges = graph.get_edges_between(path[i], path[i + 1])
            rel = edges[0].relationship if edges else "Connected To"
            path_detail.append({
                "from": path[i],
                "to": path[i + 1],
                "relationship": rel,
            })
        return {
            "source": source_id,
            "target": target_id,
            "path": path,
            "path_detail": path_detail,
            "hops": len(path) - 1,
            "message": f"Path found in {len(path) - 1} hop(s).",
        }

    @classmethod
    def connected_components(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Return all connected components."""
        components = graph.find_connected_components()
        return {
            "component_count": len(components),
            "components": [
                {
                    "size": len(c),
                    "nodes": c,
                    "node_types": list({graph._nodes[n].node_type
                                       for n in c if n in graph._nodes}),
                }
                for c in components
            ],
        }

    @classmethod
    def repeat_offender_clusters(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Find accused nodes that appear in multiple FIRs."""
        clusters = []
        for node in graph.all_nodes():
            if node.node_type != "Accused":
                continue
            fir_count = len(set(node.source_fir_ids))
            if fir_count >= 2:
                neighbors = graph.get_neighbors_by_type(node.node_id, "FIR")
                clusters.append({
                    "accused": node.label,
                    "node_id": node.node_id,
                    "fir_count": fir_count,
                    "fir_ids": list(set(node.source_fir_ids)),
                    "connected_firs": [n.label for n in neighbors],
                })
        clusters.sort(key=lambda x: x["fir_count"], reverse=True)
        return {"repeat_offender_count": len(clusters), "clusters": clusters}

    @classmethod
    def crime_clusters(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Group FIR nodes by crime category + district."""
        cluster_map: Dict[str, List[str]] = {}
        for node in graph.all_nodes():
            if node.node_type != "FIR":
                continue
            cat = node.attributes.get("category") or "UNKNOWN"
            dist = node.attributes.get("district") or "UNKNOWN"
            key = f"{cat}::{dist}"
            cluster_map.setdefault(key, []).append(node.node_id)

        clusters = []
        for key, fir_ids in cluster_map.items():
            if len(fir_ids) >= 2:
                cat, dist = key.split("::", 1)
                clusters.append({
                    "category": cat,
                    "district": dist,
                    "fir_count": len(fir_ids),
                    "fir_ids": fir_ids,
                })
        clusters.sort(key=lambda x: x["fir_count"], reverse=True)
        return {"crime_cluster_count": len(clusters), "clusters": clusters}

    @classmethod
    def district_graph(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Build District → Station → FIR hierarchy."""
        districts: Dict[str, Dict] = {}
        for node in graph.all_nodes():
            if node.node_type != "District":
                continue
            dist_label = node.label
            stations = graph.get_neighbors_by_type(node.node_id, "Station")
            station_data = []
            for st in stations:
                firs = graph.get_neighbors_by_type(st.node_id, "FIR")
                station_data.append({
                    "station": st.label,
                    "fir_count": len(firs),
                    "firs": [f.label for f in firs],
                })
            districts[dist_label] = {
                "district": dist_label,
                "station_count": len(station_data),
                "stations": station_data,
                "total_firs": sum(s["fir_count"] for s in station_data),
            }
        return {"district_count": len(districts), "districts": list(districts.values())}

    @classmethod
    def vehicle_reuse(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Find vehicles appearing in multiple FIRs."""
        reused = []
        for node in graph.all_nodes():
            if node.node_type != "Vehicle":
                continue
            fir_count = len(set(node.source_fir_ids))
            if fir_count >= 2:
                reused.append({
                    "vehicle": node.label,
                    "node_id": node.node_id,
                    "fir_count": fir_count,
                    "fir_ids": list(set(node.source_fir_ids)),
                })
        reused.sort(key=lambda x: x["fir_count"], reverse=True)
        return {"reused_vehicle_count": len(reused), "vehicles": reused}

    @classmethod
    def weapon_reuse(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Find weapons appearing in multiple FIRs."""
        reused = []
        for node in graph.all_nodes():
            if node.node_type != "Weapon":
                continue
            fir_count = len(set(node.source_fir_ids))
            if fir_count >= 2:
                reused.append({
                    "weapon": node.label,
                    "node_id": node.node_id,
                    "fir_count": fir_count,
                    "fir_ids": list(set(node.source_fir_ids)),
                })
        reused.sort(key=lambda x: x["fir_count"], reverse=True)
        return {"reused_weapon_count": len(reused), "weapons": reused}

    @classmethod
    def phone_network(cls, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Find phone numbers appearing in multiple FIRs."""
        network = []
        for node in graph.all_nodes():
            if node.node_type != "Phone":
                continue
            fir_count = len(set(node.source_fir_ids))
            if fir_count >= 2:
                network.append({
                    "phone": node.label,
                    "node_id": node.node_id,
                    "fir_count": fir_count,
                    "fir_ids": list(set(node.source_fir_ids)),
                })
        network.sort(key=lambda x: x["fir_count"], reverse=True)
        return {"shared_phone_count": len(network), "phones": network}

    # ── Extended Report Builder ───────────────────────────────────────────────

    @classmethod
    def _build_extended_report(cls, graph: KnowledgeGraph, results: List[Dict]) -> Dict[str, Any]:
        """Build the full KnowledgeGraphReport."""
        repeat_offenders = cls.repeat_offender_clusters(graph)
        crime_clust = cls.crime_clusters(graph)
        dist_graph = cls.district_graph(graph)
        veh_reuse = cls.vehicle_reuse(graph)
        wpn_reuse = cls.weapon_reuse(graph)
        ph_net = cls.phone_network(graph)

        # Summary
        summary_lines = []
        node_cnt = graph.node_count()
        edge_cnt = graph.edge_count()
        summary_lines.append(f"Knowledge graph constructed: {node_cnt} nodes, {edge_cnt} edges.")

        components = graph.find_connected_components()
        summary_lines.append(f"Connected components: {len(components)}.")

        if repeat_offenders["repeat_offender_count"] > 0:
            summary_lines.append(
                f"Repeat offender clusters: {repeat_offenders['repeat_offender_count']} accused "
                f"with multiple FIR appearances."
            )
        if veh_reuse["reused_vehicle_count"] > 0:
            summary_lines.append(f"Vehicle reuse detected: {veh_reuse['reused_vehicle_count']} vehicle(s).")
        if wpn_reuse["reused_weapon_count"] > 0:
            summary_lines.append(f"Weapon reuse detected: {wpn_reuse['reused_weapon_count']} weapon(s).")
        if ph_net["shared_phone_count"] > 0:
            summary_lines.append(f"Shared phone network: {ph_net['shared_phone_count']} number(s) across multiple FIRs.")

        return {
            "summary": " ".join(summary_lines),
            "repeat_offender_clusters": repeat_offenders,
            "crime_clusters": crime_clust,
            "district_graph": dist_graph,
            "vehicle_reuse": veh_reuse,
            "weapon_reuse": wpn_reuse,
            "phone_network": ph_net,
            "evidence_chain": [
                "Graph built from verified database query results",
                "Node extraction performed from FIR fields only",
                "Cross-FIR correlation edges require exact field match",
                "No inferred or hallucinated edges present",
            ],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_name_list(row: Dict, single_key: str, list_key: str) -> List[str]:
        """Extract a list of names from single-value or list fields."""
        names = []
        val = row.get(single_key)
        if val and isinstance(val, str) and val.strip():
            names.append(val.strip())
        else:
            lst = row.get(list_key)
            if isinstance(lst, list):
                for item in lst:
                    if item and isinstance(item, str) and item.strip():
                        names.append(item.strip())
        return names

    @staticmethod
    def _add_edge_safe(graph: KnowledgeGraph, edge: GraphEdge) -> None:
        """Add edge only if both nodes exist in graph."""
        if edge.source_id in graph._nodes and edge.target_id in graph._nodes:
            graph.add_edge(edge)

    @classmethod
    def _empty_report(cls, msg: str) -> Dict[str, Any]:
        return {
            "node_count": 0, "edge_count": 0,
            "nodes": [], "edges": [],
            "connected_components": [], "component_count": 0,
            "repeat_offender_clusters": {"repeat_offender_count": 0, "clusters": []},
            "crime_clusters": {"crime_cluster_count": 0, "clusters": []},
            "district_graph": {"district_count": 0, "districts": []},
            "vehicle_reuse": {"reused_vehicle_count": 0, "vehicles": []},
            "weapon_reuse": {"reused_weapon_count": 0, "weapons": []},
            "phone_network": {"shared_phone_count": 0, "phones": []},
            "evidence_chain": [],
            "summary": msg,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE STAGE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeGraphStage:
    """
    Pipeline stage wrapper for KnowledgeGraphEngine.
    Inserts between EvidenceCorrelationStage and MultiAgentEngineStage.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            _graph, report = KnowledgeGraphEngine.build_graph(context)
            context.knowledge_graph_report = report
            # Attach the graph object for downstream stages that need traversal
            context.knowledge_graph = _graph
        except Exception as e:
            logger.error(f"KnowledgeGraphStage failed: {e}", exc_info=True)
            context.warnings.append(f"KnowledgeGraphStage failed: {e}")
            context.knowledge_graph_report = KnowledgeGraphEngine._empty_report(
                f"Knowledge graph unavailable: {e}"
            )
        return context
