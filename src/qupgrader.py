#!/usr/bin/python3

import os,subprocess,shutil,time
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2.QtWidgets import QApplication, QWidget,QLabel,QGridLayout,QPushButton
from PySide2 import QtGui
from PySide2.QtCore import Qt,QThread,QObject,Signal
import llxupgrader
from lliurex import lliurexup

class Watchdog(QThread):
	def __init__(self,parent=None):
		super (Watchdog,self).__init__(parent)
		self.file="/var/run/lliurex-up/sourceslist/default"

	def run(self):
		while os.path.isfile(self.file)==False:
			time.sleep(0.1)
		shutil.copy("/etc/apt/sources.list",self.file)
#class Watchdog

class ChkResults(QThread):
	processEnd=Signal(list)
	def __init__(self,parent=None):
		super (ChkResults,self).__init__(parent)
		self.encoding="utf8"
	#def __init__

	def run(self):
		pkgs=[]
		toupdate=llxupgrader.getPkgsToUpdate()
		pkgs.append(len(toupdate))
		llxup=lliurexup.LliurexUpCore()
		llxup.startLliurexUp()
		err=llxup.checkErrorDistUpgrade()
		if len(err)>0:
			pkgs=self._inspectError(err)
		print(pkgs)
		self.processEnd.emit(pkgs)
	#def run

	def _inspectError(self,error):
		pkglist=[]
		f=open("/tmp/err.log","w")
		if error[0]==True:
			errlist=error[1].split(",")
			f.writelines(errlist[1:])
			f.write("\n----\n")
			pkglist.append(errlist[0].split(":")[1].split(" ")[2])
			for line in errlist[1:]:
				l=line.strip()
				l=l.replace("'","")
				f.write("raw: {}*\n".format(line))
				f.write("start: *{}*\n".format(l[0:5]))
				if l.startswith("Inst"):
					f.write("{}".format(l))
					pkglist.append(l.split(" ")[1])
		f.write("{}".format(pkglist))
		f.close()
		return(pkglist)
#class chkResults 

