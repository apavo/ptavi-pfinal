#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
# Cliente SIP simple.

class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.lista = []

    def startElement(self, name, attrs):

        if name == "account":
            self.account = {}
            self.guardar(attrs, self.account)
            self.lista.append([name, self.account])
        elif name == "uaserver":
            self.uaserver = {}
            self.guardar(attrs, self.uaserver)
            self.lista.append([name, self.uaserver])
        elif name == "rtpaudio":
            self.rtpaudio = {}
            self.guardar(attrs, self.rtpaudio)
            self.lista.append([name, self.rtpaudio])
        elif name == "regproxy":
            self.regproxy = {}
            self.guardar(attrs, self.regproxy)
            self.lista.append([name, self.regproxy])
        elif name == "log":
            self.log = {}
            self.guardar(attrs, self.log)
            self.lista.append([name, self.log])
        elif name == "audio":
            self.audio = {}
            self.guardar(attrs,self.audio)
            self.lista.append([name, self.audio])
        

    def guardar(self, attrs, diccionario):
        atributos = attrs.keys()
        n = 0
        while n < len(atributos):
            diccionario[str(atributos[n])] = str(attrs.get(atributos[n], ""))
            n = n + 1

if __name__ == "__main__":

    CONFIG=sys.argv[1]
    metodo=sys.argv[2].upper()
    opcion=sys.argv[3]
    parser = make_parser()
    sHandler = SmallSMILHandler()
    parser.setContentHandler(sHandler)
    parser.parse(open(CONFIG))
    print sHandler.lista
