from dataclasses import dataclass, field
from typing import List, Optional

SHARED = "shared"
PERSONAL = "personal"
PROPRIETARY = "proprietary"


@dataclass
class ContextItem:
    title: str
    body: str
    source_path: str
    eager: bool
    visibility: str  # SHARED | PERSONAL | PROPRIETARY


@dataclass
class CompiledContext:
    items: List[ContextItem] = field(default_factory=list)

    def filter(
        self,
        *,
        visibility: Optional[str] = None,
        eager: Optional[bool] = None,
    ) -> List[ContextItem]:
        result = []
        for item in self.items:
            if visibility is not None and item.visibility != visibility:
                continue
            if eager is not None and item.eager != eager:
                continue
            result.append(item)
        return result

    def is_empty(self) -> bool:
        return not self.items

    def render_preview(self) -> str:
        """Plain-text preview of all compiled items (for the dashboard /api/context endpoint)."""
        blocks = []
        for item in self.items:
            tag = "eager" if item.eager else "lazy"
            head = f"## {item.title} [{item.visibility}, {tag}]"
            if item.eager:
                blocks.append(f"{head}\n\n{item.body}\n")
            else:
                blocks.append(f"{head}\n\n(reference: {item.source_path or item.title})\n")
        return "\n".join(blocks)
