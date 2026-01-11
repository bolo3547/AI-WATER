"""
AquaWatch Calm - National Water Intelligence Dashboard
========================================================

Design Philosophy:
- Calm and confidence, not alarms
- Water-first aesthetics (flow, balance, stability)
- Decision-focused, not data-heavy
- Suitable for engineers, managers, and government officials
- National-grade, not student-grade

Color Palette:
- Primary blue: #1E88E5
- Soft aqua accent: #4DD0E1
- Background: #F7FAFC
- Text primary: #2D3748
- Text secondary: #4A5568
- Status: Normal #43A047, Warning #F9A825, Leak #E53935
"""

import dash
from dash import html, dcc, callback, Input, Output, State
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import os

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        "/assets/aquawatch_calm.css",
    ],
    external_scripts=[
        "/assets/suppress_aborterror.js",
    ],
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
    suppress_callback_exceptions=True,
    title="AquaWatch | Water Intelligence",
    update_title=None,
)

# =============================================================================
# CALM WATER-INSPIRED STYLES
# =============================================================================

CALM_STYLES = """
/* ============================================
   AQUAWATCH CALM - WATER INTELLIGENCE UI
   Calm • Professional • Trustworthy
   World-Class Design for National Utilities
   ============================================ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    /* Primary Water Palette */
    --primary: #1E88E5;
    --primary-light: #64B5F6;
    --primary-dark: #1565C0;
    --primary-gradient: linear-gradient(135deg, #1E88E5 0%, #4DD0E1 100%);
    
    /* Aqua Accents */
    --aqua: #4DD0E1;
    --aqua-light: #80DEEA;
    --aqua-glow: rgba(77, 208, 225, 0.15);
    
    /* Backgrounds */
    --bg-main: #F7FAFC;
    --bg-card: #FFFFFF;
    --bg-subtle: #EDF2F7;
    --bg-hover: #F0F4F8;
    --bg-glass: rgba(255, 255, 255, 0.85);
    
    /* Typography */
    --text-primary: #2D3748;
    --text-secondary: #4A5568;
    --text-muted: #718096;
    --text-light: #A0AEC0;
    
    /* Borders */
    --border: #E2E8F0;
    --border-light: #EDF2F7;
    --border-focus: #1E88E5;
    
    /* Status Colors - Muted & Professional */
    --status-normal: #43A047;
    --status-normal-bg: rgba(67, 160, 71, 0.08);
    --status-warning: #F9A825;
    --status-warning-bg: rgba(249, 168, 37, 0.08);
    --status-leak: #E53935;
    --status-leak-bg: rgba(229, 57, 53, 0.08);
    
    /* Shadows - Soft & Layered */
    --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.04), 0 2px 4px rgba(0, 0, 0, 0.03);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.06), 0 4px 6px rgba(0, 0, 0, 0.04);
    --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.08), 0 10px 10px rgba(0, 0, 0, 0.04);
    --shadow-glow: 0 0 20px rgba(30, 136, 229, 0.15);
    --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
    
    /* Border Radius */
    --radius-xs: 4px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-full: 9999px;
    
    /* Transitions */
    --transition-fast: 0.15s ease;
    --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-spring: 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Reset & Base */
*, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body, html {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-main);
    color: var(--text-primary);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    line-height: 1.6;
    font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
}

/* Subtle Water Pattern Background */
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(ellipse at 20% 80%, rgba(77, 208, 225, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(30, 136, 229, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(100, 181, 246, 0.02) 0%, transparent 70%);
    pointer-events: none;
    z-index: -1;
}

/* Hide all debug/dev tools */
._dash-loading, ._dash-error, .dash-debug-menu,
[class*="dash-debug"], .dash-error-card, ._dash-undo-redo,
.modebar, .plotly-notifier, .js-plotly-plot .plotly .modebar,
.dash-debug-alert, ._dash-debug-menu, #_dash-global-error-container {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}

/* Selection Styling */
::selection {
    background: rgba(30, 136, 229, 0.2);
    color: var(--text-primary);
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-subtle);
    border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: var(--radius-full);
    border: 2px solid var(--bg-subtle);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* ============================================
   TOP BAR - Premium Glass Effect
   ============================================ */

.top-bar {
    background: var(--bg-glass);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    padding: 14px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.02);
}

.brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.brand-icon {
    width: 42px;
    height: 42px;
    background: var(--primary-gradient);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: white;
    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.25), 0 2px 4px rgba(30, 136, 229, 0.15);
    position: relative;
    overflow: hidden;
}

.brand-icon::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.15) 50%, transparent 60%);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%) rotate(45deg); }
    100% { transform: translateX(100%) rotate(45deg); }
}

.brand-text {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.4px;
}

.brand-subtitle {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 500;
    letter-spacing: 0.2px;
    margin-top: 1px;
}

.location-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--bg-subtle);
    padding: 10px 18px;
    border-radius: var(--radius-full);
    font-size: 13px;
    color: var(--text-secondary);
    border: 1px solid transparent;
    transition: var(--transition);
    cursor: pointer;
}

.location-selector:hover {
    background: var(--bg-hover);
    border-color: var(--border);
}

.location-selector i {
    color: var(--primary);
    font-size: 12px;
}

.location-divider {
    color: var(--text-light);
    font-size: 11px;
}

.datetime {
    text-align: right;
}

.date-text {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 500;
}

.time-text {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.5px;
}

/* ============================================
   MAIN CONTAINER
   ============================================ */

.main-container {
    max-width: 1440px;
    margin: 0 auto;
    padding: 28px 40px 60px;
}

/* ============================================
   SECTION 1: STATUS OVERVIEW
   ============================================ */

.status-section {
    margin-bottom: 32px;
}

.section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--text-muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-label::before {
    content: '';
    width: 3px;
    height: 12px;
    background: var(--primary-gradient);
    border-radius: 2px;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}

.status-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: 22px 26px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-light);
    transition: all var(--transition);
    position: relative;
    overflow: hidden;
}

.status-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--border-light);
    transition: var(--transition);
}

.status-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px);
    border-color: var(--border);
}

.status-card:hover::before {
    background: var(--primary-gradient);
}

.status-card.primary {
    border-left: none;
}

.status-card.primary::before {
    background: var(--status-normal);
}

.status-card.primary.warning::before {
    background: var(--status-warning);
}

.status-card.primary.leak::before {
    background: var(--status-leak);
}

.status-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
}

.status-icon {
    width: 44px;
    height: 44px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    transition: var(--transition);
}

.status-card:hover .status-icon {
    transform: scale(1.05);
}

.status-icon.normal {
    background: var(--status-normal-bg);
    color: var(--status-normal);
}

.status-icon.warning {
    background: var(--status-warning-bg);
    color: var(--status-warning);
}

.status-icon.leak {
    background: var(--status-leak-bg);
    color: var(--status-leak);
}

.status-icon.info {
    background: rgba(30, 136, 229, 0.08);
    color: var(--primary);
}

.status-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

.status-badge.normal {
    background: var(--status-normal-bg);
    color: var(--status-normal);
}

.status-badge.warning {
    background: var(--status-warning-bg);
    color: var(--status-warning);
    animation: gentle-pulse 2s ease-in-out infinite;
}

.status-badge.leak {
    background: var(--status-leak-bg);
    color: var(--status-leak);
}

@keyframes gentle-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.status-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
    letter-spacing: -1px;
    line-height: 1.1;
}

.status-label {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 500;
}

.status-sublabel {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-sublabel::before {
    content: '';
    width: 6px;
    height: 6px;
    background: var(--status-normal);
    border-radius: 50%;
    animation: status-dot 2s ease-in-out infinite;
}

@keyframes status-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}

/* ============================================
   SECTION 2: WATER INTELLIGENCE
   ============================================ */

.intelligence-section {
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 24px;
    margin-bottom: 32px;
}

.chart-card {
    background: var(--bg-card);
    border-radius: var(--radius-xl);
    padding: 28px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-light);
    transition: var(--transition);
}

.chart-card:hover {
    box-shadow: var(--shadow-lg);
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
}

.chart-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.3px;
}

.chart-subtitle {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
}

.chart-period {
    display: flex;
    gap: 4px;
    background: var(--bg-subtle);
    padding: 4px;
    border-radius: var(--radius-sm);
}

.period-btn {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
    border: none;
    background: transparent;
    color: var(--text-muted);
    border-radius: 6px;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: inherit;
}

.period-btn:hover {
    color: var(--text-primary);
    background: var(--bg-hover);
}

.period-btn.active {
    background: var(--bg-card);
    color: var(--primary);
    box-shadow: var(--shadow-sm);
    font-weight: 600;
}

/* ============================================
   LEAK PROBABILITY INDICATOR
   ============================================ */

.probability-card {
    background: var(--bg-card);
    border-radius: var(--radius-xl);
    padding: 28px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-light);
    text-align: center;
    transition: var(--transition);
}

.probability-card:hover {
    box-shadow: var(--shadow-lg);
}

.probability-ring {
    position: relative;
    width: 160px;
    height: 160px;
    margin: 8px auto 24px;
}

.probability-value {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
}

.probability-number {
    font-size: 38px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    letter-spacing: -1px;
}

.probability-label {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}

.probability-details {
    text-align: left;
    padding-top: 20px;
    border-top: 1px solid var(--border-light);
}

.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--bg-subtle);
    transition: var(--transition-fast);
}

.detail-row:hover {
    padding-left: 8px;
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    font-size: 13px;
    color: var(--text-muted);
}

.detail-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
}

.detail-value.category {
    color: var(--status-warning);
    background: var(--status-warning-bg);
    padding: 4px 10px;
    border-radius: var(--radius-full);
    font-size: 12px;
}

/* ============================================
   SECTION 3: DECISION PANEL
   ============================================ */

.decision-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

.decision-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: 24px 28px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-light);
    transition: all var(--transition);
    position: relative;
}

.decision-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.decision-card.highlight {
    border: 2px solid var(--primary);
    background: linear-gradient(135deg, rgba(30, 136, 229, 0.02) 0%, rgba(77, 208, 225, 0.02) 100%);
}

.decision-card.highlight::before {
    content: 'Recommended';
    position: absolute;
    top: -10px;
    right: 16px;
    background: var(--primary-gradient);
    color: white;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
}

.decision-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
}

.decision-icon {
    width: 42px;
    height: 42px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    transition: var(--transition);
}

.decision-card:hover .decision-icon {
    transform: scale(1.08);
}

.decision-icon.priority-high {
    background: var(--status-leak-bg);
    color: var(--status-leak);
}

.decision-icon.priority-medium {
    background: var(--status-warning-bg);
    color: var(--status-warning);
}

.decision-icon.priority-low {
    background: var(--status-normal-bg);
    color: var(--status-normal);
}

.decision-icon.action {
    background: rgba(30, 136, 229, 0.08);
    color: var(--primary);
}

.decision-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
}

.decision-subtitle {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 2px;
}

.decision-content {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 10px;
    letter-spacing: -0.5px;
}

.decision-description {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.6;
}

.action-button {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-top: 20px;
    padding: 12px 24px;
    background: var(--primary-gradient);
    color: white;
    border: none;
    border-radius: var(--radius-sm);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition);
    font-family: inherit;
    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.25);
}

.action-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(30, 136, 229, 0.35);
}

.action-button:active {
    transform: translateY(0);
}

/* ============================================
   DMA LIST - Interactive Cards
   ============================================ */

.dma-section {
    margin-top: 32px;
}

.dma-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}

.dma-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: 18px 22px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: all var(--transition);
    position: relative;
    overflow: hidden;
}

.dma-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--status-normal);
    opacity: 0;
    transition: var(--transition);
}

.dma-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateX(4px);
    border-color: var(--primary-light);
}

.dma-card:hover::before {
    opacity: 1;
}

.dma-card.warning::before {
    background: var(--status-warning);
}

.dma-info {
    display: flex;
    align-items: center;
    gap: 14px;
}

.dma-status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    position: relative;
}

.dma-status-dot::after {
    content: '';
    position: absolute;
    top: -3px;
    left: -3px;
    right: -3px;
    bottom: -3px;
    border-radius: 50%;
    animation: ripple 2s ease-out infinite;
}

@keyframes ripple {
    0% { box-shadow: 0 0 0 0 currentColor; opacity: 0.4; }
    100% { box-shadow: 0 0 0 8px currentColor; opacity: 0; }
}

.dma-status-dot.normal {
    background: var(--status-normal);
    color: var(--status-normal);
}

.dma-status-dot.warning {
    background: var(--status-warning);
    color: var(--status-warning);
}

.dma-status-dot.leak {
    background: var(--status-leak);
    color: var(--status-leak);
}

.dma-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.2px;
}

.dma-location {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
}

.dma-metrics {
    text-align: right;
    padding-left: 16px;
}

.dma-nrw {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
}

.dma-label {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}

/* ============================================
   MODAL - Premium Styling
   ============================================ */

.modal-content {
    border-radius: var(--radius-xl) !important;
    border: none !important;
    box-shadow: var(--shadow-xl) !important;
    overflow: hidden;
}

.modal-backdrop {
    background: rgba(45, 55, 72, 0.4) !important;
    backdrop-filter: blur(4px);
}

.modal-header {
    border-bottom: 1px solid var(--border-light) !important;
    padding: 24px 28px !important;
    background: var(--bg-subtle);
}

.modal-title {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.3px;
}

.modal-body {
    padding: 28px !important;
}

.modal-footer {
    border-top: 1px solid var(--border-light) !important;
    padding: 16px 28px !important;
    background: var(--bg-subtle);
}

.btn-close {
    opacity: 0.5;
    transition: var(--transition-fast);
}

.btn-close:hover {
    opacity: 1;
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */

@media (max-width: 1200px) {
    .intelligence-section {
        grid-template-columns: 1fr;
    }
    
    .decision-section {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .probability-card {
        max-width: 400px;
        margin: 0 auto;
    }
}

@media (max-width: 992px) {
    .status-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .decision-section {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .top-bar {
        padding: 12px 20px;
        flex-wrap: wrap;
        gap: 12px;
    }
    
    .main-container {
        padding: 20px;
    }
    
    .status-grid {
        grid-template-columns: 1fr;
    }
    
    .dma-grid {
        grid-template-columns: 1fr;
    }
    
    .status-value {
        font-size: 26px;
    }
    
    .decision-content {
        font-size: 18px;
    }
}

@media (max-width: 480px) {
    .location-selector {
        display: none;
    }
    
    .top-bar {
        padding: 12px 16px;
    }
    
    .main-container {
        padding: 16px;
    }
    
    .status-card,
    .chart-card,
    .probability-card,
    .decision-card,
    .dma-card {
        padding: 16px;
    }
}

/* ============================================
   PRINT STYLES
   ============================================ */

@media print {
    .top-bar {
        position: static;
    }
    
    .status-card:hover,
    .decision-card:hover,
    .dma-card:hover {
        transform: none;
        box-shadow: var(--shadow-card);
    }
    
    body::before {
        display: none;
    }
}
"""

