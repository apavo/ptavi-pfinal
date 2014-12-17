#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socket
import SocketServer
import sys
import os
import client
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    diccionario = {}

    def procesar(self, line, HOST):
        """
        Procesa los mensajes recibidos
        """
        # Extraemos el metodo que nos envia el cliente
        linea = line.split(" ")
        metodo = linea[0]
        direccion = linea[1].split(":")[1]
        if metodo == "REGISTER":
            #Obtenemos los datos del cliente y los guardamos en un diccionario
            IP_CLIENT = str(self.client_address[0])
            PORT_CLIENT = linea[1].split(":")[-1]
            expires = linea[-1].split(":")[-1]
            EXPIRES = expires.split("\r\n")[0]
            lista = (IP_CLIENT,PORT_CLIENT)
            self.diccionario[direccion] = lista
            fecha_registro = time.time()
            #Abrimos el fichero para escribir los datos del nuevo usuario
            database = open(registro["database_path"], "a")
            database.write(direccion + "\t" + IP_CLIENT + "\t" + PORT_CLIENT
            + "\t" + str(fecha_registro) + EXPIRES + '\r\n')
            #Abrimos el fichero log y escribimos el mensaje recibido
            log_proxy=open(registro["log_path"], "a")
            hora = time.strftime('%Y%m%d%H%M%S',
            time.gmtime(time.time()))
            log_proxy.write(hora + " Received from " + IP_CLIENT + ":"
            + PORT_CLIENT + ":" + line + '\r\n')
            log_proxy.close()
            database.close()
        else:
            #Buscamos al usuario en el diccionario
            reg_direcciones = self.diccionario.keys()
            registrado = True
            n = 0
            print reg_direcciones
            while not registrado and n < len(reg_direcciones):
                if direccion == reg_direcciones[n]:
                    registrado = True
                    direccion = reg_direcciones[n]
                else: 
                    n = n + 1
            if registrado:
                if metodo == "INVITE":
                    #Obtenemos los datos del cliente y el destinatario
                    informacion=line.split('\r\n')
                    ip_ua1 = informacion[4].split(" ")[1]
                    port_ua1 = informacion[7].split(" ")[1]
                    ip_ua2 = self.diccionario[direccion][0]
                    port_ua2 = self.diccionario[direccion][1] 
                    #Escribimos el mensaje recibido
                    log_proxy=open(registro["log_path"], "a")
                    hora = time.strftime('%Y%m%d%H%M%S',
                    time.gmtime(time.time()))
                    log_proxy.write(hora + " Received from " + ip_ua1 + ":"
                    + port_ua1 + ":" + line + '\r\n')
                    #Enviamos el mensaje a su destino y esperamos respuesta
                    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((ip_ua2, int(port_ua2)))
                    my_socket.send(line)
                    hora = time.strftime('%Y%m%d%H%M%S',
                    time.gmtime(time.time()))
                    log_proxy.write(hora + "Send to " + ip_ua2 + ":" + port_ua2
                    + ":" + line + '\r\n')
                    data = my_socket.recv(1024)
                    hora = time.strftime('%Y%m%d%H%M%S',
                    time.gmtime(time.time()))
                    log_proxy.write(hora + ' Received from ' + ip_ua2 + ":"
                    + port_ua2 + data + '\r\n')
                    #Enviamos la contestacion del destinatario al cliente
                    self.wfile.write(data)
                    print data
                    log_proxy.write(hora + "Send to " + ip_ua1 + ":" + port_ua1
                    + ":" + data + '\r\n')
                    log_proxy.close()
                    my_socket.close()
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
    HOST = registro["ip"]
    PORT = int(registro["port"])
    serv = SocketServer.UDPServer((HOST, PORT), SIPHandler)
    print "Server " + registro["name"] + " Listening at port " + registro["port"] 
    serv.serve_forever()
