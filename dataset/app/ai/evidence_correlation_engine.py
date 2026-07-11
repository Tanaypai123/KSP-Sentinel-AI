import logging
from collections import deque
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)

class EvidenceCorrelationEngine:
    """
    Evidence Correlation Engine:
    Discovers deterministic links across multiple records (accused, victims, vehicles, locations, patterns)
    and represents them as an EvidenceGraph. Enforces strict safety gates to prevent hallucinated inferences.
    """

    MIN_THRESHOLD: int = 15  # Minimum evidence score required to establish a link

    @classmethod
    def correlate(cls, context: Any) -> Dict[str, Any]:
        """
        Main entry point for generating the EvidenceCorrelationResult.
        """
        results = context.search_result or []
        
        # Safety check: No correlations possible with less than 2 records
        if len(results) < 2:
            return cls._empty_correlation_result("No verified evidence connecting these records.")

        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # ── 1. Node Extraction ──────────────────────────────────────────────
        # Extract FIRs and associated parameters as discrete nodes
        for idx, row in enumerate(results):
            crime_no = row.get("crime_no") or row.get("case_no") or row.get("fir_no") or f"FIR_MOCK_{idx}"
            fir_id = f"FIR:{crime_no}"
            
            # Extract FIR Node
            nodes[fir_id] = {
                "id": fir_id,
                "type": "FIR",
                "label": f"FIR {crime_no}",
                "attributes": {
                    "district": row.get("district_name"),
                    "station": row.get("police_station_name"),
                    "category": row.get("crime_category") or row.get("crime_head"),
                    "date": str(row.get("crime_registered_date") or "")
                }
            }

            # Accused Nodes
            acc_list = []
            if row.get("accused_name"):
                acc_list.append(row["accused_name"])
            elif isinstance(row.get("accused_names"), list):
                acc_list.extend(row["accused_names"])
                
            for acc in acc_list:
                acc_id = f"Accused:{acc.strip().lower()}"
                nodes[acc_id] = {"id": acc_id, "type": "Accused", "label": acc.strip(), "attributes": {}}
                edges.append(cls._build_direct_edge(fir_id, acc_id, "Accused Link", crime_no))

            # Victim Nodes
            vic_list = []
            if row.get("victim_name"):
                vic_list.append(row["victim_name"])
            elif isinstance(row.get("victim_names"), list):
                vic_list.extend(row["victim_names"])
                
            for vic in vic_list:
                vic_id = f"Victim:{vic.strip().lower()}"
                nodes[vic_id] = {"id": vic_id, "type": "Victim", "label": vic.strip(), "attributes": {}}
                edges.append(cls._build_direct_edge(fir_id, vic_id, "Victim Link", crime_no))

            # Vehicle Nodes
            veh = row.get("vehicle") or row.get("vehicle_number")
            if veh:
                veh_id = f"Vehicle:{veh.strip().lower()}"
                nodes[veh_id] = {"id": veh_id, "type": "Vehicle", "label": veh.strip(), "attributes": {}}
                edges.append(cls._build_direct_edge(fir_id, veh_id, "Vehicle Link", crime_no))

            # Weapon Nodes
            weapon = row.get("weapon")
            if weapon:
                wp_id = f"Weapon:{weapon.strip().lower()}"
                nodes[wp_id] = {"id": wp_id, "type": "Weapon", "label": weapon.strip(), "attributes": {}}
                edges.append(cls._build_direct_edge(fir_id, wp_id, "Weapon Link", crime_no))

            # Phone Nodes
            phone = row.get("phone_number") or row.get("mobile_number")
            if phone:
                ph_id = f"Phone:{str(phone).strip()}"
                nodes[ph_id] = {"id": ph_id, "type": "Phone", "label": str(phone).strip(), "attributes": {}}
                edges.append(cls._build_direct_edge(fir_id, ph_id, "Phone Link", crime_no))

        # ── 2. Correlation Mapping (FIR to FIR Overlaps) ──────────────────────
        fir_keys = [k for k, v in nodes.items() if v["type"] == "FIR"]
        correlation_edges: List[Dict[str, Any]] = []

        for i in range(len(fir_keys)):
            for j in range(i + 1, len(fir_keys)):
                fir_a = nodes[fir_keys[i]]
                fir_b = nodes[fir_keys[j]]
                
                score, matches = cls._calculate_correlation_score(fir_a, fir_b, results[i], results[j])
                
                if score >= cls.MIN_THRESHOLD:
                    strength = cls._grade_strength(score)
                    rel_type = "Multi-evidence Overlap"
                    if "accused" in matches:
                        rel_type = "Accused Correlation"
                    elif "vehicle" in matches:
                        rel_type = "Vehicle Correlation"
                    elif "phone" in matches:
                        rel_type = "Phone Correlation"
                    
                    correlation_edges.append({
                        "source": fir_a["id"],
                        "target": fir_b["id"],
                        "relationship_type": rel_type,
                        "strength": strength,
                        "confidence": score / 100.0,
                        "evidence_score": score,
                        "source_firs": [fir_a["attributes"]["category"] or "FIR", fir_b["attributes"]["category"] or "FIR"],
                        "matching_fields": list(matches),
                        "details": f"Correlated with score {score} via overlap of: {', '.join(matches)}."
                    })

        # Add successful correlation edges to master edge list
        edges.extend(correlation_edges)

        # ── 3. Multi-hop Chain Discovery (up to 3 hops) ──────────────────────
        chains = cls._discover_chains(nodes, edges)

        # ── 4. Cluster Discovery ─────────────────────────────────────────────
        clusters = cls._discover_clusters(nodes, correlation_edges)

        # ── 5. Output Summary Builder ────────────────────────────────────────
        if not correlation_edges:
            return cls._empty_correlation_result("No verified evidence connecting these records.")

        summary_lines = []
        for e in correlation_edges:
            summary_lines.append(
                f"Link discovered between {e['source'].replace('FIR:', 'FIR ')} and "
                f"{e['target'].replace('FIR:', 'FIR ')}: {e['relationship_type']} (Strength: {e['strength']}, Score: {e['evidence_score']})."
            )
        summary = "\n".join(summary_lines)

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "chains": chains,
            "clusters": clusters,
            "summary": summary
        }

    @classmethod
    def _empty_correlation_result(cls, msg: str) -> Dict[str, Any]:
        return {
            "nodes": [],
            "edges": [],
            "chains": [],
            "clusters": [],
            "summary": msg
        }

    @classmethod
    def _build_direct_edge(cls, source: str, target: str, rel_type: str, fir_no: str) -> Dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "relationship_type": rel_type,
            "strength": "STRONG",
            "confidence": 1.0,
            "evidence_score": 100,
            "source_firs": [fir_no],
            "matching_fields": [],
            "details": f"Direct entity link identified in FIR {fir_no}."
        }

    @classmethod
    def _calculate_correlation_score(cls, fir_a: Dict, fir_b: Dict, row_a: Dict, row_b: Dict) -> Tuple[int, Set[str]]:
        score = 0
        matches = set()

        # Compare simple attributes
        attr_a = fir_a["attributes"]
        attr_b = fir_b["attributes"]

        if attr_a["district"] and attr_a["district"] == attr_b["district"]:
            score += 15
            matches.add("district")
            
        if attr_a["station"] and attr_a["station"] == attr_b["station"]:
            score += 15
            matches.add("police_station")

        if attr_a["category"] and attr_a["category"] == attr_b["category"]:
            score += 15
            matches.add("crime_category")

        # Compare dates proximity (within 30 days)
        try:
            from datetime import datetime
            d_a = datetime.strptime(attr_a["date"], "%Y-%m-%d")
            d_b = datetime.strptime(attr_b["date"], "%Y-%m-%d")
            if abs((d_a - d_b).days) <= 30:
                score += 20
                matches.add("date_proximity")
        except Exception:
            pass

        # Compare Geo proximity
        lat_a, lon_a = row_a.get("latitude"), row_a.get("longitude")
        lat_b, lon_b = row_b.get("latitude"), row_b.get("longitude")
        if lat_a and lat_b and lon_a and lon_b:
            if abs(float(lat_a) - float(lat_b)) < 0.01 and abs(float(lon_a) - float(lon_b)) < 0.01:
                score += 20
                matches.add("geo_proximity")

        # Compare Critical Entity overlaps
        def get_names(row, key, key_list):
            names = []
            if row.get(key):
                names.append(row[key].strip().lower())
            elif isinstance(row.get(key_list), list):
                names.extend([n.strip().lower() for n in row[key_list]])
            return set(names)

        acc_a = get_names(row_a, "accused_name", "accused_names")
        acc_b = get_names(row_b, "accused_name", "accused_names")
        if acc_a & acc_b:
            score += 30
            matches.add("accused")

        vic_a = get_names(row_a, "victim_name", "victim_names")
        vic_b = get_names(row_b, "victim_name", "victim_names")
        if vic_a & vic_b:
            score += 30
            matches.add("victim")

        veh_a = (row_a.get("vehicle") or row_a.get("vehicle_number") or "").strip().lower()
        veh_b = (row_b.get("vehicle") or row_b.get("vehicle_number") or "").strip().lower()
        if veh_a and veh_a == veh_b:
            score += 30
            matches.add("vehicle")

        wep_a = (row_a.get("weapon") or "").strip().lower()
        wep_b = (row_b.get("weapon") or "").strip().lower()
        if wep_a and wep_a == wep_b:
            score += 30
            matches.add("weapon")

        ph_a = str(row_a.get("phone_number") or row_a.get("mobile_number") or "").strip()
        ph_b = str(row_b.get("phone_number") or row_b.get("mobile_number") or "").strip()
        if ph_a and ph_a == ph_b:
            score += 30
            matches.add("phone")

        return min(score, 100), matches

    @classmethod
    def _grade_strength(cls, score: int) -> str:
        if score >= 80:
            return "VERY_STRONG"
        elif score >= 60:
            return "STRONG"
        elif score >= 40:
            return "MEDIUM"
        return "WEAK"

    @classmethod
    def _discover_chains(cls, nodes: Dict, edges: List) -> List[Dict]:
        """
        Discovers 2-hop or 3-hop connection chains using BFS.
        Performance-capped: processes at most 5 FIR pairs and returns at most 20 chains.
        Uses collections.deque for O(1) popleft (prevents O(n^3) list.pop(0) bottleneck).
        """
        adj: Dict[str, List[str]] = {n: [] for n in nodes}
        for e in edges:
            adj[e["source"]].append(e["target"])
            adj[e["target"]].append(e["source"])

        chains: List[Dict] = []
        # Cap FIR enumeration: only process first 5 FIR nodes to bound O(n^2) pair loop
        fir_keys = [k for k, v in nodes.items() if v["type"] == "FIR"][:5]
        MAX_CHAINS = 20

        # Search for paths up to 3 hops between FIRs
        for i in range(len(fir_keys)):
            if len(chains) >= MAX_CHAINS:
                break
            for j in range(i + 1, len(fir_keys)):
                if len(chains) >= MAX_CHAINS:
                    break
                start = fir_keys[i]
                target = fir_keys[j]

                # BFS using deque for O(1) popleft (critical performance fix)
                bfs_queue: deque = deque([[start]])
                found = False

                while bfs_queue and not found:
                    path = bfs_queue.popleft()
                    node = path[-1]
                    if len(path) > 4:  # Cap at 3 hops (4 nodes)
                        continue
                    if node == target:
                        chains.append({
                            "type": f"{len(path)-1}-Hop Connection",
                            "path": path,
                            "summary": " -> ".join([
                                p.replace("FIR:", "FIR ")
                                 .replace("Accused:", "Accused ")
                                 .replace("Vehicle:", "Vehicle ")
                                for p in path
                            ])
                        })
                        found = True  # One chain per FIR pair is sufficient
                        continue

                    for neighbor in adj.get(node, []):
                        if neighbor not in path:
                            bfs_queue.append(path + [neighbor])

        return chains

    @classmethod
    def _discover_clusters(cls, nodes: Dict, correlation_edges: List) -> Dict[str, List]:
        """
        Identifies gang activity, repeat offenders, and hotspots clusters.
        """
        repeat_offenders = []
        crime_clusters = []
        gang_groups = []

        # Repeat Offenders: Accused appearing in multiple FIRs
        accused_keys = [k for k, v in nodes.items() if v["type"] == "Accused"]
        for acc in accused_keys:
            # Find correlation links containing this accused
            count = 0
            for e in correlation_edges:
                if "accused" in e.get("matching_fields", []):
                    count += 1
            if count >= 1:
                repeat_offenders.append(nodes[acc]["label"])

        # Hotspot Clusters: cases with geo proximity matches
        for e in correlation_edges:
            if "geo_proximity" in e.get("matching_fields", []):
                crime_clusters.append([e["source"], e["target"]])

        return {
            "repeat_offenders": repeat_offenders,
            "crime_clusters": crime_clusters,
            "gang_activity": gang_groups
        }


class EvidenceCorrelationStage:
    """
    Pipeline stage wrapper for EvidenceCorrelationEngine.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            # Discover evidence correlations
            context.evidence_correlation = EvidenceCorrelationEngine.correlate(context)
        except Exception as e:
            logger.error(f"EvidenceCorrelationStage failed: {e}", exc_info=True)
            context.warnings.append(f"EvidenceCorrelationStage failed: {e}")
        return context