# =============================================================================
# DATA
# =============================================================================

# Generate smooth pressure data
def generate_pressure_data():
    hours = 24
    times = pd.date_range(end=datetime.now(), periods=hours*4, freq='15min')
    
    # Smooth sinusoidal patterns with slight noise
    base_p1 = 45
    base_p2 = 42
    
    p1_values = [base_p1 + 3*np.sin(i/16*np.pi) + np.random.normal(0, 0.3) for i in range(len(times))]
    p2_values = [base_p2 + 2.5*np.sin(i/16*np.pi + 0.5) + np.random.normal(0, 0.3) for i in range(len(times))]
    
    # Introduce a subtle anomaly in the last few hours
    for i in range(-12, 0):
        p2_values[i] -= 1.5 + np.random.normal(0, 0.2)
    
    return times, p1_values, p2_values

DMA_DATA = [
    {
        "name": "Lusaka Central", "location": "Zone A", "nrw": 28,
        "status": "normal", "leak": False, "leak_volume": "~5 m³/day",
        "pipes": [
            {"name": "Pipe A1", "status": "normal", "note": "Stable pressure"},
            {"name": "Pipe A2", "status": "normal", "note": "No issues"},
        ],
    },
    {
        "name": "Lusaka East", "location": "Zone B", "nrw": 35,
        "status": "warning", "leak": True, "leak_volume": "~22 m³/day",
        "pipes": [
            {"name": "Pipe B1", "status": "leak", "note": "Pressure drop detected"},
            {"name": "Pipe B2", "status": "warning", "note": "Monitor nightly minima"},
        ],
    },
    {
        "name": "Kitwe Industrial", "location": "Copperbelt", "nrw": 42,
        "status": "warning", "leak": True, "leak_volume": "~45 m³/day",
        "pipes": [
            {"name": "Pipe K1", "status": "leak", "note": "Suspected real loss"},
            {"name": "Pipe K2", "status": "warning", "note": "Flow imbalance"},
        ],
    },
    {
        "name": "Ndola CBD", "location": "Central", "nrw": 24,
        "status": "normal", "leak": False, "leak_volume": "~4 m³/day",
        "pipes": [
            {"name": "Pipe N1", "status": "normal", "note": "Balanced"},
            {"name": "Pipe N2", "status": "normal", "note": "Balanced"},
        ],
    },
    {
        "name": "Johannesburg North", "location": "Gauteng", "nrw": 31,
        "status": "normal", "leak": False, "leak_volume": "~9 m³/day",
        "pipes": [
            {"name": "Pipe J1", "status": "warning", "note": "Night flow slightly elevated"},
            {"name": "Pipe J2", "status": "normal", "note": "Stable"},
        ],
    },
    {
        "name": "Cape Town Metro", "location": "Western Cape", "nrw": 22,
        "status": "normal", "leak": False, "leak_volume": "~6 m³/day",
        "pipes": [
            {"name": "Pipe C1", "status": "normal", "note": "Stable"},
            {"name": "Pipe C2", "status": "normal", "note": "Stable"},
        ],
    },
    {
        "name": "Durban South", "location": "KwaZulu-Natal", "nrw": 37,
        "status": "warning", "leak": True, "leak_volume": "~18 m³/day",
        "pipes": [
            {"name": "Pipe D1", "status": "leak", "note": "Chlorine residual dip"},
            {"name": "Pipe D2", "status": "warning", "note": "Pressure fluctuation"},
        ],
    },
    {
        "name": "Port Elizabeth", "location": "Eastern Cape", "nrw": 29,
        "status": "normal", "leak": False, "leak_volume": "~7 m³/day",
        "pipes": [
            {"name": "Pipe P1", "status": "normal", "note": "Stable"},
            {"name": "Pipe P2", "status": "normal", "note": "Stable"},
        ],
    },
    {
        "name": "Gaborone", "location": "Botswana", "nrw": 33,
        "status": "warning", "leak": True, "leak_volume": "~15 m³/day",
        "pipes": [
            {"name": "Pipe G1", "status": "leak", "note": "High night flow"},
            {"name": "Pipe G2", "status": "warning", "note": "Investigate service connections"},
        ],
    },
    {
        "name": "Harare Central", "location": "Zimbabwe", "nrw": 36,
        "status": "warning", "leak": True, "leak_volume": "~20 m³/day",
        "pipes": [
            {"name": "Pipe H1", "status": "leak", "note": "Burst risk suspected"},
            {"name": "Pipe H2", "status": "warning", "note": "Pressure delta rising"},
        ],
    },
]

