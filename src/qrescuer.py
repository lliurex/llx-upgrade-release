#!/usr/bin/python3
# Copyright (c) 2023 LliureX Team
# This code is released under the GPL-3 terms
# https://www.gnu.org/licenses/gpl-3.0.en.html#license-text

import os,sys,subprocess,time
import llxupgrader
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QListWidget,QTextEdit, QCheckBox,QListWidgetItem
from PySide2 import QtGui
from PySide2.QtCore import QSize,Qt,QThread,Signal,QObject
from lliurex import lliurexup
import gettext
_ = gettext.gettext

i18n={"WLC":_("Welcome to the recovery mode"),
	"INFO":_("The upgrade process has ended with errors."),
	"GO_ONLINE":_("Try to enable the network and download broken packages from http://lliurex.net"),
	"NETWORK":_("Enable network"),
	"LOG":_("Show apt log"),
	"RELAUNCH":_("Launch lliurex-up"),
	"KONSOLE":_("Launch a terminal"),
	"REBOOT":_("Reboot")}


class qrescue(QWidget):
	def __init__(self,parent=None):
		super (qrescue,self).__init__(parent)
		self.noreturn=0
	#def __init__

	def closeEvent(self,event):
		if self.noreturn==1:
			event.ignore()
	#def closeEvent

	def _close(self):
		self.setEnabled(False)
		self.noreturn=0
	#def _close

	def renderGui(self):
		lay=QGridLayout()
		self.setLayout(lay)
		lbl=QLabel("<b>{}</b>".format(i18n.get("WLC")))
		lbl2=QLabel(i18n.get("INFO"))
		lay.addWidget(lbl,0,0,1,2)
		lay.addWidget(lbl2,1,0,1,2)
		btn_try=QPushButton(i18n.get("GO_ONLINE"))
		btn_try.clicked.connect(self._tryLaunch)
		lay.addWidget(btn_try,2,0,1,2)
		btn_net=QPushButton(i18n.get("NETWORK"))
		btn_net.clicked.connect(self._goOnline)
		lay.addWidget(btn_net,3,0,1,1)
		btn_log=QPushButton(i18n.get("LOG"))
		btn_log.clicked.connect(self._showLog)
		lay.addWidget(btn_log,3,1,1,1)
		btn_llx=QPushButton(i18n.get("RELAUNCH"))
		btn_llx.clicked.connect(self._relaunch)
		lay.addWidget(btn_llx,4,0,1,1)
		btn_tty=QPushButton(i18n.get("KONSOLE"))
		btn_tty.clicked.connect(self._konsole)
		lay.addWidget(btn_tty,4,1,1,1)
		self.show()
	#def renderGui

	def _tryLaunch(self):
		self._goOnline()
		self._relaunch()
	#def tryLaunch

	def _doFixes(self):
		llxupgrader.enableSystemdServices()
		llxupgrader.unfixAptSources()
		llxupgrader.removeAptConf()
		llxupgrader.undoHostsMod()
	#def _doFixes

	def _doClean(self):
		llxupgrader.clean()
		llxupgrader.unsetSystemdUpgradeTarget()
		llxupgrader.cleanLlxUpActions()
	#def _doClean

	def _goOnline(self):
		self._doFixes()
		cmd=["konsole","-e","nmtui"]
		subprocess.run(cmd)
	#def _goOnline

	def _showLog(self):
		logf="/var/log/apt/term.log"
		if os.path.isfile(logf):
			cmd=["/usr/bin/konsole","-e","less /var/log/apt/term.log"]
			subprocess.run(cmd)
	#def _showLog

	def _relaunch(self):
		self._doFixes()
		self._doClean()
		a=lliurexup.LliurexUpCore()
		a.cleanEnvironment()
		a.cleanLliurexUpLock()
		cmd=["/sbin/lliurex-up"]
		subprocess.run(cmd)
	#def _relaunch

	def _konsole(self):
		cmd=["konsole"]
		subprocess.run(cmd)
	#def _konsole

#class qrescuer

##### MAIN APP ######

app=QApplication(["Lliurex Release Upgrade - Repair"])
gui=qrescue()
gui.renderGui()
gui.show()
app.exec_()
