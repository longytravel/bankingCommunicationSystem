"""
Banking Sentiment Display - Shows ALL the WHY explanations
Built for banking teams who need to understand every decision
"""

import streamlit as st
import json
from typing import Dict, Any
from datetime import datetime

class BankingSentimentDisplay:
    """Display banking sentiment with full explanations"""
    
    def __init__(self):
        self.style = """
        <style>
        .sentiment-header {
            background: linear-gradient(135deg, #006A4D 0%, #00A651 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
        }
        
        .decision-box {
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
        }
        
        .ready-yes {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            border: 3px solid #28a745;
        }
        
        .ready-no {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
            border: 3px solid #dc3545;
        }
        
        .metric-card {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .metric-score {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin: 0.5rem 0;
        }
        
        .metric-why {
            background: #f8f9fa;
            border-left: 4px solid #006A4D;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 0 5px 5px 0;
        }
        
        .positive { color: #28a745; }
        .neutral { color: #ffc107; }
        .negative { color: #dc3545; }
        
        .red-flag {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 2px solid #dc3545;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .warning-box {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .strength-box {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border: 2px solid #17a2b8;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .quick-win {
            background: #e7f3ff;
            border: 2px solid #0066cc;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .why-explanation {
            font-style: italic;
            color: #495057;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(255,255,255,0.5);
            border-radius: 5px;
        }
        </style>
        """
    
    def display(self, result: Dict[str, Any], email_content: str = None) -> None:
        """Display comprehensive banking sentiment analysis"""
        
        if not result:
            st.error("❌ No sentiment analysis results available")
            return
        
        # Apply styling
        st.markdown(self.style, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="sentiment-header">
            <h2>🎯 Banking Sentiment Analysis</h2>
            <p>Comprehensive compliance & customer impact assessment</p>
        </div>
        """, unsafe_allow_html=True)
        
        # DECISION BOX - Most important thing first
        ready = result.get('ready_to_send', False)
        if ready:
            st.markdown("""
            <div class="decision-box ready-yes">
                ✅ READY TO SEND - All checks passed
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="decision-box ready-no">
                ⚠️ NOT READY - Critical issues found
            </div>
            """, unsafe_allow_html=True)
        
        # Executive Summary
        st.markdown("### 📊 Executive Summary")
        st.info(result.get('executive_summary', 'No summary available'))
        
        # Decision Rationale
        if 'decision_rationale' in result:
            rationale = result['decision_rationale']
            with st.expander("🤔 **WHY THIS DECISION?**", expanded=True):
                st.markdown("**Primary Factors:**")
                for factor in rationale.get('primary_factors', []):
                    st.write(f"• {factor}")
                
                st.markdown("**Risk Assessment:**")
                st.write(rationale.get('risk_assessment', 'No assessment'))
                
                st.markdown("**Recommendation:**")
                st.success(rationale.get('recommendation', 'No recommendation'))
        
        # Main Metrics Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎭 Sentiment & Tone",
            "⚖️ Compliance",
            "📈 Customer Impact",
            "💰 Commercial",
            "⚠️ Issues & Fixes"
        ])
        
        with tab1:
            self._display_sentiment_metrics(result)
        
        with tab2:
            self._display_compliance_metrics(result)
        
        with tab3:
            self._display_customer_impact(result)
        
        with tab4:
            self._display_commercial_metrics(result)
        
        with tab5:
            self._display_issues_and_fixes(result)
        
        # Raw JSON for debugging
        with st.expander("🔍 Full Analysis Data"):
            st.json(result)
    
    def _display_sentiment_metrics(self, result: Dict[str, Any]) -> None:
        """Display sentiment and emotional tone with WHY explanations"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment Score
            sentiment = result.get('sentiment', {})
            score = sentiment.get('score', 0)
            category = sentiment.get('category', 'neutral')
            
            color = 'positive' if score > 30 else 'negative' if score < -30 else 'neutral'
            emoji = '😊' if score > 30 else '😟' if score < -30 else '😐'
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>Overall Sentiment</h4>
                <div class="metric-score {color}">{score} {emoji}</div>
                <p style="text-align: center;">{category.upper()}</p>
                <div class="metric-why">
                    <strong>WHY this score:</strong><br>
                    {sentiment.get('why', 'No explanation provided')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Emotional Tone
            emotional = result.get('emotional_tone', {})
            warmth = emotional.get('warmth_score', 50)
            primary = emotional.get('primary_emotion', 'unknown')
            
            color = 'positive' if warmth > 70 else 'negative' if warmth < 30 else 'neutral'
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>Emotional Tone</h4>
                <div class="metric-score {color}">{warmth}/100</div>
                <p style="text-align: center;">Primary: {primary.upper()}</p>
                <div class="metric-why">
                    <strong>WHY this assessment:</strong><br>
                    {emotional.get('why', 'No explanation provided')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Readability
        readability = result.get('readability', {})
        st.markdown(f"""
        <div class="metric-card">
            <h4>Readability Analysis</h4>
            <p><strong>Score:</strong> {readability.get('score', 0)}/100</p>
            <p><strong>Grade Level:</strong> {readability.get('grade_level', 'Unknown')}</p>
            <p><strong>Complexity:</strong> {readability.get('complexity', 'Unknown')}</p>
            <div class="metric-why">
                <strong>WHY this score:</strong><br>
                {readability.get('why', 'No explanation provided')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_compliance_metrics(self, result: Dict[str, Any]) -> None:
        """Display compliance metrics with explanations"""
        
        compliance = result.get('compliance', {})
        regulatory = result.get('regulatory_flags', {})
        
        # Overall Compliance
        status = compliance.get('status', 'unknown')
        score = compliance.get('score', 0)
        tcf = compliance.get('tcf_compliant', False)
        
        status_color = 'positive' if status == 'pass' else 'negative' if status == 'fail' else 'neutral'
        status_emoji = '✅' if status == 'pass' else '❌' if status == 'fail' else '⚠️'
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>Compliance Status</h4>
            <div class="metric-score {status_color}">{score}/100 {status_emoji}</div>
            <p style="text-align: center;">Status: {status.upper()}</p>
            <p style="text-align: center;">TCF Compliant: {'✅ Yes' if tcf else '❌ No'}</p>
            <div class="metric-why">
                <strong>WHY this assessment:</strong><br>
                {compliance.get('why', 'No explanation provided')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Regulatory Flags
        col1, col2, col3 = st.columns(3)
        
        with col1:
            disclosures = regulatory.get('has_required_disclosures', False)
            st.metric(
                "Required Disclosures",
                "✅ Present" if disclosures else "❌ Missing"
            )
        
        with col2:
            vulnerable = regulatory.get('vulnerable_customer_appropriate', False)
            st.metric(
                "Vulnerable Customer Ready",
                "✅ Yes" if vulnerable else "❌ No"
            )
        
        with col3:
            promotion = regulatory.get('financial_promotion_compliant', False)
            st.metric(
                "Financial Promotion",
                "✅ Compliant" if promotion else "❌ Issues"
            )
        
        # Regulatory explanation
        if 'why' in regulatory:
            st.markdown(f"""
            <div class="metric-why">
                <strong>Regulatory Assessment Reasoning:</strong><br>
                {regulatory['why']}
            </div>
            """, unsafe_allow_html=True)
    
    def _display_customer_impact(self, result: Dict[str, Any]) -> None:
        """Display customer impact predictions with explanations"""
        
        impact = result.get('customer_impact', {})
        nps = result.get('nps_impact', {})
        
        # Risk Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            complaint_risk = impact.get('complaint_risk', 0)
            color = 'negative' if complaint_risk > 60 else 'positive' if complaint_risk < 30 else 'neutral'
            st.markdown(f"""
            <div class="metric-card">
                <h5>Complaint Risk</h5>
                <div class="metric-score {color}">{complaint_risk}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            call_risk = impact.get('call_risk', 0)
            color = 'negative' if call_risk > 60 else 'positive' if call_risk < 30 else 'neutral'
            st.markdown(f"""
            <div class="metric-card">
                <h5>Call Risk</h5>
                <div class="metric-score {color}">{call_risk}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            escalation_risk = impact.get('escalation_risk', 0)
            color = 'negative' if escalation_risk > 60 else 'positive' if escalation_risk < 30 else 'neutral'
            st.markdown(f"""
            <div class="metric-card">
                <h5>Escalation Risk</h5>
                <div class="metric-score {color}">{escalation_risk}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Impact explanation
        st.markdown(f"""
        <div class="metric-why">
            <strong>WHY these risk predictions:</strong><br>
            {impact.get('why', 'No explanation provided')}
        </div>
        """, unsafe_allow_html=True)
        
        # NPS Impact
        nps_impact = nps.get('predicted_impact', 0)
        promoter_risk = nps.get('current_promoter_risk', 'unknown')
        
        color = 'positive' if nps_impact > 0 else 'negative' if nps_impact < 0 else 'neutral'
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>NPS Impact Prediction</h4>
            <div class="metric-score {color}">{'+' if nps_impact > 0 else ''}{nps_impact}</div>
            <p style="text-align: center;">Promoter Risk: {promoter_risk.upper()}</p>
            <div class="metric-why">
                <strong>WHY this NPS prediction:</strong><br>
                {nps.get('why', 'No explanation provided')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_commercial_metrics(self, result: Dict[str, Any]) -> None:
        """Display commercial opportunity metrics"""
        
        upsell = result.get('upsell_opportunity', {})
        
        score = upsell.get('score', 0)
        receptiveness = upsell.get('receptiveness_prediction', 'unknown')
        
        color = 'positive' if score > 70 else 'negative' if score < 30 else 'neutral'
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>Upsell Opportunity</h4>
            <div class="metric-score {color}">{score}/100</div>
            <p style="text-align: center;">Customer Receptiveness: {receptiveness.upper()}</p>
            <div class="metric-why">
                <strong>WHY this commercial assessment:</strong><br>
                {upsell.get('why', 'No explanation provided')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_issues_and_fixes(self, result: Dict[str, Any]) -> None:
        """Display all issues, warnings, and improvements"""
        
        # Red Flags
        red_flags = result.get('red_flags', [])
        if red_flags:
            st.markdown("### 🚨 Critical Issues")
            for flag in red_flags:
                st.markdown(f"""
                <div class="red-flag">
                    <strong>{flag.get('severity', 'HIGH').upper()}: {flag.get('issue', '')}</strong><br>
                    <em>Impact:</em> {flag.get('impact', '')}<br>
                    <em>Fix:</em> {flag.get('fix', '')}<br>
                    <div class="why-explanation">
                        <strong>Why flagged:</strong> {flag.get('why_flagged', 'No reason provided')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Warnings
        warnings = result.get('warnings', [])
        if warnings:
            st.markdown("### ⚠️ Warnings")
            for warning in warnings:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>{warning.get('issue', '')}</strong><br>
                    <em>Impact:</em> {warning.get('impact', '')}<br>
                    <em>Suggestion:</em> {warning.get('fix', '')}<br>
                    <div class="why-explanation">
                        <strong>Why warning:</strong> {warning.get('why_warning', 'No reason provided')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Strengths
        strengths = result.get('strengths', [])
        if strengths:
            st.markdown("### ✅ What's Working Well")
            for strength in strengths:
                st.markdown(f"""
                <div class="strength-box">
                    <strong>{strength.get('element', '')}</strong><br>
                    <div class="why-explanation">
                        <strong>Why good:</strong> {strength.get('why_good', 'No reason provided')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Quick Wins
        quick_wins = result.get('quick_wins', [])
        if quick_wins:
            st.markdown("### ⚡ Quick Improvements")
            for win in quick_wins:
                st.markdown(f"""
                <div class="quick-win">
                    <strong>Current:</strong> "{win.get('original', '')}"<br>
                    <strong>Better:</strong> "{win.get('improved', '')}"<br>
                    <div class="why-explanation">
                        <strong>Why better:</strong> {win.get('why', 'No reason provided')}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def display_banking_sentiment(result: Dict[str, Any], email_content: str = None):
    """Convenience function to display banking sentiment"""
    display = BankingSentimentDisplay()
    display.display(result, email_content)