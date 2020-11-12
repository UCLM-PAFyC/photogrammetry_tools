# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5.QtWidgets import (QFrame, QGridLayout, QMainWindow, QAction, QLabel, QGroupBox, QTreeWidgetItem, QCheckBox,
                             QComboBox, QToolButton, QDockWidget, QSizePolicy)
from PyQt5.QtCore import QFileInfo, Qt
from PyQt5.QtGui import QIcon, QFont, QPalette

# Import QGIS classes
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapLayerComboBox
from qgis.core import QgsProject, QgsRasterLayer, QgsPointXY

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
                 path_workspace,
                 projected_images,
                 iPyProject,
                 pt_qt_project,
                 tool_digitize_feature,
                 parent=None):

        self.iface = iface
        self.path_workspace = path_workspace
        self.projected_images = projected_images
        self.tool_digitize_feature = tool_digitize_feature
        self.pt_qt_project = pt_qt_project
        self.iPyProject = iPyProject
        self.first_click = True

        super(PhToolsQImagesWidget, self).__init__(parent)
        self.setupUi(self)

        self.add_ribbon_images()



    def add_ribbon_images(self):
        #TODOC: initialize list qgis_projects & list qgsmapcavasses
        self.list_qgis_prjs = []
        self.list_qgsmapcavansses = []

        # initialize counters
        img_count = 0
        for image_key in self.projected_images:
            path_rlayer = os.path.normcase(os.path.join(self.path_workspace, image_key))
            rlayer = self.rlayer_builder(path_rlayer)
            if img_count == 0:
                prj, qgsmapcanvas = self.create_groupbox_map_canvas(rlayer, image_key, self.projected_images[image_key],
                                                                    img_count)
                self.list_qgis_prjs.append(prj)
                self.list_qgsmapcavansses.append(qgsmapcanvas)
                # prj_bis, qgsmapcanvas_bis = self.create_groupbox_map_canvas(rlayer, filename_img, img_count)
                # self.list_qgis_prjs.append(prj_bis)
                # self.list_qgsmapcavansses.append(qgsmapcanvas_bis)
            else:
                prj, qgsmapcanvas = self.create_groupbox_map_canvas(rlayer, image_key, self.projected_images[image_key],
                                                                    img_count)
                self.list_qgis_prjs.append(prj)
                # qgsmapcanvas.xyCoordinates.connect(self.on_xyCoordinates())
                self.list_qgsmapcavansses.append(qgsmapcanvas)
            img_count += 1
        if img_count:
            self.list_qgsmapcavansses[0].extentsChanged.connect(self.on_extent_changed)

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
        extent.scale(0.1, QgsPointXY(projected_point[0], -1.0 * projected_point[1]))
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

        return prj, qgsmapcanvas

    def on_extent_changed(self):
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
        points_count = self.tool_digitize_feature.size()
        if self.first_click:
            self.first_click = False
        elif points_count > 0:
            last_point = self.tool_digitize_feature.points()[points_count-1]
            # import pydevd_pycharm
            # pydevd_pycharm.settrace('localhost', port=54100, stdoutToServer=True, stderrToServer=True)
            digitized_points = self.tool_digitize_feature.points()
            digitized_points[points_count - 1] = QgsPointXY(last_point.x() + 20, last_point.y() + 20)
            self.tool_digitize_feature.setPoints(digitized_points)
            # self.tool_digitize_feature.undo()

            # ******************************************************************************************
            # point_id = self.iPyProject.ptCratePointFromObjectPoint(connectionPath, 'chunk 1', crsEpsgCode, pointCoordinates,
            #                                                   True)
            # point = self.iPyProject.ptGetPointFromId(point_id)
            self.pt_qt_project.points[last_point.x(), last_point.y(), 0] = 'point'
            # self.tool_digitize_feature.addVertex(QgsPointXY(point.x(), point.y())
            # digitized_points[points_count - 1] = QgsPointXY(point.x(), point.y())
            # self.tool_digitize_feature.setPoints(digitized_points)
            # ******************************************************************************************


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