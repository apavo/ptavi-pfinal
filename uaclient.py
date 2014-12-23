#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import os
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import uaserver
# Cliente SIP simple.

def procesar_contestacion(data):
    #analiza la contestacion
    hora = time.strftime('%Y%m%d%H%M%S',
    time.gmtime(time.time()))
    log_ua.write(hora + "Received from " + ip_proxy
    + ":" + puerto_proxy + data + '\r\n')
    contestacion = data.split(" ")
    if len(contestacion) >= 5 and contestacion[5] == "200":
        #obtenemos datos de sdp para enviar audio
        ip_rtp = contestacion[7].split("\r\n")[0]
        puerto_rtp = contestacion[8]
        line = "ACK " + 'sip:' + opcion + ' SIP/2.0'
        line += '\r\n' + '\r\n'
        my_socket.send(line)
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        log_ua.write(hora + "Send to " + ip_proxy
        + ":" + puerto_proxy + line + '\r\n')
        AUDIO = registro['audio_path']
        aEjecutar = './mp32rtp -i ' + ip_rtp + ' -p ' + puerto_rtp + ' < ' + AUDIO
        os.system(aEjecutar)
        print "Audio enviado"
try:
    CONFIG = sys.argv[1]
    metodo = sys.argv[2].upper()
    opcion = sys.argv[3]
    parser = make_parser()
    cHandler = uaserver.DtdXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    registro = cHandler.diccionario
    #Obtenemos los datos contenidos en DTD
    usuario = registro["username"]
    ip_ua = registro["uaserver_ip"]
    puerto_ua = registro["uaserver_puerto"]
    ip_proxy = registro["regproxy_ip"]
    puerto_proxy = registro["regproxy_puerto"]
    puerto_rtp = registro["rtpaudio_puerto"]
    log = registro["log_path"]
    hora = time.strftime('%Y%m%d%H%M%S',
    time.gmtime(time.time()))
    log_ua = open(log, "a")
    log_ua.write("...\r\n")
    #Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, int(puerto_proxy)))
    if metodo == "REGISTER":
        line = "REGISTER " + "sip:" + usuario + ":" + puerto_ua
        line += " SIP/2.0" + "\r\n" + "Expires:" + opcion + "\r\n" + "\r\n"
        log_ua.write(hora + " Starting..." + "\r\n")
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        evento = " Sent to " + ip_proxy + ":" + puerto_proxy + ":" + line
        log_ua.write(hora + evento + "\r\n")
        my_socket.send(line)
    elif metodo == "INVITE":
        line = "INVITE " + "sip:" + sys.argv[3]
        line += " SIP/2.0" + "\r\n" + "Content-Type: application/sdp\r\n\r\n"
        line += "v=0\r\no=" + usuario + " " + ip_ua + "\r\ns=misesion"
        line += "\r\nt=0\r\nm=audio " + puerto_rtp + " RTP"
        hora = hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        evento = " Sent to " + ip_proxy + ":" + puerto_proxy + line
        log_ua.write(hora + evento + "\r\n")
        #Recibimos la contestacion y la anlizamos
        my_socket.send(line)
        data = my_socket.recv(1024)
        print data
        procesar_contestacion(data)
    elif metodo == "BYE":
        line = "BYE " + "sip:" + sys.argv[3] + " SIP/2.0\r\n\r\n"
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        evento = " Sent to " + ip_proxy + ":" + puerto_proxy + line
        log_ua.write(hora + evento + "\r\n")
        my_socket.send(line)
        data = my_socket.recv(1024)
        print data
    else:    
        #Si el cliente escribe mal un metodo tambien lo enviamos al servidor se encarga de mandarnos el mensaje de error
        line = metodo + "sip:" + sys.argv[3] + "SIP/2.0\r\n\r\n"        
        my_socket.send(line)
        data = my_socket.recv(1024)
        print data
    log_ua.close()
    my_socket.close()

except socket.error:
    print "Error: No server listening at" + " " + ip_proxy + " " + str(puerto_proxy)
    hora = time.strftime('%Y%m%d%H%M%S',
    time.gmtime(time.time()))
    log_ua.write(hora + "Error: No server listening at" + " " + ip_proxy 
    + " " + str(puerto_proxy))
#except ValueError:
#    print "Usage: python uaclient.py config method option"
#except IndexError:
#    print "Usage: python uaclient.py config method option"
#except NameError:
#    print "Usage: python uaclient.py config method option"
