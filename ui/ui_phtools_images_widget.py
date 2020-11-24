# -*- coding: utf-8 -*-

POINT_TYPE_PROJECTED = 0
POINT_TYPE_MATCHED = 1
POINT_TYPE_MEASURED = 2
INITIAL_SCALE_FACTOR = 0.01

# Import PyQt5 classes
# from constant import *
import logging
from PyQt5 import uic
from PyQt5.QtWidgets import (QFrame, QGridLayout, QMainWindow, QAction, QLabel, QGroupBox, QTreeWidgetItem, QCheckBox,
                             QComboBox, QToolButton, QDockWidget, QSizePolicy, QMessageBox)
from PyQt5.QtCore import QFileInfo, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QWheelEvent

# Import QGIS classes
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapLayerComboBox, QgsMapMouseEvent
from qgis.core import QgsProject, QgsRasterLayer, QgsPointXY, QgsPoint

# Import Python classes
import os

import sys
sys.path.append(os.path.dirname(__file__))
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'ui_phtools_images_widget.ui'),
                               resource_suffix='')

class PhToolsQImagesWidget(QFrame,
                         FORM_CLASS):

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



    def add_ribbon_images(self):
        #TODOC: initialize list qgis_projects & list qgsmapcavasses
        self.list_qgis_prjs = []
        self.list_qgsmapcavansses = []
        self.list_qgsmapcavansses_dic = {}

        # initialize counters
        img_count = 0
        for image_key in self.projected_images:
            path_rlayer = os.path.normcase(self.image_paths[image_key])
            rlayer = self.rlayer_builder(path_rlayer)
            if img_count == 0:
                prj, qgsmapcanvas, group_box = self.create_groupbox_map_canvas(rlayer, image_key,
                                                                    self.projected_images[image_key]['Projected'],
                                                                    img_count)
                # self.list_qgis_prjs.append(prj)
                # self.list_qgsmapcavansses.append(qgsmapcanvas)
                self.list_qgsmapcavansses_dic[image_key] = ImageCanvas(self.i_py_project, self.connection_path, prj,
                                                                 self.digitizing_point_id, qgsmapcanvas, image_key,
                                                                 self.digitizing_feature_tool, group_box)


            else:
                prj, qgsmapcanvas, group_box = self.create_groupbox_map_canvas(rlayer, image_key,
                                                                    self.projected_images[image_key]['Projected'],
                                                                    img_count)

                # qgsmapcanvas.xyCoordinates.connect(self.on_xyCoordinates())

                self.list_qgsmapcavansses_dic[image_key] = ImageCanvas(self.i_py_project, self.connection_path, prj,
                                                                 self.digitizing_point_id, qgsmapcanvas, image_key,
                                                                 self.digitizing_feature_tool, group_box)

            self.list_qgsmapcavansses_dic[image_key].pointMeasured.connect(self.on_image_point_measured)
            self.list_qgsmapcavansses_dic[image_key].canvas.setWheelFactor(1.0)
            img_count += 1
        # if img_count:
        #     self.list_qgsmapcavansses[0].extentsChanged.connect(self.on_extent_changed)
        #     self.pantool = QgsPhToolPan(self.list_qgsmapcavansses[0])
        #     self.pantool.activate()


    def create_groupbox_map_canvas(self,
                                   rlayer,
                                   filename_img,
                                   projected_point,
                                   num_img,
                                   is_main_image=False):
        #TODOC:
        qgsmapcanvas = QgsMapCanvas()
        prj = QgsProject()
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
        qlabel_num_img = QLabel()
        str_num_img = "Nº img: " + str(num_img)
        qlabel_num_img.setText(str_num_img)
        qfont_label_num_img = self.format_qfont(int_size=7)
        qlabel_num_img.setFont(qfont_label_num_img)
        qlabel_num_img.setAttribute(Qt.WA_TransparentForMouseEvents)
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.blue)
        qlabel_num_img.setPalette(palette)

        if is_main_image:
            qgridlayout_mapcanvas_mainimg = QGridLayout()
            qgridlayout_mapcanvas_mainimg.addWidget(qgsmapcanvas)
            group_box.setLayout(qgridlayout_mapcanvas_mainimg)
            group_box.setCheckable(True)
            self.gridLayout_tabImg.addWidget(group_box)

            self.label_numImage.setText(str_num_img)
            self.label_currentCoordinates.setText("Coordinates")

            return prj, qgsmapcanvas

        # create central mark
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Plain)
        hline.setMaximumSize(16, 16)
        hline.setLineWidth(1)
        hline.setStyleSheet("color:yellow")

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)
        vline.setMaximumSize(16, 16)
        vline.setLineWidth(1)
        vline.setStyleSheet("color:yellow")

        crosshair_frame_v = QFrame()
        crosshair_layout_v = QGridLayout()
        crosshair_frame_v.setLayout(crosshair_layout_v)
        crosshair_layout_v.addWidget(vline)
        crosshair_frame_v.setAttribute(Qt.WA_TransparentForMouseEvents)

        crosshair_frame_h = QFrame()
        crosshair_layout_h = QGridLayout()
        crosshair_frame_h.setLayout(crosshair_layout_h)
        crosshair_layout_h.addWidget(hline)
        crosshair_frame_h.setAttribute(Qt.WA_TransparentForMouseEvents)

        # add qgsmapcanvas to ribbon
        qframe_ribbon_image_layout = QGridLayout()
        qframe_ribbon_image_layout.setContentsMargins(0, 0, 0, 0)
        qframe_ribbon_image_layout.setAlignment(Qt.AlignCenter)
        qframe_ribbon_image_layout.addWidget(qgsmapcanvas, 0, 0)
        qframe_ribbon_image_layout.addWidget(crosshair_frame_v, 0, 0)
        qframe_ribbon_image_layout.addWidget(crosshair_frame_h, 0, 0)
        qframe_ribbon_image_layout.addWidget(qlabel_num_img, 0, 0, Qt.AlignRight|Qt.AlignBottom)
        group_box.setLayout(qframe_ribbon_image_layout)
        group_box.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_images.addWidget(group_box)

        return prj, qgsmapcanvas, group_box

    def rlayer_builder(self,
                       path_rlayer):
        # Check if string is provided
        file_info = QFileInfo(path_rlayer)
        path = file_info.filePath()
        base_name = file_info.baseName()

        #TODO: que no pregunte por el CRS

        # https://gis.stackexchange.com/questions/27745/how-can-i-specify-the-crs-of-a-raster-layer-in-pyqgis/27765
        """
        dataset = gdal.Open(path_rlayer, GA_Update)
        print(path_rlayer)
        print(dataset)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(25830)
        dataset.SetProjection(srs.ExportToWkt())
        dataset = None
        """

        """
        qgs_coordinate_crs_project = QgsCoordinateReferenceSystem(25830,
                                                                  QgsCoordinateReferenceSystem.InternalCrsId)

        gdalDataSet = gdal.Open(path_rlayer, GA_Update)
        original_ogr_dtm_crs_wkt = gdalDataSet.GetProjection()
        original_qgs_coordinate_crs_project = QgsCoordinateReferenceSystem()
        find_crs = False
        if original_qgs_coordinate_crs_project.createFromString(original_ogr_dtm_crs_wkt):
            if qgs_coordinate_crs_project.InternalCrsId == original_qgs_coordinate_crs_project.InternalCrsId:
                find_crs = True
        if not find_crs:
            gdalDataSet.SetProjection(qgs_coordinate_crs_project.toWkt().encode('utf-8'))
        gdalDataSet = None
        """
        rlayer = QgsRasterLayer(path, base_name)

        """
        QgsProject.instance().addMapLayer(rlayer)
        if rlayer.isValid() is True:
            print("Layer was loaded successfully!")
        else:
            print("Unable to read basename and file path - Your string is probably invalid")
        """
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

    def scale_changed_main_img(self, current_scale):
        #TODOC
        if self.checkBox_linkZoomMainVsRibbonImgs.isChecked():
            factor_ui_magnified = float(self.comboBox_zoomFactorMainVsRibbonImgs.currentText())
            scale_magnified = factor_ui_magnified * current_scale
            print("scale_main_img_previous: \t" + (str(int(self.current_scale_main_img))))
            print("current_scale: \t\t\t" +(str(int(current_scale))))
            print("factor_ui_magnified: \t" + str(factor_ui_magnified))
            print("scale_magnified: \t\t\t" + str(scale_magnified))
            print("------------------------")

            contador = 0
            for qgsmapcavas_ribbon_img in self.list_qgsmapcavansses:
                if contador == 0:
                    pass
                else:
                    qgsmapcavas_ribbon_img.zoomScale(scale_magnified)
                    self.current_scale_main_img = current_scale
                contador += 1

    def on_image_point_measured(self):
        measured_images = {}
        for image_key in self.list_qgsmapcavansses_dic.keys():
            # If exists measured point
            image_canvas = self.list_qgsmapcavansses_dic[image_key]
            if image_canvas.image_points[2]:
                measured_images[image_key] = [image_canvas.image_points[2].x(), -1.0*image_canvas.image_points[2].y()]
        import pydevd_pycharm
        pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
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
            logging.warning('i_py_project.ptGetObjectPointFromMeasuredImages({},{},{},{},{},{})'.format(
                            self.connection_path, 'chunk 1',
                            self.digitizing_point_id, crs_epsg_code, True,
                            measured_images))
            ret = self.i_py_project.ptGetObjectPointFromMeasuredImages(self.connection_path, 'chunk 1',
                                                                       self.digitizing_point_id, crs_epsg_code, True,
                                                                       measured_images, [])
            logging.warning(str(ret))
            if ret[0] == 'True':
                points_count = self.digitizing_feature_tool.size()
                digitized_points = self.digitizing_feature_tool.points()
                digitized_points[points_count - 1] = QgsPointXY(ret[2][0], ret[2][1])
                # Deprecated: setPoints
                # digitized_points_sequence = self.digitizing_feature_tool.pointsZM()
                # digitized_points_sequence[points_count - 1] = QgsPoint(QgsPointXY(ret[2][0], ret[2][1]))
                # self.digitizing_feature_tool.setPoints(digitized_points_sequence)

                self.digitizing_feature_tool.setPoints(digitized_points)
                # Matches:
                if len(ret[5]):
                    for image_key in ret[5].keys():
                        if 'Matched' in ret[5][image_key].keys():
                            matched_point = QgsPointXY(ret[5][image_key]['Matched'][0],
                                                       -1.0*ret[5][image_key]['Matched'][1])
                            self.list_qgsmapcavansses_dic[image_key].image_points[POINT_TYPE_MATCHED] = matched_point
                            if 'Measured' not in ret[5][image_key].keys():
                                self.list_qgsmapcavansses_dic[image_key].centerCanvas(matched_point)


