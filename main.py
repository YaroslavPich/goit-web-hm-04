from _datetime import datetime
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import mimetypes
from pathlib import Path
import socket
from threading import Thread
import urllib.parse

BASE_DIR = Path()
BUFFER_SIZE = 2048
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		pr_url = urllib.parse.urlparse(self.path)
		if pr_url.path == '/':
			self.send_html_file('index.html')
		elif pr_url.path == '/message':
			self.send_html_file('message.html')
		else:
			if BASE_DIR.joinpath(pr_url.path[1:]).exists():
				self.send_static()
			else:
				self.send_html_file('error.html', 404)

	def do_POST(self):
		data = self.rfile.read(int(self.headers['Content-Length']))
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
		client_socket.close()
		self.send_response(302)
		self.send_header('Location', '/message')
		self.end_headers()

	def send_html_file(self, filename, status=200):
		self.send_response(status)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		with open(filename, 'rb') as fd:
			self.wfile.write(fd.read())

	def send_static(self):
		self.send_response(200)
		mt = mimetypes.guess_type(self.path)
		if mt:
			self.send_header('Content-type', mt[0])
		else:
			self.send_header('Content-type', 'text/plain')
		self.end_headers()
		with open(f'.{self.path}', 'rb') as file:
			self.wfile.write(file.read())


def save_data_from_form(data):
	data_parse = urllib.parse.unquote_plus(data.decode())
	try:
		data_dict = {str(datetime.now()): {key: value for key, value in [el.split('=') for el in data_parse.split(('&'))]}}
		with open('storage/data.json', 'a', encoding='utf-8') as f:
			json.dump(data_dict, f, ensure_ascii=False, indent=4)
	except ValueError as err:
		logging.error(err)
	except OSError as err:
		logging.error(err)


def run_http_server(host, port):
	server_address = (host, port)
	http = HTTPServer(server_address, HttpHandler)
	logging.info('Starting http server')
	try:
		http.serve_forever()
	except KeyboardInterrupt:
		pass
	finally:
		http.server_close()


def run_socket_server(host, port):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_socket.bind((host, port))
	logging.info('Starting socket server')
	try:
		while True:
			msg, address = server_socket.recvfrom(BUFFER_SIZE)
			logging.info(f'Socket recieved {address}: {msg}')
			save_data_from_form(msg)
	except KeyboardInterrupt:
		pass
	finally:
		server_socket.close()


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

	server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
	server.start()

	server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
	server_socket.start()
