from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import supabase

router = APIRouter()


class NodeCreate(BaseModel):
    project_id: str
    name: str
    node_type: str = "city"
    latitude: float
    longitude: float
    address: Optional[str] = None


class NodesBulk(BaseModel):
    nodes: List[NodeCreate]


@router.get("/project/{project_id}")
def list_nodes(project_id: str):
    res = supabase.table("nodes").select("*").eq("project_id", project_id).execute()
    return res.data


@router.post("/")
def create_node(payload: NodeCreate):
    res = supabase.table("nodes").insert(payload.dict()).execute()
    return res.data[0]


@router.post("/bulk")
def create_nodes_bulk(payload: NodesBulk):
    rows = [n.dict() for n in payload.nodes]
    res = supabase.table("nodes").insert(rows).execute()
    return res.data


@router.delete("/{node_id}")
def delete_node(node_id: str):
    supabase.table("nodes").delete().eq("id", node_id).execute()
    return {"message": "Nodo eliminado"}


@router.delete("/project/{project_id}/all")
def delete_all_nodes(project_id: str):
    supabase.table("nodes").delete().eq("project_id", project_id).execute()
    return {"message": "Nodos eliminados"}
