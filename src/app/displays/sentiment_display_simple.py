"""
Simple Sentiment Display - Built for Streamlit
Works with plain dictionaries, no complex dataclasses
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from datetime import datetime

class SimpleSentimentDisplay:
    """Simple display for sentiment analysis results"""
    
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
        
        .score-box {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            margin: 0.5rem;
        }
        
        .score-big {
            font-size: 3em;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .positive { color: #28a745; }
        .neutral { color: #ffc107; }
        .negative { color: #dc3545; }
        
        .ready-box {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .ready-yes {
            background: #d4edda;
            color: #155724;
            border: 2px solid #28a745;
        }
        
        .ready-no {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #dc3545;
        }
        
        .issue-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .red-flag-box {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        
        .quick-win-box {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }
        </style>
        """
    
    def display(self, result: Dict[str, Any], email_content: str = None) -> None:
        """
        Display sentiment analysis results
        
        Args:
            result: Dictionary with analysis results
            email_content: Optional email content for context
        """
        
        # Validate we have a result
        if not result:
            st.error("❌ No sentiment analysis results available")
            return
        
        # Apply styling
        st.markdown(self.style, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="sentiment-header">
            <h2>🎯 Sentiment Analysis Results</h2>
            <p>Banking communication intelligence report</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Executive Summary
        st.markdown(f"### 📊 Executive Summary")
        st.info(result.get('executive_summary', 'No summary available'))
        
        # Ready to Send Decision
        ready = result.get('ready_to_send', False)
        if ready:
            st.markdown("""
            <div class="ready-box ready-yes">
                ✅ READY TO SEND - No critical issues found
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ready-box ready-no">
                ⚠️ NOT READY - Issues need attention
            </div>
            """, unsafe_allow_html=True)
        
        # Core Metrics
        st.markdown("### 📈 Core Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        # Sentiment Score
        with col1:
            sentiment = result.get('sentiment', {})
            score = sentiment.get('score', 0)
            category = sentiment.get('category', 'neutral')
            
            color = 'positive' if score > 30 else 'negative' if score < -30 else 'neutral'
            emoji = '😊' if score > 30 else '😟' if score < -30 else '😐'
            
            st.markdown(f"""
            <div class="score-box">
                <strong>Sentiment</strong>
                <div class="score-big {color}">{score}</div>
                <div style="font-size: 2em;">{emoji}</div>
                <small>{sentiment.get('why', '')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Compliance
        with col2:
            compliance = result.get('compliance', {})
            status = compliance.get('status', 'warning')
            comp_score = compliance.get('score', 50)
            
            status_emoji = '✅' if status == 'pass' else '⚠️' if status == 'warning' else '❌'
            color = 'positive' if status == 'pass' else 'negative' if status == 'fail' else 'neutral'
            
            st.markdown(f"""
            <div class="score-box">
                <strong>Compliance</strong>
                <div class="score-big {color}">{comp_score}</div>
                <div style="font-size: 2em;">{status_emoji}</div>
                <small>{compliance.get('why', '')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Complaint Risk
        with col3:
            impact = result.get('customer_impact', {})
            complaint_risk = impact.get('complaint_risk', 50)
            
            risk_level = 'Low' if complaint_risk < 30 else 'High' if complaint_risk > 60 else 'Medium'
            color = 'positive' if complaint_risk < 30 else 'negative' if complaint_risk > 60 else 'neutral'
            emoji = '✅' if complaint_risk < 30 else '🚨' if complaint_risk > 60 else '⚠️'
            
            st.markdown(f"""
            <div class="score-box">
                <strong>Complaint Risk</strong>
                <div class="score-big {color}">{complaint_risk}%</div>
                <div style="font-size: 2em;">{emoji}</div>
                <small>{risk_level} Risk</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Readability
        with col4:
            readability = result.get('readability', {})
            read_score = readability.get('score', 50)
            grade = readability.get('grade_level', 10)
            
            level = 'Easy' if read_score > 60 else 'Hard' if read_score < 30 else 'Moderate'
            color = 'positive' if read_score > 60 else 'negative' if read_score < 30 else 'neutral'
            
            st.markdown(f"""
            <div class="score-box">
                <strong>Readability</strong>
                <div class="score-big {color}">{read_score}</div>
                <small>Grade {grade:.0f} • {level}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Issues Section
        red_flags = result.get('red_flags', [])
        warnings = result.get('warnings', [])
        
        if red_flags or warnings:
            st.markdown("### ⚠️ Issues to Address")
            
            # Red Flags
            for flag in red_flags:
                st.markdown(f"""
                <div class="red-flag-box">
                    <strong>🔴 CRITICAL: {flag.get('issue', '')}</strong><br>
                    <em>Impact:</em> {flag.get('impact', '')}<br>
                    <em>Fix:</em> {flag.get('fix', '')}
                </div>
                """, unsafe_allow_html=True)
            
            # Warnings
            for warning in warnings:
                st.markdown(f"""
                <div class="issue-box">
                    <strong>⚠️ WARNING: {warning.get('issue', '')}</strong><br>
                    <em>Impact:</em> {warning.get('impact', '')}<br>
                    <em>Suggestion:</em> {warning.get('fix', '')}
                </div>
                """, unsafe_allow_html=True)
        
        # Quick Wins
        quick_wins = result.get('quick_wins', [])
        if quick_wins:
            st.markdown("### ⚡ Quick Improvements")
            
            for win in quick_wins:
                st.markdown(f"""
                <div class="quick-win-box">
                    <strong>Improvement Opportunity:</strong><br>
                    ❌ Current: <em>"{win.get('original', '')}"</em><br>
                    ✅ Better: <em>"{win.get('improved', '')}"</em><br>
                    💡 Why: {win.get('why', '')}
                </div>
                """, unsafe_allow_html=True)
        
        # Analysis Details
        with st.expander("📋 Analysis Details"):
            st.json(result)
        
        # Actions
        st.markdown("### 🚀 Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download Report", use_container_width=True):
                st.download_button(
                    "Download JSON",
                    json.dumps(result, indent=2),
                    file_name=f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if not ready:
                if st.button("🔧 Apply Fixes", type="primary", use_container_width=True):
                    st.info("Auto-fix feature coming soon")
        
        with col3:
            if ready:
                if st.button("✅ Accept & Send", type="primary", use_container_width=True):
                    st.success("Email approved for sending!")
            else:
                if st.button("⚠️ Send Anyway", use_container_width=True):
                    st.warning("Sending despite issues - logged for compliance")


# Simple function to display sentiment
def display_simple_sentiment(result: Dict[str, Any], email_content: str = None):
    """
    Simple function to display sentiment results
    
    Args:
        result: Dictionary with analysis results
        email_content: Optional email content
    """
    display = SimpleSentimentDisplay()
    display.display(result, email_content)