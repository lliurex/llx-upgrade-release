#!/usr/bin/python3

import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2.QtWidgets import QApplication, QWidget,QLabel,QGridLayout
from PySide2 import QtGui
from PySide2.QtCore import Qt,QThread,Signal
import llxupgrader

class Launcher(QThread):
	end=Signal([])
	def __init__(self,parent=None):
		super (Launcher,self).__init__(parent)
		self.cmd=[]
		self.check_output=False
		self.universal_newlines=True
		self.encoding="utf8"
	#def __init__

	def setCmd(cmd):
		if isinstance(cmd,str):
			self.cmd=cmd.split()
		elif isinstance(cmd,[]):
			self.cmd=cmd
	#def setCmd

	def run(self):
		prc=subprocess.run(self.cmd,universal_newlines=self.universal_newlines,encoding=self.encoding,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		self.end.emit([cmd,prc])
	#def run
#class Launcher

class Server(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type","text/html")
		self.end_headers()

class QServer(QThread):
	def __init__(self,parent=None):
		super (QServer,self).__init__(parent)

	def run(self):
		hostname="localhost"
		serverport=10080
		try:
			web=HTTPServer((hostname,serverport),Server)
			web.serve_forever()
		except Exception as e:
			print(e)


class bkgFixer(QWidget):
	def __init__(self,parent=None):
		super (bkgFixer,self).__init__(parent)
		#self.setWindowFlags(Qt.FramelessWindowHint)
		self.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.setWindowState(Qt.WindowFullScreen)
		self.setWindowFlags(Qt.WindowStaysOnBottomHint)
		#self.setWindowModality(Qt.WindowModal)
		self.img="/usr/share/llx-upgrade-release/rsrc/1024x768.jpg"
		self.lbl=QLabel()
		self.qserver=QServer()
		self.processDict={}
		self.noreturn=1
	#def __init__

	def renderBkg(self):
		lay=QGridLayout()
		self.setLayout(lay)
		self.lbl.setPixmap(self.img)
		self.lbl.setScaledContents(True)
		lay.addWidget(self.lbl)
		self.show()
	#def renderBkg

	def closeEvent(self,event):
		if self.noreturn==1:
			event.ignore()

	def doFixes(self):
		self.fixAptSources()
		ln=Launcher()
		cmd="/usr/bin/kwin"
		ln.setCmd(cmd)
		ln.end.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
		fixer.fakeLliurexNet()
		cmd='/sbin/lliurex-up -u -s -n'
		ln=Launcher()
		ln.setCmd(cmd)
		ln.end.connect(self._processEnd)
		ln.start()
	#def doFixes

	def fixAptsources(self):
		llxup_sources="/etc/apt/lliurexup_sources.list"
		if os.path.isfile(llxup_sources):
			shutil.copy("/etc/apt/sources.list",llxup_sources)
	#def fixAptsources

	def fakeLliurexNet(self):
		self._enableIpRedirect()
		self.qserver.start()
	#def fakeLliurexNet

	def _enableIpRedirect(self):
		cmd=["nslookup","lliurex.net"]
		output=subprocess.check_output(cmd,encoding="utf8",universal_newlines=True)
		for line in output:
			if line.startswith("Address:") and "127." not in line:
				ip=line.split[-1]
				cmd=["iptables","-t","nat","-A","OUTPUT","-d",ip,"-p","tcp","--dport","10080","-j","DNAT","--to-destination","127.0.0.1"]
				subprocess.run(cmd)
	#def _enableIpRedirect

	def _processEnd(self,*args):
		if "lliurex-up" in args[0].lower():
			self.processDict[args[0]].wait()
			print("ENDED: {}".format(args[1]))
			if prc.returncode!=0:
			#ERROR!!!!
				self._errorMode()
			else:
				self._undoFixes()
				self.showEnd()
	#def _processEnd

	def showEnd(self):
		cmd=["kdialog","--title","Lliurex Release Upgrade","--msgbox","Upgrade ended. Press to reboot".format(i18n.get("REBOOT"))]
		subprocess.run(cmd)
		cmd=["systemctl","reboot"]
		subprocess.run(cmd)
	#def showEnd

	def _undoFixes(self):
		self.unfixAptSources()
		self.removeAptConf()
		llxupgrader.clean()
	#def _undoFixes()

	def unfixAptsources(self):
		sources="/etc/apt/sources.list"
		f=open(sources,"w")
		f.close()
		cmd=["repoman-cli","-e","0","-y"]
		subprocess.run(cmd)
		self.fixAptSources()
	#def unfixAptsources

	def removeAptConf(self):
		aptconf="/etc/apt/apt.conf"
		tmpaptconf=os.path.join("/tmp/llx-update-release",os.path.basename(aptconf))
		if os.path.isfile(aptconf):
			os.unlink(aptconf)
		if os.path.isfile(tmpaptconf):
			shutil.copy(tmpaptconf,aptconf)
	#def removeAptConf

	def _errorMode(self):
		ln=Launcher()
		ln.setCmd("/usr/bin/konsole")
		ln.start()
		ln.end.connect(self._endErrorMode)
	#def _errorMode

	def _endErrorMode(self):
		pass

#def bkgFixer(self):
		

app=QApplication(["Llx-Upgrader"])
if __name__=="__main__":
	fixer=bkgFixer()
	fixer.renderBkg()
	fake.doFixes()
app.exec_()

