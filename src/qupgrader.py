#!/usr/bin/python3

import os,subprocess,shutil,time
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2.QtWidgets import QApplication, QWidget,QLabel,QGridLayout
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
		print("Launching {}".format(self.cmd))
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
		self.hostname="localhost"
	#def __init__

	def run(self):
		serverport=80
		try:
			print("SERVER READY")
			web=HTTPServer((self.hostname,serverport),Server)
			web.serve_forever()
		except Exception as e:
			print("***********")
			print(e)
			print("***********")
		finally:
			print("server closed")
	#def run(self):
#class QServer

class qupgrader(QWidget):
	def __init__(self,parent=None):
		super (qupgrader,self).__init__(parent)
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.setWindowState(Qt.WindowFullScreen)
		self.setWindowFlags(Qt.WindowStaysOnBottomHint)
		#self.setWindowModality(Qt.WindowModal)
		self.img="/usr/share/llx-upgrade-release/rsrc/1024x768.jpg"
		self.wrkdir="/usr/share/llx-upgrade-release/tmp"
		if os.path.isdir(self.wrkdir)==False:
			os.makedirs(self.wrkdir)
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
	#def closeEvent

	def doFixes(self):
		self.fixAptSources()
		ln=Launcher()
		cmd="/usr/bin/kwin --replace"
		ln.setCmd(cmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
		self.fakeLliurexNet()
		self.launchLlxUp()

		wd=Watchdog()
		wd.start()
		self.processDict["wd"]=wd
		self.disableSystemdServices()
	#def doFixes

	def launchLlxUp(self):
		cmd='/sbin/lliurex-up -u -s -n'
		ln=Launcher()
		ln.setCmd(cmd)
		ln.processEnd.connect(self._processEnd)
		with open("/etc/hosts","a") as f:
			f.write("\n")
		ln.start()
		self.processDict[cmd]=ln
	#def launchLlxUp

	def fixAptSources(self):
		llxup_sources="/etc/apt/lliurexup_sources.list"
		tmpllxup_sources=os.path.join(self.wrkdir,"lliurexup_sources.list")
		sources="/etc/apt/sources.list"
		if os.path.isfile(llxup_sources):
			os.unlink(llxup_sources)
		fcontent=[]
		fcontent.append("deb [trusted=yes] file:/usr/share/llx-upgrade-release/repo/ ./")
		#with open(sources,"r") as f:
		#	for line in f.readlines():
		#		if "file:" in line:
		#			continue
		#		fcontent.append(line)
		fcontent.append("")
		tmpsources=os.path.join(self.wrkdir,"sources.list")
		with open (tmpsources,"w") as f:
			f.writelines(fcontent)
		shutil.copy(tmpsources,sources)
		shutil.copy(tmpsources,llxup_sources)
	#def fixAptsources

	def fakeLliurexNet(self):
		self._enableIpRedirect()
		self._modHosts()
		self._modHttpd()
		self._disableMirror()
		print("LAUNCH")
		self.qserver.start()
	#def fakeLliurexNet

	def _enableIpRedirect(self):
		##DEPRECATED##
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
				cmd=["iptables","-t","nat","-A","OUTPUT","-d",ip,"-p","tcp","--dport","80","-j","DNAT","--to-destination","127.0.0.2"]
				try:
					subprocess.run(cmd)
				except Exception as e:
					print("iptables: {}".format(e))
		return(len(output))
	#def _enableIpRedirect

	def _modHosts(self):
		fcontent=[]
		tmphosts=os.path.join(self.wrkdir,"hosts")
		hosts="/etc/hosts"
		with open(hosts,"r") as f:
			for line in f.readlines():
				if "localhost" in line and "lliurex.net" not in line:
					line=line.replace("localhost","localhost lliurex.net",1)
				fcontent.append(line)

		with open(hosts,"w") as f:
			f.writelines(fcontent)
			f.write("\n")
		#cmd=["mount",tmphosts,"/etc/hosts","--bind"]
		#subprocess.run(cmd)
	#def _modHosts(self):

	def _modHttpd(self):
		files=["/etc/apache2/ports.conf","/etc/apache2/sites-available/000-default.conf"]
		for filen in files:
			fcontent=[]
			with open(filen,"r") as f:
				for line in f.readlines():
					if "Listen 80" in line or "<VirtualHost *:80>" in line:
						line=line.replace("80","10880")
					fcontent.append(line)
				tmpfilen=os.path.join(self.wrkdir,os.path.basename(filen))
				with open(tmpfilen,"w") as f:
					f.writelines(fcontent)
					f.write("\n")
				cmd=["mount",tmpfilen,filen,"--bind"]
				print("CMD: {}".format(" ".join(cmd)))
				try:
					subprocess.run(cmd)
				except Exception as e:
					print (e)
		cmd=["service","apache2","restart"]
		subprocess.run(cmd)
		print(cmd)
	#def _modHttpd(self)

	def _disableMirror(self):
		mirrorDir="/etc/lliurex-mirror/conf"
		srvPath="/srv"
		if os.path.isdir(mirrorDir):
			cmd=["mount",srvPath,mirrorDir,"--bind"]
			subprocess.run(cmd)
	#def _disableMirror

	def disableSystemdServices(self):
		for i in ["network-manager","systemd-networkd"]:
			cmd=["service",i,"stop"]
			subprocess.run(cmd)
		cmd=["systemctl","stop","network.target"]
		subprocess.run(cmd)
	#def disableSystemdServices

	def _processEnd(self,prc,prcdata):
		err=True
		if "lliurex-up" in prc.lower():
			#self.processDict[prc].wait()
			print("ENDED: {}".format(prcdata))
			if prcdata.returncode==0:
				if len(llxupgrader.getPkgsToUpdate())==0:
					err=False
			if err==True:
				if prcdata.returncode!=0:
					self._relaunchLlxUp()
				else:
					self._errorMode()
			else:
				self._undoFixes()
				self.showEnd()
		print("END")
	#def _processEnd

	def _relaunchLlxUp(self):
		a=lliurexup.LliurexUpCore()
		a.cleanEnvironment()
		a.cleanLliurexUpLock()
		cmd='/sbin/lliurex-up -u -s -n'
		ln=Launcher()
		ln.setCmd(cmd)
		ln.processEnd.connect(self._processEnd)
		ln.start()
		self.processDict[cmd]=ln
	#def _relaunchLlxUp

	def showEnd(self):
		cmd=["kdialog","--title","Lliurex Release Upgrade","--msgbox","Upgrade ended. Press to reboot".format(llxupgrader.i18n("UPGRADEEND"))]
		subprocess.run(cmd)
		cmd=["systemctl","reboot"]
		subprocess.run(cmd)
	#def showEnd

	def _undoFixes(self):
		self.unfixAptSources()
		self.removeAptConf()
		self.undoHostsMod()
		llxupgrader.clean()
		llxupgrader.unsetSystemdUpgradeTarget()
		llxupgrader.cleanLlxUpActions()
	#def _undoFixes()

	def undoHostsMod(self):
		hosts="/etc/hosts"
		fcontent=[]
		with open(hosts,"r") as f:
			for line in f.readlines():
				if "localhost" in line and " lliurex.net" in line:
					line=line.replace(" lliurex.net","")
				fcontent.append(line)
		with open(hosts,"w") as f:
			f.writelines(fcontent)
			f.write("\n")
	#def undoHostsMod

	def unfixAptSources(self):
		sources="/etc/apt/sources.list"
		llxup_sources="/etc/apt/lliurexup_sources.list"
		f=open(sources,"w")
		f.close()
		cmd=["repoman-cli","-e","0","-y"]
		subprocess.run(cmd)
		if os.path.isfile(llxup_sources):
			os.unlink(llxup_sources)
		os.copy(sources,llxup_sources)
	#def unfixAptsources

	def removeAptConf(self):
		aptconf="/etc/apt/apt.conf"
		tmpaptconf=os.path.join(self.wrkdir,os.path.basename(aptconf))
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

#def qupgrader(self):
		

app=QApplication(["Llx-Upgrader"])
if __name__=="__main__":
	qup=qupgrader()
	qup.renderBkg()
	qup.doFixes()
app.exec_()