class Launcher(QThread):
	processEnd=Signal(str,subprocess.CompletedProcess)
	def __init__(self,parent=None):
		super (Launcher,self).__init__(parent)
		self.dbg=False
		self.cmd=[]
		self.check_output=False
		self.universal_newlines=True
		self.encoding="utf8"
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("{}".format(msg))
	#def _debug

	def setCmd(self,cmd):
		if isinstance(cmd,str):
			self.cmd=cmd.split()
		elif isinstance(cmd,[]):
			self.cmd=cmd
	#def setCmd

	def run(self):
		self._debug("Launching {}".format(self.cmd))
		prc=subprocess.run(self.cmd,universal_newlines=self.universal_newlines,encoding=self.encoding,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		self.processEnd.emit(" ".join(self.cmd),prc)
	#def run
#class Launcher

class Server(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type","text/ascii")
		self.end_headers()
		wrkfile="/usr/share/llx-upgrade-release/files/Release"
		if os.path.isfile(wrkfile)==True:
			if os.path.basename(self.path)=="Release":
			#	if "jammy-updates" in self.path:
			#		with open("{}_up".format(wrkfile),"rb") as file:
			#			self.wfile.write(file.read())
			#	if "jammy-security" in self.path:
			#		with open("{}_se".format(wrkfile),"rb") as file:
			#			self.wfile.write(file.read())
			#	else:
				with open(wrkfile,"rb") as file:
					self.wfile.write(file.read())
	#def do_GET
#class Server

class QServer(QThread):
	def __init__(self,parent=None):
		super (QServer,self).__init__(parent)
		self.dbg=False
		self.hostname="localhost"
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("{}".format(msg))
	#def _debug

	def run(self):
		serverport=80
		try:
			self._debug("Server at {}:{} ".format(self.hostname,serverport))
			web=HTTPServer((self.hostname,serverport),Server)
			web.serve_forever()
		except Exception as e:
			print("***********")
			print(e)
			print("***********")
		finally:
			self._debug("server closed")
	#def run(self):
#class QServer

class qupgrader(QWidget):
	def __init__(self,parent=None):
		super (qupgrader,self).__init__(parent)
		self.dbg=False
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.setWindowState(Qt.WindowFullScreen)
		self.setWindowFlags(Qt.WindowStaysOnBottomHint)
		unattendedf="/tmp/.unattended"
		if os.path.exists(unattendedf)==True:
			self.upgradeCmd='konsole -e /sbin/lliurex-upgrade -u -s -n'
		else:
			self.upgradeCmd='/sbin/lliurex-up'
		self.img="/usr/share/llx-upgrade-release/rsrc/1024x768.jpg"
		self.wrkdir="/usr/share/llx-upgrade-release"
		self.tmpdir=os.path.join(self.wrkdir,"tmp")
		if os.path.isdir(self.tmpdir)==False:
			os.makedirs(self.tmpdir)
		self.lbl_img=QLabel()
		self.lbl_txt=QLabel("LLX-UPGRADER v1.0.0<br>{}".format(llxupgrader.i18n("BEGIN")))
		self.lbl_txt.setStyleSheet("color:white")
		self.btn_end=QPushButton()
		lbl=QLabel("<p>{0}</p><p><b>{1}</b></p>".format(llxupgrader.i18n("UPGRADEOK"),llxupgrader.i18n("PRESSREBOOT")))
		btnlay=QGridLayout()
		btnlay.addWidget(lbl,0,0,1,1,Qt.AlignCenter)
		lbl.setStyleSheet("margin:3px;padding:3px;border:1px solid silver;")
		self.btn_end.setLayout(btnlay)
		self.btn_end.setMinimumWidth(lbl.sizeHint().width()+2*(btnlay.contentsMargins().left()))
		self.btn_end.setMinimumHeight(lbl.sizeHint().height()+2*(btnlay.contentsMargins().top()))
		self.btn_end.setVisible(False)
		self.btn_end.clicked.connect(self._reboot)
		self.qserver=QServer()
		self.processDict={}
		self.noreturn=1
		self.oldCursor=self.cursor()
		cursor=QtGui.QCursor(Qt.WaitCursor)
		self.setCursor(cursor)
		self.grabKeyboard()
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("QUP: {}".format(msg))
	#def _debug

	def renderBkg(self):
		lay=QGridLayout()
		self.setLayout(lay)
		self.lbl_img.setPixmap(self.img)
		self.lbl_img.setScaledContents(True)
		lay.addWidget(self.lbl_img,0,0,1,1)
		lay.addWidget(self.lbl_txt,0,0,1,1,Qt.AlignTop|Qt.AlignLeft)
		lay.addWidget(self.btn_end,0,0,1,1,Qt.AlignCenter|Qt.AlignCenter)
		self.show()
	#def renderBkg

	def closeEvent(self,event):
		if self.noreturn==1:
			event.ignore()
	#def closeEvent

	def doFixes(self):
		ln=Launcher()
		cmd="/usr/bin/kwin --replace"
		ln.setCmd(cmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
		repof="/tmp/.repo"
		repo=""
		if os.path.exists(repof):
			with open(repof,"r") as f:
				repo=f.read().strip()
		llxupgrader.fixAptSources(repo)
		llxupgrader.disableSystemdServices()
		self.fakeLliurexNet()
		self.launchLlxUp()

		wd=Watchdog()
		wd.start()
		self.processDict["wd"]=wd
		self.setCursor(self.oldCursor)
	#def doFixes

	def launchLlxUp(self):
		ln=Launcher()
		ln.setCmd(self.upgradeCmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[self.upgradeCmd]=ln
	#def launchLlxUp

	def fakeLliurexNet(self):
		llxupgrader._enableIpRedirect()
		llxupgrader._modHosts()
		llxupgrader._modHttpd()
		llxupgrader._disableMirror()
		self.qserver.start()
	#def fakeLliurexNet

	def _processEnd(self,prc,prcdata):
		err=True
		self._debug("Check {}".format(prc))
		self._debug("Return: {}".format(prcdata))
		if os.path.basename(self.upgradeCmd).split()[0] in prc.lower():
			txt=self.lbl_txt.text()
			self.lbl_txt.setText("{0}<br>{1}".format(txt,llxupgrader.i18n("CHKRESULTS")))
			if prcdata.returncode==0:
				self.oldCursor=self.cursor()
				cursor=QtGui.QCursor(Qt.WaitCursor)
				self.setCursor(cursor)
				ln=ChkResults()
				ln.processEnd.connect(self._doChkResults)
				ln.start()
				self.processDict[self.upgradeCmd]=ln
			else:
				self._relaunchLlxUp()

		self._debug("End process {}".format(prc))
	#def _processEnd

	def _doChkResults(self,pkgs):
		err=True
		self.setCursor(self.oldCursor)
		txt=self.lbl_txt.text()
		txtpending="Packages pending: {}".format(pkgs)
		if len(pkgs)==0:
			err=False
		else:
			self._debug(txtpending)
			self.lbl_txt.setText("<p>{0}</p><p>{1}</p><p>{2}</p>".format(txt,llxupgrader.i18n("DOWNGRADE"),txtpending))
		if err==True:
			self._errorMode()
		else:
			self.lbl_txt.setText("<p>{0}</p><p>{1}</p><p>{2}</p>".format(txt,llxupgrader.i18n("UPGRADEEND"),llxupgrader.i18n("UPGRADEOK")))
			self._undoFixes()
			self.showEnd()
	#def _doChkResults

	def _relaunchLlxUp(self):
		llxup=lliurexup.LliurexUpCore()
		llxup.cleanEnvironment()
		llxup.cleanLliurexUpLock()
		ln=Launcher()
		ln.setCmd(self.upgradeCmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
	#def _relaunchLlxUp

	def showEnd(self):
		self.btn_end.setVisible(True)
	#def showEnd

	def _reboot(self):
		txt=self.lbl_txt.text()
		self.lbl_txt.setText("<p>{0}</p>".format("Init 6"))
		print("Rebooting")
		cmd=["systemctl","reboot"]
		subprocess.run(cmd)
	#def _reboot

	def _undoFixes(self):
		llxupgrader._disableIpRedirect()
		llxupgrader.unfixAptSources()
		llxupgrader.removeAptConf()
		llxupgrader.undoHostsMod()
		llxupgrader.clean()
		llxupgrader.unsetSystemdUpgradeTarget()
		llxupgrader.cleanLlxUpActions()
	#def _undoFixes()

	def _errorMode(self):
		self.releaseKeyboard()
		ln=Launcher()
		cmd=os.path.join(self.wrkdir,"qrescuer.py")
		ln.setCmd(cmd)
		ln.start()
		ln.processEnd.connect(self._endErrorMode)
		self.processDict[cmd]=ln
	#def _errorMode

	def _endErrorMode(self,prc,prcdata):
		if prcdata.returncode!=0:
			cmd=["/usr/bin/konsole"]
			subprocess.run(cmd)
		print("LAUNCH")
		print(prcdata)
		self._undoFixes()
		self.showEnd()
	#def _endErrorMode
#def qupgrader(self):
		
app=QApplication(["Llx-Upgrader"])
if __name__=="__main__":
	qup=qupgrader()
	qup.renderBkg()
	qup.doFixes()
app.exec_()

