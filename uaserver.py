#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
"""

import SocketServer
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from threading import Thread
import proxy_registrar
import random
import string


class VLC(Thread):

    """Crea un hilo para lanzar VLC"""

    def __init__(self, ip_ua, puerto_rtp):
        Thread.__init__(self)
        self.ip_ua = ip_ua
        self.puerto_rtp = puerto_rtp

    def run(self):
        aEjecutar = "cvlc rtp://@" + self.ip_ua + ":"
        aEjecutar += str(self.puerto_rtp) + " 2>/dev/null"
        print aEjecutar
        os.system(aEjecutar + "&")


class crear_cabeceraproxy():

    """Crea cabecera proxy"""
    def __init__(self, ip_proxy, puerto_proxy):
        self.ip_proxy = ip_proxy
        self.puerto_proxy = puerto_proxy

    def cabecera_proxy(self):
        caracteres = string.ascii_uppercase + string.digits
        caracteres += string.ascii_lowercase
        lista = []
        #formamos el numero aleatorio
        for n in range(14):
            lista.append(random.choice(caracteres))
        branch = "".join(lista)
        #creamos la cabecera
        cabecera = "Via: SIP/2.0/UDP "
        cabecera += self.ip_proxy + ":"
        cabecera += self.puerto_proxy + " branch= " + branch
        return cabecera


class send_audio():

    """Envia audio via RTP"""

    def __init__(self, ip_ua, puerto_rtp, audio, send_ip, send_port):
        self.ip_rtp = ip_ua
        self.port_rtp = puerto_rtp
        self.audio = audio
        self.send_port = send_port
        self.send_ip = send_ip

    #Crea un hilo y envia RTP
    def enviar(self):
        hilo_reproducir = VLC(self.send_ip, self.send_port)
        hilo_reproducir.start()
        aEjecutar = './mp32rtp -i ' + self.ip_rtp + ' -p ' + self.port_rtp
        aEjecutar += ' < ' + self.audio
        print aEjecutar
        os.system(aEjecutar)
        print "Audio enviado"


class DtdXMLHandler(ContentHandler):
    """
    Clase que lee DTD
    """
    def __init__(self):
        self.diccionario = {}

    def startElement(self, name, attrs):
        if name == "account":
            self.guardar(attrs)
        elif name == "uaserver":
            self.guardar(attrs)
        elif name == "rtpaudio":
            self.guardar(attrs)
        elif name == "regproxy":
            self.guardar(attrs)
        elif name == "log":
            self.guardar(attrs)
        elif name == "audio":
            self.guardar(attrs)
        elif name == "server":
            self.guardar(attrs)
        elif name == "database":
            self.guardar(attrs)

    #Guarda en un diccionario los atributos de cada etiqueta
    def guardar(self, attrs):
        atributos = attrs.keys()
        n = 0
        while n < len(atributos):
            self.diccionario[str(atributos[n])] = str(attrs.get
            (atributos[n], ""))
            n = n + 1


class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    lista = [0, 1]

    def procesar(self, line, HOST):
        """
        Procesa los mensajes recibidos
        """
        # Extraemos el metodo que nos envia el cliente
        linea = line.split(" ")
        metodo = linea[0]
        ip_received = str(self.client_address[0])
        port_received = str(self.client_address[1])
        if metodo == "INVITE":
            #Obtenemos la informacion contenida en SDP
            informacion = line.split('\r\n')
            print informacion
            self.lista[0] = informacion[5].split(" ")[1]
            self.lista[1] = informacion[-1].split(" ")[1]
            #escribimos el mensaje recibido
            evento = " Received from " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
            #Creamos los mensajes de respuesta
            line = 'SIP/2.0 100 Trying' + '\r\n' + '\r\n'
            line += 'SIP/2.0 180 Ringing' + '\r\n' + '\r\n'
            line += 'SIP/2.0 200 OK' + '\r\n'
            line += cab_proxy.cabecera_proxy() + '\r\n'
            line += 'Content-Type:apliccation/SDP\r\n\r\nv=0\r\no='
            line += registro['username'] + " " + registro['uaserver_ip']
            line += '\r\ns=misesion\r\nt=0\r\n' + 'm=audio '
            line += registro['rtpaudio_puerto'] + ' RTP\r\n\r\n'
            self.wfile.write(line)
            evento = " Send to " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
        elif metodo == "ACK":
            evento = " Received from " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
            #Enviamos el audio
            AUDIO = registro['audio_path']
            listen_port = registro['rtpaudio_puerto']
            reproducir = send_audio(self.lista[0], self.lista[1],
            AUDIO, HOST, listen_port)
            reproducir.enviar()
        elif metodo == "BYE":
            evento = " Received from " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
            line = 'SIP/2.0 200 OK' + '\r\n'
            line += cab_proxy.cabecera_proxy() + '\r\n'
            line += 'Content-Type:apliccation/SDP\r\n\r\nv=0\r\no='
            line += registro['username'] + " " + registro['uaserver_ip']
            line += '\r\ns=misesion\r\nt=0\r\n' + 'm=audio '
            line += registro['rtpaudio_puerto'] + ' RTP\r\n'
            self.wfile.write(line)
            evento = " Send to " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
        elif metodo != "INVITE" or "ACK" or "BYE":
            evento = " Received from " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
            line = "SIP/2.0 405 Method Not Allowed" + '\r\n' + '\r\n'
            self.wfile.write(line)
            evento = " Send to " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
        else:
            evento = " Received from " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)
            line = "SIP/2.0 400 Bad Request" + '\r\n' + '\r\n'
            self.wfile.write(line)
            evento = " Send to " + ip_received + ":"
            evento += port_received + ": " + line
            log.wr(log_path, evento)

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

    try:
        CONFIG = sys.argv[1]
        #Leemos la DTD usando la clase definida en client.py
        parser = make_parser()
        sHandler = DtdXMLHandler()
        parser.setContentHandler(sHandler)
        parser.parse(open(CONFIG))
        registro = sHandler.diccionario
        HOST = registro["uaserver_ip"]
        PORT = int(registro["uaserver_puerto"])
        log_path = registro["log_path"]
        log = proxy_registrar.write_log()
        cab_proxy = crear_cabeceraproxy(
        registro["regproxy_ip"], registro["regproxy_puerto"])
        serv = SocketServer.UDPServer((HOST, PORT), SIPHandler)
        print "Listening..."
        serv.serve_forever()
    except IndexError:
        print "Usage: python uaserver.py config"
    except KeyboardInterrupt:
        log = open(log_path, "a")
        log.write("...Finishing\r\n")
        log.close()
        print "Closing Server..."
