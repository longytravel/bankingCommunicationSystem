"""Lloyds Banking Group branding utilities for Streamlit UI."""

from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Go up 3 levels: branding.py -> styles -> app -> src -> project root
BRAND_ASSETS_DIR = PROJECT_ROOT / 'assets' / 'lloyds'

BRAND_PALETTE: Dict[str, str] = {
    'green_primary': '#006A4D',
    'green_dark': '#013826',
    'green_bright': '#00A651',
    'cream': '#F5F7F4',
    'charcoal': '#1C1C1C',
    'muted': '#6E6E6E',
    'light_gray': '#F8F9FA',
    'sunlit_gold': '#C4B000',
    'surface': '#FFFFFF',
    'surface_alt': '#F8F9FA',
    'border': '#E5E5E5',
    'shadow': 'rgba(0, 0, 0, 0.08)',
    'shadow_hover': 'rgba(0, 0, 0, 0.12)',
}

FONT_FILES = {
    'normal': BRAND_ASSETS_DIR / 'OpenSans-VariableFont_wdth,wght.ttf',
    'italic': BRAND_ASSETS_DIR / 'OpenSans-Italic-VariableFont_wdth,wght.ttf',
}


def get_brand_asset(name: str) -> Optional[Path]:
    """Return a Path to a brand asset if it exists."""
    candidate = BRAND_ASSETS_DIR / name
    if candidate.exists():
        return candidate
    return None


@lru_cache(maxsize=None)
def _font_base64(key: str) -> str:
    """Return the base64 string for the requested font file."""
    font_path = FONT_FILES.get(key)
    if not font_path or not font_path.exists():
        return ''
    return base64.b64encode(font_path.read_bytes()).decode('utf-8')


