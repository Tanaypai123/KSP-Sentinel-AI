from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict, deque

class NetworkEngine:
    @staticmethod
    def build_network(start_type: str, start_val: str, db: Session, max_depth: int = 2) -> Dict[str, Any]:
        """
        Builds a localized investigation graph around a starting entity.
        start_type: 'ACCUSED', 'FIR', 'VICTIM'
        start_val: the name or ID to search for
        """
        nodes = {}  # key: (type, id/name), value: node attributes
        edges = defaultdict(list) # key: (type, id/name), value: list of (type, id/name)
        
        visited = set()
        queue = deque()
        
        # Initialize
        if start_type == "ACCUSED":
            queue.append(("ACCUSED", start_val, 0))
        elif start_type == "FIR":
            queue.append(("FIR", start_val, 0))
        elif start_type == "VICTIM":
            queue.append(("VICTIM", start_val, 0))
            
        def add_node(n_type, n_id, label):
            key = (n_type, n_id)
            if key not in nodes:
                nodes[key] = {"type": n_type, "id": n_id, "label": label, "degree": 0}
            return key
            
        def add_edge(u_key, v_key, rel_type="LINKED_TO"):
            # undirected graph
            if v_key not in edges[u_key]:
                edges[u_key].append(v_key)
                nodes[u_key]["degree"] += 1
            if u_key not in edges[v_key]:
                edges[v_key].append(u_key)
                nodes[v_key]["degree"] += 1

        # Traverse
        while queue:
            curr_type, curr_val, depth = queue.popleft()
            curr_key = (curr_type, curr_val)
            
            if curr_key in visited:
                continue
            visited.add(curr_key)
            
            if depth > max_depth:
                continue
                
            if curr_type == "ACCUSED":
                # Find all FIRs for this accused
                q = text("""
                    SELECT cm."CaseMasterID", cm."CrimeNo", u."UnitName" as "PSName", d."DistrictName"
                    FROM accused a
                    JOIN case_master cm ON a."CaseMasterID" = cm."CaseMasterID"
                    LEFT JOIN unit u ON cm."PoliceStationID" = u."UnitID"
                    LEFT JOIN district d ON u."DistrictID" = d."DistrictID"
                    WHERE a."AccusedName" ILIKE :name
                """)
                rows = db.execute(q, {"name": f"%{curr_val}%"}).fetchall()
                add_node("ACCUSED", curr_val, curr_val)
                
                for r in rows:
                    if not r.CrimeNo: continue
                    fir_key = add_node("FIR", str(r.CaseMasterID), str(r.CrimeNo))
                    add_edge(curr_key, fir_key)
                    
                    if r.PSName:
                        ps_key = add_node("POLICE_STATION", r.PSName, r.PSName)
                        add_edge(fir_key, ps_key)
                    if r.DistrictName:
                        d_key = add_node("DISTRICT", r.DistrictName, r.DistrictName)
                        if r.PSName: add_edge(ps_key, d_key)
                        
                    if depth < max_depth:
                        queue.append(("FIR", str(r.CaseMasterID), depth + 1))
                        
            elif curr_type == "VICTIM":
                q = text("""
                    SELECT cm."CaseMasterID", cm."CrimeNo"
                    FROM victim v
                    JOIN case_master cm ON v."CaseMasterID" = cm."CaseMasterID"
                    WHERE v."VictimName" ILIKE :name
                """)
                rows = db.execute(q, {"name": f"%{curr_val}%"}).fetchall()
                add_node("VICTIM", curr_val, curr_val)
                
                for r in rows:
                    if not r.CrimeNo: continue
                    fir_key = add_node("FIR", str(r.CaseMasterID), str(r.CrimeNo))
                    add_edge(curr_key, fir_key)
                    if depth < max_depth:
                        queue.append(("FIR", str(r.CaseMasterID), depth + 1))
                        
            elif curr_type == "FIR":
                # Find Accused, Victims for this FIR
                try:
                    case_id = int(curr_val)
                except ValueError:
                    # if they passed CrimeNo
                    q_id = text('SELECT "CaseMasterID", "CrimeNo" FROM case_master WHERE "CrimeNo" = :cno')
                    row = db.execute(q_id, {"cno": curr_val}).first()
                    if not row: continue
                    case_id = row.CaseMasterID
                    curr_val = str(case_id)
                    curr_key = ("FIR", curr_val)
                    add_node("FIR", curr_val, str(row.CrimeNo))
                
                # Fetch Accused
                q_a = text('SELECT "AccusedName" FROM accused WHERE "CaseMasterID" = :cid')
                for r in db.execute(q_a, {"cid": case_id}).fetchall():
                    if r.AccusedName:
                        a_key = add_node("ACCUSED", r.AccusedName, r.AccusedName)
                        add_edge(curr_key, a_key)
                        if depth < max_depth:
                            queue.append(("ACCUSED", r.AccusedName, depth + 1))
                            
                # Fetch Victims
                q_v = text('SELECT "VictimName" FROM victim WHERE "CaseMasterID" = :cid')
                for r in db.execute(q_v, {"cid": case_id}).fetchall():
                    if r.VictimName:
                        v_key = add_node("VICTIM", r.VictimName, r.VictimName)
                        add_edge(curr_key, v_key)
                        if depth < max_depth:
                            queue.append(("VICTIM", r.VictimName, depth + 1))

        # Analytics
        # Connected Components
        visited_comp = set()
        components = 0
        for n in nodes.keys():
            if n not in visited_comp:
                components += 1
                q = deque([n])
                while q:
                    curr = q.popleft()
                    if curr in visited_comp: continue
                    visited_comp.add(curr)
                    for nbr in edges[curr]:
                        if nbr not in visited_comp:
                            q.append(nbr)
                            
        # Most Influential Node (Highest Degree Centrality)
        influential = None
        max_deg = -1
        for k, attrs in nodes.items():
            if attrs["type"] not in ["POLICE_STATION", "DISTRICT"]: # Skip structural nodes for influence
                if attrs["degree"] > max_deg:
                    max_deg = attrs["degree"]
                    influential = attrs
                    
        # Filter sparse networks
        if len(nodes) <= 1:
            return {
                "nodes": [],
                "edges": [],
                "summary": "No significant investigative network connections found.",
                "risk_score": 0,
                "components": 0,
                "influential_node": None
            }
            
        # Network Summary
        accused_count = sum(1 for v in nodes.values() if v["type"] == "ACCUSED")
        fir_count = sum(1 for v in nodes.values() if v["type"] == "FIR")
        victim_count = sum(1 for v in nodes.values() if v["type"] == "VICTIM")
        
        risk_score = min(100, (accused_count * 5) + (fir_count * 10) + (victim_count * 5))
        
        summary = f"The investigative network spans {fir_count} FIRs, involving {accused_count} suspect(s) and {victim_count} victim(s)."
        if influential:
            summary += f"\nMost connected entity: **{influential['label']}** (Type: {influential['type']}) with {influential['degree']} direct connections."

        # Format output
        out_nodes = list(nodes.values())
        out_edges = []
        seen_edges = set()
        for u, nbrs in edges.items():
            for v in nbrs:
                edge_sig = tuple(sorted([str(u), str(v)]))
                if edge_sig not in seen_edges:
                    seen_edges.add(edge_sig)
                    out_edges.append({"source": nodes[u]["id"], "target": nodes[v]["id"]})

        return {
            "nodes": out_nodes,
            "edges": out_edges,
            "summary": summary,
            "risk_score": risk_score,
            "components": components,
            "influential_node": influential,
            "relationship_strength": risk_score / max(1, components)
        }
