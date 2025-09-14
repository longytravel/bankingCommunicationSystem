"""
Sentiment Display Module - Clean Executive Dashboard
Shows banking sentiment intelligence with clear WHY explanations
Designed for stakeholder clarity and actionable insights
"""

import streamlit as st
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from .base_display import BaseChannelDisplay
import json

# Import sentiment types
try:
    from src.core.sentiment_analyzer import (
        SentimentAnalysisResult,
        SentimentCategory,
        ComplianceStatus,
        SentimentZone,
        ActionableInsight,
        QuickWin,
        SentimentScore,
        ComplianceCheck,
        CustomerImpact,
        LinguisticQuality
    )
    SENTIMENT_AVAILABLE = True
    print("✅ Sentiment display: All imports successful")
except ImportError as e:
    SENTIMENT_AVAILABLE = False
    print(f"⚠️ Sentiment analyzer types not available: {e}")
    import traceback
    traceback.print_exc()

class SentimentDisplay(BaseChannelDisplay):
    """Display handler for banking sentiment intelligence"""
    
    def __init__(self):
        super().__init__("Sentiment Analysis", "🎯")
        self.style = """
        <style>
        /* Clean, professional styling */
        .executive-summary {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 4px solid #006A4D;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        .score-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
        }
        
        .score-large {
            font-size: 3em;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .score-positive { color: #28a745; }
        .score-neutral { color: #ffc107; }
        .score-negative { color: #dc3545; }
        
        .why-box {
            background: #f8f9fa;
            border-left: 3px solid #17a2b8;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        }
        
        .why-text {
            color: #495057;
            font-style: italic;
            margin: 0;
        }
        
        .metric-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .metric-title {
            font-weight: bold;
            font-size: 1.1em;
            color: #212529;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .status-pass { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-fail { color: #dc3545; }
        
        .red-flag {
            background: #fff5f5;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .warning-flag {
            background: #fffbf0;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .opportunity {
            background: #f0f9ff;
            border-left: 4px solid #17a2b8;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .quick-win {
            background: #f0fff4;
            border: 1px solid #28a745;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .decision-box {
            background: white;
            border: 2px solid;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            margin: 2rem 0;
        }
        
        .ready-yes {
            border-color: #28a745;
            background: #f0fff4;
        }
        
        .ready-no {
            border-color: #dc3545;
            background: #fff5f5;
        }
        
        .evidence-list {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
        
        .evidence-item {
            padding: 0.25rem 0;
            color: #6c757d;
        }
        
        /* Traffic light indicators */
        .traffic-light {
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .light-green { background: #28a745; }
        .light-amber { background: #ffc107; }
        .light-red { background: #dc3545; }
        
        /* Simplified headers */
        h3 {
            color: #212529;
            font-size: 1.3em;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 0.5rem;
        }
        </style>
        """
    
    def display_sentiment_analysis(
        self,
        sentiment_result: 'SentimentAnalysisResult',
        refined_email: Any,
        shared_context: Any
    ) -> None:
        """Display banking sentiment intelligence with clear WHY explanations"""
        
        # DEBUG: Log what we're receiving
        print(f"DEBUG: display_sentiment_analysis called")
        print(f"  sentiment_result type: {type(sentiment_result)}")
        print(f"  sentiment_result is None: {sentiment_result is None}")
        print(f"  SENTIMENT_AVAILABLE: {SENTIMENT_AVAILABLE}")
        
        if sentiment_result:
            print(f"  sentiment_result.overall_score: {getattr(sentiment_result, 'overall_score', 'NO ATTR')}")
            print(f"  sentiment_result.ready_to_send: {getattr(sentiment_result, 'ready_to_send', 'NO ATTR')}")
        
        if not sentiment_result or not SENTIMENT_AVAILABLE:
            st.error("❌ No sentiment analysis available")
            if not sentiment_result:
                st.info("Debug: sentiment_result is None/False")
            if not SENTIMENT_AVAILABLE:
                st.info("Debug: SENTIMENT_AVAILABLE is False")
            return
        
        try:
            # Apply clean styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            # Executive Summary at the top
            self._display_executive_summary(sentiment_result)
            
            # Ready to Send Decision
            self._display_send_decision(sentiment_result)
            
            # Core Metrics Dashboard (4 cards)
            self._display_core_metrics(sentiment_result)
            
            # Critical Issues Section
            if sentiment_result.red_flags or sentiment_result.warnings:
                self._display_issues(sentiment_result)
            
            # Business Impact Predictions
            self._display_business_predictions(sentiment_result)
            
            # Quick Wins (if any)
            if sentiment_result.quick_wins:
                self._display_quick_wins(sentiment_result)
            
            # Detailed Analysis (expandable)
            with st.expander("📊 Detailed Analysis", expanded=False):
                self._display_detailed_analysis(sentiment_result)
            
            # Actions
            self._display_actions(sentiment_result, refined_email)
            
        except Exception as e:
            st.error(f"Error displaying sentiment analysis: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _display_executive_summary(self, result: 'SentimentAnalysisResult') -> None:
        """Display executive summary with the main WHY"""
        st.markdown(f'''
        <div class="executive-summary">
            <h2 style="margin-top: 0; color: #006A4D;">Banking Sentiment Intelligence Report</h2>
            <p style="font-size: 1.2em; margin: 1rem 0;">
                {result.executive_summary}
            </p>
            <p style="color: #6c757d; margin: 0;">
                Analysis completed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_send_decision(self, result: 'SentimentAnalysisResult') -> None:
        """Display clear ready to send decision"""
        if result.ready_to_send:
            st.markdown('''
            <div class="decision-box ready-yes">
                <span class="traffic-light light-green"></span>
                <span style="font-size: 1.5em; font-weight: bold; color: #28a745;">
                    ✅ READY TO SEND
                </span>
                <p style="margin: 0.5rem 0 0 0; color: #495057;">
                    No critical issues detected. Communication meets quality standards.
                </p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            issues_count = len(result.red_flags)
            st.markdown(f'''
            <div class="decision-box ready-no">
                <span class="traffic-light light-red"></span>
                <span style="font-size: 1.5em; font-weight: bold; color: #dc3545;">
                    ⚠️ NOT READY - {issues_count} ISSUE{'S' if issues_count != 1 else ''} TO FIX
                </span>
                <p style="margin: 0.5rem 0 0 0; color: #495057;">
                    Critical issues must be addressed before sending.
                </p>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_core_metrics(self, result: 'SentimentAnalysisResult') -> None:
        """Display 4 core metrics with WHY explanations"""
        st.markdown("### 📊 Core Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # 1. Sentiment Score
        with col1:
            score = result.sentiment_score.score
            if score >= 30:
                color_class = "score-positive"
                icon = "😊"
            elif score >= -30:
                color_class = "score-neutral"
                icon = "😐"
            else:
                color_class = "score-negative"
                icon = "😟"
            
            st.markdown(f'''
            <div class="score-card">
                <div class="metric-title">Sentiment Score</div>
                <div class="score-large {color_class}">{score}</div>
                <div style="font-size: 2em;">{icon}</div>
                <div class="why-box">
                    <p class="why-text">WHY: {result.sentiment_score.why}</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 2. Compliance Check
        with col2:
            status = result.compliance_check.status
            if status == ComplianceStatus.PASS:
                status_color = "status-pass"
                status_text = "✅ PASS"
            elif status == ComplianceStatus.WARNING:
                status_color = "status-warning"
                status_text = "⚠️ WARNING"
            else:
                status_color = "status-fail"
                status_text = "❌ FAIL"
            
            st.markdown(f'''
            <div class="score-card">
                <div class="metric-title">Compliance</div>
                <div class="score-large {status_color}">{result.compliance_check.tcf_score}</div>
                <div style="font-size: 1.2em; margin: 0.5rem 0;">{status_text}</div>
                <div class="why-box">
                    <p class="why-text">WHY: {result.compliance_check.why}</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 3. Complaint Risk
        with col3:
            risk = result.customer_impact.complaint_probability
            if risk < 30:
                risk_color = "score-positive"
                risk_level = "Low"
            elif risk < 60:
                risk_color = "score-neutral"
                risk_level = "Medium"
            else:
                risk_color = "score-negative"
                risk_level = "High"
            
            st.markdown(f'''
            <div class="score-card">
                <div class="metric-title">Complaint Risk</div>
                <div class="score-large {risk_color}">{risk:.0f}%</div>
                <div style="font-size: 1.2em;">{risk_level} Risk</div>
                <div class="why-box">
                    <p class="why-text">WHY: {result.customer_impact.why}</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 4. Readability
        with col4:
            readability = result.linguistic_quality.readability_score
            grade = result.linguistic_quality.grade_level
            if readability >= 60:
                read_color = "score-positive"
                read_level = "Easy"
            elif readability >= 30:
                read_color = "score-neutral"
                read_level = "Moderate"
            else:
                read_color = "score-negative"
                read_level = "Difficult"
            
            st.markdown(f'''
            <div class="score-card">
                <div class="metric-title">Readability</div>
                <div class="score-large {read_color}">{readability}</div>
                <div style="font-size: 1.2em;">Grade {grade:.0f}</div>
                <div class="why-box">
                    <p class="why-text">WHY: {result.linguistic_quality.why}</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_issues(self, result: 'SentimentAnalysisResult') -> None:
        """Display issues that need attention"""
        st.markdown("### ⚠️ Issues to Address")
        
        # Red Flags (Must Fix)
        if result.red_flags:
            for flag in result.red_flags:
                st.markdown(f'''
                <div class="red-flag">
                    <strong>🔴 CRITICAL: {flag.issue}</strong><br>
                    <span style="color: #dc3545;">Impact:</span> {flag.impact}<br>
                    <span style="color: #28a745;">Fix:</span> {flag.fix}
                    {f'<br><span style="color: #17a2b8;">Example:</span> <em>"{flag.example}"</em>' if flag.example else ''}
                </div>
                ''', unsafe_allow_html=True)
        
        # Warnings (Should Fix)
        if result.warnings:
            for warning in result.warnings[:3]:  # Show top 3
                st.markdown(f'''
                <div class="warning-flag">
                    <strong>🟡 WARNING: {warning.issue}</strong><br>
                    <span style="color: #ffc107;">Impact:</span> {warning.impact}<br>
                    <span style="color: #28a745;">Suggestion:</span> {warning.fix}
                </div>
                ''', unsafe_allow_html=True)
    
    def _display_business_predictions(self, result: 'SentimentAnalysisResult') -> None:
        """Display predicted business outcomes"""
        st.markdown("### 📈 Predicted Business Impact")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            complaint_icon = "🚨" if result.will_cause_complaint else "✅"
            complaint_text = "Likely" if result.will_cause_complaint else "Unlikely"
            complaint_color = "#dc3545" if result.will_cause_complaint else "#28a745"
            
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Customer Complaint</span>
                    <span style="font-size: 2em;">{complaint_icon}</span>
                </div>
                <div class="metric-value" style="color: {complaint_color};">{complaint_text}</div>
                <div class="why-box">
                    <p class="why-text">Based on: {result.customer_impact.complaint_probability:.0f}% probability</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            call_icon = "📞" if result.will_cause_call else "✅"
            call_text = "Likely" if result.will_cause_call else "Unlikely"
            call_color = "#dc3545" if result.will_cause_call else "#28a745"
            
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Call Center Contact</span>
                    <span style="font-size: 2em;">{call_icon}</span>
                </div>
                <div class="metric-value" style="color: {call_color};">{call_text}</div>
                <div class="why-box">
                    <p class="why-text">Based on: {result.customer_impact.call_probability:.0f}% probability</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            nps = result.customer_impact.nps_impact
            if nps > 0:
                nps_icon = "📈"
                nps_text = f"+{nps} points"
                nps_color = "#28a745"
            elif nps < 0:
                nps_icon = "📉"
                nps_text = f"{nps} points"
                nps_color = "#dc3545"
            else:
                nps_icon = "➡️"
                nps_text = "No change"
                nps_color = "#6c757d"
            
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">NPS Impact</span>
                    <span style="font-size: 2em;">{nps_icon}</span>
                </div>
                <div class="metric-value" style="color: {nps_color};">{nps_text}</div>
                <div class="why-box">
                    <p class="why-text">{result.nps_impact_prediction.title()} impact expected</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_quick_wins(self, result: 'SentimentAnalysisResult') -> None:
        """Display quick improvements"""
        st.markdown("### ⚡ Quick Wins")
        st.markdown("Simple changes that will improve the communication:")
        
        for win in result.quick_wins[:3]:
            if isinstance(win, QuickWin):
                st.markdown(f'''
                <div class="quick-win">
                    <strong>Improvement Opportunity:</strong><br>
                    ❌ Current: <em>"{win.original}"</em><br>
                    ✅ Better: <em>"{win.improved}"</em><br>
                    <span style="color: #17a2b8;">WHY:</span> {win.why}<br>
                    <span style="color: #28a745;">Impact:</span> {win.impact}
                </div>
                ''', unsafe_allow_html=True)
            else:
                # Handle string quick wins from older format
                st.markdown(f'''
                <div class="quick-win">
                    ✨ {win}
                </div>
                ''', unsafe_allow_html=True)
    
    def _display_detailed_analysis(self, result: 'SentimentAnalysisResult') -> None:
        """Display detailed analysis for those who want more"""
        
        # Scoring Rationale
        st.markdown("#### 📋 Detailed Scoring Rationale")
        for category, rationale in result.scoring_rationale.items():
            st.markdown(f"**{category.title()}:** {rationale}")
        
        # Key Evidence
        if result.key_evidence:
            st.markdown("#### 🔍 Key Evidence")
            st.markdown('<div class="evidence-list">', unsafe_allow_html=True)
            for evidence in result.key_evidence:
                st.markdown(f'<div class="evidence-item">• {evidence}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Comparison to Best Practice
        if result.comparison_to_best_practice:
            st.markdown("#### 🎯 Comparison to Best Practice")
            st.info(result.comparison_to_best_practice)
        
        # Risk and Success Factors
        col1, col2 = st.columns(2)
        
        with col1:
            if result.customer_impact.risk_factors:
                st.markdown("#### ⚠️ Risk Factors")
                for risk in result.customer_impact.risk_factors:
                    st.write(f"• {risk}")
        
        with col2:
            if result.customer_impact.success_factors:
                st.markdown("#### ✅ Success Factors")
                for success in result.customer_impact.success_factors:
                    st.write(f"• {success}")
        
        # Compliance Details
        if result.compliance_check.issues:
            st.markdown("#### 🏛️ Compliance Issues")
            for issue, fix in zip(result.compliance_check.issues, result.compliance_check.fixes):
                st.warning(f"**Issue:** {issue}\n\n**Fix:** {fix}")
    
    def _display_actions(self, result: 'SentimentAnalysisResult', refined_email: Any) -> None:
        """Display action buttons"""
        st.markdown("---")
        st.markdown("### 🚀 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if not result.ready_to_send:
                if st.button("🔧 Auto-Fix Issues", type="primary", use_container_width=True):
                    st.info("Auto-fix would apply all suggested improvements")
        
        with col2:
            if st.button("📊 Export Report", use_container_width=True):
                report = self._create_executive_report(result)
                st.download_button(
                    "Download Report",
                    report,
                    file_name=f"sentiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if result.customer_impact.complaint_probability > 50:
                if st.button("⚠️ Flag for Review", use_container_width=True):
                    st.warning("Flagged for senior review before sending")
        
        with col4:
            button_text = "✅ Accept & Send" if result.ready_to_send else "⚠️ Send Anyway"
            button_type = "primary" if result.ready_to_send else "secondary"
            if st.button(button_text, type=button_type, use_container_width=True):
                if result.ready_to_send:
                    st.success("Communication approved for sending")
                else:
                    st.error("Sending despite issues - logged for compliance")
    
    def _create_executive_report(self, result: 'SentimentAnalysisResult') -> str:
        """Create executive-friendly report"""
        
        report = {
            'executive_summary': result.executive_summary,
            'ready_to_send': result.ready_to_send,
            'overall_score': result.overall_score,
            'timestamp': result.analysis_timestamp,
            
            'core_metrics': {
                'sentiment_score': {
                    'value': result.sentiment_score.score,
                    'category': result.sentiment_score.category.value,
                    'why': result.sentiment_score.why
                },
                'compliance': {
                    'status': result.compliance_check.status.value,
                    'tcf_score': result.compliance_check.tcf_score,
                    'why': result.compliance_check.why
                },
                'complaint_risk': {
                    'probability': result.customer_impact.complaint_probability,
                    'why': result.customer_impact.why
                },
                'readability': {
                    'score': result.linguistic_quality.readability_score,
                    'grade_level': result.linguistic_quality.grade_level,
                    'why': result.linguistic_quality.why
                }
            },
            
            'predictions': {
                'will_cause_complaint': result.will_cause_complaint,
                'will_cause_call': result.will_cause_call,
                'nps_impact': result.customer_impact.nps_impact
            },
            
            'issues': {
                'red_flags': [
                    {
                        'issue': flag.issue,
                        'impact': flag.impact,
                        'fix': flag.fix
                    }
                    for flag in result.red_flags
                ],
                'warnings': [
                    {
                        'issue': warning.issue,
                        'impact': warning.impact,
                        'fix': warning.fix
                    }
                    for warning in result.warnings[:5]
                ]
            },
            
            'quick_wins': [
                {
                    'original': win.original,
                    'improved': win.improved,
                    'why': win.why
                } if isinstance(win, QuickWin) else str(win)
                for win in result.quick_wins[:5]
            ]
        }
        
        return json.dumps(report, indent=2)
    
    # Required base class methods (keep for compatibility)
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Required by base class"""
        pass
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate sentiment analysis result"""
        validation = {
            'is_valid': True,
            'issues': [],
            'achievements': [],
            'metrics': {}
        }
        
        if hasattr(result, 'ready_to_send'):
            if result.ready_to_send:
                validation['achievements'].append("Communication ready to send")
            else:
                validation['issues'].append(f"{len(result.red_flags)} critical issues to fix")
                validation['is_valid'] = False
        
        if hasattr(result, 'customer_impact'):
            validation['metrics']['complaint_risk'] = f"{result.customer_impact.complaint_probability:.0f}%"
            validation['metrics']['call_risk'] = f"{result.customer_impact.call_probability:.0f}%"
            
            if result.customer_impact.complaint_probability < 30:
                validation['achievements'].append("Low complaint risk")
            elif result.customer_impact.complaint_probability > 60:
                validation['issues'].append("High complaint risk")
        
        return validation
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for sentiment analysis"""
        
        if not hasattr(result, 'analysis_timestamp'):
            return "", "", ""
        
        report = self._create_executive_report(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sentiment_report_{customer_name}_{timestamp}.json"
        
        return report, filename, "application/json"

# Convenience function for standalone display
def display_sentiment_analysis(
    sentiment_result: Any,
    refined_email: Any = None,
    shared_context: Any = None
):
    """Display sentiment analysis results"""
    display = SentimentDisplay()
    display.display_sentiment_analysis(sentiment_result, refined_email, shared_context)