# =============================================================================
# CHARTS
# =============================================================================

def create_pressure_chart():
    times, p1, p2 = generate_pressure_data()
    delta_p = [a - b for a, b in zip(p1, p2)]
    
    fig = go.Figure()
    
    # Sensor P1
    fig.add_trace(go.Scatter(
        x=times, y=p1,
        name='Sensor P1',
        line=dict(color='#1E88E5', width=2.5),
        mode='lines',
        hovertemplate='<b>Sensor P1</b><br>%{x|%H:%M}<br>%{y:.1f} bar<extra></extra>'
    ))
    
    # Sensor P2
    fig.add_trace(go.Scatter(
        x=times, y=p2,
        name='Sensor P2',
        line=dict(color='#4DD0E1', width=2.5),
        mode='lines',
        hovertemplate='<b>Sensor P2</b><br>%{x|%H:%M}<br>%{y:.1f} bar<extra></extra>'
    ))
    
    # Delta P (subtle fill)
    fig.add_trace(go.Scatter(
        x=times, y=delta_p,
        name='Pressure Difference (ΔP)',
        line=dict(color='#F9A825', width=1.5, dash='dot'),
        mode='lines',
        opacity=0.7,
        hovertemplate='<b>ΔP</b><br>%{x|%H:%M}<br>%{y:.2f} bar<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        font=dict(family='Inter', color='#4A5568', size=11),
        xaxis=dict(
            gridcolor='#E2E8F0',
            linecolor='#E2E8F0',
            tickformat='%H:%M',
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            gridcolor='#E2E8F0',
            linecolor='#E2E8F0',
            title=dict(text='Pressure (bar)', font=dict(size=12, color='#718096')),
            showgrid=True,
            gridwidth=1,
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#E2E8F0',
            font_size=12,
            font_family='Inter'
        ),
        hovermode='x unified'
    )
    
    return fig

def create_probability_gauge(probability=72):
    """Create a circular probability gauge."""
    fig = go.Figure()
    
    # Determine color based on probability
    if probability < 40:
        color = '#43A047'
    elif probability < 70:
        color = '#F9A825'
    else:
        color = '#E53935'
    
    fig.add_trace(go.Pie(
        values=[probability, 100 - probability],
        hole=0.75,
        marker=dict(colors=[color, '#EDF2F7']),
        textinfo='none',
        hoverinfo='none',
        direction='clockwise',
        sort=False
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        height=160,
        width=160,
        showlegend=False,
        annotations=[
            dict(
                text=f'<b>{probability}%</b>',
                x=0.5, y=0.55,
                font=dict(size=28, color='#2D3748', family='Inter'),
                showarrow=False
            ),
            dict(
                text='Probability',
                x=0.5, y=0.35,
                font=dict(size=11, color='#718096', family='Inter'),
                showarrow=False
            )
        ]
    )
    
    return fig

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_top_bar():
    return html.Div([
        # Brand
        html.Div([
            html.Div("💧", className="brand-icon"),
            html.Div([
                html.Div("AquaWatch", className="brand-text"),
                html.Div("Water Intelligence Platform", className="brand-subtitle"),
            ]),
        ], className="brand"),
        
        # Location Selector
        html.Div([
            html.I(className="fas fa-map-marker-alt"),
            html.Span("Zambia"),
            html.Span("›", className="location-divider"),
            html.Span("Lusaka"),
            html.Span("›", className="location-divider"),
            html.Span("DMA-LSK-002", style={"fontWeight": "500", "color": "#2D3748"}),
        ], className="location-selector"),
        
        # Date/Time
        html.Div([
            html.Div(datetime.now().strftime("%A, %d %B %Y"), className="date-text"),
            html.Div(id="live-time", className="time-text"),
        ], className="datetime"),
    ], className="top-bar")


def create_status_section():
    return html.Div([
        html.Div("System Status", className="section-label"),
        html.Div([
            # Overall Status
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-shield-alt"),
                    ], className="status-icon warning"),
                    html.Span("Monitoring", className="status-badge warning"),
                ], className="status-card-header"),
                html.Div("Unusual Behavior", className="status-value"),
                html.Div("System Status", className="status-label"),
                html.Div("Pressure instability detected", className="status-sublabel"),
            ], className="status-card primary warning"),
            
            # Active DMAs
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-broadcast-tower"),
                    ], className="status-icon info"),
                ], className="status-card-header"),
                html.Div("6", className="status-value"),
                html.Div("Active DMAs", className="status-label"),
                html.Div("All sensors online", className="status-sublabel"),
            ], className="status-card"),
            
            # Priority Alerts
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-exclamation-circle"),
                    ], className="status-icon warning"),
                ], className="status-card-header"),
                html.Div("2", className="status-value"),
                html.Div("Priority Alerts", className="status-label"),
                html.Div("Requires attention", className="status-sublabel"),
            ], className="status-card"),
            
            # Last Update
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-clock"),
                    ], className="status-icon normal"),
                ], className="status-card-header"),
                html.Div("Just now", className="status-value"),
                html.Div("Last Data Update", className="status-label"),
                html.Div("Real-time monitoring active", className="status-sublabel"),
            ], className="status-card"),
        ], className="status-grid"),
    ], className="status-section")


