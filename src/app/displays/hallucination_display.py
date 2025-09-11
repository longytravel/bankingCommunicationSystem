"""
Hallucination Display Module - Visualizes hallucination detection results
Shows findings, risk scores, and recommendations in the Streamlit UI
"""

import streamlit as st
from typing import Any, Dict, Tuple, List, Optional
from datetime import datetime
import json
import html

# Import base display if available
try:
    from .base_display import BaseChannelDisplay
except ImportError:
    # Create a minimal base class if not available
    class BaseChannelDisplay:
        def __init__(self, channel_name: str, icon: str):
            self.channel_name = channel_name
            self.icon = icon

# Import hallucination types
try:
    from src.core.hallucination_detector import (
        HallucinationReport,
        HallucinationFinding,
        HallucinationCategory,
        SeverityLevel
    )
    HALLUCINATION_TYPES_AVAILABLE = True
except ImportError:
    HALLUCINATION_TYPES_AVAILABLE = False
    print("⚠️ Hallucination types not available")

class HallucinationDisplay(BaseChannelDisplay):
    """Display handler for hallucination detection results"""
    
    def __init__(self):
        super().__init__("Hallucination Check", "🚨")
        self.style = """
        <style>
        .hallucination-header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .risk-gauge {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
        }
        
        .risk-meter {
            width: 100%;
            height: 30px;
            background: linear-gradient(to right, #4CAF50 0%, #FFC107 50%, #FF5252 100%);
            border-radius: 15px;
            position: relative;
            margin: 1rem 0;
        }
        
        .risk-indicator {
            position: absolute;
            top: -10px;
            width: 50px;
            height: 50px;
            background: white;
            border: 3px solid #333;
            border-radius: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        .finding-card {
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 5px solid;
        }
        
        .finding-high {
            background: #ffebee;
            border-left-color: #f44336;
        }
        
        .finding-medium {
            background: #fff3e0;
            border-left-color: #ff9800;
        }
        
        .finding-low {
            background: #fff8e1;
            border-left-color: #ffc107;
        }
        
        .hallucinated-text {
            background: #ffcccc;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .suggested-fix {
            background: #c8e6c9;
            padding: 2px 6px;
            border-radius: 4px;
            font-style: italic;
        }
        
        .context-box {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 5px;
            margin: 0.5rem 0;
            font-family: monospace;
            font-size: 0.9em;
            border: 1px solid #ddd;
        }
        
        .recommendation-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        }
        
        .summary-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .stat-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        </style>
        """
    
    def display_result(self, report: Any, shared_context: Any = None) -> None:
        """Main display method for hallucination report"""
        
        if not report or not HALLUCINATION_TYPES_AVAILABLE:
            st.error("❌ No hallucination report available or types not imported")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            # Header
            self._display_header(report)
            
            # Risk gauge
            self._display_risk_gauge(report)
            
            # Summary statistics
            self._display_statistics(report)
            
            # Executive summary
            self._display_summary(report)
            
            # Findings by channel
            self._display_findings_by_channel(report)
            
            # Recommendations
            self._display_recommendations(report)
            
            # Technical details
            self._display_technical_details(report)
            
        except Exception as e:
            st.error(f"Error displaying hallucination report: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _display_header(self, report: Any) -> None:
        """Display the header section"""
        st.markdown(f'''
        <div class="hallucination-header">
            <h2>{self.icon} Hallucination Detection Report</h2>
            <p>AI-powered analysis of fabricated content in generated communications</p>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_risk_gauge(self, report: Any) -> None:
        """Display visual risk gauge"""
        risk_score = report.risk_score if hasattr(report, 'risk_score') else 0
        risk_percentage = risk_score * 100
        
        # Determine risk level and color
        if risk_score > 0.7:
            risk_level = "HIGH RISK"
            color = "#FF5252"
        elif risk_score > 0.4:
            risk_level = "MEDIUM RISK"
            color = "#FFC107"
        else:
            risk_level = "LOW RISK"
            color = "#4CAF50"
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f'''
            <div class="risk-gauge">
                <h3>Overall Risk Assessment</h3>
                <div class="risk-meter">
                    <div class="risk-indicator" style="left: {risk_percentage}%;">
                        {risk_percentage:.0f}%
                    </div>
                </div>
                <h2 style="color: {color}; margin-top: 2rem;">{risk_level}</h2>
                <p>{report.summary if hasattr(report, 'summary') else 'No summary available'}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_statistics(self, report: Any) -> None:
        """Display statistics grid"""
        total = report.total_hallucinations if hasattr(report, 'total_hallucinations') else 0
        findings = report.findings if hasattr(report, 'findings') else []
        
        # Count by severity
        high_count = len([f for f in findings if f.severity == SeverityLevel.HIGH])
        medium_count = len([f for f in findings if f.severity == SeverityLevel.MEDIUM])
        low_count = len([f for f in findings if f.severity == SeverityLevel.LOW])
        
        # Count by category
        categories = {}
        for finding in findings:
            cat = finding.category.value if hasattr(finding.category, 'value') else str(finding.category)
            categories[cat] = categories.get(cat, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Findings", total)
        with col2:
            st.metric("High Severity", high_count, delta_color="inverse")
        with col3:
            st.metric("Medium Severity", medium_count, delta_color="inverse")
        with col4:
            st.metric("Low Severity", low_count, delta_color="normal")
        
        # Category breakdown
        if categories:
            st.markdown("### 📊 Findings by Category")
            cat_cols = st.columns(min(len(categories), 4))
            for i, (cat, count) in enumerate(categories.items()):
                with cat_cols[i % len(cat_cols)]:
                    st.metric(cat.replace('_', ' ').title(), count)
    
    def _display_summary(self, report: Any) -> None:
        """Display executive summary"""
        if hasattr(report, 'summary') and report.summary:
            st.markdown(f'''
            <div class="summary-box">
                <h3>📋 Executive Summary</h3>
                <p>{report.summary}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_findings_by_channel(self, report: Any) -> None:
        """Display findings organized by channel"""
        if not hasattr(report, 'findings') or not report.findings:
            st.success("✅ No hallucinations detected!")
            return
        
        st.markdown("### 🔍 Detailed Findings")
        
        # Group findings by channel
        channels = {}
        for finding in report.findings:
            channel = finding.channel if hasattr(finding, 'channel') else 'unknown'
            if channel not in channels:
                channels[channel] = []
            channels[channel].append(finding)
        
        # Create tabs for each channel
        if channels:
            tabs = st.tabs([f"{ch.upper()} ({len(findings)})" for ch, findings in channels.items()])
            
            for tab, (channel, findings) in zip(tabs, channels.items()):
                with tab:
                    self._display_channel_findings(channel, findings)
    
    def _display_channel_findings(self, channel: str, findings: List[Any]) -> None:
        """Display findings for a specific channel"""
        
        # Sort by severity
        findings_sorted = sorted(findings, 
                                key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(
                                    x.severity.value if hasattr(x.severity, 'value') else str(x.severity), 3))
        
        for i, finding in enumerate(findings_sorted, 1):
            self._display_single_finding(finding, i)
    
    def _display_single_finding(self, finding: Any, index: int) -> None:
        """Display a single hallucination finding"""
        
        # Determine severity class
        severity = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
        severity_class = f"finding-{severity}"
        
        # Get category
        category = finding.category.value if hasattr(finding.category, 'value') else str(finding.category)
        
        # Escape HTML in text
        hallucinated_text = html.escape(finding.text if hasattr(finding, 'text') else '')
        context = html.escape(finding.context if hasattr(finding, 'context') else '')
        explanation = finding.explanation if hasattr(finding, 'explanation') else ''
        suggested_fix = finding.suggested_fix if hasattr(finding, 'suggested_fix') else ''
        confidence = finding.confidence if hasattr(finding, 'confidence') else 0
        
        st.markdown(f'''
        <div class="finding-card {severity_class}">
            <h4>Finding #{index}: {category.replace('_', ' ').title()}</h4>
            <p><strong>Severity:</strong> <span style="color: {"#f44336" if severity == "high" else "#ff9800" if severity == "medium" else "#ffc107"};">{severity.upper()}</span></p>
            <p><strong>Confidence:</strong> {confidence:.0%}</p>
            <p><strong>Hallucinated Text:</strong> <span class="hallucinated-text">{hallucinated_text}</span></p>
            <div class="context-box">
                <strong>Context:</strong><br>
                ...{context}...
            </div>
            <p><strong>Why this is a hallucination:</strong> {explanation}</p>
            <p><strong>Suggested Fix:</strong> <span class="suggested-fix">{suggested_fix}</span></p>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_recommendations(self, report: Any) -> None:
        """Display recommendations"""
        if hasattr(report, 'recommendations') and report.recommendations:
            st.markdown("### 💡 Recommendations")
            
            for rec in report.recommendations:
                st.markdown(f'''
                <div class="recommendation-box">
                    ✅ {rec}
                </div>
                ''', unsafe_allow_html=True)
    
    def _display_technical_details(self, report: Any) -> None:
        """Display technical details"""
        with st.expander("🔧 Technical Details", expanded=False):
            details = {
                "Model Used": report.model_used if hasattr(report, 'model_used') else 'Unknown',
                "Processing Time": f"{report.processing_time:.2f}s" if hasattr(report, 'processing_time') else 'N/A',
                "Analysis Confidence": f"{report.analysis_confidence:.0%}" if hasattr(report, 'analysis_confidence') else 'N/A',
                "Channels Analyzed": report.channels_analyzed if hasattr(report, 'channels_analyzed') else [],
                "Total Findings": report.total_hallucinations if hasattr(report, 'total_hallucinations') else 0,
                "Risk Score": f"{report.risk_score:.2%}" if hasattr(report, 'risk_score') else 'N/A'
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                for key in list(details.keys())[:3]:
                    st.write(f"**{key}:** {details[key]}")
            
            with col2:
                for key in list(details.keys())[3:]:
                    value = details[key]
                    if isinstance(value, list):
                        value = ', '.join(value)
                    st.write(f"**{key}:** {value}")
    
    def validate_result(self, report: Any, shared_context: Any = None) -> Dict[str, Any]:
        """Validate the hallucination report"""
        validation = {
            'is_valid': True,
            'quality_score': 1.0 - (report.risk_score if hasattr(report, 'risk_score') else 0),
            'issues': [],
            'achievements': [],
            'metrics': {}
        }
        
        if hasattr(report, 'total_hallucinations'):
            validation['metrics']['total_findings'] = report.total_hallucinations
            
            if report.total_hallucinations == 0:
                validation['achievements'].append("No hallucinations detected")
            else:
                validation['issues'].append(f"{report.total_hallucinations} hallucinations found")
        
        if hasattr(report, 'risk_score'):
            validation['metrics']['risk_score'] = report.risk_score
            
            if report.risk_score > 0.7:
                validation['issues'].append("High risk level - immediate attention required")
            elif report.risk_score < 0.3:
                validation['achievements'].append("Low risk level")
        
        return validation
    
    def get_download_data(self, report: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for the report"""
        
        if not report:
            return "", "", ""
        
        # Convert report to JSON
        try:
            report_dict = report.to_dict() if hasattr(report, 'to_dict') else {
                'summary': report.summary if hasattr(report, 'summary') else '',
                'total_hallucinations': report.total_hallucinations if hasattr(report, 'total_hallucinations') else 0,
                'risk_score': report.risk_score if hasattr(report, 'risk_score') else 0
            }
            
            report_json = json.dumps(report_dict, indent=2)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"hallucination_report_{customer_name}_{timestamp}.json"
            
            return report_json, filename, "application/json"
            
        except Exception as e:
            st.error(f"Error preparing download: {e}")
            return "", "", ""

# Convenience function for standalone display
def display_hallucination_report(report: Any, shared_context: Any = None):
    """Display a hallucination report"""
    display = HallucinationDisplay()
    display.display_result(report, shared_context)