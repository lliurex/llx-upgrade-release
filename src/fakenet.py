#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostname="localhost"
serverport=80

class Server(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type","text/html")
		self.end_headers()
		
if __name__=="__main__":
	try:
		web=HTTPServer((hostname,serverport),Server)
		web.serve_forever()
	except Exception as e:
		print(e)

