# -*- coding: utf-8 -*-
"""
Calculation Dialog for Building Calculator
"""

import json
import math
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QComboBox
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
        self.update_mode_visibility()
        self.calculate()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle('Building Calculator - Расчёт')
        self.setMinimumWidth(550)
        self.setMinimumHeight(600)
        
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
        
        # Apartment settings group
        apt_group = QGroupBox('Параметры квартир')
        apt_layout = QFormLayout()
        
        # Use apartment types checkbox
        use_types = self.settings.value(SettingsDialog.KEY_USE_APT_TYPES, SettingsDialog.DEFAULT_USE_APT_TYPES)
        if isinstance(use_types, str):
            use_types = use_types.lower() == 'true'
        self.check_use_types = QCheckBox('Использовать типы квартир')
        self.check_use_types.setChecked(use_types)
        self.check_use_types.stateChanged.connect(self.on_mode_changed)
        apt_layout.addRow(self.check_use_types)
        
        # Apartment size input (only visible in simple mode)
        self.apt_size_label = QLabel('Средняя площадь квартиры:')
        self.spin_apt_size = QDoubleSpinBox()
        self.spin_apt_size.setRange(10.0, 500.0)
        self.spin_apt_size.setValue(float(self.settings.value(
            SettingsDialog.KEY_AVG_APT_SIZE, SettingsDialog.DEFAULT_AVG_APT_SIZE
        )))
        self.spin_apt_size.setSuffix(' м²')
        self.spin_apt_size.setDecimals(1)
        self.spin_apt_size.valueChanged.connect(self.calculate)
        apt_layout.addRow(self.apt_size_label, self.spin_apt_size)
        
        apt_group.setLayout(apt_layout)
        layout.addWidget(apt_group)
        
        # Residents settings group
        residents_group = QGroupBox('Жители')
        residents_layout = QFormLayout()
        
        # Residents calculation mode selector
        self.combo_residents_mode = QComboBox()
        self.combo_residents_mode.addItem('Жителей на квартиру', 'per_apt')
        self.combo_residents_mode.addItem('М² на 1 жителя', 'per_sqm')
        self.combo_residents_mode.currentIndexChanged.connect(self.on_residents_mode_changed)
        residents_layout.addRow('Режим расчёта:', self.combo_residents_mode)
        
        # Residents per apartment
        self.residents_label = QLabel('Жителей на квартиру:')
        self.spin_residents = QDoubleSpinBox()
        self.spin_residents.setRange(0.5, 10.0)
        self.spin_residents.setValue(float(self.settings.value(
            SettingsDialog.KEY_RESIDENTS_PER_APT, SettingsDialog.DEFAULT_RESIDENTS_PER_APT
        )))
        self.spin_residents.setDecimals(1)
        self.spin_residents.valueChanged.connect(self.calculate)
        residents_layout.addRow(self.residents_label, self.spin_residents)
        
        # Sqm per resident
        self.sqm_per_resident_label = QLabel('М² на 1 жителя:')
        self.spin_sqm_per_resident = QDoubleSpinBox()
        self.spin_sqm_per_resident.setRange(5.0, 100.0)
        self.spin_sqm_per_resident.setValue(20.0)
        self.spin_sqm_per_resident.setSuffix(' м²')
        self.spin_sqm_per_resident.setDecimals(1)
        self.spin_sqm_per_resident.valueChanged.connect(self.calculate)
        residents_layout.addRow(self.sqm_per_resident_label, self.spin_sqm_per_resident)
        
        residents_group.setLayout(residents_layout)
        layout.addWidget(residents_group)
        self.residents_group = residents_group
        
        # Apartment types table
        self.types_group = QGroupBox('Типы квартир')
        types_layout = QVBoxLayout()
        
        self.apt_table = QTableWidget()
        self.apt_table.setColumnCount(5)
        self.apt_table.setHorizontalHeaderLabels(['Название', 'Площадь (м²)', 'Кол-во', 'Жителей', 'Парковка'])
        self.apt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.apt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.apt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.apt_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.apt_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.apt_table.cellChanged.connect(self.calculate)
        types_layout.addWidget(self.apt_table)
        
        self.load_apartment_types()
        
        table_buttons = QHBoxLayout()
        self.btn_add = QPushButton('+ Добавить')
        self.btn_add.clicked.connect(self.add_apt_type)
        table_buttons.addWidget(self.btn_add)
        self.btn_remove = QPushButton('- Удалить')
        self.btn_remove.clicked.connect(self.remove_apt_type)
        table_buttons.addWidget(self.btn_remove)
        table_buttons.addStretch()
        types_layout.addLayout(table_buttons)
        
        # Unused area label
        self.label_unused_area = QLabel()
        self.label_unused_area.setStyleSheet('font-style: italic; color: #888;')
        types_layout.addWidget(self.label_unused_area)
        
        self.types_group.setLayout(types_layout)
        layout.addWidget(self.types_group)
        
        # Parking settings
        parking_group = QGroupBox('Парковка')
        parking_layout = QFormLayout()
        
        self.spin_parking_size = QDoubleSpinBox()
        self.spin_parking_size.setRange(1.0, 500.0)
        self.spin_parking_size.setValue(float(self.settings.value(
            SettingsDialog.KEY_PARKING_SPOT_SIZE, SettingsDialog.DEFAULT_PARKING_SPOT_SIZE
        )))
        self.spin_parking_size.setSuffix(' м²')
        self.spin_parking_size.setDecimals(1)
        self.spin_parking_size.valueChanged.connect(self.calculate)
        parking_layout.addRow('Площадь 1 парковки:', self.spin_parking_size)
        
        # Parking mode selector
        self.combo_parking_mode = QComboBox()
        self.combo_parking_mode.addItem('На квартиру', 'per_apt')
        self.combo_parking_mode.addItem('На жителей', 'per_residents')
        self.combo_parking_mode.addItem('На м² квартиры', 'per_sqm')
        self.combo_parking_mode.setCurrentIndex(1)  # Default: per_residents (350 on 1000)
        self.combo_parking_mode.currentIndexChanged.connect(self.on_parking_mode_changed)
        parking_layout.addRow('Режим расчёта:', self.combo_parking_mode)
        
        # Parking per apartment
        self.parking_per_apt_label = QLabel('Парковок на квартиру:')
        self.spin_parking_per_apt = QDoubleSpinBox()
        self.spin_parking_per_apt.setRange(0.0, 5.0)
        self.spin_parking_per_apt.setValue(float(self.settings.value(
            SettingsDialog.KEY_PARKING_PER_APT, SettingsDialog.DEFAULT_PARKING_PER_APT
        )))
        self.spin_parking_per_apt.setDecimals(2)
        self.spin_parking_per_apt.valueChanged.connect(self.calculate)
        parking_layout.addRow(self.parking_per_apt_label, self.spin_parking_per_apt)
        
        # Parkings per N residents (two fields: X parkings per Y residents)
        self.parkings_residents_label = QLabel('Парковок:')
        self.spin_parkings_for_residents = QDoubleSpinBox()
        self.spin_parkings_for_residents.setRange(1.0, 10000.0)
        self.spin_parkings_for_residents.setValue(350.0)  # 350 parkings per 1000 residents
        self.spin_parkings_for_residents.setDecimals(0)
        self.spin_parkings_for_residents.valueChanged.connect(self.calculate)
        parking_layout.addRow(self.parkings_residents_label, self.spin_parkings_for_residents)
        
        self.per_residents_label = QLabel('На жителей:')
        self.spin_per_residents = QDoubleSpinBox()
        self.spin_per_residents.setRange(1.0, 100000.0)
        self.spin_per_residents.setValue(1000.0)  # 350 parkings per 1000 residents
        self.spin_per_residents.setDecimals(0)
        self.spin_per_residents.valueChanged.connect(self.calculate)
        parking_layout.addRow(self.per_residents_label, self.spin_per_residents)
        
        # Parkings per N sqm (two fields: X parkings per Y sqm)
        self.parkings_sqm_label = QLabel('Парковок:')
        self.spin_parkings_for_sqm = QDoubleSpinBox()
        self.spin_parkings_for_sqm.setRange(1.0, 10000.0)
        self.spin_parkings_for_sqm.setValue(1.0)
        self.spin_parkings_for_sqm.setDecimals(0)
        self.spin_parkings_for_sqm.valueChanged.connect(self.calculate)
        parking_layout.addRow(self.parkings_sqm_label, self.spin_parkings_for_sqm)
        
        self.per_sqm_label = QLabel('На м² квартиры:')
        self.spin_per_sqm = QDoubleSpinBox()
        self.spin_per_sqm.setRange(1.0, 100000.0)
        self.spin_per_sqm.setValue(50.0)  # 1 parking per 50 sqm
        self.spin_per_sqm.setDecimals(0)
        self.spin_per_sqm.valueChanged.connect(self.calculate)
        parking_layout.addRow(self.per_sqm_label, self.spin_per_sqm)
        
        parking_group.setLayout(parking_layout)
        layout.addWidget(parking_group)
        
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
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setDefault(True)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_apartment_types(self):
        """Load apartment types into table."""
        self.apt_table.blockSignals(True)
        types_json = self.settings.value(SettingsDialog.KEY_APARTMENT_TYPES, None)
        if types_json:
            try:
                apt_types = json.loads(types_json)
            except:
                apt_types = SettingsDialog.DEFAULT_APARTMENT_TYPES
        else:
            apt_types = SettingsDialog.DEFAULT_APARTMENT_TYPES
        
        self.apt_table.setRowCount(0)
        for apt in apt_types:
            row = self.apt_table.rowCount()
            self.apt_table.insertRow(row)
            self.apt_table.setItem(row, 0, QTableWidgetItem(apt.get("name", "")))
            self.apt_table.setItem(row, 1, QTableWidgetItem(str(apt.get("size", 50))))
            self.apt_table.setItem(row, 2, QTableWidgetItem(str(apt.get("count", 1))))
            self.apt_table.setItem(row, 3, QTableWidgetItem(str(apt.get("residents", 2.0))))
            self.apt_table.setItem(row, 4, QTableWidgetItem(str(apt.get("parking", 1.0))))
        self.apt_table.blockSignals(False)
    
    def get_apartment_types_from_table(self):
        """Get apartment types from table."""
        types = []
        for row in range(self.apt_table.rowCount()):
            name = self.apt_table.item(row, 0).text() if self.apt_table.item(row, 0) else ""
            try:
                size = float(self.apt_table.item(row, 1).text()) if self.apt_table.item(row, 1) else 50
            except:
                size = 50
            try:
                count = int(self.apt_table.item(row, 2).text()) if self.apt_table.item(row, 2) else 1
            except:
                count = 1
            try:
                residents = float(self.apt_table.item(row, 3).text()) if self.apt_table.item(row, 3) else 2.0
            except:
                residents = 2.0
            try:
                parking = float(self.apt_table.item(row, 4).text()) if self.apt_table.item(row, 4) else 1.0
            except:
                parking = 1.0
            types.append({"name": name, "size": size, "count": count, "residents": residents, "parking": parking})
        return types
    
    def add_apt_type(self):
        """Add a new apartment type row."""
        row = self.apt_table.rowCount()
        self.apt_table.insertRow(row)
        self.apt_table.setItem(row, 0, QTableWidgetItem("Новый тип"))
        self.apt_table.setItem(row, 1, QTableWidgetItem("50"))
        self.apt_table.setItem(row, 2, QTableWidgetItem("1"))
        self.apt_table.setItem(row, 3, QTableWidgetItem("2.0"))
        self.apt_table.setItem(row, 4, QTableWidgetItem("1.0"))
        self.calculate()
    
    def remove_apt_type(self):
        """Remove selected apartment type row."""
        row = self.apt_table.currentRow()
        if row >= 0:
            self.apt_table.removeRow(row)
            self.calculate()
    
    def on_mode_changed(self, state):
        """Handle apartment types checkbox change."""
        self.update_mode_visibility()
        self.calculate()
    
    def on_residents_mode_changed(self, index):
        """Handle residents mode change."""
        mode = self.combo_residents_mode.currentData()
        self.residents_label.setVisible(mode == 'per_apt')
        self.spin_residents.setVisible(mode == 'per_apt')
        self.sqm_per_resident_label.setVisible(mode == 'per_sqm')
        self.spin_sqm_per_resident.setVisible(mode == 'per_sqm')
        self.calculate()
    
    def on_parking_mode_changed(self, index):
        """Handle parking mode change."""
        mode = self.combo_parking_mode.currentData()
        # Per apartment mode
        self.parking_per_apt_label.setVisible(mode == 'per_apt')
        self.spin_parking_per_apt.setVisible(mode == 'per_apt')
        # Per residents mode (X parkings per Y residents)
        self.parkings_residents_label.setVisible(mode == 'per_residents')
        self.spin_parkings_for_residents.setVisible(mode == 'per_residents')
        self.per_residents_label.setVisible(mode == 'per_residents')
        self.spin_per_residents.setVisible(mode == 'per_residents')
        # Per sqm mode (X parkings per Y sqm)
        self.parkings_sqm_label.setVisible(mode == 'per_sqm')
        self.spin_parkings_for_sqm.setVisible(mode == 'per_sqm')
        self.per_sqm_label.setVisible(mode == 'per_sqm')
        self.spin_per_sqm.setVisible(mode == 'per_sqm')
        self.calculate()
    
    def update_mode_visibility(self):
        """Update visibility of fields based on apartment types mode."""
        use_types = self.check_use_types.isChecked()
        
        # Simple mode fields
        self.apt_size_label.setVisible(not use_types)
        self.spin_apt_size.setVisible(not use_types)
        
        # Residents group only visible in simple mode
        self.residents_group.setVisible(not use_types)
        
        # Types table only visible in types mode
        self.types_group.setVisible(use_types)
        
        # Update residents mode visibility
        if not use_types:
            self.on_residents_mode_changed(0)
        
        # Update parking mode visibility
        self.on_parking_mode_changed(0)
    
    def calculate(self):
        """Perform the calculation and update results."""
        floors = self.spin_floors.value()
        parking_spot_size = self.spin_parking_size.value()
        
        total_area = self.building_area * floors
        self.label_total_area.setText(f'{total_area:,.1f} м²')
        
        if self.check_use_types.isChecked():
            apt_types = self.get_apartment_types_from_table()
            if apt_types:
                self.calculate_with_types(total_area, apt_types, parking_spot_size)
        else:
            self.calculate_simple(total_area, parking_spot_size)
    
    def calculate_with_types(self, total_area, apt_types, parking_spot_size):
        """Calculate using apartment types."""
        total_apartments = 0
        total_residents = 0
        used_area = 0
        
        for apt in apt_types:
            apt_count = apt.get("count", 1)
            apt_size = apt.get("size", 50)
            apt_residents = apt_count * apt.get("residents", 2.0)
            
            total_apartments += apt_count
            total_residents += apt_residents
            used_area += apt_count * apt_size
        
        # Check if apartments exceed building area
        if used_area > total_area:
            self.label_apartments.setText(f'{total_apartments:,} ⚠️')
            self.label_apartments.setStyleSheet('font-weight: bold; color: #d32f2f;')
            self.label_residents.setText(f'Превышение площади! ({int(used_area):,} > {int(total_area):,} м²)')
            self.label_residents.setStyleSheet('font-weight: bold; color: #d32f2f;')
            self.label_parking.setText('-')
            self.label_parking_area.setText('-')
            self.label_unused_area.setText(f'⚠️ Превышение на {int(used_area - total_area):,} м²')
            self.label_unused_area.setStyleSheet('font-weight: bold; color: #d32f2f;')
            return
        else:
            self.label_apartments.setStyleSheet('font-weight: bold;')
            self.label_residents.setStyleSheet('font-weight: bold; font-size: 16px; color: #2e7d32;')
            unused = total_area - used_area
            self.label_unused_area.setText(f'Использовано: {int(used_area):,} м² | Свободно: {int(unused):,} м²')
            self.label_unused_area.setStyleSheet('font-style: italic; color: #888;')
        
        # Apply parking mode
        total_parking = self.calculate_parking(total_apartments, total_residents, total_area)
        total_parking = math.floor(total_parking)  # Round down before calculating area
        parking_area = total_parking * parking_spot_size
        
        self.label_apartments.setText(f'{total_apartments:,}')
        self.label_residents.setText(f'{int(total_residents):,} человек')
        self.label_parking.setText(f'{total_parking:,} мест')
        self.label_parking_area.setText(f'{int(parking_area):,} м²')
    
    def calculate_simple(self, total_area, parking_spot_size):
        """Calculate using simple mode."""
        avg_apt_size = self.spin_apt_size.value()
        apartments = math.floor(total_area / avg_apt_size)
        
        # Calculate residents based on mode
        residents_mode = self.combo_residents_mode.currentData()
        if residents_mode == 'per_apt':
            residents = apartments * self.spin_residents.value()
        else:  # per_sqm - residents per sqm of apartment
            residents_per_apt = avg_apt_size / self.spin_sqm_per_resident.value()
            residents = apartments * residents_per_apt
        
        # Calculate parking
        parking = self.calculate_parking(apartments, residents, total_area)
        parking = math.floor(parking)  # Round down before calculating area
        parking_area = parking * parking_spot_size
        
        self.label_apartments.setText(f'{apartments:,}')
        self.label_residents.setText(f'{int(residents):,} человек')
        self.label_parking.setText(f'{parking:,} мест')
        self.label_parking_area.setText(f'{int(parking_area):,} м²')
    
    def calculate_parking(self, apartments, residents, total_area):
        """Calculate parking based on selected mode."""
        parking_mode = self.combo_parking_mode.currentData()
        
        if parking_mode == 'per_apt':
            # Парковок на 1 квартиру
            return apartments * self.spin_parking_per_apt.value()
        elif parking_mode == 'per_residents':
            # X парковок на Y жителей
            parkings = self.spin_parkings_for_residents.value()
            per_residents = self.spin_per_residents.value()
            if per_residents > 0:
                return (residents / per_residents) * parkings
            return 0
        else:  # per_sqm
            # X парковок на Y м²
            parkings = self.spin_parkings_for_sqm.value()
            per_sqm = self.spin_per_sqm.value()
            if per_sqm > 0:
                return (total_area / per_sqm) * parkings
            return 0
