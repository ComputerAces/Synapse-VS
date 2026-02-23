
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QSpinBox, 
                             QDoubleSpinBox, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt

class CustomFormDialog(QDialog):
    def __init__(self, form_name, schema, parent=None):
        super().__init__(parent)
        self.setWindowTitle(form_name)
        self.resize(400, 300)
        self.schema = schema
        self.data_widgets = {} # label -> widget
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        for field in self.schema:
            label_text = field.get("label", "Field")
            f_type = field.get("type", "text")
            default = field.get("default", "")
            options = field.get("options", []) # For dropdowns

            widget = None
            
            if f_type == "text":
                widget = QLineEdit()
                if default: widget.setText(str(default))
                
            elif f_type == "number":
                # Integer or Float?
                if isinstance(default, float):
                    widget = QDoubleSpinBox()
                    widget.setRange(-999999, 999999)
                    widget.setValue(float(default) if default else 0.0)
                else:
                    widget = QSpinBox()
                    widget.setRange(-999999, 999999)
                    widget.setValue(int(default) if default else 0)

            elif f_type == "boolean":
                widget = QCheckBox()
                if default: widget.setChecked(True)
                
            elif f_type == "select":
                widget = QComboBox()
                widget.addItems([str(o) for o in options])
                if default and default in options:
                    widget.setCurrentText(str(default))

            if widget:
                self.data_widgets[label_text] = widget
                form_layout.addRow(label_text, widget)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_data(self):
        data = {}
        for label, widget in self.data_widgets.items():
            val = None
            if isinstance(widget, QLineEdit):
                val = widget.text()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                val = widget.value()
            elif isinstance(widget, QCheckBox):
                val = widget.isChecked()
            elif isinstance(widget, QComboBox):
                val = widget.currentText()
            
            data[label] = val
        return data
