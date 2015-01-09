#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socket
import SocketServer
import sys
import os
import uaserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time


class write_log():

    """Escribe en el fichero log"""

    def wr(self, log_path, linea):
        log = open(log_path, "a")
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        log.write(hora + " " + linea + '\r\n')
        log.close


class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    diccionario = {}

    def register2file(self):
        """escribe en el fichero el contenido del diccionario"""

        database = open(registro["database_path"], "w")
        claves = self.diccionario.keys()
        for i in claves:
            database.write(i + "\t" + self.diccionario[i][0]
            + "\t" + self.diccionario[i][1] + "\t"
            + str(self.diccionario[i][3]) + "\t"
            + self.diccionario[i][2] + '\r\n')
        database.close()

    def caducidad(self, hora_actual):
        """
        Borra usuarios caducados.
        """
        claves = self.diccionario.keys()
        if len(claves) != 0:
            for i in claves:
                hora_entrada = self.diccionario[i][3]
                expir = float(hora_entrada) + float(self.diccionario[i][2])
                if hora_actual > expir:
                    del self.diccionario[i]
        #actualizamos la base de datos
        self.register2file()

    def buscar_usuario(self):
        """Comprueba que el cliente este regitrado"""
        encontrado = False
        IP = str(self.client_address[0])
        n = 0
        claves = self.diccionario.keys()
        if len(claves) == 0:
            #Si no hay nadie registrado no buscamos
            encontrado = False
        else:
            while not encontrado and n < len(claves):
                if self.diccionario[claves[n]][0] == IP:
                    encontrado = True
                else:
                    n = n + 1
        return encontrado

    def reenvio(self, ip_ua1, port_ua1, metodo, direccion, line):
        """Envia el mensaje al destinatario"""
        try:
            ip_ua2 = self.diccionario[direccion][0]
            port_ua2 = self.diccionario[direccion][1]
            #Escribimos el mensaje recibido
            evento = " Received from " + ip_ua1 + ":"
            evento += str(port_ua1) + ": " + line
            log.wr(log_path, evento)
            #Enviamos el mensaje a su destino
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip_ua2, int(port_ua2)))
            my_socket.send(line)
            evento = "Send to " + ip_ua2 + ":" + port_ua2
            evento += ": " + line
            log.wr(log_path, evento)
            #Si no es un ACK esperamos contestacion
            if metodo != "ACK":
                data = my_socket.recv(1024)
                my_socket.close()
                evento = ' Received from ' + ip_ua2 + ": "
                evento += port_ua2 + data
                log.wr(log_path, evento)
                #Enviamos la contestacion del destinatario al cliente
                self.wfile.write(data)
                print data
                evento = "Send to " + ip_ua1 + ":" + str(port_ua1)
                evento += ": " + data
                log.wr(log_path, evento)
        except socket.error:
            #si el receptor no esta conectado mandamos el error
            print "Error: No server listening at " + ip_ua2 + " " + port_ua2
            self.wfile.write("SIP/2.0 404 User Not Found")

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
            ip_client = str(self.client_address[0])
            port_listen = linea[1].split(":")[-1]
            port_send = str(self.client_address[1])
            expires = linea[2].split(":")[1]
            expires = expires.split("\r\n")[0]
            fecha_registro = time.time()
            lista = (ip_client, port_listen, expires, fecha_registro)
            self.diccionario[direccion] = lista
            #escribimos el mensaje recibido en log
            evento = " Received from " + ip_client + ":"
            evento += port_send + ": " + line
            log.wr(log_path, evento)
            #enviamos la confimacion al cliente
            respuesta = 'SIP/2.0 200 OK' + '\r\n' + '\r\n'
            self.wfile.write(respuesta)
            evento = " Send to " + ip_client + ":"
            evento += port_send + ": " + line
            log.wr(log_path, evento)
            #actualizamos base de datos
            self.register2file()
        elif metodo != "INVITE" and metodo != "BYE" and metodo != "ACK":
            #si nos envia un metodo no valido se lo notificamos
            linea = "SIP/2.0 405 Method Not Allowed" + '\r\n'
            linea += cab_proxy.cabecera_proxy() + '\r\n\r\n'
            print linea
            self.wfile.write(linea)
            evento = "Send to: " + str(self.client_address[0])
            evento += ":" + str(self.client_address[1]) + ": " + linea
            log.wr(log_path, evento)

        else:
            #Buscamos al destinatario en el diccionario
            reg_direcciones = self.diccionario.keys()
            registrado = False
            n = 0
            while not registrado and n < len(reg_direcciones):
                if direccion == reg_direcciones[n]:
                    registrado = True
                    direccion = reg_direcciones[n]
                else:
                    n = n + 1
            #comprobamos que el cliente esta registrado
            encontrado = self.buscar_usuario()
            if registrado and encontrado:
                if metodo == "INVITE":
                    #Obtenemos ip y puerto de envio
                    ip_ua1 = str(self.client_address[0])
                    port_ua1 = str(self.client_address[1])
                    self.reenvio(ip_ua1, port_ua1, metodo, direccion, line)
                elif metodo == "BYE" or "ACK":
                    ip_ua1 = str(self.client_address[0])
                    port_ua1 = str(self.client_address[1])
                    self.reenvio(ip_ua1, port_ua1, metodo,
                    direccion, line)
                else:
                    #metodo mal formado
                    linea = "SIP/2.0 400 Bad Request" + '\r\n'
                    linea += cab_proxy.cabecera_proxy() + '\r\n\r\n'
                    print linea
                    self.wfile.write(linea)
                    evento = " Send to: " + str(self.client_address[0])
                    evento += ":" + str(self.client_address[1]) + ": " + linea
                    log.wr(log_path, evento)
            else:
                #Usuario o cliente no registrados
                linea = "SIP/2.0 404 User Not Found" + '\r\n'
                linea += cab_proxy.cabecera_proxy() + '\r\n\r\n'
                self.wfile.write(linea)
                evento = "Send to: " + str(self.client_address[0])
                evento += ":" + str(self.client_address[1]) + ": " + linea
                log.wr(log_path, evento)

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        try:
            while 1:
                # Leyendo línea a línea lo que nos envía el cliente
                if len(self.diccionario) == 0:
                    self.diccionario == restablecer()
                line = self.rfile.read()
                if not line:
                    break
                print "El cliente nos manda " + line
                hora = float(time.time())
                self.caducidad(hora)
                self.procesar(line, HOST)
                # Si no hay más líneas salimos del bucle infinito
        except IndexError:
            print "Ficheros mal escritos"