def create_intelligence_section():
    return html.Div([
        html.Div("Water Intelligence", className="section-label"),
        html.Div([
            # Pressure Chart
            html.Div([
                html.Div([
                    html.Div([
                        html.Div("Pressure Over Time", className="chart-title"),
                        html.Div("24-hour pressure monitoring for segment P1 – P2", className="chart-subtitle"),
                    ]),
                    html.Div([
                        html.Button("6H", className="period-btn"),
                        html.Button("12H", className="period-btn"),
                        html.Button("24H", className="period-btn active"),
                        html.Button("7D", className="period-btn"),
                    ], className="chart-period"),
                ], className="chart-header"),
                dcc.Graph(
                    figure=create_pressure_chart(),
                    config={
                        "displayModeBar": False,
                        "staticPlot": False,
                        "responsive": True
                    },
                    style={"height": "280px"},
                    animate=False
                ),
            ], className="chart-card"),
            
            # Probability Card
            html.Div([
                html.Div([
                    html.Div("Leak Probability", className="chart-title"),
                    html.Div("AI confidence assessment", className="chart-subtitle"),
                ], className="chart-header"),
                html.Div([
                    dcc.Graph(
                        figure=create_probability_gauge(72),
                        config={
                            "displayModeBar": False,
                            "staticPlot": True
                        },
                        style={"height": "160px", "margin": "0 auto"},
                        animate=False
                    ),
                ], className="probability-ring"),
                html.Div([
                    html.Div([
                        html.Span("Category", className="detail-label"),
                        html.Span("Real Loss (Leakage)", className="detail-value category"),
                    ], className="detail-row"),
                    html.Div([
                        html.Span("Affected Segment", className="detail-label"),
                        html.Span("P1 – P2", className="detail-value"),
                    ], className="detail-row"),
                    html.Div([
                        html.Span("Est. Volume Loss", className="detail-label"),
                        html.Span("~45 m³/day", className="detail-value"),
                    ], className="detail-row"),
                ], className="probability-details"),
            ], className="probability-card"),
        ], className="intelligence-section"),
    ])


