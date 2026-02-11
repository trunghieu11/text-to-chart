"""
Plotter registry initialization.

All plotters and add-ons are registered here on import.
"""

from chart_service.plotters.registry import PlotterRegistry
from chart_service.plotters.line_plotter import LinePlotter
from chart_service.plotters.bar_plotter import BarPlotter
from chart_service.plotters.scatter_plotter import ScatterPlotter
from chart_service.plotters.pie_plotter import PiePlotter
from chart_service.plotters.addons.color_palette import ColorPaletteAddon
from chart_service.plotters.addons.custom_lines import CustomLinesAddon
from chart_service.plotters.addons.layout import LayoutAddon

# Create and populate the global plotter registry
plotter_registry = PlotterRegistry()
plotter_registry.register_plotter(LinePlotter())
plotter_registry.register_plotter(BarPlotter())
plotter_registry.register_plotter(ScatterPlotter())
plotter_registry.register_plotter(PiePlotter())

# Register add-ons (applied in order)
plotter_registry.register_addon(ColorPaletteAddon())
plotter_registry.register_addon(CustomLinesAddon())
plotter_registry.register_addon(LayoutAddon())

__all__ = [
    "plotter_registry",
    "PlotterRegistry",
    "LinePlotter",
    "BarPlotter",
    "ScatterPlotter",
    "PiePlotter",
]
