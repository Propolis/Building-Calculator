# -*- coding: utf-8 -*-
"""
Settings Dialog for Building Calculator
"""

import json
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox
)


class SettingsDialog(QDialog):
    """Dialog for configuring calculation parameters."""
    
    # Settings keys
    KEY_RESIDENTS_PER_APT = 'BuildingCalculator/residentsPerApartment'
    KEY_APARTMENT_TYPES = 'BuildingCalculator/apartmentTypes'
    KEY_PARKING_SPOT_SIZE = 'BuildingCalculator/parkingSpotSize'
    KEY_USE_APT_TYPES = 'BuildingCalculator/useApartmentTypes'
    KEY_AVG_APT_SIZE = 'BuildingCalculator/avgApartmentSize'
    KEY_PARKING_PER_APT = 'BuildingCalculator/parkingPerApartment'
    
    # Default values
    DEFAULT_RESIDENTS_PER_APT = 2.5
    DEFAULT_PARKING_SPOT_SIZE = 25.0
    DEFAULT_USE_APT_TYPES = True
    DEFAULT_AVG_APT_SIZE = 50.0
    DEFAULT_PARKING_PER_APT = 1.0
    DEFAULT_APARTMENT_TYPES = [
        {"name": "Студия", "size": 25, "parking": 0.5, "residents": 1.0},
        {"name": "1-комн", "size": 40, "parking": 1.0, "residents": 1.5},
        {"name": "2-комн", "size": 60, "parking": 1.0, "residents": 2.5},
        {"name": "3-комн", "size": 90, "parking": 1.5, "residents": 3.5},
        {"name": "4-комн", "size": 130, "parking": 2.0, "residents": 4.5},
    ]
    
    def __init__(self, parent=None, settings=None):
        """Constructor."""
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle('Building Calculator - Настройки')
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        # General settings
        general_group = QGroupBox('Общие параметры')
        general_layout = QFormLayout()
        
        self.spin_parking_size = QDoubleSpinBox()
        self.spin_parking_size.setRange(10, 50)
        self.spin_parking_size.setSuffix(' м²')
        self.spin_parking_size.setDecimals(1)
        general_layout.addRow('Площадь на 1 парковку:', self.spin_parking_size)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Simple mode settings
        simple_group = QGroupBox('Простой режим (без типов квартир)')
        simple_layout = QFormLayout()
        
        self.check_use_types = QCheckBox('Использовать типы квартир')
        self.check_use_types.stateChanged.connect(self.toggle_mode)
        simple_layout.addRow(self.check_use_types)
        
        self.spin_avg_size = QDoubleSpinBox()
        self.spin_avg_size.setRange(10, 300)
        self.spin_avg_size.setSuffix(' м²')
        self.spin_avg_size.setDecimals(1)
        simple_layout.addRow('Средняя площадь квартиры:', self.spin_avg_size)
        
        self.spin_residents = QDoubleSpinBox()
        self.spin_residents.setRange(0.5, 10)
        self.spin_residents.setSuffix(' чел.')
        self.spin_residents.setDecimals(1)
        simple_layout.addRow('Жителей на квартиру:', self.spin_residents)
        
        self.spin_parking_per_apt = QDoubleSpinBox()
        self.spin_parking_per_apt.setRange(0, 5)
        self.spin_parking_per_apt.setSuffix(' мест')
        self.spin_parking_per_apt.setDecimals(1)
        simple_layout.addRow('Парковок на квартиру:', self.spin_parking_per_apt)
        
        simple_group.setLayout(simple_layout)
        layout.addWidget(simple_group)
        self.simple_group = simple_group
        
        # Apartment types table
        self.types_group = QGroupBox('Типы квартир')
        types_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Название', 'Площадь (м²)', 'Жителей', 'Парковка'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        types_layout.addWidget(self.table)
        
        # Buttons for table
        table_buttons = QHBoxLayout()
        
        self.btn_add = QPushButton('+ Добавить')
        self.btn_add.clicked.connect(self.add_row)
        table_buttons.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton('- Удалить')
        self.btn_remove.clicked.connect(self.remove_row)
        table_buttons.addWidget(self.btn_remove)
        
        table_buttons.addStretch()
        types_layout.addLayout(table_buttons)
        
        self.types_group.setLayout(types_layout)
        layout.addWidget(self.types_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton('Сбросить')
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(self.btn_reset)
        
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton('Отмена')
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton('Сохранить')
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setDefault(True)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def toggle_mode(self, state):
        """Toggle between simple and detailed mode."""
        use_types = state == Qt.Checked
        self.types_group.setEnabled(use_types)
        self.spin_avg_size.setEnabled(not use_types)
        self.spin_residents.setEnabled(not use_types)
        self.spin_parking_per_apt.setEnabled(not use_types)
    
    def add_row(self):
        """Add a new row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("Новый тип"))
        self.table.setItem(row, 1, QTableWidgetItem("50"))
        self.table.setItem(row, 2, QTableWidgetItem("2.0"))
        self.table.setItem(row, 3, QTableWidgetItem("1.0"))
    
    def remove_row(self):
        """Remove selected row from the table."""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
    
    def load_settings(self):
        """Load settings from QSettings."""
        self.spin_parking_size.setValue(
            float(self.settings.value(
                self.KEY_PARKING_SPOT_SIZE,
                self.DEFAULT_PARKING_SPOT_SIZE
            ))
        )
        
        use_types = self.settings.value(self.KEY_USE_APT_TYPES, self.DEFAULT_USE_APT_TYPES)
        if isinstance(use_types, str):
            use_types = use_types.lower() == 'true'
        self.check_use_types.setChecked(use_types)
        self.toggle_mode(Qt.Checked if use_types else Qt.Unchecked)
        
        self.spin_avg_size.setValue(
            float(self.settings.value(self.KEY_AVG_APT_SIZE, self.DEFAULT_AVG_APT_SIZE))
        )
        self.spin_residents.setValue(
            float(self.settings.value(self.KEY_RESIDENTS_PER_APT, self.DEFAULT_RESIDENTS_PER_APT))
        )
        self.spin_parking_per_apt.setValue(
            float(self.settings.value(self.KEY_PARKING_PER_APT, self.DEFAULT_PARKING_PER_APT))
        )
        
        # Load apartment types
        types_json = self.settings.value(self.KEY_APARTMENT_TYPES, None)
        if types_json:
            try:
                apt_types = json.loads(types_json)
            except:
                apt_types = self.DEFAULT_APARTMENT_TYPES
        else:
            apt_types = self.DEFAULT_APARTMENT_TYPES
        
        self.table.setRowCount(0)
        for apt in apt_types:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(apt.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(apt.get("size", 50))))
            self.table.setItem(row, 2, QTableWidgetItem(str(apt.get("residents", 2.0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(apt.get("parking", 1.0))))
    
    def get_apartment_types(self):
        """Get apartment types from table."""
        types = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            try:
                size = float(self.table.item(row, 1).text()) if self.table.item(row, 1) else 50
            except:
                size = 50
            try:
                residents = float(self.table.item(row, 2).text()) if self.table.item(row, 2) else 2.0
            except:
                residents = 2.0
            try:
                parking = float(self.table.item(row, 3).text()) if self.table.item(row, 3) else 1.0
            except:
                parking = 1.0
            types.append({"name": name, "size": size, "residents": residents, "parking": parking})
        return types
    
    def save_settings(self):
        """Save settings to QSettings."""
        self.settings.setValue(self.KEY_PARKING_SPOT_SIZE, self.spin_parking_size.value())
        self.settings.setValue(self.KEY_USE_APT_TYPES, self.check_use_types.isChecked())
        self.settings.setValue(self.KEY_AVG_APT_SIZE, self.spin_avg_size.value())
        self.settings.setValue(self.KEY_RESIDENTS_PER_APT, self.spin_residents.value())
        self.settings.setValue(self.KEY_PARKING_PER_APT, self.spin_parking_per_apt.value())
        
        apt_types = self.get_apartment_types()
        if self.check_use_types.isChecked() and not apt_types:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один тип квартиры!")
            return
            
        self.settings.setValue(
            self.KEY_APARTMENT_TYPES,
            json.dumps(apt_types, ensure_ascii=False)
        )
        self.accept()
    
    def reset_to_defaults(self):
        """Reset all values to defaults."""
        self.spin_parking_size.setValue(self.DEFAULT_PARKING_SPOT_SIZE)
        self.check_use_types.setChecked(self.DEFAULT_USE_APT_TYPES)
        self.spin_avg_size.setValue(self.DEFAULT_AVG_APT_SIZE)
        self.spin_residents.setValue(self.DEFAULT_RESIDENTS_PER_APT)
        self.spin_parking_per_apt.setValue(self.DEFAULT_PARKING_PER_APT)
        
        self.table.setRowCount(0)
        for apt in self.DEFAULT_APARTMENT_TYPES:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(apt["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(apt["size"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(apt["residents"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(apt["parking"])))
