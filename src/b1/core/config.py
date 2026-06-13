from pydantic import BaseModel, Field
import yaml
from pathlib import Path
from typing import List, Optional, Dict

class B1Config(BaseModel):
    upstream_repo: str = ""
    active_agents: List[str] = Field(default_factory=list)
    clickup_list_id: Optional[str] = None
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None
    default_branch: Optional[str] = None
    skillsmp_api_key: Optional[str] = None
    bundles: Dict[str, List[str]] = Field(default_factory=dict)
    
    @classmethod
    def load(cls, project_dir: Path) -> "B1Config":
        config_path = project_dir / ".agents" / "config.yaml"
        if not config_path.exists():
            return cls()
            
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return cls(**(data or {}))
            
    def save(self, project_dir: Path):
        config_path = project_dir / ".agents" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(), f)
