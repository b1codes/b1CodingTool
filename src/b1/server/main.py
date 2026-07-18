from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from typing import List, Dict, Optional
from pydantic import BaseModel

from b1.core.config import B1Config
from b1.core.compiler import ContextCompiler
from b1.core.translator import AgentTranslator
from b1.core.hook_engine import HookEngine
from b1.core.fetcher import ModuleFetcher
from b1.core.installer import ModuleInstaller
from b1.core.scaffolder import scaffold_project
from b1.core.context_manager import setup_context
from b1.core.exceptions import B1Error, ProjectError, ValidationError

app = FastAPI(title="b1CodingTool Dashboard API")

# --- Request Models ---

class ConfigUpdateRequest(BaseModel):
    upstream_repo: Optional[str] = None
    active_agents: Optional[List[str]] = None
    clickup_list_id: Optional[str] = None
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None
    default_branch: Optional[str] = None

class InstallRequest(BaseModel):
    source: str
    link: bool = False

class PairRequest(BaseModel):
    agents: Optional[List[str]] = None

# --- Exception Handlers ---

@app.exception_handler(B1Error)
async def b1_error_handler(request: Request, exc: B1Error):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "suggestions": getattr(exc, "suggestions", [])}
    )

@app.exception_handler(ProjectError)
async def project_error_handler(request: Request, exc: ProjectError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "suggestions": getattr(exc, "suggestions", [])}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "suggestions": getattr(exc, "suggestions", [])}
    )

# --- Endpoints ---

@app.get("/api/project")
def get_project_info():
    project_dir = Path.cwd()
    return {
        "name": project_dir.name,
        "path": str(project_dir),
        "initialized": (project_dir / ".agents").exists()
    }

@app.post("/api/project/init")
def init_project():
    project_dir = Path.cwd()
    scaffold_project(project_dir)
    setup_context(project_dir)
    return {"status": "success", "message": f"Project initialized at {project_dir}"}

@app.get("/api/config")
def get_config():
    project_dir = Path.cwd()
    config = B1Config.load(project_dir)
    return config.model_dump()

@app.put("/api/config")
def update_config(req: ConfigUpdateRequest):
    project_dir = Path.cwd()
    config = B1Config.load(project_dir)
    
    # Apply updates
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    config.save(project_dir)
    return config.model_dump()

@app.get("/api/modules")
def get_modules():
    project_dir = Path.cwd()
    modules_dir = project_dir / ".agents" / "modules"
    if not modules_dir.exists():
        return []
    
    modules = []
    for d in modules_dir.iterdir():
        if d.is_dir():
            modules.append({
                "name": d.name,
                "status": "installed",
                "path": str(d.relative_to(project_dir))
            })
    return modules

@app.post("/api/modules/install")
def install_module(req: InstallRequest):
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        raise ProjectError("Project not initialized. Run init first.")
        
    fetcher = ModuleFetcher()
    installer = ModuleInstaller(target_project_dir=project_dir)
    
    module_path = fetcher.fetch(req.source)
    installer.install(module_path, link=req.link)
    
    return {"status": "success", "module": req.source}

@app.get("/api/context")
def get_compiled_context():
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        raise HTTPException(status_code=400, detail="Project not initialized")
    
    config = B1Config.load(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    return {"content": compiler.compile().render_preview()}

@app.post("/api/context/pair")
def pair_context(req: Optional[PairRequest] = None):
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        raise ProjectError("Project not initialized.")
        
    config = B1Config.load(project_dir)
    
    # Update active agents if provided
    if req and req.agents:
        config.active_agents = req.agents
        config.save(project_dir)
        
    if not config.active_agents:
        raise ProjectError("No active agents configured for pairing.")
        
    hook_engine = HookEngine(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)
    
    # 1. Pre-pair hooks
    hook_engine.run_hooks("pre-pair")
    
    # 2. Compile
    compiled_text = compiler.compile()
    
    # 3. Translate
    translator.generate_files(config.active_agents, compiled_text)
    
    # 4. Post-pair hooks
    hook_engine.run_hooks("post-pair")
    
    return {"status": "success", "agents": config.active_agents}

# Path to the React build artifacts
DASHBOARD_DIST = Path(__file__).parent.parent.parent.parent / "dashboard" / "dist"

# Serve static files if the dist directory exists
if DASHBOARD_DIST.exists():
    app.mount("/", StaticFiles(directory=str(DASHBOARD_DIST), html=True), name="static")
else:
    @app.get("/")
    def root_no_dist():
        return {"message": "Welcome to b1CodingTool API. Dashboard not built yet. Run 'npm run build' in the dashboard directory."}