def create_decision_section():
    return html.Div([
        html.Div("Recommended Actions", className="section-label"),
        html.Div([
            # Priority Level
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-flag"),
                    ], className="decision-icon priority-medium"),
                    html.Div([
                        html.Div("Priority Level", className="decision-title"),
                        html.Div("Based on leak probability", className="decision-subtitle"),
                    ]),
                ], className="decision-header"),
                html.Div("Medium", className="decision-content"),
                html.Div("Unusual pressure behavior detected. Recommend inspection within 24-48 hours.", className="decision-description"),
            ], className="decision-card"),
            
            # Suggested Action
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-tools"),
                    ], className="decision-icon action"),
                    html.Div([
                        html.Div("Suggested Action", className="decision-title"),
                        html.Div("Primary recommendation", className="decision-subtitle"),
                    ]),
                ], className="decision-header"),
                html.Div("Inspect Segment", className="decision-content"),
                html.Div("Deploy field team to visually inspect pipe segment P1 – P2 for signs of leakage.", className="decision-description"),
                html.Button([
                    html.I(className="fas fa-clipboard-check"),
                    html.Span("Create Work Order"),
                ], className="action-button"),
            ], className="decision-card highlight"),
            
            # Secondary Action
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-line"),
                    ], className="decision-icon priority-low"),
                    html.Div([
                        html.Div("Continue Monitoring", className="decision-title"),
                        html.Div("Secondary recommendation", className="decision-subtitle"),
                    ]),
                ], className="decision-header"),
                html.Div("Pressure Review", className="decision-content"),
                html.Div("If inspection is delayed, continue monitoring pressure patterns for 24 hours to confirm anomaly.", className="decision-description"),
            ], className="decision-card"),
        ], className="decision-section"),
    ])


