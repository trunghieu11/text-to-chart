"""
Plotter add-ons package.
"""

from chart_service.plotters.addons.base import PlotAddon
from chart_service.plotters.addons.color_palette import ColorPaletteAddon
from chart_service.plotters.addons.custom_lines import CustomLinesAddon
from chart_service.plotters.addons.layout import LayoutAddon

__all__ = ["PlotAddon", "ColorPaletteAddon", "CustomLinesAddon", "LayoutAddon"]
