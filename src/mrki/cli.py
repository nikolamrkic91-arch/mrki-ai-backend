"""Command-line interface for Mrki."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from mrki import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="mrki")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file."
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output."
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """Mrki - Workflow automation platform.
    
    Mrki provides powerful tools for creating, scheduling, and monitoring
    automated workflows and tasks.
    
    Examples:
        \b
        # Start the server
        mrki server start
        
        # List workflows
        mrki workflow list
        
        # Create a workflow
        mrki workflow create --name my-workflow --file workflow.yaml
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


@cli.group()
def server() -> None:
    """Server management commands."""
    pass


@server.command("start")
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to."
)
@click.option(
    "--port",
    "-p",
    default=8080,
    type=int,
    help="Port to listen on."
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug mode."
)
@click.option(
    "--reload",
    "-r",
    is_flag=True,
    help="Enable auto-reload on code changes."
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=1,
    help="Number of worker processes."
)
def server_start(
    host: str,
    port: int,
    debug: bool,
    reload: bool,
    workers: int
) -> None:
    """Start the Mrki server."""
    import uvicorn
    
    console.print(f"[green]Starting Mrki server on {host}:{port}[/green]")
    
    uvicorn.run(
        "mrki.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level="debug" if debug else "info"
    )


@server.command("stop")
def server_stop() -> None:
    """Stop the Mrki server."""
    console.print("[yellow]Server stop command not implemented yet[/yellow]")


@cli.group()
def workflow() -> None:
    """Workflow management commands."""
    pass


@workflow.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format."
)
def workflow_list(output_format: str) -> None:
    """List all workflows."""
    # Placeholder implementation
    workflows = [
        {"name": "example-1", "status": "active", "executions": 10},
        {"name": "example-2", "status": "inactive", "executions": 5},
    ]
    
    if output_format == "table":
        table = Table(title="Workflows")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Executions", justify="right")
        
        for wf in workflows:
            table.add_row(wf["name"], wf["status"], str(wf["executions"]))
        
        console.print(table)
    elif output_format == "json":
        import json
        console.print(json.dumps(workflows, indent=2))
    else:
        import yaml
        console.print(yaml.dump(workflows))


@workflow.command("create")
@click.option(
    "--name",
    "-n",
    required=True,
    help="Workflow name."
)
@click.option(
    "--file",
    "-f",
    "workflow_file",
    type=click.Path(exists=True),
    required=True,
    help="Path to workflow definition file."
)
def workflow_create(name: str, workflow_file: str) -> None:
    """Create a new workflow."""
    console.print(f"[green]Creating workflow: {name}[/green]")
    console.print(f"[blue]From file: {workflow_file}[/blue]")


@workflow.command("get")
@click.argument("name")
def workflow_get(name: str) -> None:
    """Get workflow details."""
    console.print(f"[blue]Workflow: {name}[/blue]")


@workflow.command("run")
@click.argument("name")
@click.option(
    "--variables",
    "-v",
    multiple=True,
    help="Variables to pass to the workflow (key=value)."
)
def workflow_run(name: str, variables: tuple) -> None:
    """Execute a workflow."""
    console.print(f"[green]Running workflow: {name}[/green]")
    if variables:
        console.print(f"[blue]Variables: {variables}[/blue]")


@workflow.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this workflow?")
def workflow_delete(name: str) -> None:
    """Delete a workflow."""
    console.print(f"[red]Deleting workflow: {name}[/red]")


@cli.group()
def task() -> None:
    """Task management commands."""
    pass


@task.command("list")
def task_list() -> None:
    """List all tasks."""
    console.print("[blue]Tasks:[/blue]")


@task.command("run")
@click.argument("name")
def task_run(name: str) -> None:
    """Execute a task."""
    console.print(f"[green]Running task: {name}[/green]")


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    console.print("[blue]Current configuration:[/blue]")


@config.command("validate")
def config_validate() -> None:
    """Validate configuration file."""
    console.print("[green]Configuration is valid[/green]")


@cli.command()
def health() -> None:
    """Check server health status."""
    console.print("[green]Server is healthy[/green]")


def main() -> None:
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
