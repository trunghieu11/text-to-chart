"""
Chart type registry initialization.

All chart types are registered here on import.
"""

from chart_service.chart_types.registry import ChartTypeRegistry
from chart_service.chart_types.line_chart import LineChartType
from chart_service.chart_types.bar_chart import BarChartType
from chart_service.chart_types.scatter_chart import ScatterChartType
from chart_service.chart_types.pie_chart import PieChartType

# Create and populate the global chart type registry
chart_type_registry = ChartTypeRegistry()
chart_type_registry.register(LineChartType())
chart_type_registry.register(BarChartType())
chart_type_registry.register(ScatterChartType())
chart_type_registry.register(PieChartType())

__all__ = [
    "chart_type_registry",
    "ChartTypeRegistry",
    "LineChartType",
    "BarChartType",
    "ScatterChartType",
    "PieChartType",
]
