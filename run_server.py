"""
Launch all microservices in a single process (development mode).

For production, run each service separately with uvicorn.
This script mounts all services under a single FastAPI app
with path-based routing for easy development.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.api import (
    create_orchestrator_app,
    create_attention_app,
    create_profiler_app,
    create_content_app,
    create_quiz_app,
    create_data_store_app,
)

# Main gateway app
app = FastAPI(title="Attention-Aware Study Assistant — API Gateway", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all service apps
app.mount("/attention", create_attention_app())
app.mount("/profiler", create_profiler_app())
app.mount("/content", create_content_app())
app.mount("/quiz", create_quiz_app())
app.mount("/data", create_data_store_app())

# Orchestrator endpoints at root level
orch_app = create_orchestrator_app()
for route in orch_app.routes:
    app.routes.append(route)


@app.get("/")
def root():
    return {
        "name": "Attention-Aware Study Assistant",
        "version": "1.0",
        "services": {
            "orchestrator": "/docs (root)",
            "attention_monitor": "/attention/docs",
            "learner_profiler": "/profiler/docs",
            "content_adapter": "/content/docs",
            "quiz_engine": "/quiz/docs",
            "data_store": "/data/docs",
        },
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  Starting all services on port 8000...")
    print("  API Docs: http://localhost:8000/docs")
    print("  Service docs: /attention/docs, /profiler/docs, etc.")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
