from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import projects, nodes, connections, mst, upload, export

app = FastAPI(title="NetGrid API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(mst.router, prefix="/api/mst", tags=["mst"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/")
def root():
    return {"message": "NetGrid API funcionando"}
