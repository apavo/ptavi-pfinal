#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
# Cliente SIP simple.


class DtdXMLHandler(ContentHandler):
    """
    Clase que lee DTD
    """
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
            self.guardar(attrs, self.audio)
            self.lista.append([name, self.audio])

    def guardar(self, attrs, diccionario):
        #Guarda en un diccionario los atributos de cada etiqueta
        atributos = attrs.keys()
        n = 0
        while n < len(atributos):
            diccionario[str(atributos[n])] = str(attrs.get(atributos[n], ""))
            n = n + 1

if __name__ == "__main__":

    CONFIG = sys.argv[1]
    metodo = sys.argv[2].upper()
    opcion = sys.argv[3]
    parser = make_parser()
    sHandler = DtdXMLHandler()
    parser.setContentHandler(sHandler)
    parser.parse(open(CONFIG))
    registro = sHandler.lista
    #Obtenemos los datos contenidos en DTD
    usuario = registro[0][1]["username"]
    ip_ua = registro[1][1]["ip"]
    puerto_ua = registro[1][1]["puerto"]
    ip_proxy = registro[3][1]["ip"]
    puerto_proxy = registro[3][1]["puerto"]
    puerto_rtp = registro[2][1]["puerto"]
    log = registro[4][1]["path"]
    hora = time.strftime('%Y%m%d%H%M%S',
    time.gmtime(time.time()))
    log_ua = open(log, "a")
    log_ua.write("...\n")
    #Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, int(puerto_proxy)))
    #Definimos las acciones de cada metodo
    if metodo == "REGISTRER":
        line = "REGISTRER " + "sip:" + usuario + ":" + puerto_ua
        line += " SIP/2.0" + "\r\n" + "Expires:" + opcion + "\r\n" + "\r\n"
        log_ua.write(hora + " Starting...")
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        evento = " Sent to " + ip_proxy + ":" + puerto_proxy + ":" + "REGISTER"
        evento += "sip:" + usuario + ":" + puerto_ua + " SIP/2.0" + "[...]"
        log_ua.write(hora + evento)
    elif metodo == "INVITE":
        line = "INVITE " + + "sip:" + sys.argv[3]
        line += " SIP/2.0" + "\r\n" + "Content-type:application/sdp\r\n \r\n"
        line += "v=0\r\no=" + usuario + ip_ua + "\r\ns=misesion"
        line += "\r\nt=0\r\nm=audio" + puerto_rtp + "RTP"
        hora = hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        evento = " Sent to " + ip_proxy + ":" + puerto_proxy + ":" + "INVITE "
        evento += sys.argv[3] + "[...]"
