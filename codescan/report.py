"""
报告生成模块
~~~~~~~~~

生成各种格式的报告
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import html
from pathlib import Path
import tempfile
import io
import base64
from typing import Tuple

logger = logging.getLogger(__name__)

class ReportGenerator:
    """报告生成器基类"""
    
    def generate_report(self, scan_result, output_path: Optional[str] = None) -> str:
        """生成报告
        
        Args:
            scan_result: 扫描结果
            output_path: 输出文件路径(如果为None，则返回报告内容)
            
        Returns:
            如果output_path为None，则返回报告内容；否则返回输出文件路径
        """
        report_content = self._generate_content(scan_result)
        
        if output_path:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            logger.info(f"报告已保存到: {output_path}")
            return output_path
        else:
            return report_content
    
    def _generate_content(self, scan_result) -> str:
        """生成报告内容(子类实现)
        
        Args:
            scan_result: 扫描结果
            
        Returns:
            报告内容
        """
        raise NotImplementedError("子类必须实现此方法")

class HTMLReportGenerator(ReportGenerator):
    """HTML报告生成器"""
    
    def _generate_content(self, scan_result) -> str:
        """生成HTML格式报告"""
        # 生成HTML报告
        scan_timestamp = datetime.fromtimestamp(scan_result.timestamp)
        formatted_date = scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        severity_colors = {
            "critical": "#FF0000",
            "high": "#FF6600",
            "medium": "#FFCC00",
            "low": "#FFFF00",
            "info": "#00CC00"
        }
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>代码漏洞检测报告</title>
            <style>
                :root {{
                    --primary-color: #2563eb;
                    --secondary-color: #4b5563;
                    --danger-color: #dc2626;
                    --warning-color: #f59e0b;
                    --success-color: #10b981;
                    --info-color: #3b82f6;
                    --background-color: #f9fafb;
                    --card-bg: #ffffff;
                    --header-bg: #1e40af;
                    --text-color: #1f2937;
                    --text-light: #6b7280;
                    --border-color: #e5e7eb;
                }}
                
                body {{ 
                    font-family: 'Segoe UI', Roboto, -apple-system, BlinkMacSystemFont, sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    color: var(--text-color);
                    background-color: var(--background-color);
                    line-height: 1.6;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 0 20px;
                }}
                h1, h2, h3 {{ 
                    color: #1a1a1a; 
                    font-weight: 700;
                    letter-spacing: -0.025em;
                }}
                h1 {{ font-size: 2rem; margin-bottom: 1rem; }}
                h2 {{ font-size: 1.5rem; margin: 2rem 0 1rem 0; position: relative; }}
                h2::after {{
                    content: '';
                    position: absolute;
                    bottom: -10px;
                    left: 0;
                    width: 50px;
                    height: 4px;
                    background: var(--primary-color);
                    border-radius: 2px;
                }}
                h3 {{ font-size: 1.25rem; margin: 1.5rem 0 0.75rem 0; }}
                
                .header {{ 
                    background: linear-gradient(135deg, var(--header-bg), #2563eb); 
                    color: white; 
                    padding: 30px; 
                    margin-bottom: 30px; 
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    position: relative;
                    overflow: hidden;
                }}
                
                .header::before {{
                    content: "";
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none"><path fill="rgba(255,255,255,0.05)" d="M0 0 L100 0 L100 100 Z"></path></svg>');
                    background-size: 100% 100%;
                }}
                
                .header h1 {{
                    color: white;
                    margin-top: 0;
                    font-size: 2.25rem;
                    position: relative;
                }}
                
                .header p {{
                    position: relative;
                    margin: 0.5rem 0;
                    opacity: 0.9;
                    font-weight: 300;
                }}
                
                .summary, .card {{ 
                    background-color: var(--card-bg); 
                    padding: 25px; 
                    border-radius: 8px; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                    border: 1px solid var(--border-color);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                
                .summary:hover, .card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
                }}
                
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .grid-item {{
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid var(--border-color);
                }}
                
                .stats-card {{
                    text-align: center;
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                    border: 1px solid var(--border-color);
                    transition: transform 0.2s;
                }}
                
                .stats-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
                }}
                
                .stats-card .number {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: var(--primary-color);
                    line-height: 1;
                    margin: 10px 0;
                }}
                
                .stats-card .label {{
                    font-size: 0.9rem;
                    color: var(--text-light);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                .issues {{ margin-bottom: 30px; }}
                
                .issue {{ 
                    background-color: var(--card-bg); 
                    padding: 20px 25px; 
                    margin-bottom: 20px; 
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                    border-left: 5px solid #ccc; 
                    transition: transform 0.2s, box-shadow 0.2s;
                    position: relative;
                }}
                
                .issue:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.08);
                }}
                
                .issue::after {{
                    content: '';
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background-color: #ccc;
                }}
                
                .critical {{ 
                    border-left-color: #dc2626; 
                }}
                .critical::after {{ 
                    background-color: #dc2626; 
                }}
                
                .high {{ 
                    border-left-color: #ea580c; 
                }}
                .high::after {{ 
                    background-color: #ea580c; 
                }}
                
                .medium {{ 
                    border-left-color: #f59e0b; 
                }}
                .medium::after {{ 
                    background-color: #f59e0b; 
                }}
                
                .low {{ 
                    border-left-color: #3b82f6; 
                }}
                .low::after {{ 
                    background-color: #3b82f6; 
                }}
                
                .info {{ 
                    border-left-color: #10b981; 
                }}
                .info::after {{ 
                    background-color: #10b981; 
                }}
                
                .code {{ 
                    background-color: #1e293b; 
                    color: #e2e8f0; 
                    padding: 15px; 
                    border-radius: 6px; 
                    font-family: 'Fira Code', 'Consolas', monospace; 
                    white-space: pre-wrap;
                    position: relative;
                    margin: 15px 0;
                    overflow-x: auto;
                }}
                
                .code::before {{
                    content: "代码片段";
                    position: absolute;
                    top: 0;
                    right: 0;
                    background: rgba(0,0,0,0.3);
                    color: #ffffff;
                    padding: 2px 8px;
                    font-size: 0.75rem;
                    border-radius: 0 5px 0 5px;
                }}
                
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0; 
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                }}
                
                th, td {{ 
                    border: 1px solid var(--border-color);
                    padding: 12px 15px; 
                    text-align: left; 
                }}
                
                th {{ 
                    background-color: #f3f4f6; 
                    font-weight: 600;
                    position: relative;
                }}
                
                tr:nth-child(even) {{ 
                    background-color: #fafafa; 
                }}
                
                tr:hover {{
                    background-color: #f1f5f9;
                }}
                
                .chart {{ 
                    height: 350px; 
                    margin: 30px 0;
                    background: var(--card-bg);
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
                    border: 1px solid var(--border-color);
                }}
                
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    margin-right: 5px;
                }}
                
                .badge-critical {{ background-color: #fee2e2; color: #b91c1c; }}
                .badge-high {{ background-color: #ffedd5; color: #c2410c; }}
                .badge-medium {{ background-color: #fef3c7; color: #b45309; }}
                .badge-low {{ background-color: #dbeafe; color: #1d4ed8; }}
                .badge-info {{ background-color: #d1fae5; color: #047857; }}
                
                .recommendation {{
                    background-color: #ecfdf5;
                    border: 1px solid #d1fae5;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 15px 0;
                    position: relative;
                }}
                
                .recommendation::before {{
                    content: "💡";
                    margin-right: 8px;
                    font-size: 1.2em;
                }}
                
                .file-path {{
                    font-family: 'Fira Code', 'Consolas', monospace;
                    background-color: #f1f5f9;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.9em;
                }}
                
                .issue-meta {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin: 15px 0;
                }}
                
                .issue-meta-item {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                
                .severity-icon {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 5px;
                }}
                
                .footer {{
                    margin-top: 50px;
                    padding: 20px;
                    text-align: center;
                    color: var(--text-light);
                    font-size: 0.9rem;
                    border-top: 1px solid var(--border-color);
                }}
                
                @media (max-width: 768px) {{
                    .grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .header h1 {{
                        font-size: 1.8rem;
                    }}
                }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>代码漏洞检测报告</h1>
                    <p>扫描路径: {html.escape(scan_result.scan_path)}</p>
                    <p>扫描类型: {html.escape(scan_result.scan_type)}</p>
                    <p>扫描时间: {formatted_date}</p>
                </div>
                
                <div class="summary">
                    <h2>摘要统计</h2>
                    
                    <div class="grid">
                        <div class="stats-card">
                            <div class="number">{scan_result.total_issues}</div>
                            <div class="label">总漏洞数</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="number">{scan_result.issues_by_severity.get('critical', 0) + scan_result.issues_by_severity.get('high', 0)}</div>
                            <div class="label">高危漏洞</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="number">{scan_result.stats.get('total_files', 0)}</div>
                            <div class="label">已扫描文件</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="number">{scan_result.stats.get('total_lines_of_code', 0)}</div>
                            <div class="label">代码行数</div>
                        </div>
                    </div>
                    
                    <h3>漏洞严重程度分布</h3>
                    <table>
                        <tr>
                            <th>严重程度</th>
                            <th>数量</th>
                            <th>百分比</th>
                        </tr>
        """
        
        # 添加问题统计
        for severity, count in scan_result.issues_by_severity.items():
            severity_name = {
                "critical": "严重",
                "high": "高危",
                "medium": "中危",
                "low": "低危",
                "info": "信息"
            }.get(severity, severity.capitalize())
            
            percentage = 0
            if scan_result.total_issues > 0:
                percentage = round(count / scan_result.total_issues * 100, 1)
            
            badge_class = f"badge badge-{severity}"
            
            html_content += f"""
                        <tr>
                            <td><span class="{badge_class}">{severity_name}</span></td>
                            <td>{count}</td>
                            <td>{percentage}%</td>
                        </tr>
            """
        
        html_content += """
                    </table>
                </div>
        """
        
        # 添加统计图表
        if scan_result.issues:
            html_content += """
                <div class="card">
                    <h2>漏洞分析图表</h2>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                        <div style="flex: 1; min-width: 300px;">
                            <h3>漏洞严重度分布</h3>
                            <div class="chart">
                                <canvas id="severityChart"></canvas>
                            </div>
                </div>
                
                        <div style="flex: 1; min-width: 300px;">
                            <h3>漏洞类型分布</h3>
                            <div class="chart">
                                <canvas id="issueTypeChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    Chart.register(ChartDataLabels);
                    
                    document.addEventListener('DOMContentLoaded', function() {
                        // 严重度图表
                        const ctxSeverity = document.getElementById('severityChart').getContext('2d');
                        new Chart(ctxSeverity, {
                            type: 'doughnut',
                            data: {
                                labels: ["严重", "高危", "中危", "低危", "信息"],
                                datasets: [{
                                    data: [
                                        """ + str(scan_result.issues_by_severity.get('critical', 0)) + """,
                                        """ + str(scan_result.issues_by_severity.get('high', 0)) + """,
                                        """ + str(scan_result.issues_by_severity.get('medium', 0)) + """,
                                        """ + str(scan_result.issues_by_severity.get('low', 0)) + """,
                                        """ + str(scan_result.issues_by_severity.get('info', 0)) + """
                                    ],
                                    backgroundColor: [
                                        '#dc2626',
                                        '#ea580c',
                                        '#f59e0b',
                                        '#3b82f6',
                                        '#10b981'
                                    ],
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'right',
                                    },
                                    datalabels: {
                                        color: '#fff',
                                        formatter: (value, ctx) => {
                                            if (value === 0) return '';
                                            return value;
                                        }
                                    }
                                }
                            }
                        });
                        
                        // 漏洞类型分布
                        // 计算不同类型的漏洞
                        const issueTypes = {};
                        const issues = """ + json.dumps([{'description': issue.description} for issue in scan_result.issues]) + """;
                        
                        issues.forEach(issue => {
                            // 提取漏洞类型（通常是描述的前几个字或冒号前的内容）
                            let type = issue.description.split(':')[0].trim();
                            if (type.length > 25) {
                                type = type.substring(0, 25) + '...';
                            }
                            issueTypes[type] = (issueTypes[type] || 0) + 1;
                        });
                        
                        const typeLabels = Object.keys(issueTypes).slice(0, 8); // 取前8个类型
                        const typeCounts = typeLabels.map(label => issueTypes[label]);
                        
                        const ctxIssueType = document.getElementById('issueTypeChart').getContext('2d');
                        new Chart(ctxIssueType, {
                            type: 'pie',
                            data: {
                                labels: typeLabels,
                                datasets: [{
                                    data: typeCounts,
                                    backgroundColor: [
                                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                                        '#8b5cf6', '#ec4899', '#f97316', '#14b8a6'
                                    ],
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'right',
                                        labels: {
                                            boxWidth: 15
                                        }
                                    },
                                    datalabels: {
                                        color: '#fff',
                                        formatter: (value, ctx) => {
                                            if (value === 0) return '';
                                            const sum = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                            const percentage = Math.round((value / sum) * 100);
                                            return percentage + '%';
                                        }
                                    }
                                }
                            }
                        });
                    });
                </script>
            """
        
        # 添加项目信息
        if scan_result.project_info:
            html_content += """
                <div class="card">
                    <h2>项目详细信息</h2>
            """
            
            # 显示项目基本信息
            if 'basic_info' in scan_result.project_info:
                html_content += """
                    <div style="margin-bottom: 20px;">
                        <h3>基本信息</h3>
                        <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));">
                """
                
                basic_info = scan_result.project_info['basic_info']
                for key, value in basic_info.items():
                        html_content += f"""
                        <div class="grid-item">
                            <div class="label">{key}</div>
                            <div class="value">{html.escape(str(value))}</div>
                        </div>
                    """
            
            html_content += """
                        </div>
                </div>
            """
        
            # AI 分析结果
            if 'project_type' in scan_result.project_info:
                project_type = scan_result.project_info.get('project_type', '未知')
                main_functionality = scan_result.project_info.get('main_functionality', '未知')
                architecture = scan_result.project_info.get('architecture', '未知')
                components = scan_result.project_info.get('components', [])
            
            html_content += """
                    <div style="margin-top: 30px;">
                        <h3>AI 智能分析</h3>
                    <table>
                        <tr>
                                <th width="20%">项目类型</th>
                            <td>""" + html.escape(str(project_type)) + """</td>
                        </tr>
                        <tr>
                            <th>主要功能</th>
                            <td>""" + html.escape(str(main_functionality)) + """</td>
                        </tr>
                        <tr>
                            <th>架构概述</th>
                            <td>""" + html.escape(str(architecture)) + """</td>
                        </tr>
            """
        
            if components:
                html_content += """
                            <tr>
                                <th>主要组件</th>
                                <td>
                                    <ul>
                    """
                    
                for component in components:
                    html_content += f"""
                                        <li>{html.escape(str(component))}</li>
                        """
                    
                html_content += """
                                    </ul>
                                </td>
                            </tr>
                    """
                
            html_content += """
                        </table>
                    </div>
                """
            
            # 显示语言统计
            if 'language_stats' in scan_result.project_info or 'languages' in scan_result.stats:
                html_content += """
                    <div style="margin-top: 30px;">
                        <h3>语言分布</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div style="flex: 1; min-width: 300px;">
                                <table>
                                    <tr>
                                        <th>语言</th>
                                        <th>文件数</th>
                                        <th>占比</th>
                                    </tr>
                """
                
                lang_stats = scan_result.project_info.get('language_stats', scan_result.stats.get('languages', {}))
                total_files = sum(lang_stats.values())
                
                for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
                    percentage = round((count / total_files) * 100, 1) if total_files > 0 else 0
                html_content += f"""
                                    <tr>
                                        <td>{html.escape(str(lang))}</td>
                                        <td>{count}</td>
                                        <td>{percentage}%</td>
                                    </tr>
                """
                
            html_content += """
                                </table>
                    </div>
                            <div style="flex: 1; min-width: 300px;">
                                <div class="chart" style="height: 250px;">
                                    <canvas id="languageChart"></canvas>
                </div>
            </div>
                        </div>
                    </div>
                    
                    <script>
                        document.addEventListener('DOMContentLoaded', function() {
                            // 语言分布图表
                            const langData = {
                """
                
                # 添加语言数据
            lang_pairs = []
            for lang, count in lang_stats.items():
                lang_pairs.append(f"'{lang}': {count}")
                
                html_content += ", ".join(lang_pairs)
                
                html_content += """
                            };
                            
                            const langLabels = Object.keys(langData);
                            const langValues = Object.values(langData);
                            const langColors = [
                                '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                                '#8b5cf6', '#ec4899', '#f97316', '#14b8a6',
                                '#a855f7', '#06b6d4', '#84cc16', '#64748b'
                            ];
                            
                            const ctxLang = document.getElementById('languageChart').getContext('2d');
                            new Chart(ctxLang, {
                                type: 'doughnut',
                                data: {
                                    labels: langLabels,
                                    datasets: [{
                                        data: langValues,
                                        backgroundColor: langColors,
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                        legend: {
                                            position: 'right',
                                            labels: {
                                                boxWidth: 15
                                            }
                                        },
                                        datalabels: {
                                            color: '#fff',
                                            formatter: (value, ctx) => {
                                                const sum = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                                const percentage = Math.round((value / sum) * 100);
                                                return percentage > 5 ? percentage + '%' : '';
                                            }
                                        }
                                    }
                                }
                            });
                        });
                    </script>
                """
            
            # 显示代码统计信息
            if 'code_stats' in scan_result.project_info or 'total_lines_of_code' in scan_result.stats:
                html_content += """
                    <div style="margin-top: 30px;">
                        <h3>代码统计</h3>
                        <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));">
                """
                
                code_stats = scan_result.project_info.get('code_stats', {})
                if 'total_lines_of_code' in scan_result.stats:
                    code_stats['总代码行数'] = scan_result.stats['total_lines_of_code']
                
                for key, value in code_stats.items():
                    if isinstance(value, (int, float)):
                        html_content += f"""
                            <div class="stats-card">
                                <div class="number">{value:,}</div>
                                <div class="label">{html.escape(str(key))}</div>
                            </div>
                        """
                
                html_content += """
                        </div>
                    </div>
                """
            
            # 显示文件类型分布
            if 'file_extensions' in scan_result.stats:
                html_content += """
                    <div style="margin-top: 30px;">
                        <h3>文件类型分布</h3>
                        <table>
                            <tr>
                                <th>文件类型</th>
                                <th>数量</th>
                            </tr>
                """
                
                file_extensions = scan_result.stats['file_extensions']
                for ext, count in sorted(file_extensions.items(), key=lambda x: x[1], reverse=True):
                    ext_display = ext if ext else "无扩展名"
                    html_content += f"""
                            <tr>
                                <td>{html.escape(ext_display)}</td>
                                <td>{count}</td>
                            </tr>
                    """
                
                html_content += """
                        </table>
                    </div>
                """
            
            # 显示项目结构
            if 'directory_structure' in scan_result.project_info:
                html_content += """
                    <div style="margin-top: 30px;">
                        <h3>项目结构</h3>
                        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; 
                                    font-family: 'Fira Code', Consolas, monospace; white-space: pre-wrap;">
                """
                
                dir_structure = scan_result.project_info['directory_structure']
                
                def format_dir_structure_html(structure, prefix=""):
                    result = ""
                    items = list(structure.items())
                    for i, (name, content) in enumerate(items):
                        is_last = i == len(items) - 1
                        if isinstance(content, dict):  # 目录
                            branch = '└── ' if is_last else '├── '
                            result += f"{prefix}{branch}<span style='color: #2563eb;'>{html.escape(name)}/</span><br>"
                            next_prefix = prefix + ('&nbsp;&nbsp;&nbsp;&nbsp;' if is_last else '│&nbsp;&nbsp;&nbsp;')
                            result += format_dir_structure_html(content, next_prefix)
                        else:  # 文件
                            branch = '└── ' if is_last else '├── '
                            result += f"{prefix}{branch}{html.escape(name)}<br>"
                    return result
                
                html_content += format_dir_structure_html(dir_structure)
                
                html_content += """
                        </div>
                    </div>
                """
            
            # 其他项目信息
            other_info = {}
            for key, value in scan_result.project_info.items():
                if key not in ['basic_info', 'language_stats', 'code_stats', 'directory_structure', 
                               'project_type', 'main_functionality', 'architecture', 'components']:
                    other_info[key] = value
            
            if other_info:
                html_content += """
                    <div style="margin-top: 30px;">
                        <h3>其他项目信息</h3>
                        <table>
                """
                
                for key, value in other_info.items():
                    if isinstance(value, dict):
                        html_content += f"""
                            <tr>
                                <th colspan="2">{html.escape(str(key))}</th>
                            </tr>
                        """
                    for sub_key, sub_value in value.items():
                            html_content += f"""
                            <tr>
                                <td style="padding-left: 30px;">{html.escape(str(sub_key))}</td>
                                <td>{html.escape(str(sub_value))}</td>
                            </tr>
                            """
                else:
                        html_content += f"""
                            <tr>
                                <td>{html.escape(str(key))}</td>
                                <td>{html.escape(str(value))}</td>
                            </tr>
                        """
                
                html_content += """
                        </table>
                    </div>
                """
            
            html_content += """
                </div>
            """
        
        # 添加问题详情
        html_content += """
                <div class="issues">
                    <h2>漏洞详情</h2>
        """
        
        # 根据风险程度对漏洞排序
        sorted_issues = sorted(
            scan_result.issues,
            key=lambda x: {
                'critical': 0,
                'high': 1,
                'medium': 2,
                'low': 3,
                'info': 4
            }.get(x.severity, 5)
        )
        
        for issue in sorted_issues:
            severity_name = {
                "critical": "严重",
                "high": "高危",
                "medium": "中危",
                "low": "低危",
                "info": "信息"
            }.get(issue.severity, issue.severity.capitalize())
            
            badge_class = f"badge badge-{issue.severity}"
            
            html_content += f"""
                    <div class="issue {issue.severity}">
                        <h3>{html.escape(issue.description)}</h3>
                        
                        <div class="issue-meta">
                            <div class="issue-meta-item">
                                <strong>文件:</strong>
                                <span class="file-path">{html.escape(issue.file_path)}</span>
                            </div>
            """
            
            if issue.line_number:
                html_content += f"""
                            <div class="issue-meta-item">
                                <strong>行号:</strong> {issue.line_number}
                            </div>
                """
                
            html_content += f"""
                            <div class="issue-meta-item">
                                <strong>严重程度:</strong>
                                <span class="{badge_class}">{severity_name}</span>
                            </div>
                            
                            <div class="issue-meta-item">
                                <strong>置信度:</strong> {issue.confidence.capitalize()}
                            </div>
            """
                
            if issue.cwe_id:
                html_content += f"""
                            <div class="issue-meta-item">
                                <strong>CWE ID:</strong>
                                <a href="https://cwe.mitre.org/data/definitions/{issue.cwe_id}.html" target="_blank">{issue.cwe_id}</a>
                            </div>
                """
            
            html_content += """
                        </div>
            """
            
            if issue.code_snippet:
                html_content += f"""
                        <pre class="code">{html.escape(issue.code_snippet)}</pre>
                """
            
            if issue.recommendation:
                html_content += f"""
                        <div class="recommendation">
                            <strong>修复建议:</strong> {html.escape(issue.recommendation)}
                        </div>
                """
                
            html_content += """
                    </div>
            """
        
        html_content += """
                </div>
                
                <div class="footer">
                    <p>由代码漏洞扫描工具生成 | 报告生成时间: """ + formatted_date + """</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content

class JSONReportGenerator(ReportGenerator):
    """JSON报告生成器"""
    
    def _generate_content(self, scan_result) -> str:
        """生成JSON格式报告"""
        report_data = {
            "timestamp": scan_result.timestamp,
            "formatted_time": datetime.fromtimestamp(scan_result.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "scan_type": scan_result.scan_type,
            "scan_path": scan_result.scan_path,
            "scan_model": scan_result.scan_model,
            "stats": scan_result.stats,
            "project_info": scan_result.project_info,
            "issues": []
        }
        
        for issue in scan_result.issues:
            issue_data = {
                "title": issue.title,
                "description": issue.description,
                "severity": issue.severity,
                "confidence": issue.confidence,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "location": issue.location,
                "code_snippet": issue.code_snippet,
                "recommendation": issue.recommendation,
                "cwe_id": issue.cwe_id,
                "owasp_category": issue.owasp_category,
                "vulnerability_type": issue.vulnerability_type
            }
            report_data["issues"].append(issue_data)
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)

class TextReportGenerator(ReportGenerator):
    """文本报告生成器"""
    
    def _generate_content(self, scan_result) -> str:
        """生成文本格式报告"""
        # 扫描信息
        scan_timestamp = datetime.fromtimestamp(scan_result.timestamp)
        formatted_date = scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建报告标题
        report = [
            "=" * 80,
            "                     代码安全扫描报告                     ",
            "=" * 80,
            f"扫描时间: {formatted_date}",
            f"扫描类型: {'目录扫描' if scan_result.scan_type.lower() == 'directory' else '文件扫描'}",
            f"扫描路径: {scan_result.scan_path}",
            f"使用模型: {scan_result.scan_model}",
            "-" * 80
        ]
        
        # 统计信息
        stats = scan_result.stats
        report.append("\n统计信息:")
        report.append("-" * 80)
        
        if scan_result.scan_type.lower() == "directory":
            report.append(f"扫描文件总数: {stats.get('total_files', 0)}")
            report.append(f"代码总行数: {stats.get('total_lines_of_code', 0):,}")
            
            # 语言分布
            if "languages" in stats and stats["languages"]:
                report.append("\n语言分布:")
                for lang, count in sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True):
                    report.append(f"  {lang}: {count} 个文件")
                    
            # 文件类型分布
            if "file_extensions" in stats and stats["file_extensions"]:
                report.append("\n文件类型分布:")
                for ext, count in sorted(stats["file_extensions"].items(), key=lambda x: x[1], reverse=True):
                    report.append(f"  {ext if ext else '无扩展名'}: {count} 个文件")
        else:
            report.append(f"文件: {os.path.basename(scan_result.scan_path)}")
            report.append(f"代码行数: {stats.get('lines_of_code', 0):,}")
            if "language" in stats:
                report.append(f"语言: {stats['language']}")
        
        # 漏洞概述
        report.append("\n漏洞概述:")
        report.append("-" * 80)
        
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        # 计算各严重性级别的漏洞数量
        for issue in scan_result.issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1
        
        # 添加严重程度统计
        report.append(f"严重 (Critical): {severity_counts['critical']} 个")
        report.append(f"高危 (High): {severity_counts['high']} 个")
        report.append(f"中危 (Medium): {severity_counts['medium']} 个")
        report.append(f"低危 (Low): {severity_counts['low']} 个")
        report.append(f"提示 (Info): {severity_counts['info']} 个")
        report.append(f"总计: {sum(severity_counts.values())} 个")
        
        # 项目分析信息
        if scan_result.project_info:
            report.append("\n项目分析:")
            report.append("-" * 80)
            
            project_info = scan_result.project_info
            if "project_type" in project_info:
                report.append(f"项目类型: {project_info['project_type']}")
                
            if "main_functionality" in project_info:
                report.append(f"主要功能: {project_info['main_functionality']}")
                
            if "components" in project_info:
                report.append("\n主要组件:")
                if isinstance(project_info["components"], list):
                    for comp in project_info["components"]:
                        report.append(f"  • {comp}")
                else:
                    report.append(f"  {project_info['components']}")
                    
            if "architecture" in project_info:
                report.append(f"\n架构概述: {project_info['architecture']}")
                
            if "use_cases" in project_info:
                report.append("\n使用场景:")
                if isinstance(project_info["use_cases"], list):
                    for case in project_info["use_cases"]:
                        report.append(f"  • {case}")
                else:
                    report.append(f"  {project_info['use_cases']}")
                    
            # 单文件扫描特有信息
            if scan_result.scan_type.lower() == "file" and "file_analysis" in project_info:
                file_analysis = project_info["file_analysis"]
                
                if "code_quality" in file_analysis:
                    report.append("\n代码质量评估:")
                    code_quality = file_analysis["code_quality"]
                    if isinstance(code_quality, dict):
                        for key, value in code_quality.items():
                            report.append(f"  {key}: {value}")
                    else:
                        report.append(f"  {code_quality}")
                        
                if "suggested_improvements" in file_analysis:
                    report.append("\n建议改进:")
                    improvements = file_analysis["suggested_improvements"]
                    if isinstance(improvements, list):
                        for imp in improvements:
                            report.append(f"  • {imp}")
                    else:
                        report.append(f"  {improvements}")
        
        # 详细漏洞信息
        if scan_result.issues:
            report.append("\n详细漏洞信息:")
            report.append("=" * 80)
            
            # 按严重程度排序漏洞
            severity_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
                "info": 4
            }
            
            sorted_issues = sorted(
                scan_result.issues, 
                key=lambda x: severity_order.get(x.severity, 5)
            )
            
            for i, issue in enumerate(sorted_issues, 1):
                report.append(f"\n[{i}] {issue.title}")
                report.append("-" * 80)
                
                if issue.severity:
                    report.append(f"严重程度: {issue.severity.capitalize()}")
                    
                if issue.confidence:
                    report.append(f"置信度: {issue.confidence.capitalize()}")
                    
                if issue.location:
                    report.append(f"位置: {issue.location}")
                    
                if issue.description:
                    report.append(f"\n问题描述:\n{issue.description}")
            
            if issue.cwe_id:
                    report.append(f"\nCWE ID: {issue.cwe_id}")
                    
            if issue.owasp_category:
                    report.append(f"OWASP类别: {issue.owasp_category}")
                    
            if issue.vulnerability_type:
                    report.append(f"漏洞类型: {issue.vulnerability_type}")
                    
            if issue.code_snippet:
                    report.append(f"\n代码片段:\n{issue.code_snippet}")
                
            if issue.recommendation:
                    report.append(f"\n修复建议:\n{issue.recommendation}")
        else:
            report.append("\n未发现漏洞。")
            
        return "\n".join(report)
            
def get_report_generator(format_type: str) -> ReportGenerator:
    """获取报告生成器
    
    Args:
        format_type: 报告格式类型(html, json, text)
        
    Returns:
        ReportGenerator: 对应格式的报告生成器
        
    Raises:
        ValueError: 不支持的报告格式
    """
    format_type = format_type.lower()
    
    if format_type == 'html':
        return HTMLReportGenerator() 
    elif format_type == 'json':
        return JSONReportGenerator()
    elif format_type == 'text':
        return TextReportGenerator()
    else:
        raise ValueError(f"不支持的报告格式: {format_type}") 