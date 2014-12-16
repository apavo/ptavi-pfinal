#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import sys
import os
import client
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    def procesar(self, line, HOST):
        """
        Procesa los mensajes recibidos
        """
        # Extraemos el metodo que nos envia el cliente
        linea = line.split(" ")
        metodo = linea[0]
        IP = str(self.client_address[0])
        if metodo == "INVITE":
            #Obtenemos la informacion contenida en SDP
            informacion=line.split('\r\n')
            IP_CLIENT = informacion[4].split(" ")[1]
            PORT_CLIENT = informacion[7].split(" ")[1]
            #Creamos los mensajes de respuesta
            line = 'SIP/2.0 100 Trying' + '\r\n' + '\r\n'
            line += 'SIP/2.0 180 Ringing' + '\r\n' + 'Content-Type: '
            line += 'SIP/2.0 200 OK' + '\r\n' + '\r\n' 
            line += 'apliccation/SDP\r\n\r\nv=0\r\no=' + registro['username']
            line += registro['uaserver_ip'] + '\r\ns=misesion\r\nt=0m=audio'
            line += registro['rtpaudio_puerto'] 
            self.wfile.write(line)
        elif metodo == "ACK":
            #Enviamos el audio
            AUDIO = registro['audio_path']
            aEjecutar = './mp32rtp -i ' + IP_CLIENT + ' -p ' + PORT_CLIENT < + AUDIO
            os.system(aEjecutar)
        elif metodo == "BYE":
            line = 'SIP/2.0 200 OK' + '\r\n' + '\r\n'
            self.wfile.write(line)
        elif metodo != "INVITE" or "ACK" or "BYE":
            line = "SIP/2.0 405 Method Not Allowed" + '\r\n' + '\r\n'
            self.wfile.write(line)
        else:
            line = "SIP/2.0 400 Bad Request" + '\r\n' + '\r\n'
            self.wfile.write(line)

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
                # Leyendo línea a línea lo que nos envía el cliente
                line = self.rfile.read()
                if not line:
                    break

                print "El cliente nos manda " + line
                self.procesar(line, HOST)
                # Si no hay más líneas salimos del bucle infinito


if __name__ == "__main__":

    CONFIG= sys.argv[1]
    #Leemos la DTD usando la clase definida en client.py
    parser = make_parser()
    pHandler = client.DtdXMLHandler()
    parser.setContentHandler(pHandler)
    parser.parse(open(CONFIG))
    registro = pHandler.diccionario
    print registro
    HOST = registro["ip"]
    PORT = int(registro["port"])
    serv = SocketServer.UDPServer((HOST, PORT), SIPHandler)
    print "Server " + registro["name"] + " Listening at port " + registro["port"] 
    serv.serve_forever()

