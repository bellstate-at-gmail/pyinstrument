import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import random

class Trace:
    def __init__(self, label=None, color=None, mode='Group', data=None, line_thickness=1.0, alpha=1.0, line_style='-'):
        self.label = label
        self.color = color
        self.mode = mode
        self.data = data if data is not None else np.array([])
        self.visible = True
        self.x_range = None
        self.y_range = None
        self.line_thickness = line_thickness
        self.alpha = alpha
        self.line_style = line_style

class TraceManager(QtCore.QObject):
    traceDataChanged = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        self.traces = []
        self.plot_mode = 'Add'
        self.trace_mode = 'Group'  # Add this line

    def add_trace(self, trace):
        if self.plot_mode == "Replace":
            self.traces.clear()
        trace.mode = self.trace_mode 
        self.traces.append(trace)
        self.emit_trace_data()

    def remove_trace(self, trace):
        if trace in self.traces:
            self.traces.remove(trace)
            self.emit_trace_data()

    def emit_trace_data(self):
        trace_data = {trace.label: {
            'label': trace.label,
            'color': trace.color,
            'mode': trace.mode,
            'data': trace.data.tolist(),
            'visible': trace.visible,
            'line_thickness': trace.line_thickness,
            'line_style': trace.line_style
        } for trace in self.traces}
        self.traceDataChanged.emit(trace_data)

class TraceDock(QtWidgets.QDockWidget):

    traceModeChanged = QtCore.Signal(str)  # Add this line
    roiPlotEnabled = QtCore.Signal(bool)

    def __init__(self, parent=None, trace_manager=None):
        super().__init__("Trace Settings", parent)
        self.setMinimumWidth(200) 
        self.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)

        self.trace_manager = trace_manager

        self.dock_widget = QtWidgets.QWidget()
        self.dock_layout = QtWidgets.QVBoxLayout(self.dock_widget)

        self.plot_mode_combo_box = QtWidgets.QComboBox()
        self.plot_mode_combo_box.addItems(["Add", "Replace"])
        self.plot_mode_combo_box.currentIndexChanged.connect(self.on_plot_mode_changed)
        self.dock_layout.addWidget(self.plot_mode_combo_box)

        self.trace_mode_combo_box = QtWidgets.QComboBox()
        self.trace_mode_combo_box.addItems(["Group", "Isolate"])
        self.trace_mode_combo_box.currentIndexChanged.connect(self.on_trace_mode_changed)
        self.dock_layout.addWidget(self.trace_mode_combo_box)
        self.trace_mode_combo_box.setCurrentText(self.trace_manager.trace_mode)

        self.roi_plot_toggle = QtWidgets.QPushButton("ROI Plot")
        self.roi_plot_toggle.setCheckable(True)
        self.roi_plot_toggle.setChecked(False)
        self.roi_plot_toggle.toggled.connect(self.on_roi_plot_toggled)
        self.dock_layout.addWidget(self.roi_plot_toggle)

        self.trace_parameter_tree = pg.parametertree.ParameterTree()
        self.dock_layout.addWidget(self.trace_parameter_tree)

        self.setWidget(self.dock_widget)

        self.trace_manager.traceDataChanged.connect(self.update_parameter_tree)

    def on_roi_plot_toggled(self, checked):
        self.roiPlotEnabled.emit(checked)

    def on_plot_mode_changed(self, index):
        plot_mode = self.plot_mode_combo_box.itemText(index)
        self.trace_manager.plot_mode = plot_mode
        self.trace_manager.emit_trace_data()

    def on_trace_mode_changed(self, index):
        trace_mode = self.trace_mode_combo_box.itemText(index)
        self.traceModeChanged.emit(trace_mode)  # Update this line
        self.trace_manager.trace_mode = trace_mode  # Add this line

    def update_parameter_tree(self, trace_data):
        self.trace_parameter_tree.clear()
        for trace_id, trace_info in trace_data.items():
            trace_param = pg.parametertree.Parameter.create(name=trace_id, type='group', children=[
                {'name': 'Label', 'type': 'str', 'value': trace_info['label']},
                {'name': 'Visible', 'type': 'bool', 'value': trace_info['visible']},
                {'name': 'Color', 'type': 'color', 'value': trace_info['color']},
                {'name': 'Mode', 'type': 'list', 'limits': ['Group', 'Isolate'], 'value': trace_info['mode']},
                {'name': 'Extra', 'type': 'group', 'expanded': False, 'children': [
                    {'name': 'Line Thickness', 'type': 'float', 'value': trace_info.get('line_thickness', 1.0), 'step': 0.1, 'limits': (0.1, 10.0)},
                    {'name': 'Line Style', 'type': 'list', 'limits': ['Solid', 'Dash', 'Dot', 'Dash-Dot'], 'value': trace_info.get('line_style', 'Solid')}
                ]},
                {'name': 'Delete', 'type': 'action'}
            ])
            trace_param.child('Delete').sigActivated.connect(lambda _, tid=trace_id: self.remove_trace(tid))
            trace_param.child('Label').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_label(tid, val))
            trace_param.child('Visible').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_parameter(tid, 'visible', val))
            trace_param.child('Color').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_parameter(tid, 'color', val))
            trace_param.child('Mode').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_parameter(tid, 'mode', val))
            trace_param.child('Extra').child('Line Thickness').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_parameter(tid, 'line_thickness', val))
            trace_param.child('Extra').child('Line Style').sigValueChanged.connect(lambda param, val, tid=trace_id: self.update_trace_parameter(tid, 'line_style', val))
            self.trace_parameter_tree.addParameters(trace_param)

    def update_trace_label(self, trace_id, label):
        for trace in self.trace_manager.traces:
            if trace.label == trace_id:
                trace.label = label
                self.trace_manager.emit_trace_data()
                break

    def update_trace_parameter(self, trace_id, parameter, value):
        for trace in self.trace_manager.traces:
            if trace.label == trace_id:
                setattr(trace, parameter, value)
                if parameter == 'color' and trace.mode == 'Isolate':
                    axis = self.parent().plot_widget.trace_axes.get(trace)  # Access trace_axes from the PlotWidget instance
                    if axis is not None:
                        axis.setPen(value)
                self.trace_manager.emit_trace_data()
                break

    def remove_trace(self, trace_id):
        for trace in self.trace_manager.traces:
            if trace.label == trace_id:
                self.trace_manager.remove_trace(trace)
                break

