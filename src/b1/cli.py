import typer
from rich.console import Console
from b1.core.exceptions import B1Error

from b1.commands.init import init_cmd
from b1.commands.install import install_cmd
from b1.commands.pull import pull_cmd
from b1.commands.push import push_cmd
from b1.commands.pair import pair_cmd
from b1.commands.rule import rule_cmd
from b1.commands.edge_case import edge_case_cmd
from b1.commands.dashboard import dashboard_cmd
from b1.commands.link_clickup import link_clickup_cmd
from b1.commands.link_github import link_github_cmd
from b1.commands.skill import app as skill_app

app = typer.Typer(
    name="b1",
    help="b1CodingTool: Agent-agnostic development environment manager.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

app.command(name="init")(init_cmd)
app.command(name="install")(install_cmd)
app.command(name="pull")(pull_cmd)
app.command(name="push")(push_cmd)
app.command(name="pair")(pair_cmd)
app.command(name="rule")(rule_cmd)
app.command(name="edge-case")(edge_case_cmd)
app.command(name="dashboard")(dashboard_cmd)
app.command(name="link-to-clickup-list")(link_clickup_cmd)
app.command(name="link-to-github-repo")(link_github_cmd)
app.add_typer(skill_app, name="skill")

def main():
    try:
        app()
    except B1Error as e:
        console.print(f"\n[bold red]Error:[/bold red] {e.message}")
        if e.suggestions:
            console.print("\n[bold yellow]Suggestions:[/bold yellow]")
            for suggestion in e.suggestions:
                console.print(f"  - {suggestion}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(1)
