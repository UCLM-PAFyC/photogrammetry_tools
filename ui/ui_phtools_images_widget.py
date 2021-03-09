# -*- coding: utf-8 -*-

POINT_TYPE_PROJECTED = 0
POINT_TYPE_MATCHED = 1
POINT_TYPE_MEASURED = 2
INITIAL_SCALE_FACTOR = 0.01
WHEEL_FACTOR = 2
CANVAS_RLAYER_EXTENT_FACTOR = 2.0

# Import PyQt5 classes
# from constant import *
import logging
from PyQt5 import uic
from PyQt5.QtWidgets import (QFrame, QGridLayout, QMainWindow, QAction, QLabel, QGroupBox, QTreeWidgetItem, QCheckBox,
                             QComboBox, QToolButton, QDockWidget, QSizePolicy, QMessageBox)
from PyQt5.QtCore import QFileInfo, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QWheelEvent, QPixmap

# Import QGIS classes
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapLayerComboBox, QgsMapMouseEvent
from qgis.core import QgsProject, QgsRasterLayer, QgsPointXY, QgsPoint, QgsCoordinateReferenceSystem

# Import Python classes
import os, sys, math

sys.path.append(os.path.dirname(__file__))
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'ui_phtools_images_widget.ui'),
                               resource_suffix='')

