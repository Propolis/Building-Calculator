# -*- coding: utf-8 -*-
"""
Building Calculator - Main Plugin Class
"""

import os
import importlib
import sys
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsWkbTypes
from qgis.utils import reloadPlugin

from .settings_dialog import SettingsDialog
from .calculation_dialog import CalculationDialog


class BuildingCalculator:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'Building Calculator'
        self.toolbar = self.iface.addToolBar('Building Calculator')
        self.toolbar.setObjectName('BuildingCalculator')
        
        # Settings
        self.settings = QSettings()
        
    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('BuildingCalculator', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        
        # Main action - calculate
        self.add_action(
            icon_path,
            text=self.tr('Calculate Building'),
            callback=self.run_calculation,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Calculate residents and parking for selected building')
        )
        
        # Settings action
        self.add_action(
            icon_path,
            text=self.tr('Settings'),
            callback=self.run_settings,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            status_tip=self.tr('Configure calculation parameters')
        )
        
        # Reload action
        self.add_action(
            icon_path,
            text=self.tr('Reload Plugin'),
            callback=self.reload_plugin,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            status_tip=self.tr('Reload the plugin without restarting QGIS')
        )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def get_selected_polygon(self):
        """Get the currently selected polygon feature."""
        layer = self.iface.activeLayer()
        
        if layer is None:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('No Layer Selected'),
                self.tr('Please select a vector layer with polygons.')
            )
            return None
            
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Wrong Layer Type'),
                self.tr('Please select a polygon layer.')
            )
            return None
            
        selected_features = layer.selectedFeatures()
        
        if len(selected_features) == 0:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('No Selection'),
                self.tr('Please select a polygon feature on the map.')
            )
            return None
            
        if len(selected_features) > 1:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Multiple Selection'),
                self.tr('Please select only one polygon.')
            )
            return None
            
        return selected_features[0]

    def run_calculation(self):
        """Run the calculation dialog."""
        feature = self.get_selected_polygon()
        if feature is None:
            return
            
        geometry = feature.geometry()
        area = geometry.area()
        
        # Get CRS to check if we need to convert area
        layer = self.iface.activeLayer()
        crs = layer.crs()
        
        # If CRS is geographic (degrees), we need to calculate area differently
        if crs.isGeographic():
            # Use ellipsoidal calculation
            from qgis.core import QgsDistanceArea
            da = QgsDistanceArea()
            da.setSourceCrs(crs, QgsProject.instance().transformContext())
            da.setEllipsoid(QgsProject.instance().ellipsoid())
            area = da.measureArea(geometry)
        
        dialog = CalculationDialog(self.iface.mainWindow(), area, self.settings)
        dialog.exec_()

    def run_settings(self):
        """Run the settings dialog."""
        dialog = SettingsDialog(self.iface.mainWindow(), self.settings)
        dialog.exec_()
    
    def reload_plugin(self):
        """Reload the plugin without restarting QGIS."""
        reloadPlugin('building_calculator')