if __name__ == "__main__":

    #Obtiene datos de usuarios ya registrados
    def restablecer():
        diccionario = {}
        base_datos = open(registro["database_path"])
        for linea in base_datos:
            #si el campo expires es igual 0 no guarda
            if linea != "":
                line = linea.split('\t')
                lista = (line[1], line[2], line[4].split("\r\n")[0],
                line[3])
                diccionario[line[0]] = lista
        base_datos.close()
    try:
        CONFIG = sys.argv[1]
        #Leemos la DTD usando la clase definida en client.py
        parser = make_parser()
        pHandler = uaserver.DtdXMLHandler()
        parser.setContentHandler(pHandler)
        parser.parse(open(CONFIG))
        registro = pHandler.diccionario
        log = write_log()
        log_path = registro["log_path"]
        log_pr = open(log_path, "a")
        log_pr.write("...Starting\r\n")
        log_pr.close()
        HOST = registro["ip"]
        PORT = int(registro["port"])
        cab_proxy = uaserver.crear_cabeceraproxy(HOST, str(PORT))
        serv = SocketServer.UDPServer((HOST, PORT), SIPHandler)
        message = "Server " + registro["name"] + " Listening at port "
        message += registro["port"]
        print message
        serv.serve_forever()
    except KeyboardInterrupt:
        print "Closing proxy..."
        log_pr = open(log_path, "a")
        log_pr.write("...Finishing\r\n")
        log_pr.close()
