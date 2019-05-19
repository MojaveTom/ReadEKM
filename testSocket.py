#!/usr/bin/env python3

import socket
import threading
import socketserver
import time
from Messages import *
from ekmmeters import calc_crc16, calc_crc16_as_bytes
from binascii import a2b_hex, b2a_hex
import datetime

def sendMessages(ip, port, messages):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        for msg in messages:
            #  make msg a bytearay
            if isinstance(msg, str):
                aMsg = msg
                bMsg = msg.encode('ascii')
            elif isinstance(msg, bytearray) or isinstance(msg, bytes):
                bMsg = msg
                aMsg = msg.decode('ascii')
            else:
                print('Messages must be byte-like or str.  Got %s which is a %s.'%(msg, msg.__class__))
                return
            print('Sending (bytes): "{}"'.format(bMsg))
            print('Sending (ascii): "{}"'.format(aMsg))
            sock.sendall(bMsg)
            response = sock.recv(1024)
            print('Received (bytes): "{}"'.format(response))
            print('Received (ascii): "{}"'.format(response.decode('ascii')))
            # time.sleep(1)
            # response = sock.recv(1024)        ####  Blocking read, waits for something to read
            # print('Received (bytes): "{}"'.format(response))
            # print('Received (ascii): "{}"'.format(response.decode('ascii')))
            time.sleep(4)


def client(ip, port, message):
    if isinstance(message, str):
        aMsg = message
        bMsg = message.encode('ascii')
    elif isinstance(message, bytearray) or isinstance(message, bytes):
        bMsg = message
        aMsg = message.decode('ascii')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        count = 0
        while count < 1:
            count += 1
            print('Sending (bytes): "{}"'.format(bMsg))
            print('Sending (ascii): "{}"'.format(aMsg))
            sock.sendall(bMsg)
            # time.sleep(1)
            # print('Wait a sec')
            response = sock.recv(1024)
            print('Received (bytes): "{}"'.format(response))
            print('Received (ascii): "{}"'.format(response.decode('ascii')))
            time.sleep(2)
        # sock.sendall(b'')       # send empty message to close server thread

def fixCrc(message):
    msg = bytearray(message)
    msg[CrcField]=calc_crc16_as_bytes(msg[CrcCalc])
    return msg

def makeSetTimeMessage(dt = datetime.datetime.now()):
    print('Creating SetTimeMessage for %s'%dt.isoformat())
    msg = bytearray(SetTimeMsg)     # do this so we get a fresh copy of SetTimeMsg
    dtstr = '%02d%02d%02d%02d%02d%02d%02d'%(dt.year%100,dt.month,dt.day,dt.isoweekday(),dt.hour,dt.minute,dt.second)
    ##  Stuffing SetTimeMsg_meterDateTime fields individually didn't work.  Setting them altogether does.
    msg[SetTimeMsg_meterDateTime]=dtstr.encode('ascii')
    msg = fixCrc(msg)
    print('Set time message is: %s'%msg)
    return msg


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 7777
        ####  trying to send an empty message doesn't actually send anything.
    sendMessages(HOST, PORT, (RequestMsgV4, fixCrc(SendPasswordMsg), makeSetTimeMessage(), "something", CloseMsg))
