#!/usr/bin/python3

import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from PySide2.QtWidgets import QApplication, QWidget,QLabel,QGridLayout
from PySide2 import QtGui
from PySide2.QtCore import Qt,QThread

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
		self.th=QServer()
	#def __init__

	def renderBkg(self):
		lay=QGridLayout()
		self.setLayout(lay)
		self.lbl.setPixmap(self.img)
		self.lbl.setScaledContents(True)
		lay.addWidget(self.lbl)
		self.show()
	#def renderBkg

	def fakeLliurexNet(self):
		self._enableIpRedirect()
		self.th.start()
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

#def bkgFixer(self):
		

app=QApplication(["Llx-Upgrader"])
if __name__=="__main__":
	fixer=bkgFixer()
	fixer.renderBkg()
	fixer.fakeLliurexNet()
app.exec_()

