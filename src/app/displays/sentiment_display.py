"""
Sentiment Display Module - Advanced Visualization of Email Sentiment Analysis
Creates stunning visualizations for multi-dimensional sentiment insights
Designed to impress in demos with rich, interactive displays
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
        EmotionalDimension,
        BankingOutcome,
        SentimentZone,
        SentimentRecommendation
    )
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("⚠️ Sentiment analyzer types not available")

class SentimentDisplay(BaseChannelDisplay):
    """Display handler for advanced sentiment analysis results"""
    
    def __init__(self):
        super().__init__("Sentiment Analysis", "🎭")
        self.style = """
        <style>
        /* Main container */
        .sentiment-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            color: white;
        }
        
        /* Sentiment gauge */
        .sentiment-gauge {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .gauge-meter {
            height: 40px;
            background: linear-gradient(to right, 
                #ef4444 0%, 
                #f59e0b 25%, 
                #eab308 50%, 
                #84cc16 75%, 
                #22c55e 100%);
            border-radius: 20px;
            position: relative;
            margin: 1rem 0;
        }
        
        .gauge-needle {
            position: absolute;
            top: -15px;
            width: 70px;
            height: 70px;
            background: white;
            border: 4px solid #764ba2;
            border-radius: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2em;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        /* Emotional dimensions radar */
        .emotion-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .dimension-bar {
            background: #e5e7eb;
            height: 30px;
            border-radius: 15px;
            margin: 0.5rem 0;
            position: relative;
            overflow: hidden;
        }
        
        .dimension-fill {
            height: 100%;
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            padding-left: 1rem;
            color: white;
            font-weight: bold;
        }
        
        /* Emotional journey */
        .journey-container {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .journey-path {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 2rem 0;
            position: relative;
        }
        
        .journey-point {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            z-index: 2;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .journey-line {
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(to right, var(--start-color), var(--end-color));
            z-index: 1;
        }
        
        /* Banking insights cards */
        .banking-card {
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
            color: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
        }
        
        .risk-indicator {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-weight: bold;
            margin: 0.25rem;
        }
        
        .risk-high {
            background: #ef4444;
            color: white;
        }
        
        .risk-medium {
            background: #f59e0b;
            color: white;
        }
        
        .risk-low {
            background: #22c55e;
            color: white;
        }
        
        /* Recommendations */
        .recommendation-card {
            background: white;
            border-left: 5px solid;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        
        .rec-high {
            border-left-color: #ef4444;
            background: #fef2f2;
        }
        
        .rec-medium {
            border-left-color: #f59e0b;
            background: #fffbeb;
        }
        
        .rec-low {
            border-left-color: #3b82f6;
            background: #eff6ff;
        }
        
        /* Sentiment heatmap */
        .heatmap-container {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .heatmap-paragraph {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border: 2px solid;
            transition: transform 0.2s;
            cursor: pointer;
        }
        
        .heatmap-paragraph:hover {
            transform: translateX(5px);
        }
        
        /* Psychological profile */
        .psych-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .psych-metric {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }
        
        .psych-score {
            font-size: 2.5em;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .psych-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        /* Quick wins */
        .quick-win {
            background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
        }
        
        .quick-win::before {
            content: "⚡";
            font-size: 1.5em;
            margin-right: 0.5rem;
        }
        
        /* Outcome predictions */
        .outcome-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .outcome-card {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .outcome-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .outcome-percentage {
            font-size: 2em;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .outcome-label {
            font-size: 0.85em;
            color: #6b7280;
        }
        </style>
        """
    
    def display_sentiment_analysis(
        self,
        sentiment_result: 'SentimentAnalysisResult',
        refined_email: Any,
        shared_context: Any
    ) -> None:
        """Display comprehensive sentiment analysis with stunning visuals"""
        
        if not sentiment_result or not SENTIMENT_AVAILABLE:
            st.error("❌ No sentiment analysis available")
            return
        
        try:
            # Apply custom styling
            st.markdown(self.style, unsafe_allow_html=True)
            
            # Header
            self._display_header(sentiment_result)
            
            # Main sentiment gauge
            self._display_sentiment_gauge(sentiment_result)
            
            # Emotional journey visualization
            self._display_emotional_journey(sentiment_result)
            
            # Multi-dimensional emotional analysis
            self._display_emotional_dimensions(sentiment_result)
            
            # Banking insights dashboard
            self._display_banking_insights(sentiment_result)
            
            # Outcome predictions
            self._display_outcome_predictions(sentiment_result)
            
            # Psychological profile
            self._display_psychological_profile(sentiment_result)
            
            # Sentiment heatmap
            self._display_sentiment_heatmap(sentiment_result)
            
            # Recommendations
            self._display_recommendations(sentiment_result)
            
            # Quick wins
            self._display_quick_wins(sentiment_result)
            
            # Segment alignment
            self._display_segment_alignment(sentiment_result)
            
            # Action buttons
            self._display_action_buttons(sentiment_result, refined_email)
            
        except Exception as e:
            st.error(f"Error displaying sentiment analysis: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _display_header(self, result: 'SentimentAnalysisResult') -> None:
        """Display impressive header"""
        
        zone_colors = {
            'optimal': '#22c55e',
            'positive': '#84cc16',
            'neutral': '#eab308',
            'concerning': '#f59e0b',
            'critical': '#ef4444'
        }
        
        zone_color = zone_colors.get(result.sentiment_zone.value, '#6b7280')
        
        st.markdown(f'''
        <div class="sentiment-container">
            <h1 style="text-align: center; margin-bottom: 0;">🎭 Advanced Sentiment Analysis</h1>
            <p style="text-align: center; opacity: 0.9; margin-top: 0.5rem;">
                Multi-Dimensional Emotional & Banking Intelligence
            </p>
            <div style="text-align: center; margin-top: 1.5rem;">
                <span style="background: {zone_color}; color: white; padding: 0.5rem 1.5rem; 
                      border-radius: 25px; font-size: 1.2em; font-weight: bold;">
                    {result.sentiment_zone.value.upper()} ZONE
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_sentiment_gauge(self, result: 'SentimentAnalysisResult') -> None:
        """Display main sentiment gauge"""
        
        # Convert sentiment to percentage position (0-100)
        position = (result.overall_sentiment + 1) * 50
        
        # Determine color based on sentiment
        if result.overall_sentiment >= 0.5:
            color = '#22c55e'
            label = 'Excellent'
        elif result.overall_sentiment >= 0:
            color = '#84cc16'
            label = 'Good'
        elif result.overall_sentiment >= -0.5:
            color = '#eab308'
            label = 'Neutral'
        else:
            color = '#ef4444'
            label = 'Poor'
        
        st.markdown(f'''
        <div class="sentiment-gauge">
            <h3 style="text-align: center; color: #1f2937;">Overall Sentiment Score</h3>
            <div class="gauge-meter">
                <div class="gauge-needle" style="left: {position}%; background: {color}; border-color: {color};">
                    {result.overall_sentiment:.2f}
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; color: #6b7280;">
                <span>Very Negative</span>
                <span>Neutral</span>
                <span>Very Positive</span>
            </div>
            <p style="text-align: center; font-size: 1.5em; color: {color}; margin-top: 1rem;">
                <strong>{label}</strong> - Confidence: {result.confidence_score:.0%}
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    def _display_emotional_journey(self, result: 'SentimentAnalysisResult') -> None:
        """Display emotional journey through the email"""
        
        journey = result.emotional_journey
        
        # Determine colors based on sentiment
        def get_color(sentiment):
            if sentiment >= 0.5:
                return '#22c55e'
            elif sentiment >= 0:
                return '#84cc16'
            elif sentiment >= -0.5:
                return '#f59e0b'
            else:
                return '#ef4444'
        
        opening_color = get_color(journey.opening_sentiment)
        middle_color = get_color(journey.middle_sentiment)
        closing_color = get_color(journey.closing_sentiment)
        
        st.markdown("### 🎢 Emotional Journey")
        
        # Calculate gradient for the connecting line
        gradient_start = opening_color
        gradient_end = closing_color
        
        st.markdown(f'''
        <div class="journey-container">
            <h4 style="color: #1f2937; text-align: center;">How Sentiment Flows Through the Email</h4>
            <div class="journey-path" style="--start-color: {gradient_start}; --end-color: {gradient_end};">
                <div class="journey-line"></div>
                <div class="journey-point" style="background: {opening_color};">
                    <span style="font-size: 1.5em;">{journey.opening_sentiment:.1f}</span>
                    <span style="font-size: 0.8em;">Opening</span>
                </div>
                <div class="journey-point" style="background: {middle_color};">
                    <span style="font-size: 1.5em;">{journey.middle_sentiment:.1f}</span>
                    <span style="font-size: 0.8em;">Middle</span>
                </div>
                <div class="journey-point" style="background: {closing_color};">
                    <span style="font-size: 1.5em;">{journey.closing_sentiment:.1f}</span>
                    <span style="font-size: 0.8em;">Closing</span>
                </div>
            </div>
            <div style="text-align: center; color: #6b7280; margin-top: 1rem;">
                <strong>Trajectory:</strong> {journey.trajectory.upper()} | 
                <strong>Volatility:</strong> {journey.volatility:.0%}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Show dead zones and peak moments if any
        if journey.dead_zones or journey.peak_moments:
            col1, col2 = st.columns(2)
            
            with col1:
                if journey.dead_zones:
                    st.warning(f"**⚠️ Emotional Dead Zones:** {', '.join(journey.dead_zones[:2])}")
            
            with col2:
                if journey.peak_moments:
                    st.success(f"**✨ Peak Moments:** {', '.join(journey.peak_moments[:2])}")
    
    def _display_emotional_dimensions(self, result: 'SentimentAnalysisResult') -> None:
        """Display multi-dimensional emotional analysis"""
        
        st.markdown("### 🎯 Emotional Dimensions")
        
        # Create two columns for dimensions
        col1, col2 = st.columns(2)
        
        dimensions_list = list(result.emotional_dimensions.items())
        half = len(dimensions_list) // 2
        
        for i, (dimension, score) in enumerate(dimensions_list):
            # Determine color based on dimension and score
            if dimension == EmotionalDimension.ANXIETY:
                # For anxiety, lower is better
                color = '#ef4444' if score > 0.6 else '#f59e0b' if score > 0.3 else '#22c55e'
            else:
                # For others, higher is generally better
                color = '#22c55e' if score > 0.7 else '#f59e0b' if score > 0.4 else '#ef4444'
            
            html = f'''
            <div class="emotion-card">
                <h5 style="color: #1f2937; margin-bottom: 0.5rem;">
                    {dimension.value.title()}
                </h5>
                <div class="dimension-bar">
                    <div class="dimension-fill" style="width: {score*100}%; background: {color};">
                        {score:.0%}
                    </div>
                </div>
            </div>
            '''
            
            if i < half:
                with col1:
                    st.markdown(html, unsafe_allow_html=True)
            else:
                with col2:
                    st.markdown(html, unsafe_allow_html=True)
    
    def _display_banking_insights(self, result: 'SentimentAnalysisResult') -> None:
        """Display banking-specific insights"""
        
        insights = result.banking_insights
        
        st.markdown("### 🏦 Banking Intelligence")
        
        # Risk indicators
        complaint_risk_level = 'high' if insights.complaint_probability > 0.6 else 'medium' if insights.complaint_probability > 0.3 else 'low'
        
        st.markdown(f'''
        <div class="banking-card">
            <h4 style="margin-bottom: 1rem;">Risk Assessment</h4>
            <div>
                <span class="risk-indicator risk-{complaint_risk_level}">
                    Complaint Risk: {insights.complaint_probability:.0%}
                </span>
                <span class="risk-indicator risk-{insights.call_center_impact.lower()}">
                    Call Center Impact: {insights.call_center_impact.upper()}
                </span>
                <span class="risk-indicator" style="background: #6366f1;">
                    Regulatory Tone: {insights.regulatory_tone_score:.0%}
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Additional insights in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if insights.cross_sell_opportunities:
                st.info(f"**💰 Cross-Sell Opportunities:**\n" + "\n".join(f"• {opp}" for opp in insights.cross_sell_opportunities[:3]))
        
        with col2:
            if insights.trust_markers_present:
                st.success(f"**✅ Trust Markers:**\n" + "\n".join(f"• {marker}" for marker in insights.trust_markers_present[:3]))
        
        with col3:
            if insights.risk_flags:
                st.error(f"**🚩 Risk Flags:**\n" + "\n".join(f"• {flag}" for flag in insights.risk_flags[:3]))
    
    def _display_outcome_predictions(self, result: 'SentimentAnalysisResult') -> None:
        """Display predicted customer outcomes"""
        
        st.markdown("### 🔮 Outcome Predictions")
        
        st.markdown('<div class="outcome-grid">', unsafe_allow_html=True)
        
        # Create cards for each outcome
        outcomes_html = ""
        for outcome, probability in result.outcome_predictions.items():
            # Determine color based on outcome type and probability
            if outcome in [BankingOutcome.COMPLAINT_RISK, BankingOutcome.CHURN_RISK]:
                # For negative outcomes, lower is better
                color = '#ef4444' if probability > 0.6 else '#f59e0b' if probability > 0.3 else '#22c55e'
            else:
                # For positive outcomes, higher is better
                color = '#22c55e' if probability > 0.6 else '#f59e0b' if probability > 0.3 else '#ef4444'
            
            outcomes_html += f'''
            <div class="outcome-card">
                <div class="outcome-label">{outcome.value.replace('_', ' ').title()}</div>
                <div class="outcome-percentage" style="color: {color};">
                    {probability:.0%}
                </div>
            </div>
            '''
        
        st.markdown(outcomes_html + '</div>', unsafe_allow_html=True)
    
    def _display_psychological_profile(self, result: 'SentimentAnalysisResult') -> None:
        """Display psychological profile analysis"""
        
        st.markdown("### 🧠 Psychological Profile")
        
        profile = result.psychological_profile
        
        metrics = [
            ("Cognitive Load", profile.cognitive_load, "How easy to understand"),
            ("Psychological Safety", profile.psychological_safety, "Feeling of security"),
            ("Autonomy Support", profile.autonomy_support, "Empowerment level"),
            ("Social Connection", profile.social_connection, "Human warmth"),
            ("Competence Building", profile.competence_building, "Educational value")
        ]
        
        st.markdown('<div class="psych-grid">', unsafe_allow_html=True)
        
        for name, score, description in metrics:
            # Determine color based on score
            if score > 0.7:
                gradient = "linear-gradient(135deg, #34d399 0%, #10b981 100%)"
            elif score > 0.4:
                gradient = "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)"
            else:
                gradient = "linear-gradient(135deg, #f87171 0%, #ef4444 100%)"
            
            st.markdown(f'''
            <div class="psych-metric" style="background: {gradient};">
                <div class="psych-label">{name}</div>
                <div class="psych-score">{score:.0%}</div>
                <div style="font-size: 0.8em; opacity: 0.9;">{description}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _display_sentiment_heatmap(self, result: 'SentimentAnalysisResult') -> None:
        """Display paragraph-by-paragraph sentiment heatmap"""
        
        if not result.heatmap_data.get('paragraphs'):
            return
        
        st.markdown("### 🌡️ Sentiment Heatmap")
        
        with st.expander("View paragraph-by-paragraph sentiment", expanded=False):
            for para_data in result.heatmap_data['paragraphs']:
                sentiment = para_data['sentiment']
                
                # Determine color and border based on sentiment
                if sentiment >= 0.5:
                    bg_color = '#dcfce7'
                    border_color = '#22c55e'
                elif sentiment >= 0:
                    bg_color = '#fef3c7'
                    border_color = '#f59e0b'
                else:
                    bg_color = '#fee2e2'
                    border_color = '#ef4444'
                
                st.markdown(f'''
                <div class="heatmap-paragraph" style="background: {bg_color}; border-color: {border_color};">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <strong>Paragraph {para_data['index'] + 1}</strong><br>
                            <span style="color: #6b7280; font-size: 0.9em;">{para_data['text']}</span>
                        </div>
                        <div style="background: {border_color}; color: white; padding: 0.25rem 0.75rem; 
                             border-radius: 15px; margin-left: 1rem;">
                            {sentiment:.2f}
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
    
    def _display_recommendations(self, result: 'SentimentAnalysisResult') -> None:
        """Display actionable recommendations"""
        
        if not result.recommendations:
            return
        
        st.markdown("### 💡 Recommendations")
        
        # Group by priority
        high_priority = [r for r in result.recommendations if r.priority == 'high']
        medium_priority = [r for r in result.recommendations if r.priority == 'medium']
        low_priority = [r for r in result.recommendations if r.priority == 'low']
        
        for rec in high_priority[:3]:
            st.markdown(f'''
            <div class="recommendation-card rec-high">
                <h5 style="color: #dc2626; margin-bottom: 0.5rem;">🔴 HIGH PRIORITY - {rec.category.upper()}</h5>
                <p><strong>Issue:</strong> {rec.issue}</p>
                <p><strong>Suggestion:</strong> {rec.suggestion}</p>
                <p><strong>Expected Impact:</strong> {rec.impact}</p>
                {f'<p><em>Example: "{rec.example}"</em></p>' if rec.example else ''}
            </div>
            ''', unsafe_allow_html=True)
        
        for rec in medium_priority[:2]:
            st.markdown(f'''
            <div class="recommendation-card rec-medium">
                <h5 style="color: #d97706; margin-bottom: 0.5rem;">🟡 MEDIUM PRIORITY - {rec.category.upper()}</h5>
                <p><strong>Issue:</strong> {rec.issue}</p>
                <p><strong>Suggestion:</strong> {rec.suggestion}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        for rec in low_priority[:2]:
            st.markdown(f'''
            <div class="recommendation-card rec-low">
                <h5 style="color: #2563eb; margin-bottom: 0.5rem;">🔵 LOW PRIORITY - {rec.category.upper()}</h5>
                <p><strong>Suggestion:</strong> {rec.suggestion}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_quick_wins(self, result: 'SentimentAnalysisResult') -> None:
        """Display quick win improvements"""
        
        if not result.quick_wins:
            return
        
        st.markdown("### ⚡ Quick Wins")
        st.markdown("Simple changes with high impact:")
        
        for win in result.quick_wins[:5]:
            st.markdown(f'<div class="quick-win">{win}</div>', unsafe_allow_html=True)
    
    def _display_segment_alignment(self, result: 'SentimentAnalysisResult') -> None:
        """Display segment alignment analysis"""
        
        st.markdown("### 🎯 Segment Alignment")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Alignment score visualization
            score = result.segment_alignment_score
            color = '#22c55e' if score > 0.8 else '#f59e0b' if score > 0.6 else '#ef4444'
            
            st.markdown(f"""
            **Alignment Score: {score:.0%}**
            """)
            st.progress(score)
            
            if result.segment_mismatches:
                st.warning("**Mismatches found:**")
                for mismatch in result.segment_mismatches[:3]:
                    st.write(f"• {mismatch}")
        
        with col2:
            # Cultural sensitivity scores
            st.metric("Cultural Appropriateness", f"{result.cultural_appropriateness:.0%}")
            st.metric("Formality Score", f"{result.language_formality_score:.0%}")
    
    def _display_action_buttons(self, result: 'SentimentAnalysisResult', refined_email: Any) -> None:
        """Display action buttons for next steps"""
        
        st.markdown("---")
        st.markdown("### 🚀 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if result.sentiment_zone in [SentimentZone.CONCERNING, SentimentZone.CRITICAL]:
                if st.button("🔧 Auto-Improve Sentiment", type="primary", use_container_width=True):
                    st.session_state.improve_sentiment_triggered = True
                    st.info("Sentiment improvement would be triggered here")
        
        with col2:
            if st.button("📊 Export Analysis", use_container_width=True):
                # Create downloadable report
                report = self._create_analysis_report(result)
                st.download_button(
                    "Download Report",
                    report,
                    file_name=f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if result.banking_insights.complaint_probability > 0.5:
                if st.button("⚠️ Flag for Review", use_container_width=True):
                    st.warning("Email flagged for manual review before sending")
        
        with col4:
            if st.button("✅ Accept & Send", use_container_width=True):
                st.success("Email accepted with current sentiment profile")
    
    def _create_analysis_report(self, result: 'SentimentAnalysisResult') -> str:
        """Create downloadable analysis report"""
        
        report = {
            'timestamp': result.analysis_timestamp,
            'overall_sentiment': result.overall_sentiment,
            'sentiment_zone': result.sentiment_zone.value,
            'confidence': result.confidence_score,
            'emotional_dimensions': {d.value: v for d, v in result.emotional_dimensions.items()},
            'banking_insights': {
                'complaint_probability': result.banking_insights.complaint_probability,
                'call_center_impact': result.banking_insights.call_center_impact,
                'cross_sell_opportunities': result.banking_insights.cross_sell_opportunities
            },
            'outcome_predictions': {o.value: v for o, v in result.outcome_predictions.items()},
            'recommendations': [
                {
                    'priority': r.priority,
                    'issue': r.issue,
                    'suggestion': r.suggestion
                }
                for r in result.recommendations[:10]
            ],
            'quick_wins': result.quick_wins
        }
        
        return json.dumps(report, indent=2)
    
    # Required base class methods
    def display_result(self, result: Any, shared_context: Any) -> None:
        """Required by base class"""
        # This is called by the main display system
        # We'll handle this differently since sentiment needs the refined email too
        pass
    
    def validate_result(self, result: Any, shared_context: Any) -> Dict[str, Any]:
        """Validate sentiment analysis result"""
        validation = {
            'is_valid': True,
            'issues': [],
            'achievements': [],
            'metrics': {}
        }
        
        if hasattr(result, 'overall_sentiment'):
            validation['metrics']['overall_sentiment'] = result.overall_sentiment
            
            if result.sentiment_zone == SentimentZone.OPTIMAL:
                validation['achievements'].append("Optimal sentiment achieved")
            elif result.sentiment_zone == SentimentZone.CRITICAL:
                validation['issues'].append("Critical sentiment issues detected")
                validation['is_valid'] = False
        
        if hasattr(result, 'banking_insights'):
            if result.banking_insights.complaint_probability > 0.7:
                validation['issues'].append(f"High complaint risk: {result.banking_insights.complaint_probability:.0%}")
            
            if result.banking_insights.complaint_probability < 0.3:
                validation['achievements'].append("Low complaint risk")
        
        return validation
    
    def get_download_data(self, result: Any, customer_name: str) -> Tuple[str, str, str]:
        """Get download data for sentiment analysis"""
        
        if not hasattr(result, 'analysis_timestamp'):
            return "", "", ""
        
        report = self._create_analysis_report(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sentiment_analysis_{customer_name}_{timestamp}.json"
        
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