class PlotWidget(QtWidgets.QWidget):
    def __init__(self, trace_manager, parent=None):
        super().__init__(parent)
        self.trace_manager = trace_manager
        self.layout = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.setTitle("Plot")
        self.plot_item.setLabel("left", "Y")
        self.plot_item.setLabel("bottom", "X")
        self.plot_item.showGrid(x=True, y=True)

        self.legend = pg.LegendItem(offset=(70, 30))
        self.legend.setParentItem(self.plot_item) 

        self.additional_axes = []
        self.additional_view_boxes = []
        self.trace_view_boxes = {}
        self.trace_axes = {}
        self.traces = []

        self.roi_plot_item = None
        self.roi_plot = None
        self.roi = None

        self.trace_manager.traceDataChanged.connect(self.update_plot)
        self.plot_item.vb.sigRangeChanged.connect(self.update_roi_region)

    def update_plot(self, trace_data):
        self.plot_item.clear() 
        self.legend.setParentItem(self.plot_item) 
        self.clear_traces()
        self.clear_additional_axes() 
        for trace in self.trace_manager.traces:
            visible = trace.visible
            color = trace.color
            legend_alias = trace.label
            x = np.arange(len(trace.data))
            y = trace.data
            mode = trace.mode

            if visible:
                pen = pg.mkPen(color=color, width=trace.line_thickness, style=self.get_line_style(trace.line_style))

                if mode == "Group":
                    curve = pg.PlotCurveItem(x, y, pen=pen, name=legend_alias)
                    self.plot_item.addItem(curve)
                    self.legend.addItem(curve, legend_alias)
                    self.traces.append(curve)
                else:  # Isolate mode
                    if trace in self.trace_view_boxes:
                        view_box = self.trace_view_boxes[trace]
                        axis = self.trace_axes[trace]
                    else:
                        axis = pg.AxisItem("right", pen=pen)
                        self.plot_item.layout.addItem(axis, 2, self.trace_manager.traces.index(trace) + 1)
                        self.additional_axes.append(axis)

                        view_box = pg.ViewBox()
                        axis.linkToView(view_box)
                        view_box.setXLink(self.plot_item.vb)
                        self.plot_item.scene().addItem(view_box)
                        self.additional_view_boxes.append(view_box)

                        self.trace_view_boxes[trace] = view_box
                        self.trace_axes[trace] = axis

                    curve = pg.PlotCurveItem(x, y, pen=pen, name=legend_alias)
                    curve.setOpacity(trace.alpha)
                    view_box.addItem(curve)
                    self.legend.addItem(curve, legend_alias)
                    self.traces.append(curve)

                    if trace.y_range is not None:
                        view_box.setRange(yRange=trace.y_range)
                        view_box.enableAutoRange(axis='y', enable=False)
                    else:
                        view_box.setRange(yRange=self.plot_item.vb.viewRange()[1])
                        trace.y_range = view_box.viewRange()[1]  # Store the initial y-range of the isolated trace
            else:
                if trace.mode == 'Isolate' and trace in self.trace_view_boxes:
                    view_box = self.trace_view_boxes[trace]
                    trace.y_range = view_box.viewRange()[1]  # Store the y-range when the isolated trace becomes invisible

            print(f"Trace: {trace.label}, Visible: {trace.visible}, Mode: {trace.mode}, Y-Range: {trace.y_range}")

        self.plot_item.vb.sigResized.connect(self.update_view_boxes)
        self.restore_view_ranges()
        self.update_roi_plot()

    def handle_view_box_range_changed(self, view_box, range_):
        x_range, y_range = range_
        for trace, vb in self.trace_view_boxes.items():
            if vb == view_box:
                trace.x_range = x_range
                trace.y_range = y_range
                print(f"Trace: {trace.label}, X-Range: {x_range}, Y-Range: {y_range}")
                break

    def clear_additional_axes(self):
        for axis in self.additional_axes:
            self.plot_item.layout.removeItem(axis)
            axis.deleteLater()
        for view_box in self.additional_view_boxes:
            self.plot_item.scene().removeItem(view_box)
            view_box.deleteLater()
        self.additional_axes.clear()
        self.additional_view_boxes.clear()
        self.trace_view_boxes.clear()
        self.trace_axes.clear()

    def on_trace_mode_changed(self, trace_mode):
        self.trace_manager.trace_mode = trace_mode
        self.update_plot(self.trace_manager.traces)

    def clear_traces(self):
        for trace in self.traces:
            if trace in self.plot_item.items:
                self.plot_item.removeItem(trace)
            else:
                for view_box in self.trace_view_boxes.values():
                    if trace in view_box.addedItems:
                        view_box.removeItem(trace)
        self.traces.clear()
        self.legend.clear()

    def restore_view_ranges(self):
        if self.plot_item.vb.viewRange()[0] is not None:
            self.plot_item.vb.setRange(xRange=self.plot_item.vb.viewRange()[0], yRange=self.plot_item.vb.viewRange()[1], padding=0)
        for trace, view_box in self.trace_view_boxes.items():
            if trace.y_range is not None:
                view_box.setRange(yRange=trace.y_range, padding=0)

    def get_line_style(self, line_style):
        if line_style == 'Solid':
            return QtCore.Qt.SolidLine
        elif line_style == 'Dash':
            return QtCore.Qt.DashLine
        elif line_style == 'Dot':
            return QtCore.Qt.DotLine
        elif line_style == 'Dash-Dot':
            return QtCore.Qt.DashDotLine
        else:
            return QtCore.Qt.SolidLine

    def update_view_boxes(self):
        for view_box in self.additional_view_boxes:
            view_box.setGeometry(self.plot_item.vb.sceneBoundingRect())

    def on_roi_plot_enabled(self, enabled):
        if enabled:
            if not self.roi_plot_item:
                self.roi_plot_item = pg.PlotWidget()
                self.roi_plot_item.setMaximumHeight(100)  # Set the height of the ROI plot to 100 pixels
                self.layout.addWidget(self.roi_plot_item)
                self.roi_plot = self.roi_plot_item.getPlotItem()

                self.roi = pg.LinearRegionItem()
                self.roi.setZValue(-10)
                self.roi_plot.addItem(self.roi)  # Add the ROI to the correct plot

                self.roi.sigRegionChanged.connect(self.update_main_plot)
                self.plot_item.sigXRangeChanged.connect(self.update_roi_region)
        else:
            if self.roi_plot_item:
                self.layout.removeWidget(self.roi_plot_item)
                self.roi_plot_item.deleteLater()
                self.roi_plot_item = None
                self.roi = None
        self.update_roi_plot()

    def update_roi_plot(self):
        if self.roi_plot_item is not None:
            self.roi_plot_item.clear()
            for trace in self.trace_manager.traces:
                if trace.visible:
                    x = np.arange(len(trace.data))
                    y = trace.data
                    pen = pg.mkPen(color=trace.color, width=trace.line_thickness, style=self.get_line_style(trace.line_style))
                    roi_curve = self.roi_plot_item.plot(x, y, pen=pen, name=trace.label)
            self.roi_plot_item.autoRange()
        self.set_roi_region()
        self.update_roi_region()

    def restore_view_ranges(self):
        if self.plot_item.vb.viewRange()[0] is not None:
            self.plot_item.vb.setRange(xRange=self.plot_item.vb.viewRange()[0], yRange=self.plot_item.vb.viewRange()[1], padding=0)
        for trace, view_box in self.trace_view_boxes.items():
            if trace.y_range is not None:
                view_box.setRange(yRange=trace.y_range, padding=0)

    def update_roi_region(self):
        if self.roi is not None and self.roi_plot is not None:
            self.roi.setRegion(self.plot_item.vb.viewRange()[0])

    def update_main_plot(self):
        if self.roi is not None:
            self.plot_item.setXRange(*self.roi.getRegion(), padding=0)

    def set_roi_region(self):
        if self.roi is not None:
            self.roi.setRegion(self.plot_item.vb.viewRange()[0])

    def on_roi_plot_toggled(self, checked):
        if checked:
            self.roi_plot_item = self.plot_widget.addPlot(row=1, col=0)
            self.roi_plot_item.setMaximumHeight(100)
            self.roi_plot = self.roi_plot_item.vb

            self.roi = pg.LinearRegionItem()
            self.roi.setZValue(-10)
            self.roi_plot.addItem(self.roi)

            self.roi.sigRegionChanged.connect(self.update_main_plot)
            self.plot_item.sigXRangeChanged.connect(self.update_roi_plot)

            self.update_roi_plot()
            self.set_roi_region()
        else:
            if self.roi_plot_item is not None:
                self.plot_widget.removeItem(self.roi_plot_item)
                self.roi_plot_item = None
                self.roi_plot = None
                self.roi = None

    def create_roi_region(self):
        if self.roi is None:
            self.roi = pg.LinearRegionItem()
            self.roi.setZValue(-10)
            self.roi_plot_item.addItem(self.roi)
            self.roi.sigRegionChanged.connect(self.update_main_plot)

    def remove_roi_region(self):
        if self.roi is not None:
            self.roi_plot_item.removeItem(self.roi)
            self.roi.sigRegionChanged.disconnect(self.update_main_plot)
            self.roi = None
            
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.trace_manager = TraceManager()
        self.plot_widget = PlotWidget(self.trace_manager, parent=self)
        self.layout.addWidget(self.plot_widget)

        self.trace_dock = TraceDock(self, self.trace_manager)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.trace_dock)

        self.add_trace_button = QtWidgets.QPushButton("Add Trace")
        self.add_trace_button.clicked.connect(self.add_trace)
        self.layout.addWidget(self.add_trace_button)

        self.setCentralWidget(self.central_widget)

        self.trace_dock.roiPlotEnabled.connect(self.plot_widget.on_roi_plot_enabled)

    def add_trace(self):
        trace = TraceGenerator.generate_random_trace(self.trace_manager.trace_mode)
        self.trace_manager.add_trace(trace)

class TraceGenerator:
    trace_counter = 1

    @staticmethod
    def generate_random_trace(mode='Group'):
        trace_name = f"Trace {TraceGenerator.trace_counter}"
        TraceGenerator.trace_counter += 1
        random_color = pg.intColor(random.randint(0, 255))
        x = np.arange(100)
        y = np.random.normal(loc=0, scale=20, size=100)
        trace = Trace(label=trace_name, color=random_color, mode=mode, data=y)
        return trace

if __name__ == "__main__":

    import sys    
    sys.argv += ['-platform', 'windows:darkmode=2']
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    main_window = MainWindow()
    main_window.show()
    app.exec()