class QgsPhToolPan(QgsMapToolPan):
    canvasPressSignal = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        self.canvas = canvas
        super(QgsMapToolPan, self).__init__(self.canvas)

    def canvasDoubleClickEvent(self, e: QgsMapMouseEvent):
        e.accept()
        # self.canvas.zoomIn()

    def wheelEvent(self, e: QWheelEvent):
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
        if e.angleDelta().y() > 0:
            self.canvas.setWheelFactor(2)
            self.canvas.zoomIn()
            self.canvas.setWheelFactor(1)
        elif e.angleDelta().y() < 0:
            self.canvas.setWheelFactor(2)
            self.canvas.zoomOut()
            self.canvas.setWheelFactor(1)

        e.accept()


class ImageCanvas(QObject):
    """
        Canvas Item and auxiliary data for image canvas list
    """
    pointMeasured = pyqtSignal()

    def __init__(self, i_py_project, connection_path, qgis_project, digitizing_point_id, canvas, image_name,
                                                                         digitizing_feature_tool, group_box):
        super(QObject, self).__init__()
        self.canvas = canvas
        self.image_name = image_name
        self.digitizing_feature_tool = digitizing_feature_tool
        self.connection_path = connection_path
        self.i_py_project = i_py_project
        self.qgis_project = qgis_project
        self.group_box = group_box
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
        self.first_click = True
        self.digitizing_point_id = digitizing_point_id

    def on_extent_changed(self):
        points_count = self.digitizing_feature_tool.size()
        if self.first_click:
            self.first_click = False
        elif points_count > 0:
            current_center = self.canvas.center()
            """ QgsPointXY """
            self.image_points[POINT_TYPE_MEASURED] = current_center
            self.setMeasuredColor(True)
            self.pointMeasured.emit()

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

        self.canvas.extentsChanged.connect(self.on_extent_changed)



