import socket
import struct

VER = 5
METHODS = [b"\x02", b"\x01"]
NMETHOD = len(METHODS)
servername = "localhost"
serverport = 1234

# sends a request to choose authentication method
# receive response from server, decode the method chosen by server(user/password)
# send username and password to server
# receive authentication result from server
# succeed, send request; fail, close connection
# pass data


class AuthRequest:
    def __init__(self, METHODS: bytes, VER: int = 5, NMETHOD: int = 1):
        """create a authentication request message for client

        @param METHODS available methods to choose
        @param VER SOCKS version, here is 5
        @param NMETHOD number of bytes in METHODS
        """
        self.METHODS = METHODS
        self.VER = VER
        self.NMETHOD = NMETHOD

    def toBytes(self):
        """convert the request into bytes packet to transmitt"""
        format = f"!BB{self.NMETHOD}s"
        # print(len(METHODS))
        # print(format)
        combined_bytes = b"".join(self.METHODS)
        # print(combined_bytes)
        return struct.pack(format, self.VER, self.NMETHOD, combined_bytes)


requestPacket = AuthRequest(METHODS, VER, NMETHOD)

# create a socket of ipv4 and streaming
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # connect to the server
    s.connect((servername, serverport))
    print(repr(requestPacket.toBytes()))
    # send data
    s.send(requestPacket.toBytes())
    # receive data
    data = s.recv(1024)
    # print the data
    print(repr(data))
