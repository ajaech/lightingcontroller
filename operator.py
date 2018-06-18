#encoding: utf-8
import json
import logging
import pigpio
import time
import random
from cgi import parse_header
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer


logging.basicConfig(filename='log.txt', filemode='a', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
logging.getLogger().addHandler(logging.StreamHandler())
logging.info('starting up')

# load the color names
with open('colors.json', 'r') as f:
  colors = json.load(f)

pi = pigpio.pi()  # initialize pigpio

def SetColor(rgb):
  r = int(rgb[1:3], 16)
  g = int(rgb[3:5], 16)
  b = int(rgb[5:7], 16)

  pi.set_PWM_dutycycle(17, r)
  pi.set_PWM_dutycycle(22, g)
  pi.set_PWM_dutycycle(24, b)


def MatchColor(request):
  if request in colors:
    logging.info(colors[request])
    SetColor(colors[request])


PORT_NUMBER = 80

class myHandler(BaseHTTPRequestHandler):

  #Handler for the GET requests
  def do_GET(self):
    logging.info('get request received')
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    # Send the html message
    self.wfile.write("Hello World !")
    return

  def do_POST(self):
    logging.info('post request received')
    ctype, pdict = parse_header(self.headers['content-type'])
    length = int(self.headers['Content-Length'])
    contents = self.rfile.read(length).lower()
    logging.info('contents')
    MatchColor(contents)


try:
  server = HTTPServer(('', PORT_NUMBER), myHandler)
  logging.info('started server on port {0}'.format(PORT_NUMBER))

  server.serve_forever()

except KeyboardInterrupt:
  logging.info('shutting down')
  server.socket.close()
  SetColor('#000000')
  pi.stop()
