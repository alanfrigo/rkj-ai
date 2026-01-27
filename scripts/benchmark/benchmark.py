#!/usr/bin/env python3
"""
RKJ.AI Benchmark CLI
Professional load testing framework for the meeting recording system
"""
import asyncio
import os
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from scenarios import BotStressScenario, TranscriptionLoadScenario, APISecurityScenario
from generators import HTMLReportGenerator, JSONReportGenerator

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🚀 RKJ.AI Benchmark CLI
    
    Professional load testing for the meeting recording system.
    
    \b
    Examples:
        python benchmark.py stress --bots 10 --duration 300
        python benchmark.py transcription --files 20
        python benchmark.py report results/latest.json --format html
    """
    pass


@cli.command()
@click.option('--bots', '-b', default=10, help='Number of bot containers to spawn')
@click.option('--duration', '-d', default=300, help='Duration to keep containers running (seconds)')
@click.option('--output', '-o', default=None, help='Output file path for results')
def stress(bots: int, duration: int, output: str):
    """
    🤖 Bot Stress Test
    
    Spawns multiple bot containers to test resource usage.
    Measures CPU, RAM, and network consumption.
    """
    console.print(Panel.fit(
        f"[bold blue]Bot Stress Test[/bold blue]\n"
        f"Bots: {bots} | Duration: {duration}s",
        title="🤖 Starting Benchmark"
    ))
    
    async def run():
        scenario = BotStressScenario()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running stress test...", total=None)
            result = await scenario.run(bots=bots, duration=duration)
        
        # Display results
        display_results(result.to_dict())
        
        # Save results
        output_path = output or f"results/stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(result.to_dict(), output_path)
        
        return result
    
    asyncio.run(run())


@cli.command()
@click.option('--files', '-f', default=10, help='Number of transcription jobs to enqueue')
@click.option('--duration-minutes', '-d', default=1, help='Duration of audio files in minutes')
@click.option('--output', '-o', default=None, help='Output file path for results')
def transcription(files: int, duration_minutes: int, output: str):
    """
    📝 Transcription Load Test
    
    Tests transcription worker throughput.
    Measures queue processing time and API usage.
    """
    console.print(Panel.fit(
        f"[bold green]Transcription Load Test[/bold green]\n"
        f"Files: {files} | Duration: {duration_minutes}min each",
        title="📝 Starting Benchmark"
    ))
    
    async def run():
        scenario = TranscriptionLoadScenario()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running transcription test...", total=None)
            result = await scenario.run(files=files, file_duration_minutes=duration_minutes)
        
        # Display results
        display_results(result.to_dict())
        
        # Save results
        output_path = output or f"results/transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(result.to_dict(), output_path)
        
        return result
    
    asyncio.run(run())


@cli.command()
@click.option('--target', '-t', default="http://localhost:8000", help='Target API URL')
@click.option('--rps', '-r', default=100, help='Requests per second for flood tests')
@click.option('--duration', '-d', default=10, help='Duration for sustained tests (seconds)')
@click.option('--auth-token', '-a', default=None, help='Optional auth token for authenticated tests')
@click.option('--output', '-o', default=None, help='Output file path for results')
def security(target: str, rps: int, duration: int, auth_token: str, output: str):
    """
    🔒 API Security Test
    
    Tests rate limiting, authentication, and general API security.
    Run from OUTSIDE the VPS to test external rate limiting.
    """
    console.print(Panel.fit(
        f"[bold red]API Security Test[/bold red]\n"
        f"Target: {target} | RPS: {rps} | Duration: {duration}s",
        title="🔒 Starting Security Benchmark"
    ))
    
    async def run():
        scenario = APISecurityScenario()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running security tests...", total=None)
            result = await scenario.run(target=target, rps=rps, duration=duration, auth_token=auth_token)
        
        # Display results
        display_results(result.to_dict())
        
        # Save results
        output_path = output or f"results/security_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(result.to_dict(), output_path)
        
        return result
    
    asyncio.run(run())


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--format', '-f', 'output_format', default='html', 
              type=click.Choice(['html', 'json']), help='Output format')
@click.option('--output', '-o', default=None, help='Output file path')
def report(input_file: str, output_format: str, output: str):
    """
    📊 Generate Report
    
    Generate HTML or JSON report from benchmark results.
    """
    import json
    
    with open(input_file, 'r') as f:
        result = json.load(f)
    
    if output_format == 'html':
        generator = HTMLReportGenerator()
        output_path = output or input_file.replace('.json', '.html')
        generator.generate(result, output_path)
    else:
        generator = JSONReportGenerator()
        output_path = output or input_file
        generator.generate(result, output_path)
    
    console.print(f"[green]✓[/green] Report saved to: {output_path}")


@cli.command()
def info():
    """
    ℹ️ Show System Information
    
    Display current system resources and configuration.
    """
    from collectors import SystemStatsCollector
    
    collector = SystemStatsCollector()
    stats = collector.get_system_stats()
    
    table = Table(title="System Information")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("CPU Cores", str(stats["cpu_count"]))
    table.add_row("CPU Usage", f"{stats['cpu_percent']}%")
    table.add_row("Total Memory", f"{stats['memory_total_gb']} GB")
    table.add_row("Available Memory", f"{stats['memory_available_gb']} GB")
    table.add_row("Memory Usage", f"{stats['memory_percent']}%")
    table.add_row("Disk Total", f"{stats['disk_total_gb']} GB")
    table.add_row("Disk Free", f"{stats['disk_free_gb']} GB")
    table.add_row("Disk Usage", f"{stats['disk_percent']}%")
    
    console.print(table)
    
    # Capacity estimation
    ram_available = stats['memory_available_gb']
    estimated_bots = int(ram_available / 1.0)  # ~1GB per bot
    
    console.print(f"\n[yellow]💡 Estimated capacity:[/yellow] {estimated_bots} concurrent bots")
    console.print(f"   (based on ~1GB RAM per bot)")


def display_results(result: dict):
    """Display benchmark results in a formatted table"""
    console.print("\n")
    
    # Summary table
    table = Table(title="📊 Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Scenario", result.get("scenario_name", "N/A"))
    table.add_row("Duration", f"{result.get('duration_seconds', 0):.1f}s")
    table.add_row("Status", "✓ Success" if result.get("success") else "✗ Failed")
    
    # Docker metrics
    if result.get("docker_metrics", {}).get("peak"):
        peak = result["docker_metrics"]["peak"]
        table.add_row("Peak Containers", str(peak.get("peak_containers", 0)))
        table.add_row("Peak CPU", f"{peak.get('peak_cpu_percent', 0):.1f}%")
        table.add_row("Peak Memory", f"{peak.get('peak_memory_gb', 0):.2f} GB")
    
    console.print(table)
    
    # Recommendations
    if result.get("recommendations"):
        recs = result["recommendations"]
        console.print("\n[yellow]💡 Recommendations:[/yellow]")
        
        if recs.get("vps_recommendations"):
            for rec in recs["vps_recommendations"]:
                console.print(f"   → {rec}")
        
        if recs.get("projections"):
            console.print("\n[cyan]📈 Scaling Projections:[/cyan]")
            for scale, proj in recs["projections"].items():
                console.print(f"   {scale}: {proj['estimated_ram_gb']}GB RAM, {proj['estimated_cpu_cores']} CPUs")


def save_results(result: dict, output_path: str):
    """Save results to file"""
    import json
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    console.print(f"\n[green]✓[/green] Results saved to: {output_path}")
    
    # Also generate HTML report
    html_path = output_path.replace('.json', '.html')
    generator = HTMLReportGenerator()
    generator.generate(result, html_path)
    console.print(f"[green]✓[/green] HTML report saved to: {html_path}")


if __name__ == "__main__":
    cli()
