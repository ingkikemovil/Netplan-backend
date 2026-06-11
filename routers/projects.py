from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from database import supabase

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.get("/")
def list_projects(user_id: str):
    res = supabase.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data


@router.post("/")
def create_project(payload: ProjectCreate):
    res = supabase.table("projects").insert({
        "name": payload.name,
        "description": payload.description,
        "user_id": payload.user_id,
        "status": "draft",
    }).execute()
    return res.data[0]


@router.get("/{project_id}")
def get_project(project_id: str):
    res = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return res.data


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    data = {k: v for k, v in payload.dict().items() if v is not None}
    res = supabase.table("projects").update(data).eq("id", project_id).execute()
    return res.data[0]


@router.delete("/{project_id}")
def delete_project(project_id: str):
    supabase.table("projects").delete().eq("id", project_id).execute()
    return {"message": "Proyecto eliminado"}
