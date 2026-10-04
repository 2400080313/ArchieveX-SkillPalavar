"""
ArchiveX UI Package
"""
from ui.dashboard_view import render_dashboard
from ui.explorer_view import render_explorer
from ui.recommendations_view import render_recommendations
from ui.simulator_view import render_simulator
from ui.lifecycle_view import render_lifecycle_builder
from ui.it_view import render_intelligent_tiering
from ui.copilot_view import render_copilot_interface
from ui.settings_view import render_settings
from ui.styles import CUSTOM_CSS

__all__ = [
    "render_dashboard",
    "render_explorer",
    "render_recommendations",
    "render_simulator",
    "render_lifecycle_builder",
    "render_intelligent_tiering",
    "render_copilot_interface",
    "render_settings",
    "CUSTOM_CSS"
]
