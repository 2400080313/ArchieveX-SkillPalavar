"""
ArchiveX - UI Custom Styling & AWS Cloud Aesthetic Theme
"""

CUSTOM_CSS = """
<style>
/* Main typography and headers */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

code, pre {
    font-family: 'JetBrains+Mono', monospace !important;
}

/* Header Banner */
.archivex-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
}

.archivex-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.archivex-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
    margin-top: 6px;
    font-weight: 400;
}

.archivex-badge-demo {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fbbf24;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.archivex-badge-live {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Metric Cards */
.kpi-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    border-color: #3b82f6;
}

.kpi-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
}

.kpi-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #f8fafc;
    margin-top: 4px;
}

.kpi-subtext {
    font-size: 0.8rem;
    color: #10b981;
    margin-top: 4px;
    font-weight: 500;
}

/* Story Pipeline Flow Box */
.story-pipeline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px 20px;
    margin: 16px 0;
    overflow-x: auto;
}

.pipeline-step {
    text-align: center;
    padding: 6px 12px;
    border-radius: 6px;
    background: #1e293b;
    border: 1px solid #475569;
    font-size: 0.72rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.04em;
    white-space: nowrap;
}

.pipeline-arrow {
    color: #64748b;
    font-weight: 800;
    margin: 0 6px;
}

/* Guardrail Banner */
.guardrail-box {
    background: rgba(59, 130, 246, 0.08);
    border-left: 4px solid #3b82f6;
    padding: 14px 18px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
    color: #cbd5e1;
    font-size: 0.9rem;
}

/* Assistant Chat Bubble */
.chat-bot-bubble {
    background: #1e293b;
    border-left: 3px solid #8b5cf6;
    border-radius: 0 8px 8px 8px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #f1f5f9;
}

.chat-user-bubble {
    background: #0f172a;
    border-right: 3px solid #3b82f6;
    border-radius: 8px 0 8px 8px;
    padding: 14px 18px;
    margin: 10px 0;
    text-align: right;
    color: #e2e8f0;
}
</style>
"""

def render_story_pipeline():
    """Renders the hackathon positioning story pipeline."""
    return """
    <div class="story-pipeline">
        <div class="pipeline-step">DATA GENERATION</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">S3 STORAGE</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">OBJECT ANALYSIS</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step" style="border-color:#8b5cf6; color:#c084fc;">ARCHIVE INTELLIGENCE</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step" style="border-color:#3b82f6; color:#60a5fa;">RECOMMENDATION</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step">LIFECYCLE / INT-TIERING</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step" style="border-color:#10b981; color:#34d399;">OPTIMIZED STORAGE</div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step" style="border-color:#f59e0b; color:#fbbf24;">COST VISIBILITY</div>
    </div>
    """
