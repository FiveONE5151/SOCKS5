import socket
import struct

VER = 5
METHODS = [b"\x02", b"\x01"]
NMETHOD = len(METHODS)
servername = "localhost"
serverport = 1234
USERNAME = "wuyi"
PASSWORD = "123456"
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


if __name__ == "__main__":
    requestPacket = AuthRequest(METHODS, VER, NMETHOD)

    # create a socket of ipv4 and streaming
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # connect to the server
        s.connect((servername, serverport))
        print(repr(requestPacket.toBytes()))
        # send authentication methods available
        s.send(requestPacket.toBytes())
        # receive method chosen
        serverVersion, chosenMethod = struct.unpack("!Bc", s.recv(2))
        if serverVersion != VER:
            raise RuntimeError("Server version is not {}".format(VER))
        if chosenMethod not in METHODS:
            raise RuntimeError("Chosen method {} not available ".format(chosenMethod))

        s.sendall(
            struct.pack(
                f"!BB{len(USERNAME)}sB{len(PASSWORD)}s",
                VER,
                len(USERNAME),
                USERNAME.encode("utf-8"),
                len(PASSWORD),
                PASSWORD.encode("utf-8"),
            )
        )
        authResult = struct.unpack("!BB", s.recv(2))
        if authResult[1] != 0:
            quit()

        # send specific request
        dstAddress = "31.13.68.169"  # "106.13.245.94"
        dstPort = 80
        s.sendall(
            struct.pack("!BBBB4sH", VER, 1, 0, 1, socket.inet_aton(dstAddress), dstPort)
        )

        # receive connection message
        _, rep, rsv, atyp = struct.unpack("!BBBB", s.recv(4))
        if rep != 0:
            print("conncection to dst server failed.")
            quit()
        if atyp == 1:
            bndAddr = socket.inet_ntoa(s.recv(4))
            bndPort = struct.unpack("!H", s.recv(2))[0]
            print("connection to dst server succeed.")

        # connection succeed, passing data