def create_dma_section():
    dma_cards = []
    for i, dma in enumerate(DMA_DATA):
        dma_cards.append(
            html.Div([
                html.Div([
                    html.Div(className=f"dma-status-dot {dma['status']}"),
                    html.Div([
                        html.Div(dma["name"], className="dma-name"),
                        html.Div(dma["location"], className="dma-location"),
                    ]),
                ], className="dma-info"),
                html.Div([
                    html.Div(f"{dma['nrw']}%", className="dma-nrw"),
                    html.Div("NRW", className="dma-label"),
                ], className="dma-metrics"),
            ], className="dma-card", id={"type": "dma-card", "index": i})
        )
    
    return html.Div([
        html.Div("District Metered Areas", className="section-label"),
        html.Div(dma_cards, className="dma-grid"),
    ], className="dma-section")


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    # Explicit asset includes to ensure styles/scripts load
    html.Link(rel="stylesheet", href="/assets/aquawatch_calm.css"),
    html.Script(src="/assets/suppress_aborterror.js"),
    # External Font Awesome
    html.Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
    
    # Top Bar
    create_top_bar(),
    
    # Main Container
    html.Div([
        create_status_section(),
        create_intelligence_section(),
        create_decision_section(),
        create_dma_section(),
    ], className="main-container"),
    
    # Modal for DMA details
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="btn btn-secondary")
        ),
    ], id="dma-modal", is_open=False, size="lg"),
    
    # Live time update
    dcc.Interval(id="time-interval", interval=1000, n_intervals=0),
])

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output("live-time", "children"),
    Input("time-interval", "n_intervals")
)
def update_time(n):
    return datetime.now().strftime("%H:%M:%S")


