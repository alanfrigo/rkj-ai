"""
HTML Report Generator
Generates visual HTML reports with charts
"""
import os
import json
from datetime import datetime
from typing import Dict, List
from jinja2 import Template


class HTMLReportGenerator:
    """Generates HTML reports from benchmark results"""
    
    def __init__(self):
        self.template = self._get_template()
    
    def generate(self, result: Dict, output_path: str) -> str:
        """Generate HTML report from benchmark result"""
        
        html_content = self.template.render(
            result=result,
            generated_at=datetime.now().isoformat(),
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _get_template(self) -> Template:
        return Template('''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Report - {{ result.scenario_name }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a; 
            color: #e5e5e5;
            line-height: 1.6;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #fff; margin-bottom: 0.5rem; }
        h2 { color: #a3a3a3; font-size: 1.25rem; margin: 2rem 0 1rem; }
        h3 { color: #737373; font-size: 1rem; margin: 1rem 0 0.5rem; }
        
        .header { 
            border-bottom: 1px solid #262626; 
            padding-bottom: 1rem; 
            margin-bottom: 2rem;
        }
        .meta { color: #737373; font-size: 0.875rem; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
        
        .card {
            background: #171717;
            border: 1px solid #262626;
            border-radius: 0.75rem;
            padding: 1.5rem;
        }
        .card-title { color: #a3a3a3; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem; }
        .card-value { font-size: 2rem; font-weight: 600; color: #fff; }
        .card-unit { color: #737373; font-size: 1rem; }
        
        .success { color: #22c55e; }
        .warning { color: #eab308; }
        .error { color: #ef4444; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #262626; }
        th { color: #a3a3a3; font-weight: 500; font-size: 0.875rem; }
        
        .chart-container { background: #171717; border-radius: 0.75rem; padding: 1.5rem; margin-top: 1rem; }
        
        .recommendations {
            background: linear-gradient(135deg, #1e3a5f 0%, #172554 100%);
            border: 1px solid #1e40af;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-top: 2rem;
        }
        .recommendations h2 { color: #60a5fa; margin-top: 0; }
        .recommendations ul { list-style: none; padding: 0; }
        .recommendations li { padding: 0.5rem 0; padding-left: 1.5rem; position: relative; }
        .recommendations li::before { content: "→"; position: absolute; left: 0; color: #60a5fa; }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .badge-success { background: #14532d; color: #22c55e; }
        .badge-error { background: #450a0a; color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Benchmark Report</h1>
            <p class="meta">
                Scenario: <strong>{{ result.scenario_name }}</strong> | 
                Duration: {{ "%.1f"|format(result.duration_seconds) }}s |
                Status: 
                {% if result.success %}
                    <span class="badge badge-success">✓ Success</span>
                {% else %}
                    <span class="badge badge-error">✗ Failed</span>
                {% endif %}
            </p>
            <p class="meta">Generated at: {{ generated_at }}</p>
        </div>
        
        <!-- Summary Cards -->
        <h2>📈 Summary</h2>
        <div class="grid">
            {% if result.docker_metrics.peak %}
            <div class="card">
                <div class="card-title">Peak Containers</div>
                <div class="card-value">{{ result.docker_metrics.peak.peak_containers }}</div>
            </div>
            <div class="card">
                <div class="card-title">Peak CPU Usage</div>
                <div class="card-value">{{ "%.1f"|format(result.docker_metrics.peak.peak_cpu_percent) }}<span class="card-unit">%</span></div>
            </div>
            <div class="card">
                <div class="card-title">Peak Memory</div>
                <div class="card-value">{{ "%.2f"|format(result.docker_metrics.peak.peak_memory_gb) }}<span class="card-unit">GB</span></div>
            </div>
            <div class="card">
                <div class="card-title">Network I/O</div>
                <div class="card-value">{{ "%.1f"|format(result.docker_metrics.peak.peak_network_rx_mb + result.docker_metrics.peak.peak_network_tx_mb) }}<span class="card-unit">MB</span></div>
            </div>
            {% endif %}
        </div>
        
        <!-- Timing Statistics -->
        {% if result.timing_summary %}
        <h2>⏱️ Timing Statistics</h2>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Operation</th>
                        <th>Count</th>
                        <th>Success Rate</th>
                        <th>Avg (ms)</th>
                        <th>P50 (ms)</th>
                        <th>P95 (ms)</th>
                        <th>P99 (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for op, stats in result.timing_summary.items() %}
                    <tr>
                        <td>{{ op }}</td>
                        <td>{{ stats.count }}</td>
                        <td class="{% if stats.success_rate >= 95 %}success{% elif stats.success_rate >= 80 %}warning{% else %}error{% endif %}">
                            {{ stats.success_rate }}%
                        </td>
                        <td>{{ "%.2f"|format(stats.avg_ms) }}</td>
                        <td>{{ "%.2f"|format(stats.p50_ms) }}</td>
                        <td>{{ "%.2f"|format(stats.p95_ms) }}</td>
                        <td>{{ "%.2f"|format(stats.p99_ms) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <!-- System Metrics -->
        {% if result.system_metrics.final %}
        <h2>🖥️ System Resources</h2>
        <div class="grid">
            <div class="card">
                <div class="card-title">CPU Cores</div>
                <div class="card-value">{{ result.system_metrics.final.cpu_count }}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Memory</div>
                <div class="card-value">{{ result.system_metrics.final.memory_total_gb }}<span class="card-unit">GB</span></div>
            </div>
            <div class="card">
                <div class="card-title">Memory Used</div>
                <div class="card-value">{{ result.system_metrics.final.memory_percent }}<span class="card-unit">%</span></div>
            </div>
            <div class="card">
                <div class="card-title">Disk Free</div>
                <div class="card-value">{{ result.system_metrics.final.disk_free_gb }}<span class="card-unit">GB</span></div>
            </div>
        </div>
        {% endif %}
        
        <!-- Recommendations -->
        {% if result.recommendations %}
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            
            {% if result.recommendations.per_bot_resources %}
            <h3>Per Bot Resources</h3>
            <p>RAM: {{ "%.0f"|format(result.recommendations.per_bot_resources.ram_mb) }} MB | CPU: {{ "%.1f"|format(result.recommendations.per_bot_resources.cpu_percent) }}%</p>
            {% endif %}
            
            {% if result.recommendations.projections %}
            <h3>Scaling Projections</h3>
            <table style="width: auto;">
                <thead>
                    <tr>
                        <th>Scale</th>
                        <th>Estimated RAM</th>
                        <th>Estimated CPUs</th>
                    </tr>
                </thead>
                <tbody>
                    {% for scale, proj in result.recommendations.projections.items() %}
                    <tr>
                        <td>{{ scale }}</td>
                        <td>{{ proj.estimated_ram_gb }} GB</td>
                        <td>{{ proj.estimated_cpu_cores }} cores</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            
            {% if result.recommendations.vps_recommendations %}
            <h3>VPS Recommendations</h3>
            <ul>
                {% for rec in result.recommendations.vps_recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
        
        <!-- Config Used -->
        <h2>⚙️ Test Configuration</h2>
        <div class="card">
            <pre style="color: #a3a3a3;">{{ result.config | tojson(indent=2) }}</pre>
        </div>
        
        {% if result.error %}
        <h2>❌ Error</h2>
        <div class="card" style="border-color: #ef4444;">
            <pre style="color: #ef4444;">{{ result.error }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
''')


class JSONReportGenerator:
    """Generates JSON reports from benchmark results"""
    
    def generate(self, result: Dict, output_path: str) -> str:
        """Generate JSON report"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        return output_path
