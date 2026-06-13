from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import yaml
import re
from pathlib import Path
from b1.core.exceptions import ValidationError

class ModuleType(str, Enum):
    cross_cutting = "cross_cutting"
    development = "development"
    deployment = "deployment"

class SkillConfig(BaseModel):
    name: str = Field(..., description="Name of the skill")
    description: Optional[str] = Field(None, description="Brief description of what this skill does")
    install_command: Optional[str] = Field(None, description="Shell command to install/prepare this skill (e.g., npx set up)")

class CommandConfig(BaseModel):
    name: str = Field(..., description="The slash command name (e.g., /setup-flutter-bloc)")
    description: Optional[str] = Field(None, description="Brief description of what the command does")
    usage: Optional[str] = Field(None, description="Example usage of the command")
    
class ModuleConfig(BaseModel):
    name: str
    version: str
    type: ModuleType
    proprietary: bool = False
    description: Optional[str] = None
    skills: List[SkillConfig] = Field(default_factory=list)
    commands: List[CommandConfig] = Field(default_factory=list)
    hooks: dict = Field(default_factory=dict)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Module name must only contain alphanumeric characters, underscores, or hyphens.")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        # Simple semver-like regex
        if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", v):
            raise ValueError(f"Version '{v}' must follow semantic versioning (e.g., 1.0.0 or 1.0.0-alpha).")
        return v

    @classmethod
    def from_yaml(cls, filepath: Path) -> "ModuleConfig":
        if not filepath.exists():
            raise FileNotFoundError(f"Module config not found at {filepath}")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML format in {filepath}: {e}",
                suggestions=["Check for syntax errors in your YAML file.", "Ensure you are using valid YAML indentation."]
            )
            
        if not data:
            raise ValidationError(f"Empty or invalid YAML at {filepath}")
            
        try:
            return cls(**data)
        except Exception as e:
            raise ValidationError(
                f"Configuration validation failed for module at {filepath}\n{e}",
                suggestions=[
                    "Ensure all required fields (name, version, type) are present.",
                    "Verify that 'type' is one of: cross_cutting, development, deployment.",
                    "Check that 'name' and 'version' follow the required formats."
                ]
            )