def apply_lloyds_branding() -> None:
    """Inject Lloyds-specific CSS, fonts, and design tokens into Streamlit."""
    normal_font = _font_base64('normal')
    italic_font = _font_base64('italic')

    font_face = ''
    if normal_font:
        font_face += f"""
    @font-face {{
        font-family: 'LBG Open Sans';
        src: url(data:font/ttf;base64,{normal_font}) format('truetype');
        font-weight: 100 900;
        font-style: normal;
    }}
    """
    if italic_font:
        font_face += f"""
    @font-face {{
        font-family: 'LBG Open Sans';
        src: url(data:font/ttf;base64,{italic_font}) format('truetype');
        font-weight: 100 900;
        font-style: italic;
    }}
    """

    css = f"""
    <style>
    {font_face}

    :root {{
        --lbg-green: {BRAND_PALETTE['green_primary']};
        --lbg-green-dark: {BRAND_PALETTE['green_dark']};
        --lbg-green-light: {BRAND_PALETTE['green_bright']};
        --lbg-cream: {BRAND_PALETTE['cream']};
        --lbg-charcoal: {BRAND_PALETTE['charcoal']};
        --lbg-muted: {BRAND_PALETTE['muted']};
        --lbg-light-gray: {BRAND_PALETTE['light_gray']};
        --lbg-gold: {BRAND_PALETTE['sunlit_gold']};
        --lbg-surface: {BRAND_PALETTE['surface']};
        --lbg-surface-alt: {BRAND_PALETTE['surface_alt']};
        --lbg-border: {BRAND_PALETTE['border']};
        --lbg-shadow: {BRAND_PALETTE['shadow']};
        --lbg-shadow-hover: {BRAND_PALETTE['shadow_hover']};
        --lbg-radius-lg: 16px;
        --lbg-radius-md: 12px;
        --lbg-radius-sm: 8px;
    }}

    html, body, [class*='block-container'] {{
        font-family: 'LBG Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        background: #F8F9FA;
        color: var(--lbg-charcoal);
    }}

    .stApp {{
        background: #F8F9FA;
    }}

    .main .block-container {{
        padding: 1.5rem 2.5rem 3rem;
        max-width: 1200px;
    }}

    .lbg-hero-wrapper {{
        display: flex;
        align-items: stretch;
        gap: 20px;
        margin-bottom: 24px;
        min-height: 120px;
    }}

    .lbg-hero {{
        display: flex;
        align-items: center;
        flex: 1;
        background: linear-gradient(135deg, var(--lbg-green-dark), var(--lbg-green));
        color: white;
        padding: 32px;
        border-radius: var(--lbg-radius-lg);
        box-shadow: 0 6px 18px rgba(0, 106, 77, 0.22);
        position: relative;
        overflow: hidden;
    }}

    .lbg-hero::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.18), transparent 55%);
        pointer-events: none;
    }}

    .lbg-hero-content {{
        position: relative;
        z-index: 1;
        flex: 1;
        max-width: 640px;
    }}

    .lbg-hero h1 {{
        font-size: 26px;
        font-weight: 600;
        margin: 0 0 10px 0;
    }}

    .lbg-hero p {{
        font-size: 15px;
        margin: 0;
        opacity: 0.95;
        line-height: 1.5;
    }}

    .lbg-hero-logo {{
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: white;
        border-radius: var(--lbg-radius-lg);
        padding: 15px 25px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
        min-width: 200px;
    }}

    .lbg-hero-logo img {{
        height: 90px;
        width: auto;
        max-width: 100%;
        display: block;
    }}

    @media (max-width: 1024px) {{
        .lbg-hero-wrapper {{
            flex-direction: column;
            gap: 16px;
        }}

        .lbg-hero {{
            min-height: auto;
        }}

        .lbg-hero-logo {{
            padding: 12px 20px;
            min-width: 180px;
        }}

        .lbg-hero-logo img {{
            height: 70px;
        }}
    }}

    @media (max-width: 640px) {{
        .lbg-hero-wrapper {{
            gap: 12px;
        }}

        .lbg-hero {{
            padding: 20px;
        }}

        .lbg-hero h1 {{
            font-size: 20px;
        }}

        .lbg-hero p {{
            font-size: 13px;
        }}

        .lbg-hero-logo {{
            padding: 10px 18px;
            min-width: 160px;
        }}

        .lbg-hero-logo img {{
            height: 60px;
        }}
    }}

    .lbg-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.18);
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }}

    .lbg-card {{
        background: var(--lbg-surface);
        border-radius: var(--lbg-radius-lg);
        border: none;
        padding: 32px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }}

    .lbg-card:hover {{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }}

    .lbg-card.is-highlight {{
        border-color: rgba(0, 166, 81, 0.45);
        box-shadow: 0 24px 42px rgba(0, 166, 81, 0.25);
    }}

    .lbg-section-title {{
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-weight: 600;
        color: var(--lbg-muted);
        margin-bottom: 0.8rem;
    }}

    .lbg-subtitle {{
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--lbg-charcoal);
        margin-bottom: 0.5rem;
    }}

    .lbg-divider {{
        height: 1px;
        width: 100%;
        background: linear-gradient(90deg, rgba(0, 106, 77, 0.0), rgba(0, 106, 77, 0.45), rgba(0, 106, 77, 0.0));
        margin: 2rem 0 1.8rem;
    }}

    .lbg-tag {{
        display: inline-flex;
        padding: 0.35rem 0.75rem;
        background: rgba(0, 106, 77, 0.12);
        border-radius: 999px;
        font-size: 0.75rem;
        color: var(--lbg-green-dark);
        margin-right: 0.5rem;
    }}

    .lbg-badge-critical {{
        background: rgba(196, 0, 0, 0.12);
        color: #7A0000;
    }}

    .stTabs [data-baseweb='tab-list'] {{
        gap: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--lbg-border);
    }}

    .stTabs [data-baseweb='tab'] {{
        padding: 0.6rem 1rem;
        background: rgba(0, 106, 77, 0.05);
        color: var(--lbg-charcoal);
        border-radius: var(--lbg-radius-md);
    }}

    .stTabs [data-baseweb='tab'][aria-selected='true'] {{
        background: var(--lbg-surface);
        color: var(--lbg-green-dark);
        border: 1px solid rgba(0, 106, 77, 0.25);
        box-shadow: 0 12px 20px rgba(0, 166, 81, 0.12);
    }}

    .stButton>button {{
        border-radius: var(--lbg-radius-sm);
        border: none;
        font-weight: 500;
        padding: 10px 20px;
        background: var(--lbg-green);
        color: white;
        font-size: 14px;
        transition: all 0.2s ease;
        box-shadow: none;
    }}

    .stButton>button:hover {{
        background: var(--lbg-green-dark);
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 106, 77, 0.2);
    }}

    .stButton>button:focus {{
        outline: 2px solid rgba(0, 166, 81, 0.4);
    }}

    .stDownloadButton>button, .stDownloadButton>button:hover {{
        border-radius: var(--lbg-radius-md);
        border: 1px solid rgba(0, 166, 81, 0.28);
        background: var(--lbg-surface);
        color: var(--lbg-green-dark);
        box-shadow: none;
    }}

    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb='select']>div {{
        border-radius: var(--lbg-radius-md);
        border: 1px solid var(--lbg-border);
        background: rgba(255, 255, 255, 0.92);
        box-shadow: none;
    }}

    .stTextInput>div>div>input:focus,
    .stTextArea textarea:focus,
    .stSelectbox div[data-baseweb='select']>div:focus {{
        border-color: var(--lbg-green);
        box-shadow: 0 0 0 3px rgba(0, 106, 77, 0.18);
    }}

    .stMetric {{
        background: var(--lbg-surface);
        padding: 1rem 1.4rem;
        border-radius: var(--lbg-radius-md);
        border: 1px solid rgba(0, 0, 0, 0.05);
        box-shadow: 0 16px 30px rgba(1, 56, 38, 0.12);
    }}

    /* Clean Expanders */
    .stExpander {{
        border-radius: var(--lbg-radius-md);
        border: none;
        background: var(--lbg-surface);
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .stExpander summary {{
        font-weight: 500;
        color: var(--lbg-charcoal);
        font-size: 16px;
        padding: 16px 20px;
    }}

    .stExpander summary:hover {{
        background: rgba(0, 106, 77, 0.02);
    }}

    .stExpander [data-testid="stExpanderToggleIcon"] {{
        font-size: 12px;
        color: #999;
    }}

    .stAlert {{
        border-radius: var(--lbg-radius-md);
        border: none;
        box-shadow: 0 12px 24px rgba(1, 56, 38, 0.1);
    }}

    .stAlert > div {{
        padding: 0.9rem 1.1rem;
    }}

    .stSidebar {{
        background: linear-gradient(180deg, rgba(1, 56, 38, 0.96), rgba(1, 56, 38, 0.75));
    }}

    .stSidebar [class*='block-container'] {{
        padding: 2rem 1.5rem;
    }}

    .stSidebar .lbg-card {{
        background: rgba(255, 255, 255, 0.14);
        border-radius: var(--lbg-radius-md);
        border: 1px solid rgba(255, 255, 255, 0.22);
        padding: 1.2rem 1rem;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
        margin-bottom: 1.3rem;
        backdrop-filter: blur(6px);
    }}

    .stSidebar h1,
    .stSidebar h2,
    .stSidebar h3,
    .stSidebar p,
    .stSidebar label {{
        color: #F6FFFC;
    }}

    .stSidebar .lbg-sidebar-status span:first-child {{
        color: rgba(255, 255, 255, 0.86);
    }}

    .stSidebar .lbg-sidebar-status span:last-child {{
        color: #0A291E;
        font-weight: 600;
    }}

    .stSidebar .stButton>button {{
        width: 100%;
        background: rgba(255, 255, 255, 0.08);
        color: #E8F3ED;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: none;
    }}

    .stSidebar .stButton>button:hover {{
        background: rgba(255, 255, 255, 0.16);
    }}

    .stSidebar .stTextInput>div>div>input,
    .stSidebar .stSelectbox div[data-baseweb='select']>div {{
        background: rgba(255, 255, 255, 0.12);
        color: #F8FFFB;
        border-color: rgba(255, 255, 255, 0.18);
    }}

    /* Clean Table Styling */
    .stDataFrame {{
        background: transparent;
    }}

    .stDataFrame div[data-testid='StyledTable'] {{
        border: none;
        background: var(--lbg-surface);
        border-radius: var(--lbg-radius-md);
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .stDataFrame table {{
        border: none !important;
    }}

    .stDataFrame thead tr th {{
        background: #FAFAFA !important;
        border: none !important;
        color: #666 !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 12px 16px !important;
    }}

    .stDataFrame tbody tr {{
        border-bottom: 1px solid #F0F0F0 !important;
    }}

    .stDataFrame tbody tr:last-child {{
        border-bottom: none !important;
    }}

    .stDataFrame tbody tr:hover {{
        background: rgba(0, 106, 77, 0.02) !important;
    }}

    .stDataFrame tbody tr td {{
        border: none !important;
        padding: 14px 16px !important;
        color: var(--lbg-charcoal) !important;
        font-size: 14px !important;
    }}
    .lbg-sidebar-status {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        font-size: 0.85rem;
    }}

    .lbg-sidebar-status:last-child {{
        border-bottom: none;
    }}

    .stSidebar .lbg-tag {{
        margin-right: 0;
        background: rgba(255, 255, 255, 0.92);
        color: #0A291E;
        font-weight: 600;
    }}

    .stSidebar .lbg-tag.lbg-badge-critical {{
        background: rgba(255, 86, 48, 0.92);
        color: #FFFFFF;
    }}

    .lbg-metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }}

    .lbg-metric-tile {{
        background: var(--lbg-surface-alt);
        border-radius: var(--lbg-radius-md);
        padding: 1rem 1.1rem;
        border: 1px solid rgba(0, 106, 77, 0.12);
    }}

    .lbg-metric-label {{
        font-size: 0.78rem;
        text-transform: uppercase;
        color: var(--lbg-muted);
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
    }}

    .lbg-metric-value {{
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--lbg-green-dark);
    }}


    .lbg-surface-card {{
        background: var(--lbg-surface);
        border-radius: 24px;
        border: 1px solid rgba(1, 56, 38, 0.08);
        padding: 1.8rem 2rem;
        box-shadow: 0 28px 48px rgba(1, 56, 38, 0.08);
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
    }}

    .lbg-surface-card::after {{
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(0, 166, 81, 0.06), transparent 65%);
        pointer-events: none;
    }}

    .lbg-card-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 1.2rem;
        gap: 0.75rem;
        position: relative;
        z-index: 1;
    }}

    .lbg-card-title {{
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--lbg-green-dark);
        margin: 0;
    }}

    .lbg-card-subtitle {{
        font-size: 0.92rem;
        color: var(--lbg-muted);
        margin-top: 0.2rem;
    }}

    .lbg-card-badge {{
        display: inline-flex;
        align-items: center;
        background: rgba(0, 106, 77, 0.12);
        color: var(--lbg-green-dark);
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    .lbg-card-body {{
        position: relative;
        z-index: 1;
    }}

    .lbg-step-list {{
        display: grid;
        gap: 1.1rem;
        margin: 0;
        padding: 0;
        list-style: none;
    }}

    .lbg-step-list-item {{
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 0.9rem;
        align-items: start;
    }}

    .lbg-step-icon {{
        width: 36px;
        height: 36px;
        border-radius: 12px;
        background: rgba(0, 106, 77, 0.12);
        color: var(--lbg-green-dark);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
    }}

    .lbg-step-content h4 {{
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--lbg-charcoal);
    }}

    .lbg-step-content p {{
        margin: 0.2rem 0 0;
        color: var(--lbg-muted);
        font-size: 0.9rem;
    }}

    .lbg-empty-state {{
        background: rgba(0, 106, 77, 0.08);
        border-radius: var(--lbg-radius-md);
        padding: 1rem 1.4rem;
        color: var(--lbg-green-dark);
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
        margin: 0.5rem 0 0;
    }}

    .lbg-empty-state::before {{
        content: '\26A0';
        font-size: 1.2rem;
    }}

    /* Clean File Upload Area */
    [data-testid="stFileUploader"] {{
        background: var(--lbg-surface);
        border-radius: var(--lbg-radius-md);
        padding: 24px;
        border: 2px dashed transparent;
        transition: all 0.2s ease;
        position: relative;
    }}

    [data-testid="stFileUploader"]:hover {{
        border-color: #E0E0E0;
        background: #FAFAFA;
    }}

    [data-testid="stFileUploader"] > div {{
        background: transparent !important;
        border: none !important;
    }}

    [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
        background: transparent !important;
        border: none !important;
    }}

    [data-testid="stFileUploader"] button {{
        background: var(--lbg-surface) !important;
        border: none !important;
        color: var(--lbg-green) !important;
        border-radius: var(--lbg-radius-sm) !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }}

    [data-testid="stFileUploader"] button:hover {{
        background: var(--lbg-green) !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0, 106, 77, 0.15) !important;
    }}

    /* Clean file display */
    [data-testid="stFileUploader"] small {{
        color: #999 !important;
        font-size: 12px !important;
    }}

    /* Clean Step Cards */
    .lbg-step-item {{
        background: transparent;
        padding: 20px 0;
        border-bottom: 1px solid #F0F0F0;
        transition: all 0.2s ease;
    }}

    .lbg-step-item:last-child {{
        border-bottom: none;
    }}

    .lbg-step-item:hover {{
        background: rgba(0, 106, 77, 0.02);
        padding-left: 8px;
    }}

    .lbg-step-icon {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--lbg-green);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        font-size: 14px;
    }}

    /* Typography Hierarchy */
    .lbg-section-title {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        color: #999;
        margin-bottom: 16px;
    }}

    .lbg-card-title {{
        font-size: 20px;
        font-weight: 600;
        color: var(--lbg-charcoal);
        margin: 0 0 8px 0;
    }}

    .lbg-card-subtitle {{
        font-size: 14px;
        color: #666;
        margin: 0 0 24px 0;
        line-height: 1.5;
    }}

    /* Modern Metrics */
    .stMetric {{
        background: white;
        padding: 20px;
        border-radius: var(--lbg-radius-md);
        border: none;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .stMetric [data-testid="metric-container"] > div:first-child {{
        font-size: 12px;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }}

    .stMetric [data-testid="metric-container"] > div:nth-child(2) {{
        font-size: 24px;
        font-weight: 600;
        color: var(--lbg-charcoal);
        margin-top: 4px;
    }}

    /* Custom Scrollbar Styling */
    .lbg-scrollable {{
        scrollbar-width: thin;
        scrollbar-color: #006A4D #F0F0F0;
    }}

    .lbg-scrollable::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    .lbg-scrollable::-webkit-scrollbar-track {{
        background: #F0F0F0;
        border-radius: 4px;
    }}

    .lbg-scrollable::-webkit-scrollbar-thumb {{
        background: #006A4D;
        border-radius: 4px;
        transition: background 0.2s ease;
    }}

    .lbg-scrollable::-webkit-scrollbar-thumb:hover {{
        background: #013826;
    }}

    /* Upload Card Container */
    .lbg-upload-card {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 20px 0;
        border-bottom: 1px solid #F0F0F0;
    }}

    .lbg-upload-card:last-child {{
        border-bottom: none;
    }}

    .lbg-upload-header {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        width: 100%;
    }}

    .lbg-upload-content {{
        flex: 1;
    }}

    .lbg-upload-content h4 {{
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #1C1C1C;
    }}

    .lbg-upload-content p {{
        margin: 4px 0 0;
        color: #666;
        font-size: 14px;
        line-height: 1.5;
    }}

    /* Letter Preview Container */
    .letter-preview-container {{
        background: white;
        border: none;
        border-radius: 12px;
        padding: 24px;
        height: 500px;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 14px;
        line-height: 1.8;
        color: #333;
        white-space: pre-wrap;
        word-wrap: break-word;
        scrollbar-width: thin;
        scrollbar-color: #006A4D #F0F0F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .letter-preview-container::-webkit-scrollbar {{
        width: 8px;
    }}

    .letter-preview-container::-webkit-scrollbar-track {{
        background: #F0F0F0;
        border-radius: 4px;
    }}

    .letter-preview-container::-webkit-scrollbar-thumb {{
        background: #006A4D;
        border-radius: 4px;
    }}

    .letter-preview-container::-webkit-scrollbar-thumb:hover {{
        background: #013826;
    }}

    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


def render_brand_header(title: str, subtitle: str, *, badge: Optional[str] = None, logo: Optional[str] = None) -> None:
    """Render a consistent hero header with optional badge and logo."""
    # New layout: wrapper contains green bar and logo side by side
    elements = ["<div class='lbg-hero-wrapper'>"]

    # Green bar with content
    elements.append("<div class='lbg-hero'>")
    content_segments = ["<div class='lbg-hero-content'>"]

    if badge:
        content_segments.append(
            f"<div class='lbg-pill'>{html.escape(badge)}</div>"
        )

    content_segments.append(f"<h1>{html.escape(title)}</h1>")

    if subtitle:
        content_segments.append(f"<p>{html.escape(subtitle)}</p>")

    content_segments.append('</div>')
    elements.extend(content_segments)
    elements.append('</div>')  # Close green bar

    # Logo on the right, outside green bar
    if logo:
        elements.append(
            "<div class='lbg-hero-logo'>"
            f"<img src='{logo}' alt='Lloyds Banking Group logo'>"
            "</div>"
        )

    elements.append('</div>')  # Close wrapper

    header_html = '\n'.join(elements)
    st.markdown(header_html, unsafe_allow_html=True)

def asset_to_data_uri(name: str, mime: Optional[str] = None) -> Optional[str]:
    """Return a base64 data URI for a branding asset."""
    asset_path = get_brand_asset(name)
    if not asset_path:
        return None

    if mime is None:
        ext = asset_path.suffix.lower()
        mime = {
            '.png': 'image/png',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
        }.get(ext, 'application/octet-stream')

    encoded = base64.b64encode(asset_path.read_bytes()).decode('utf-8')
    return f"data:{mime};base64,{encoded}"


def render_upload_card(title: str, description: str, icon_number: str = "1") -> str:
    """Render a clean upload card component."""
    return f"""
    <div class="lbg-upload-card">
        <div class="lbg-upload-header">
            <div class="lbg-step-icon">{icon_number}</div>
            <div class="lbg-upload-content">
                <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: #1C1C1C;">{html.escape(title)}</h4>
                <p style="margin: 4px 0 0; color: #666; font-size: 14px;">{html.escape(description)}</p>
            </div>
        </div>
    </div>
    """


def render_clean_section(title: str, subtitle: str = "") -> str:
    """Render a clean section header like Lloyds app."""
    return f"""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 20px; font-weight: 600; color: #1C1C1C; margin: 0;">
            {html.escape(title)}
        </h2>
        {f'<p style="font-size: 14px; color: #666; margin: 4px 0 0;">{html.escape(subtitle)}</p>' if subtitle else ''}
    </div>
    """
