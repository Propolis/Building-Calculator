# -*- coding: utf-8 -*-
"""
Calculation Dialog for Building Calculator
"""

import json
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QPushButton, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from .settings_dialog import SettingsDialog


class CalculationDialog(QDialog):
    """Dialog for calculating building statistics."""
    
    def __init__(self, parent=None, building_area=0, settings=None):
        """Constructor.
        
        :param building_area: Area of the selected polygon in square meters.
        """
        super().__init__(parent)
        self.building_area = building_area
        self.settings = settings
        self.setup_ui()
        self.calculate()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle('Building Calculator - Расчёт')
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout()
        
        # Building info
        info_group = QGroupBox('Информация о здании')
        info_layout = QFormLayout()
        
        area_label = QLabel(f'<b>{self.building_area:,.1f} м²</b>')
        info_layout.addRow('Площадь застройки:', area_label)
        
        # Floors input
        self.spin_floors = QSpinBox()
        self.spin_floors.setRange(1, 200)
        self.spin_floors.setValue(5)
        self.spin_floors.valueChanged.connect(self.calculate)
        info_layout.addRow('Количество этажей:', self.spin_floors)
        
        self.label_total_area = QLabel()
        self.label_total_area.setStyleSheet('font-weight: bold;')
        info_layout.addRow('Общая площадь:', self.label_total_area)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Detailed breakdown table
        self.breakdown_group = QGroupBox('Распределение по типам квартир')
        breakdown_layout = QVBoxLayout()
        
        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(5)
        self.breakdown_table.setHorizontalHeaderLabels(['Тип', 'Площадь', 'Кол-во', 'Жителей', 'Парковка'])
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.breakdown_table.setEditTriggers(QTableWidget.NoEditTriggers)
        breakdown_layout.addWidget(self.breakdown_table)
        
        self.breakdown_group.setLayout(breakdown_layout)
        layout.addWidget(self.breakdown_group)
        
        # Totals
        totals_group = QGroupBox('ИТОГО')
        totals_layout = QFormLayout()
        
        self.label_apartments = QLabel()
        self.label_apartments.setStyleSheet('font-weight: bold;')
        totals_layout.addRow('Всего квартир:', self.label_apartments)
        
        self.label_residents = QLabel()
        self.label_residents.setStyleSheet('font-weight: bold; font-size: 16px; color: #2e7d32;')
        totals_layout.addRow('👥 Жителей:', self.label_residents)
        
        self.label_parking = QLabel()
        self.label_parking.setStyleSheet('font-weight: bold; font-size: 16px; color: #1565c0;')
        totals_layout.addRow('🚗 Парковочных мест:', self.label_parking)
        
        self.label_parking_area = QLabel()
        self.label_parking_area.setStyleSheet('font-weight: bold; font-size: 16px; color: #7b1fa2;')
        totals_layout.addRow('🏟️ Площадь парковки:', self.label_parking_area)
        
        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.btn_settings = QPushButton('⚙ Настройки')
        self.btn_settings.clicked.connect(self.open_settings)
        buttons_layout.addWidget(self.btn_settings)
        
        buttons_layout.addStretch()
        
        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setDefault(True)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_settings_values(self):
        """Get current settings values."""
        parking_spot_size = float(self.settings.value(
            SettingsDialog.KEY_PARKING_SPOT_SIZE,
            SettingsDialog.DEFAULT_PARKING_SPOT_SIZE
        ))
        
        use_types = self.settings.value(SettingsDialog.KEY_USE_APT_TYPES, SettingsDialog.DEFAULT_USE_APT_TYPES)
        if isinstance(use_types, str):
            use_types = use_types.lower() == 'true'
        
        if use_types:
            types_json = self.settings.value(SettingsDialog.KEY_APARTMENT_TYPES, None)
            if types_json:
                try:
                    apt_types = json.loads(types_json)
                except:
                    apt_types = SettingsDialog.DEFAULT_APARTMENT_TYPES
            else:
                apt_types = SettingsDialog.DEFAULT_APARTMENT_TYPES
        else:
            apt_types = None
        
        # Simple mode settings
        avg_apt_size = float(self.settings.value(
            SettingsDialog.KEY_AVG_APT_SIZE, SettingsDialog.DEFAULT_AVG_APT_SIZE
        ))
        residents_per_apt = float(self.settings.value(
            SettingsDialog.KEY_RESIDENTS_PER_APT, SettingsDialog.DEFAULT_RESIDENTS_PER_APT
        ))
        parking_per_apt = float(self.settings.value(
            SettingsDialog.KEY_PARKING_PER_APT, SettingsDialog.DEFAULT_PARKING_PER_APT
        ))
            
        return parking_spot_size, use_types, apt_types, avg_apt_size, residents_per_apt, parking_per_apt
    
    def calculate(self):
        """Perform the calculation and update results."""
        floors = self.spin_floors.value()
        parking_spot_size, use_types, apt_types, avg_apt_size, residents_per_apt, parking_per_apt = self.get_settings_values()
        
        # Total building area
        total_area = self.building_area * floors
        self.label_total_area.setText(f'{total_area:,.1f} м²')
        
        if use_types and apt_types:
            # Detailed mode with apartment types
            self.breakdown_group.setVisible(True)
            self.calculate_with_types(total_area, apt_types, parking_spot_size)
        else:
            # Simple mode
            self.breakdown_group.setVisible(False)
            self.calculate_simple(total_area, avg_apt_size, residents_per_apt, parking_per_apt, parking_spot_size)
    
    def calculate_with_types(self, total_area, apt_types, parking_spot_size):
        """Calculate using apartment types."""
        total_size_weight = sum(apt["size"] for apt in apt_types)
        
        # Clear and populate breakdown table
        self.breakdown_table.setRowCount(0)
        
        total_apartments = 0
        total_residents = 0
        total_parking = 0
        
        for apt in apt_types:
            apt_share = apt["size"] / total_size_weight
            apt_area = total_area * apt_share
            apt_count = apt_area / apt["size"]
            apt_residents = apt_count * apt.get("residents", 2.0)
            apt_parking = apt_count * apt["parking"]
            
            total_apartments += apt_count
            total_residents += apt_residents
            total_parking += apt_parking
            
            # Add row to table
            row = self.breakdown_table.rowCount()
            self.breakdown_table.insertRow(row)
            self.breakdown_table.setItem(row, 0, QTableWidgetItem(apt["name"]))
            self.breakdown_table.setItem(row, 1, QTableWidgetItem(f'{apt["size"]:.0f} м²'))
            self.breakdown_table.setItem(row, 2, QTableWidgetItem(f'{apt_count:.0f}'))
            self.breakdown_table.setItem(row, 3, QTableWidgetItem(f'{apt_residents:.0f}'))
            self.breakdown_table.setItem(row, 4, QTableWidgetItem(f'{apt_parking:.0f}'))
        
        parking_area = total_parking * parking_spot_size
        
        self.label_apartments.setText(f'{total_apartments:,.0f}')
        self.label_residents.setText(f'{total_residents:,.0f} человек')
        self.label_parking.setText(f'{total_parking:,.0f} мест')
        self.label_parking_area.setText(f'{parking_area:,.0f} м²')
    
    def calculate_simple(self, total_area, avg_apt_size, residents_per_apt, parking_per_apt, parking_spot_size):
        """Calculate using simple mode."""
        apartments = total_area / avg_apt_size
        residents = apartments * residents_per_apt
        parking = apartments * parking_per_apt
        parking_area = parking * parking_spot_size
        
        self.label_apartments.setText(f'{apartments:,.0f}')
        self.label_residents.setText(f'{residents:,.0f} человек')
        self.label_parking.setText(f'{parking:,.0f} мест')
        self.label_parking_area.setText(f'{parking_area:,.0f} м²')
    
    def open_settings(self):
        """Open settings dialog and recalculate after."""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec_():
            self.calculate()
