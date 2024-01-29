# -*- coding: utf-8 -*-
"""
/***************************************************************************
#
# MODULE:       ui_tool_accuracy_report.py
# VERSION:      0.0.1 - first version
# AUTHOR(S):    David Hernández López
# PURPOSE:
# REQUIREMENT:
# DATE:         08/01/2024
#
 ***************************************************************************/
"""

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QTextBrowser

# Import PyQGIS classes


# Import Python classes
import os
import sys

# import self classes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'ui_phtools_accuracy_report_widget.ui'),
                               resource_suffix='')

class PhToolsAccuracyReportWidget(QDialog,
                                  FORM_CLASS):
    def __init__(self,
                 iface,
                 report_str,                 
                 parent=None):
        """Constructor"""       
        self.iface = iface
        self.report_str = report_str
        super(PhToolsAccuracyReportWidget, self).__init__(parent)
        self.setupUi(self)

        self.initialize()
        self.initilize_signals_slots()

    def initialize(self):
        """
        Método inicialización.
        """        
        self.accuracyReportTextBrowser.setLineWrapMode(QTextBrowser.NoWrap)
        self.accuracyReportTextBrowser.horizontalScrollBar().setValue(0)
        self.accuracyReportTextBrowser.setText(self.report_str)

    def initilize_signals_slots(self):
        """
        Connect signals / slots
        """
        pass

    def process(self):
        """
        """
        pass

    def ui_set_default_values_from_qsettings(self):
        """
        Establece los últimos valores introducidos en un procesamiento anterior recopilados del fichero qsetings.ini
        """
        pass