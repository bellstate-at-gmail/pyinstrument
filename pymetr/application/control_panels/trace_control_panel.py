# pymetr/application/control_dock.py
import logging
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLineEdit, QComboBox, QColorDialog,  QDoubleSpinBox
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal

class TraceControlPanel(QWidget):
    def __init__(self, trace_manager, parent=None):
        super().__init__(parent)
        self.trace_manager = trace_manager

        layout = QVBoxLayout()
        self.trace_list = QListWidget()
        layout.addWidget(self.trace_list)

        self.setLayout(layout)

        self.trace_manager.traceAdded.connect(self.add_trace)
        self.trace_manager.traceRemoved.connect(self.remove_trace)

    def add_trace(self, trace):
        print(f"Trace added called with {trace}")
        item = TraceListItem(trace, self.trace_manager, self)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item.sizeHint())
        self.trace_list.addItem(list_item)
        self.trace_list.setItemWidget(list_item, item)

        # Connect the signals from TraceListItem to the corresponding slots in TraceManager
        item.visibilityChanged.connect(self.trace_manager.set_trace_visibility)
        item.labelChanged.connect(self.trace_manager.set_trace_label)
        item.colorChanged.connect(self.trace_manager.set_trace_color)
        item.modeChanged.connect(self.trace_manager.set_trace_mode)
        item.lineThicknessChanged.connect(self.trace_manager.set_trace_line_thickness)
        item.lineStyleChanged.connect(self.trace_manager.set_trace_line_style)
        item.traceRemoved.connect(self.trace_manager.remove_trace)

    def remove_trace(self, trace_id):
        for i in range(self.trace_list.count()):
            list_item = self.trace_list.item(i)
            item_widget = self.trace_list.itemWidget(list_item)
            if item_widget.trace.label == trace_id:
                self.trace_list.takeItem(i)
                break

    def clear_traces(self):
        self.trace_list.clear()

    def group_all_traces(self):
        for i in range(self.trace_list.count()):
            list_item = self.trace_list.item(i)
            item_widget = self.trace_list.itemWidget(list_item)
            item_widget.mode_combo.setCurrentText("Group")

    def isolate_all_traces(self):
        for i in range(self.trace_list.count()):
            list_item = self.trace_list.item(i)
            item_widget = self.trace_list.itemWidget(list_item)
            item_widget.mode_combo.setCurrentText("Isolate")

class TraceListItem(QWidget):
    visibilityChanged = Signal(str, bool)
    labelChanged = Signal(str, str)
    colorChanged = Signal(str, str)
    modeChanged = Signal(str, str)
    lineThicknessChanged = Signal(str, float)
    lineStyleChanged = Signal(str, str)
    traceRemoved = Signal(str)

    def __init__(self, trace, trace_manager, parent=None):
        super().__init__(parent)
        self.trace = trace
        self.trace_manager = trace_manager
        layout = QHBoxLayout()

        self.visible_checkbox = QCheckBox()
        self.visible_checkbox.setChecked(trace.visible)
        self.visible_checkbox.stateChanged.connect(self.toggle_visibility)
        self.visible_checkbox.setMinimumWidth(20)
        layout.addWidget(self.visible_checkbox)

        self.label = QLineEdit(trace.label)
        self.label.textChanged.connect(self.update_label)
        self.label.setMinimumWidth(120)
        layout.addWidget(self.label)

        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {trace.color}")
        self.color_button.clicked.connect(self.select_color)
        self.color_button.setMinimumWidth(80)
        layout.addWidget(self.color_button)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Group", "Isolate"])
        self.mode_combo.setCurrentText(trace.mode)
        self.mode_combo.currentTextChanged.connect(self.update_mode)
        self.mode_combo.setMinimumWidth(80)
        layout.addWidget(self.mode_combo)

        self.line_width_spinbox = QDoubleSpinBox()
        self.line_width_spinbox.setRange(1, 10.0)
        self.line_width_spinbox.setSingleStep(1)
        self.line_width_spinbox.setValue(trace.line_thickness)
        self.line_width_spinbox.valueChanged.connect(self.update_line_width)
        self.line_width_spinbox.setMinimumWidth(80)
        layout.addWidget(self.line_width_spinbox)

        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Solid", "Dash", "Dot", "Dash-Dot"])
        self.line_style_combo.setCurrentText(trace.line_style)
        self.line_style_combo.currentTextChanged.connect(self.update_line_style)
        self.line_style_combo.setMinimumWidth(80)
        layout.addWidget(self.line_style_combo)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_trace)
        self.delete_button.setMinimumWidth(120)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def toggle_visibility(self, state):
        logger.debug(f"Toggling visibility for trace '{self.trace.label}' to {bool(state)}")
        self.visibilityChanged.emit(self.trace.label, bool(state))

    def update_label(self, text):
        logger.debug(f"Updating label for trace '{self.trace.label}' to '{text}'")
        self.labelChanged.emit(self.trace.label, text)

    def select_color(self):
        color = QColorDialog.getColor(QColor(self.trace.color), self)
        if color.isValid():
            logger.debug(f"Updating color for trace '{self.trace.label}' to '{color.name()}'")
            self.colorChanged.emit(self.trace.label, color.name())
            self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def update_mode(self, mode):
        logger.debug(f"Updating mode for trace '{self.trace.label}' to '{mode}'")
        self.modeChanged.emit(self.trace.label, mode)

    def update_line_width(self, width):
        logger.debug(f"Updating line width for trace '{self.trace.label}' to '{width}'")
        self.lineThicknessChanged.emit(self.trace.label, width)

    def update_line_style(self, style):
        logger.debug(f"Updating line style for trace '{self.trace.label}' to '{style}'")
        self.lineStyleChanged.emit(self.trace.label, style)

    def delete_trace(self):
        logger.debug(f"Deleting trace '{self.trace.label}'")
        self.traceRemoved.emit(self.trace.label)