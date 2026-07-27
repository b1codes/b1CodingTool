# b1CodingTool: Project Context
This is the project-specific `AGENTS.md` context file.
It contains app logic, directory structures, and active tasks.

## Active Tasks
- Build out the module registry with real modules

## Key Design Decisions
- `b1 pair` compiles the full AGENTS.md hierarchy (root → project → module context files) into one string, then writes identical content to all agent-specific files. Per-agent formatting differences (e.g., XML tags for Claude) are a future enhancement in `translator.py`.
- Module install is intentionally non-destructive: if a skill's setup script fails, the error is logged but the rest of the installation completes.
- `ContextCompiler` assembles content in order: root `AGENTS.md` → `.agents/project/AGENTS.md` → each installed module's `context/*.md` files.

## Architecture Notes
- Follow the guidelines specified in the root `AGENTS.md`.
