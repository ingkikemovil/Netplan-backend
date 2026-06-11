from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from database import supabase

router = APIRouter()


class ConnectionCreate(BaseModel):
    project_id: str
    source_node_id: str
    target_node_id: str
    cost: float
    conn_type: str = "normal"


class ConnectionsBulk(BaseModel):
    connections: List[ConnectionCreate]


@router.get("/project/{project_id}")
def list_connections(project_id: str):
    res = (
        supabase.table("connections")
        .select("*, source:source_node_id(id,name,latitude,longitude), target:target_node_id(id,name,latitude,longitude)")
        .eq("project_id", project_id)
        .execute()
    )
    return res.data


@router.post("/")
def create_connection(payload: ConnectionCreate):
    res = supabase.table("connections").insert(payload.dict()).execute()
    return res.data[0]


@router.post("/bulk")
def create_connections_bulk(payload: ConnectionsBulk):
    rows = [c.dict() for c in payload.connections]
    res = supabase.table("connections").insert(rows).execute()
    return res.data


@router.patch("/{conn_id}")
def update_constraint(conn_id: str, conn_type: str):
    res = supabase.table("connections").update({"conn_type": conn_type}).eq("id", conn_id).execute()
    return res.data[0]


@router.delete("/{conn_id}")
def delete_connection(conn_id: str):
    supabase.table("connections").delete().eq("id", conn_id).execute()
    return {"message": "Conexión eliminada"}


@router.delete("/project/{project_id}/all")
def delete_all_connections(project_id: str):
    supabase.table("connections").delete().eq("project_id", project_id).execute()
    return {"message": "Conexiones eliminadas"}
