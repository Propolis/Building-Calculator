# -*- coding: utf-8 -*-
"""
Building Calculator QGIS Plugin
"""


def classFactory(iface):
    """Load BuildingCalculator class from file building_calculator.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .building_calculator import BuildingCalculator
    return BuildingCalculator(iface)