class PhToolsQImagesWidget(QFrame,
                         FORM_CLASS):
    debugTextGenerated = pyqtSignal(str)
    reportGenerated = pyqtSignal(str)
    newVertexCoords = pyqtSignal(QgsPoint)

    def __init__(self,
                 iface,
                 connection_path,
                 digitizing_point_id,
                 image_paths,
                 projected_images,
                 iPyProject,
                 pt_qt_project,
                 digitizing_feature_tool,
                 parent=None):

        self.iface = iface
        self.connection_path = connection_path
        self.image_paths = image_paths
        self.projected_images = projected_images
        self.digitizing_feature_tool = digitizing_feature_tool
        self.pt_qt_project = pt_qt_project
        self.i_py_project = iPyProject
        self.first_click = True
        self.digitizing_point_id = digitizing_point_id

        super(PhToolsQImagesWidget, self).__init__(parent)
        self.setupUi(self)

        self.add_ribbon_images()


    def add_ribbon_images_map_canvas(self, image_key):
        path_rlayer = os.path.normcase(self.image_paths[image_key])
        rlayer = self.rlayer_builder(path_rlayer)
        rlayer_extent = rlayer.extent()
        x_offset = abs(rlayer_extent.width() / 2 - self.projected_images[image_key]['Projected'][0])
        y_offset = abs(rlayer_extent.height() / 2 - self.projected_images[image_key]['Projected'][1])
        center_offset = math.sqrt(x_offset ** 2 + y_offset ** 2)

        index = 0

        for image in self.list_qgsmapcavansses_dic.keys():
            if self.list_qgsmapcavansses_dic[image].distance_from_image_center < center_offset:
                index += 1
            else:
                break

        prj, qgsmapcanvas, group_box = self.create_groupbox_map_canvas(rlayer, image_key,
                                                                       self.projected_images[image_key]['Projected'],
                                                                       index=index)

        # qgsmapcanvas.xyCoordinates.connect(self.on_xyCoordinates())

        image_canvas = ImageCanvas(self.i_py_project, self.connection_path, prj,
                                                               self.digitizing_point_id, qgsmapcanvas, image_key,
                                                               self.digitizing_feature_tool, group_box,
                                                               center_offset)
        self.list_qgsmapcavansses_dic[image_key] = image_canvas

        self.list_qgsmapcavansses_dic[image_key].pointMeasured.connect(self.on_image_point_measured)

    def add_ribbon_images(self):
        #TODOC: initialize list qgis_projects & list qgsmapcavasses
        self.list_qgis_prjs = []
        self.list_qgsmapcavansses_dic = {}

        # initialize counters
        img_count = 0

        ## Ordenar imágenes según lo centrado que está su punto proyectado
        offsets = {}
        for image_key in self.projected_images:
            path_rlayer = os.path.normcase(self.image_paths[image_key])
            rlayer = self.rlayer_builder(path_rlayer)
            rlayer_extent = rlayer.extent()
            x_offset = abs(rlayer_extent.width()/2 - self.projected_images[image_key]['Projected'][0])
            y_offset = abs(rlayer_extent.height() / 2 - self.projected_images[image_key]['Projected'][1])
            center_offset = math.sqrt(x_offset**2 + y_offset**2)
            offsets[image_key] = [center_offset, rlayer]
        sorted_offsets = dict(sorted(offsets.items(), key=lambda item: item[1]))
        ###

        for image_key in sorted_offsets:
            # path_rlayer = os.path.normcase(self.image_paths[image_key])
            # rlayer = self.rlayer_builder(path_rlayer)
            rlayer = sorted_offsets[image_key][1]

            prj, qgsmapcanvas, group_box = self.create_groupbox_map_canvas(rlayer, image_key,
                                                                self.projected_images[image_key]['Projected'])

            # qgsmapcanvas.xyCoordinates.connect(self.on_xyCoordinates())

            self.list_qgsmapcavansses_dic[image_key] = ImageCanvas(self.i_py_project, self.connection_path, prj,
                                                             self.digitizing_point_id, qgsmapcanvas, image_key,
                                                             self.digitizing_feature_tool, group_box,
                                                             sorted_offsets[image_key][0])

            self.list_qgsmapcavansses_dic[image_key].pointMeasured.connect(self.on_image_point_measured)
            self.list_qgsmapcavansses_dic[image_key].userZoomSignal.connect(self.on_user_zoom)
            # self.list_qgsmapcavansses_dic[image_key].canvas.setWheelFactor(1.0)
        # if img_count:
        #     self.list_qgsmapcavansses[0].extentsChanged.connect(self.on_extent_changed)
        #     self.pantool = QgsPhToolPan(self.list_qgsmapcavansses[0])
        #     self.pantool.activate()


    def create_groupbox_map_canvas(self,
                                   rlayer,
                                   filename_img,
                                   projected_point,
                                   index=None,
                                   is_main_image=False):
        #TODOC:
        qgsmapcanvas = QgsMapCanvas()
        # qgsmapcanvas.setDestinationCrs(QgsCoordinateReferenceSystem())
        # rlayer.setCrs(QgsCoordinateReferenceSystem())
        prj = QgsProject()
        # prj.setCrs(QgsCoordinateReferenceSystem())
        prj.addMapLayer(rlayer)
        qgsmapcanvas.setLayers([rlayer])
        qgsmapcanvas.zoomToFullExtent()
        # qgsmapcanvas.zoomWithCenter(projected_point[0], -1.0 * projected_point[1], True)
        extent = qgsmapcanvas.extent()
        extent.scale(INITIAL_SCALE_FACTOR, QgsPointXY(projected_point[0], -1.0 * projected_point[1]))
        qgsmapcanvas.setExtent(extent)
        qgsmapcanvas.setContentsMargins(0, 0, 0, 0)

        # create qgroupbox
        group_box = QGroupBox(filename_img)
        # if num_img == 0:
        #     qfont_label_groupbox = self.format_qfont(is_bold=True)
        #     palette = QPalette()
        #     palette.setColor(QPalette.WindowText, Qt.red)
        #     group_box.setPalette(palette)
        #     group_box.setFont(qfont_label_groupbox)
        # else:
        qfont_label_groupbox = self.format_qfont()
        group_box.setFont(qfont_label_groupbox)
        group_box.setCheckable(True)
        group_box.setMinimumHeight(300)
        group_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # qlabel imagen number
        # qlabel_num_img = QLabel()
        # str_num_img = "Nº img: " + str(num_img)
        # qlabel_num_img.setText(str_num_img)
        # qfont_label_num_img = self.format_qfont(int_size=7)
        # qlabel_num_img.setFont(qfont_label_num_img)
        # qlabel_num_img.setAttribute(Qt.WA_TransparentForMouseEvents)
        # palette = QPalette()
        # palette.setColor(QPalette.WindowText, Qt.blue)
        # qlabel_num_img.setPalette(palette)

        if is_main_image:
            qgridlayout_mapcanvas_mainimg = QGridLayout()
            qgridlayout_mapcanvas_mainimg.addWidget(qgsmapcanvas)
            group_box.setLayout(qgridlayout_mapcanvas_mainimg)
            group_box.setCheckable(True)
            self.gridLayout_tabImg.addWidget(group_box)

            # self.label_numImage.setText(str_num_img)
            self.label_currentCoordinates.setText("Coordinates")

            return prj, qgsmapcanvas

        # create central mark
        # hline = QFrame()
        # hline.setFrameShape(QFrame.HLine)
        # hline.setFrameShadow(QFrame.Plain)
        # hline.setMaximumSize(16, 16)
        # hline.setLineWidth(1)
        # hline.setStyleSheet("color:red")
        #
        # vline = QFrame()
        # vline.setFrameShape(QFrame.VLine)
        # vline.setFrameShadow(QFrame.Plain)
        # vline.setMaximumSize(16, 16)
        # vline.setLineWidth(1)
        # vline.setStyleSheet("color:red")

        crosshair_label = QLabel()
        crosshair_label.setWindowFlags(Qt.FramelessWindowHint)
        p = QPixmap(["16 16 3 1",
                     "      c None",
                     ".     c #FF0000",
                     "+     c #FFFFFF",
                     "                ",
                     "       +.+      ",
                     "      ++.++     ",
                     "     +.....+    ",
                     "    +.     .+   ",
                     "   +.   .   .+  ",
                     "  +.    .    .+ ",
                     " ++.    .    .++",
                     " ... ...+... ...",
                     " ++.    .    .++",
                     "  +.    .    .+ ",
                     "   +.   .   .+  ",
                     "   ++.     .+   ",
                     "    ++.....+    ",
                     "      ++.++     ",
                     "       +.+      "])

        crosshair_label.setAlignment(Qt.AlignCenter)
        crosshair_label.setPixmap(p)
        crosshair_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # crosshair_frame_v = QFrame()
        # crosshair_layout_v = QGridLayout()
        # crosshair_frame_v.setLayout(crosshair_layout_v)
        # crosshair_layout_v.addWidget(vline)
        # crosshair_frame_v.setAttribute(Qt.WA_TransparentForMouseEvents)
        #
        # crosshair_frame_h = QFrame()
        # crosshair_layout_h = QGridLayout()
        # crosshair_frame_h.setLayout(crosshair_layout_h)
        # crosshair_layout_h.addWidget(hline)
        # crosshair_frame_h.setAttribute(Qt.WA_TransparentForMouseEvents)

        # add qgsmapcanvas to ribbon
        qframe_ribbon_image_layout = QGridLayout()
        qframe_ribbon_image_layout.setContentsMargins(0, 0, 0, 0)
        qframe_ribbon_image_layout.setAlignment(Qt.AlignCenter)
        qframe_ribbon_image_layout.addWidget(qgsmapcanvas, 0, 0)
        # qframe_ribbon_image_layout.addWidget(crosshair_frame_v, 0, 0)
        # qframe_ribbon_image_layout.addWidget(crosshair_frame_h, 0, 0)
        qframe_ribbon_image_layout.addWidget(crosshair_label, 0, 0)

        # qframe_ribbon_image_layout.addWidget(qlabel_num_img, 0, 0, Qt.AlignRight|Qt.AlignBottom)
        group_box.setLayout(qframe_ribbon_image_layout)
        group_box.setContentsMargins(0, 0, 0, 0)

        if index:
            self.verticalLayout_images.insertWidget(index, group_box)
        else:
            self.verticalLayout_images.addWidget(group_box)

        return prj, qgsmapcanvas, group_box

    def rlayer_builder(self,
                       path_rlayer):
        # Check if string is provided
        file_info = QFileInfo(path_rlayer)
        path = file_info.filePath()
        base_name = file_info.baseName()

        layer_options = QgsRasterLayer.LayerOptions()
        layer_options.skipCrsValidation = True
        rlayer = QgsRasterLayer(path, base_name, "gdal", layer_options)

        return rlayer

    def format_qfont(self,
                     str_fuente="Calibri",
                     int_size=8,
                     is_bold=False,
                     is_italic=False):
        #TODOC:
        qfont = QFont(str_fuente, int_size)
        if is_bold: qfont.setBold(True)
        else: qfont.setBold(False)
        if is_italic: qfont.setItalic(True)
        else: qfont.setItalic(False)
        return qfont

    def on_user_zoom(self, image_name, is_in):
        for image_key in self.list_qgsmapcavansses_dic.keys():
            if not image_key is image_name:
                if is_in:
                    self.list_qgsmapcavansses_dic[image_key].canvas.zoomIn()
                else:
                    self.list_qgsmapcavansses_dic[image_key].canvas.zoomOut()


    def on_image_point_measured(self):
        measured_images = {}
        disabled_images = []
        for image_key in self.list_qgsmapcavansses_dic.keys():
            # If exists measured point
            image_canvas = self.list_qgsmapcavansses_dic[image_key]
            if not image_canvas.group_box.isChecked():
                disabled_images.append(image_key)
            elif image_canvas.image_points[2]:
                measured_images[image_key] = [image_canvas.image_points[2].x(), -1.0*image_canvas.image_points[2].y()]

        if len(measured_images):
            crs = QgsProject.instance().crs()
            is_valid_crs = crs.isValid()
            crs_auth_id = crs.authid()
            if not "EPSG:" in crs_auth_id:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("---")
                msg_box.setText("Selected CRS is not EPSG")
                msg_box.exec_()
                return
            crs_epsg_code = int(crs_auth_id.replace('EPSG:', ''))

            # # TODO: CHUNK!!!
            logging.warning('#')
            logging.warning('i_py_project.ptGetObjectPointFromMeasuredImages({},{},{},{},{},{},{},{},{}'.format(
                            self.connection_path, 'chunk 1',
                            self.digitizing_point_id, crs_epsg_code, True, True, False,
                            measured_images, disabled_images))
            ret = self.i_py_project.ptGetObjectPointFromMeasuredImages(self.connection_path, 'chunk 1',
                                                                       self.digitizing_point_id, crs_epsg_code, True,
                                                                       True, False, measured_images, [])
            logging.warning(str(ret))
            # import pydevd_pycharm
            # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
            if ret[0] == 'True':
                if not self.digitizing_feature_tool.isActive() or self.digitizing_feature_tool.mode() == 1:  # CapturePoint
                    self.newVertexCoords.emit(QgsPoint(ret[2][0], ret[2][1], ret[2][2]))
                else:
                    points_count = self.digitizing_feature_tool.size()
                    self.digitizing_feature_tool.digitized_points_z[points_count - 1] = ret[2][2]
                    if points_count == 1:
                        self.digitizing_feature_tool.stopCapturing()
                        self.digitizing_feature_tool.startCapturing()
                    else:
                        self.digitizing_feature_tool.undo()
                    self.digitizing_feature_tool.addVertex(QgsPointXY(ret[2][0], ret[2][1]))

                    # Deprecated: setPoints

                    # Valido dedes QGIS 3.12:
                    # ***********************
                    # digitized_points_sequence = self.digitizing_feature_tool.pointsZM()
                    # digitized_points_sequence[points_count - 1] = QgsPoint(ret[2][0], ret[2][1], ret[2][2])
                    # self.digitizing_feature_tool.setPoints(digitized_points_sequence)
                    # ***********************

                ## Eliminar los canvas de las imágenes que ya no intervienen y añadir los nuevos
                for image_key in self.list_qgsmapcavansses_dic.keys():
                    if image_key not in ret[5].keys():
                        self.verticalLayout_images.removeWidget(self.list_qgsmapcavansses_dic[image_key].group_box)

                for image_key in ret[5].keys():
                    if image_key not in self.list_qgsmapcavansses_dic.keys():
                        self.projected_images[image_key] = ret[5][image_key]
                        self.add_ribbon_images_map_canvas(image_key)
                ##

                self.debugTextGenerated.emit('Número de Imágenes: {}'.format(self.list_qgsmapcavansses_dic.__len__()))
                self.debugTextGenerated.emit('\n---------------------------')
                self.debugTextGenerated.emit('\nObject Point: {}, {}, {}'.format(ret[2][0], ret[2][1], ret[2][2]))
                if len(ret[5]):
                    self.debugTextGenerated.emit('\n---------------------------')
                    self.debugTextGenerated.emit('\n---------------------------')
                    for image_key in ret[5].keys():
                        debug_str = image_key
                        if 'Matched' in ret[5][image_key].keys():
                            matched_point = QgsPointXY(ret[5][image_key]['Matched'][0],
                                                       -1.0*ret[5][image_key]['Matched'][1])
                            debug_str += '\nMatched: Point({} {})'.format(ret[5][image_key]['Matched'][0],
                                                                        ret[5][image_key]['Matched'][1])
                            self.list_qgsmapcavansses_dic[image_key].image_points[POINT_TYPE_MATCHED] = matched_point
                            if 'Measured' not in ret[5][image_key].keys():
                                self.list_qgsmapcavansses_dic[image_key].centerCanvas(matched_point)
                                self.list_qgsmapcavansses_dic[image_key].current_center = matched_point

                        if 'Measured' in ret[5][image_key].keys():
                            debug_str += '\nMeasured: Point({} {})'.format(ret[5][image_key]['Measured'][0],
                                                                            ret[5][image_key]['Measured'][1])
                        if 'Projected' in ret[5][image_key].keys():
                            debug_str += '\nProjected: Point({} {})'.format(ret[5][image_key]['Projected'][0],
                                                                            ret[5][image_key]['Projected'][1])
                        self.debugTextGenerated.emit(debug_str + '\n---------------------------')

                # Report:
                ret = self.i_py_project.ptGetObjectPointReport(self.connection_path, 'chunk 1',
                                                                       self.digitizing_point_id, crs_epsg_code)
                if ret[0]:
                    self.reportGenerated.emit(ret[1])

