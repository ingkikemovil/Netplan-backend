from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import networkx as nx
from database import supabase

router = APIRouter()


class MSTRequest(BaseModel):
    project_id: str
    algorithm: str = "kruskal"
    budget: Optional[float] = None


def build_graph(nodes: list, connections: list) -> nx.Graph:
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], name=n["name"], lat=n["latitude"], lng=n["longitude"], node_type=n["node_type"])
    for c in connections:
        if c["conn_type"] != "forbidden":
            G.add_edge(c["source_node_id"], c["target_node_id"],
                       weight=c["cost"], conn_id=c["id"], conn_type=c["conn_type"])
    return G


def apply_mandatory_edges(G: nx.Graph, connections: list) -> list:
    return [c for c in connections if c["conn_type"] == "mandatory"]


@router.post("/calculate")
def calculate_mst(payload: MSTRequest):
    nodes_res = supabase.table("nodes").select("*").eq("project_id", payload.project_id).execute()
    conn_res = supabase.table("connections").select("*").eq("project_id", payload.project_id).execute()

    nodes = nodes_res.data
    connections = conn_res.data

    if len(nodes) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 nodos")

    G = build_graph(nodes, connections)

    if not nx.is_connected(G):
        raise HTTPException(status_code=400, detail="El grafo no está completamente conectado. Revisa las conexiones.")

    mandatory = [c for c in connections if c["conn_type"] == "mandatory"]

    # Forzar aristas obligatorias contrayendo sus nodos antes del MST
    working_G = G.copy()

    if payload.algorithm == "kruskal":
        mst_edges = list(nx.minimum_spanning_edges(working_G, algorithm="kruskal", data=True))
    else:
        mst_edges = list(nx.minimum_spanning_edges(working_G, algorithm="prim", data=True))

    mandatory_ids = {(c["source_node_id"], c["target_node_id"]) for c in mandatory}
    mandatory_ids |= {(c["target_node_id"], c["source_node_id"]) for c in mandatory}

    node_map = {n["id"]: n for n in nodes}
    tree_edges = []
    total_cost = 0.0

    mandatory_pairs_added = set()
    for c in mandatory:
        src = c["source_node_id"]
        tgt = c["target_node_id"]
        if (src, tgt) not in mandatory_pairs_added and (tgt, src) not in mandatory_pairs_added:
            tree_edges.append({
                "source_node_id": src,
                "target_node_id": tgt,
                "cost": c["cost"],
                "conn_type": "mandatory",
                "source": node_map[src],
                "target": node_map[tgt],
            })
            total_cost += c["cost"]
            mandatory_pairs_added.add((src, tgt))

    for u, v, data in mst_edges:
        pair = (u, v)
        pair_rev = (v, u)
        if pair in mandatory_ids or pair_rev in mandatory_ids:
            continue
        cost = data.get("weight", 0)
        tree_edges.append({
            "source_node_id": u,
            "target_node_id": v,
            "cost": cost,
            "conn_type": data.get("conn_type", "normal"),
            "source": node_map[u],
            "target": node_map[v],
        })
        total_cost += cost

    if payload.budget and total_cost > payload.budget:
        raise HTTPException(
            status_code=400,
            detail=f"El costo total ({total_cost:.2f}) supera el presupuesto ({payload.budget:.2f})"
        )

    # Guardar resultado en Supabase
    result_res = supabase.table("results").insert({
        "project_id": payload.project_id,
        "total_cost": total_cost,
        "nodes_connected": len(nodes),
        "edges_used": len(tree_edges),
        "algorithm": payload.algorithm,
        "tree_edges": tree_edges,
    }).execute()

    result_id = result_res.data[0]["id"]

    # Guardar aristas individuales
    edge_rows = [
        {
            "result_id": result_id,
            "source_node_id": e["source_node_id"],
            "target_node_id": e["target_node_id"],
            "cost": e["cost"],
        }
        for e in tree_edges
    ]
    supabase.table("result_edges").insert(edge_rows).execute()

    # Marcar proyecto como calculado
    supabase.table("projects").update({"status": "calculated"}).eq("id", payload.project_id).execute()

    return {
        "result_id": result_id,
        "total_cost": total_cost,
        "nodes_connected": len(nodes),
        "edges_used": len(tree_edges),
        "algorithm": payload.algorithm,
        "tree_edges": tree_edges,
    }


@router.get("/results/{project_id}")
def get_results(project_id: str):
    res = (
        supabase.table("results")
        .select("*")
        .eq("project_id", project_id)
        .order("calculated_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Sin resultados para este proyecto")
    return res.data[0]
