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

    def wr(self, log_path, linea):
        log = open(log_path, "a")
        hora = time.strftime('%Y%m%d%H%M%S',
        time.gmtime(time.time()))
        log.write(hora + " " + linea + '\r\n')
        log.close

class identification():

    def crear_registro(self, fpaswords):
        diccionario = {}
        paswords = open(fpaswords)
        contenido = paswords.readlines()
        for usuario in contenido:
            datos = usuario.split(" ")
            diccionario[datos[0]] = datos[1]
        return diccionario
 
    def comprobar_cliente(self, diccionario, cliente, pasword):
        claves = self.diccionario.keys()
        correcto = False
        n = 0
        if len(claves) == 0:
            #Si no hay nadie registrado no buscamos
            correcto = False
        else:
            while not correcto and n < len(claves):
                if clave[n] == nombre and diccionario[clave[n]] == pasword:
                    correcto = True
                else:
                    n = n + 1
        return correcto
     

class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    diccionario = {}

    def buscar_datos(self):
        #Comprueba que el cliente este regitrado y su puerto
        encontrado = False
        IP = str(self.client_address[0])  
        port = 0
        n = 0
        claves = self.diccionario.keys()
        if len(claves) == 0:
            #Si no hay nadie registrado no buscamos
            encontrado = False
        else:
            while not encontrado and n < len(claves):
                if self.diccionario[claves[n]][0] == IP:
                    encontrado = True
                    port = claves[n][1]
                else:
                    n = n + 1
        return encontrado,port

    def reenvio(self, ip_ua1, port_ua1, metodo, direccion, line):
        #Envia el mensaje al destinatario
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
            evento =' Received from ' + ip_ua2 + ": "
            evento += port_ua2 + data
            log.wr(log_path, evento)
            #Enviamos la contestacion del destinatario al cliente
            self.wfile.write(data)
            print data
            evento = "Send to " + ip_ua1 + ":" + str(port_ua1)
            evento += ":" + data
            log.wr(log_path, evento)


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
            + "\t" + str(fecha_registro) + "\t" + EXPIRES + '\r\n')
            #Abrimos el fichero log y escribimos el mensaje recibido
            evento = " Received from " + IP_CLIENT + ":"
            evento += PORT_CLIENT + ": " + line
            log.wr(log_path, evento)
            #enviamos la confimacion al cliente
            respuesta = 'SIP/2.0 200 OK' + '\r\n' + '\r\n'
            self.wfile.write(respuesta)
            evento = " Send to " + IP_CLIENT + ":"
            evento += PORT_CLIENT + ": " + line
            log.wr(log_path, evento)
            database.close()
            
        else:
            #Buscamos al usuario en el diccionario
            reg_direcciones = self.diccionario.keys()
            registrado = False
            n = 0
            while not registrado and n < len(reg_direcciones):
                if direccion == reg_direcciones[n]:
                    registrado = True
                    direccion = reg_direcciones[n]
                else: 
                    n = n + 1
            if registrado:
                if metodo == "INVITE" or "BYE" or "ACK":
                    if metodo == "INVITE":
                        #Obtenemos los datos del cliente contenidos en SDP
                        informacion = line.split('\r\n')
                        ip_ua1 = informacion[4].split(" ")[1]
                        port_ua1 = informacion[7].split(" ")[1]
                        self.reenvio(ip_ua1, port_ua1, metodo, direccion, line)
                    elif metodo == "BYE" or "ACK":
                        #Comprobamos que el emisor esta registrado y si es asi obtenemos sus datos
                        encontrado,port_ua1 = self.buscar_datos()
                        if encontrado:
                             ip_ua1 = str(self.client_address[0])
                             self.reenvio(ip_ua1, port_ua1, metodo, direccion, line)
                        else:
                            self.wfile.write("Debes registrarte primero") ### REVISAAAAAAAAAAAAAARRRRRRRRRRRRRRRRRRRR!!!!!!!!!!!!!!!
                    else:
                        linea = "SIP/2.0 400 Bad Request" + "\r\n\r\n"
                        print linea
                        self.wfile.write(linea)
                        hora = hora = time.strftime('%Y%m%d%H%M%S',
                        time.gmtime(time.time()))
                        encontrado,port = self.buscar_datos()
                        evento = " Send to: " + str(self.client_address[0])
                        evento += ":" + port + ": " + linea
                        log.wr(log_path, evento)    
                else:
                    #si nos envia un metodo no valido se lo notificamos
                    linea = "SIP/2.0 405 Method Not Allowed" + '\r\n' + '\r\n'
                    print linea
                    self.wfile.write(linea)
                    encontrado,port = self.buscar_datos()
                    evento ="Send to: " + str(self.client_address[0])
                    evento += ":" + port + ":" + linea
                    log.wr(log_path, evento)      
            else:
                encontrado,port = self.buscar_datos()
                if encontrado:
                    linea = "SIP/2.0 404 User Not Found: usuario no registrado"
                    self.wfile.write(linea)
                    evento ="Send to: " + str(self.client_address[0]) 
                    evento += ":" + str(port) + ":" + linea
                    log.wr(log_path, evento)
                else:
                    self.wfile.write("Debes registrarte primero") ### REVISAAAAAAAAAAAAAARRRRRRRRRRRRRRRRRRRR!!!!!!!!!!!!!!!
                              
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

    def restablecer():
        #Obtiene datos de usuarios ya registrados
        diccionario = {}
        base_datos = open(registro["database_path"])
        for linea in base_datos:
            if linea != "":
                line = linea.split('\t')
                lista = (line[1], line[2])
                diccionario[line[0]] = lista
        base_datos.close()
        print diccionario
        return diccionario

    try:
        CONFIG= sys.argv[1]
        #Leemos la DTD usando la clase definida en client.py
        parser = make_parser()
        pHandler = uaserver.DtdXMLHandler()
        parser.setContentHandler(pHandler)
        parser.parse(open(CONFIG))
        registro = pHandler.diccionario
        log = write_log()
        log_path = registro["log_path"]
        log_pr = open(log_path, "a")
        log_pr.write("...Starting")
        log_pr.close()
        HOST = registro["ip"]
        PORT = int(registro["port"])
        #usuarios = restablecer()
        serv = SocketServer.UDPServer((HOST, PORT), SIPHandler)
        print "Server " + registro["name"] + " Listening at port " + registro["port"]
        serv.serve_forever()
    except IndexError:
        print "Usage: python proxy_registrar.py config"
