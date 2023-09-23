#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostname="lliurex.net"
serverport=80

class Server(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type","text/html")
		self.end_headers()
		
if __name__=="__main__":
	web=HTTPServer((hostname,serverport),Server)
	web.serve_forever()

