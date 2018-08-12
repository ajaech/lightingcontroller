#encoding: utf-8
import json
import logging
import pigpio
import time
import random
import numpy as np
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


def levenshtein(source, target, cutoff=None):
    if len(source) < len(target):
        return levenshtein(target, source, cutoff=cutoff)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We call tuple() to force strings to be used as sequences
    # ('c', 'a', 't', 's') - numpy uses them as values by default.
    source = np.array(tuple(source))
    target = np.array(tuple(target))

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(target.size + 1)
    for s in source:
        # Insertion (target grows longer than source):
        current_row = previous_row + 1

        # Substitution or matching:
        # Target and source items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).
        current_row[1:] = np.minimum(
                current_row[1:],
                np.add(previous_row[:-1], target != s))

        # Deletion (target grows shorter than source):
        current_row[1:] = np.minimum(
                current_row[1:],
                current_row[0:-1] + 1)

        previous_row = current_row

        if cutoff is not None and previous_row.min() > cutoff:
          return cutoff

    return previous_row[-1]

  
def MatchColor(request):
  if request in colors:
    logging.info(colors[request])
    SetColor(colors[request])
    return

  # fall back to soft matching
  best_match = 'off'
  best_dist = 3
  for color in colors:
    d = levenshtein(color, request, cutoff=5)
    if d < best_dist:
      best_match = color
      best_dist = d
  logging.info('{0} matched as {1}'.format(request, best_match))
  SetColor(colors[best_match])


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
    ctype, pdict = parse_header(self.headers['content-type'])
    length = min(int(self.headers['Content-Length']), 40)
    contents = self.rfile.read(length).lower()
    logging.info(contents)
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
