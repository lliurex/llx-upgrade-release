#!/usr/bin/python3

import os,subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2.QtWidgets import QApplication, QWidget,QLabel,QGridLayout
from PySide2 import QtGui
from PySide2.QtCore import Qt,QThread,QObject,Signal
import llxupgrader

class Launcher(QThread):
	processEnd=Signal(str,subprocess.CompletedProcess)
	def __init__(self,parent=None):
		super (Launcher,self).__init__(parent)
		self.cmd=[]
		self.check_output=False
		self.universal_newlines=True
		self.encoding="utf8"
	#def __init__

	def setCmd(self,cmd):
		if isinstance(cmd,str):
			self.cmd=cmd.split()
		elif isinstance(cmd,[]):
			self.cmd=cmd
	#def setCmd

	def run(self):
		prc=subprocess.run(self.cmd,universal_newlines=self.universal_newlines,encoding=self.encoding,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		print("---")
		print(self.cmd)
		print("---")
		self.processEnd.emit(" ".join(self.cmd),prc)
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
		self.hostname="localhost"

	def run(self):
		serverport=10080
		try:
			web=HTTPServer((self.hostname,serverport),Server)
			web.serve_forever()
		except Exception as e:
			print(e)
#class QServer

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
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
		fixer.fakeLliurexNet()
		cmd='/sbin/lliurex-up -u -s -n'
		ln=Launcher()
		ln.setCmd(cmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
	#def doFixes

	def fixAptSources(self):
		llxup_sources="/etc/apt/lliurexup_sources.list"
		if os.path.isfile(llxup_sources):
			shutil.copy("/etc/apt/sources.list",llxup_sources)
	#def fixAptsources

	def fakeLliurexNet(self):
		if self._enableIpRedirect()==0:
			pass
			#cmd=["hostname","lliurex.net"]
			#subprocess.run(cmd)
			#self.qserver.hostname="lliurex.net"
			#self._enableIpRedirect()
		self.qserver.start()
	#def fakeLliurexNet

	def _enableIpRedirect(self):
		cmd=["nslookup","lliurex.net"]
		local127=False
		try:
			output=subprocess.check_output(cmd,encoding="utf8",universal_newlines=True)
		except Exception as e:
			output=""
		for line in output.split("\n"):
			if line.startswith("Address:"):
				ip=line.split()[-1]
				if ip.startswith("127"):
					if not ip.endswith(".1"):
						continue
					local127=True
				cmd=["iptables","-t","nat","-A","OUTPUT","-d",ip,"-p","tcp","--dport","80","-j","DNAT","--to-destination","127.0.0.1:10080"]
				try:
					print(cmd)
					subprocess.run(cmd)
				except Exception as e:
					print("iptables: {}".format(e))
		if local127==False:
			cmd=["iptables","-t","nat","-A","OUTPUT","-d","127.0.0.1","-p","tcp","--dport","80","-j","DNAT","--to-destination","127.0.0.1:10080"]
			try:
				print(cmd)
				subprocess.run(cmd)
			except Exception as e:
				print("iptables: {}".format(e))
			
		self._modHosts()
		return(len(output))
	#def _enableIpRedirect

	def _modHosts(self):
		with open("/etc/apt/hosts","r") as f:
			fcontent=f.readlines(f)
		fcontent.append("127.0.0.1 lliurex.net")
		with open("/tmp/.hosts","w") as f:
			f.writelines(fcontent)
		cmd=["mount","/tmp/.hosts","etc/hosts"]
		os.subprocess.run(cmd)
	#def _modHosts(self):

	def _processEnd(self,prc,prcdata):
		if "lliurex-up" in prc.lower():
			#self.processDict[prc].wait()
			print("ENDED: {}".format(prcdata))
			if prcdata.returncode==0 and len(llxupgrader.getPkgsToUpdate())==0:
				self._undoFixes()
				self.showEnd()
			else:
				#ERROR!!!!
				self._errorMode()
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
		llxupgrader.unsetSystemdUpgradeTarget()
		llxupgrader.cleanLLxUpActions()
	#def _undoFixes()

	def unfixAptSources(self):
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
		cmd="/usr/bin/konsole"
		ln.setCmd(cmd)
		ln.start()
		ln.processEnd.connect(self._endErrorMode)
		self.processDict[cmd]=ln
	#def _errorMode

	def _endErrorMode(self):
		pass

#def bkgFixer(self):
		

app=QApplication(["Llx-Upgrader"])
if __name__=="__main__":
	fixer=bkgFixer()
	fixer.renderBkg()
	fixer.doFixes()
app.exec_()