class QgsPhToolPan(QgsMapToolPan):
    canvasPressSignal = pyqtSignal(QgsPointXY)
    userZoomSignal = pyqtSignal(bool)

    def __init__(self, canvas):
        self.canvas = canvas
        super(QgsMapToolPan, self).__init__(self.canvas)

    def canvasDoubleClickEvent(self, e: QgsMapMouseEvent):
        e.accept()
        # self.canvas.zoomIn()

    def wheelEvent(self, e: QWheelEvent):
        if e.angleDelta().y() > 0:
            # self.canvas.setWheelFactor(WHEEL_FACTOR)
            self.canvas.zoomIn()
            self.userZoomSignal.emit(True)
            # self.canvas.setWheelFactor(1)
        elif e.angleDelta().y() < 0:
            # self.canvas.setWheelFactor(WHEEL_FACTOR)
            scale = self.canvas.scale()
            extent = self.canvas.extent()

            if len(self.canvas.layers()) and \
                    extent.height() < self.canvas.layers()[0].extent().height() * CANVAS_RLAYER_EXTENT_FACTOR:
                self.canvas.zoomOut()
                self.userZoomSignal.emit(False)
            # self.canvas.setWheelFactor(1)
        e.accept()


class ImageCanvas(QObject):
    """
        Canvas Item and auxiliary data for image canvas list
    """
    pointMeasured = pyqtSignal()
    userZoomSignal = pyqtSignal(str, bool)

    def __init__(self, i_py_project, connection_path, qgis_project, digitizing_point_id, canvas, image_name,
                                                                         digitizing_feature_tool, group_box,
                                                                         distance_from_image_center):
        super(QObject, self).__init__()
        self.canvas = canvas
        self.current_center = self.canvas.center()
        self.image_name = image_name
        self.digitizing_feature_tool = digitizing_feature_tool
        self.connection_path = connection_path
        self.i_py_project = i_py_project
        self.qgis_project = qgis_project
        self.group_box = group_box
        self.distance_from_image_center = distance_from_image_center
        """
        pt.POINT_TYPE_PROJECTED: QgsPoint(0, 0, 0)
        """
        self.image_points = {POINT_TYPE_PROJECTED: None,
                             POINT_TYPE_MATCHED: None,
                             POINT_TYPE_MEASURED: None}

        self.canvas.extentsChanged.connect(self.on_extent_changed)
        self.pan_tool = QgsPhToolPan(self.canvas)
        # self.pan_tool.activate()
        self.canvas.setMapTool(self.pan_tool)
        self.pan_tool.userZoomSignal.connect(self.on_user_zoom)
        self.first_click = True
        self.digitizing_point_id = digitizing_point_id

    def on_user_zoom(self, is_in):
        self.userZoomSignal.emit(self.image_name, is_in)

    def on_extent_changed(self):
        points_count = self.digitizing_feature_tool.size()
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
        if self.first_click:
            self.first_click = False
        else:
            ignore_sensor_percentage = float(self.digitizing_feature_tool.parameters['OPM_IgnoredSensorPercentage'])
            layer_extent = self.canvas.layers()[0].extent()
            reduced_layer_extent = layer_extent.scaled(1 - ignore_sensor_percentage*2/100)
            if not reduced_layer_extent.contains(self.canvas.center()):
            # if not self.canvas.layers()[0].extent().contains(self.canvas.center()):
                self.canvas.setCenter(self.current_center)
            elif not self.current_center == self.canvas.center():
                # if points_count > 0 or self.digitizing_feature_tool.mode() == 1: # CapturePoint
                """ QgsPointXY """
                self.image_points[POINT_TYPE_MEASURED] = self.canvas.center()
                self.setMeasuredColor(True)
                self.pointMeasured.emit()
        self.current_center = self.canvas.center()

    def setMeasuredColor(self, measured):

        if measured:
            font = self.group_box.font()
            font.setBold(True)
            self.group_box.setFont(font)
            palette = self.group_box.palette()
            palette.setColor(QPalette.Normal, QPalette.ColorRole.WindowText, QColor(78, 255, 83))
            self.group_box.setPalette(palette)
        else:
            font = self.group_box.font()
            font.setBold(False)
            self.group_box.setFont(font)
            palette = self.group_box.palette()
            palette.setColor(QPalette.Normal, QPalette.ColorRole.WindowText, QColor(78, 255, 83))
            self.group_box.setPalette(palette)

    def centerCanvas(self, point):
        """ center de canvas extent in point
            Parameters:
            point (QgsPointXY)
        """
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
        self.canvas.extentsChanged.disconnect(self.on_extent_changed)

        extent = self.canvas.extent()
        extent.scale(1, point)
        self.canvas.setExtent(extent)
        self.canvas.refresh()

        self.canvas.extentsChanged.connect(self.on_extent_changed)