@app.callback(
    [Output("dma-modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-body", "children")],
    [Input({"type": "dma-card", "index": ALL}, "n_clicks"),
     Input("close-modal", "n_clicks")],
    [State("dma-modal", "is_open")]
)
def toggle_dma_modal(dma_clicks, close_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", ""
    
    trigger = ctx.triggered[0]["prop_id"]
    
    if "close-modal" in trigger:
        return False, "", ""
    
    if "dma-card" in trigger:
        # Find which card was clicked
        for i, clicks in enumerate(dma_clicks):
            if clicks:
                dma = DMA_DATA[i]
                status_color = {"normal": "#43A047", "warning": "#F9A825", "leak": "#E53935"}
                leak_label = "Leakage suspected" if dma.get("leak") else "No active leakage"
                leak_color = "#E53935" if dma.get("leak") else "#2D3748"
                
                body = html.Div([
                    html.Div([
                        html.Div([
                            html.Span("Status", style={"color": "#718096", "fontSize": "13px"}),
                            html.Div(dma["status"].capitalize(), style={
                                "fontSize": "18px", "fontWeight": "600",
                                "color": status_color.get(dma["status"], "#2D3748")
                            }),
                        ], style={"marginBottom": "16px"}),
                        html.Div([
                            html.Span("Non-Revenue Water", style={"color": "#718096", "fontSize": "13px"}),
                            html.Div(f"{dma['nrw']}%", style={
                                "fontSize": "28px", "fontWeight": "700", "color": "#2D3748"
                            }),
                        ], style={"marginBottom": "16px"}),
                        html.Div([
                            html.Span("Leakage", style={"color": "#718096", "fontSize": "13px"}),
                            html.Div([
                                html.Span(leak_label, style={
                                    "fontSize": "16px", "fontWeight": "600", "color": leak_color
                                }),
                                html.Span(
                                    f" | Est. loss {dma.get('leak_volume', 'N/A')}",
                                    style={"color": "#4A5568", "fontSize": "13px", "marginLeft": "6px"}
                                ),
                            ]),
                        ], style={"marginBottom": "16px"}),
                        html.Div([
                            html.Span("Location", style={"color": "#718096", "fontSize": "13px"}),
                            html.Div(dma["location"], style={
                                "fontSize": "16px", "fontWeight": "500", "color": "#2D3748"
                            }),
                        ]),
                    ], style={"padding": "8px 0"}),
                    html.Hr(style={"margin": "16px 0", "borderColor": "#E2E8F0"}),
                    html.Div("Pipe Status", style={"fontSize": "13px", "letterSpacing": "0.5px", "textTransform": "uppercase", "color": "#718096", "marginBottom": "10px"}),
                    html.Div([
                        html.Div([
                            html.Div(pipe.get("name", "Pipe"), style={"fontWeight": "600", "color": "#2D3748"}),
                            html.Div(pipe.get("note", ""), style={"color": "#718096", "fontSize": "12px"}),
                        ]),
                        html.Div(pipe.get("status", "" ).capitalize(), style={
                            "fontSize": "12px",
                            "fontWeight": "600",
                            "color": "#E53935" if pipe.get("status") == "leak" else ("#F9A825" if pipe.get("status") == "warning" else "#43A047"),
                        }),
                    ], style={
                        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                        "padding": "10px 0", "borderBottom": "1px solid #E2E8F0"
                    })
                    for pipe in dma.get("pipes", [])
                    ], style={"marginBottom": "10px"}),
                    html.Hr(style={"margin": "20px 0", "borderColor": "#E2E8F0"}),
                    html.P("Detailed analytics, historical trends, and sensor data for this DMA will be displayed here.", 
                           style={"color": "#4A5568", "fontSize": "14px"}),
                ])
                
                return True, f"{dma['name']} - {dma['location']}", body
    
    return is_open, dash.no_update, dash.no_update


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💧 AQUAWATCH CALM - Water Intelligence Dashboard")
    print("="*60)
    print(f"Assets folder: {app.config.get('assets_folder')}")
    print(f"Assets URL path: {app.config.get('assets_url_path')}")
    try:
        import os
        if os.path.isdir(app.config.get('assets_folder', '')):
            files = [f for f in os.listdir(app.config['assets_folder']) if not f.startswith('.')]
            print(f"Assets files: {files}")
        else:
            print("Assets folder not found on disk")
    except Exception as e:
        print(f"Assets scan failed: {e}")
    print("\n✨ Dashboard: http://127.0.0.1:8050")
    print("🎨 Design: Calm • Professional • Trustworthy")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=False, port=8050)
