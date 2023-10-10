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
	"INFO":_("The upgrade process has ended with errors"),
	"INFO1":_("If there's a network connection then try to upgrade from lliurex.net"),
	"INFO2":_("If you know about you're doing you can enable network and launch a konsole or retry the process."),
	"GO_ONLINE":_("Upgrade from lliurex.net"),
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
		if self.noreturn==0:
			event.ignore()
	#def closeEvent

	def _close(self):
		self.setEnabled(False)
		self.noreturn=1
	#def _close

	def renderGui(self):
		lay=QGridLayout()
		self.setLayout(lay)
		lbl_inf=QLabel("<b>{0}. {1}</b><br>".format(i18n.get("WLC"),i18n.get("INFO")))
		lay.addWidget(lbl_inf,0,0,1,2)
		lbl_inf1=QLabel("<p>{0}</p>".format(i18n.get("INFO1")))
		lbl_inf1.setWordWrap(True)
		lay.addWidget(lbl_inf1,1,0,1,2)
		btn_try=QPushButton("{}".format(i18n.get("GO_ONLINE")))
		btn_try.clicked.connect(self._tryLaunch)
		lay.addWidget(btn_try,2,0,1,1)
		lbl_inf2=QLabel("<br><p>{0}</p>".format(i18n.get("INFO2")))
		lay.addWidget(lbl_inf2,3,0,1,2,Qt.AlignTop)
		btn_net=QPushButton(i18n.get("NETWORK"))
		btn_net.clicked.connect(self._goOnline)
		lay.addWidget(btn_net,4,0,1,1)
		btn_log=QPushButton(i18n.get("LOG"))
		btn_log.clicked.connect(self._showLog)
		lay.addWidget(btn_log,4,1,1,1)
		btn_llx=QPushButton(i18n.get("RELAUNCH"))
		btn_llx.clicked.connect(self._relaunch)
		lay.addWidget(btn_llx,5,0,1,1)
		btn_tty=QPushButton(i18n.get("KONSOLE"))
		btn_tty.clicked.connect(self._konsole)
		lay.addWidget(btn_tty,5,1,1,1)
		btn_rbt=QPushButton(i18n.get("REBOOT"))
		btn_rbt.clicked.connect(self._reboot)
		lay.addWidget(btn_rbt,6,0,1,2,Qt.AlignCenter)
		self.show()
	#def renderGui

	def _tryLaunch(self):
		self._goOnline()
		self._relaunch()
	#def tryLaunch

	def _doFixes(self):
		llxupgrader.unfixAptSources()
		llxupgrader.removeAptConf()
		llxupgrader.undoHostsMod()
		llxupgrader._disableIpRedirect()
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

	def _reboot(self):
		self._doFixes()
		self._doClean()
		cmd=["systemctl","reboot"]
		subprocess.run(cmd)
	#def _reboot

#class qrescuer

##### MAIN APP ######

app=QApplication(["Lliurex Release Upgrade - Repair"])
gui=qrescue()
gui.renderGui()
gui.show()
app.exec_()
