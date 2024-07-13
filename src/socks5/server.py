from ast import match_case
import socketserver
from ssl import SOCK_STREAM
import struct
from socket import AF_INET, socket

serverport = 1234
servername = "localhost"


# Create a TCP server
class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


# create a handler
class SocksProxyHandler(socketserver.StreamRequestHandler):
    """handler class for socks proxy"""

    VERSION = b"\x05"
    AUTHMETHOD = b"\x02"  # authentication method is USER/PASSWORD
    username = "wuyi"
    password = "123456"

    def getAvailableMethods(self, clientSocket):
        """reveive authRequest from client and get available authentication methods

        Args:
            clientSocket (socket): socket connected to client

        Returns:
            (version:int, nmethods:int, methods:tuple)
        """

        version = int.from_bytes(clientSocket.recv(1), "big")
        nmethods = int.from_bytes(clientSocket.recv(1), "big")

        format = "!" + "c" * nmethods
        methods = struct.unpack(format, clientSocket.recv(nmethods))
        return (version, nmethods, methods)

    def verifyCredential(self, clientSocket) -> bool:
        """
        verify username and password sent by client

        success return true, else false
        """

        version = int.from_bytes(clientSocket.recv(1), "big")
        ulen = int.from_bytes(clientSocket.recv(1), "big")
        rcvdUsername = clientSocket.recv(ulen).decode()
        plen = int.from_bytes(clientSocket.recv(1), "big")
        rcvdPassword = clientSocket.recv(plen).decode()

        if rcvdUsername != self.username or rcvdPassword != self.password:
            # authentication failed, send back reply and close connection
            failureMsg = bytes(self.VERSION) + b"\xff"
            self.connection.sendall(failureMsg)
            self.server.close_request(self.request)
            return False

        # success, status code is x'00'
        successMsg = bytes(self.VERSION) + b"\x00"
        self.connection.sendall(successMsg)
        return True

    def processCMD(self, clientSocket: socket.socket):
        """
        process specific request from client, mainly focus on CMD field
        """

        version, cmd, rsv, addressType = struct.unpack("!BBBB")
        assert version == 5

        match addressType:
            case 1:  # ipv4
                dstAddress = clientSocket.inet_ntoa(self.connection.recv(4))
            case 3:  # domain name
                domain_length = ord(self.connection.recv(1)[0])
                dstAddress = self.connection.recv(domain_length)
            case 4:  # ipv6
                pass

        dstPort = clientSocket.recv(2)

        if cmd == 1:  # CONNECT
            # establish connection with given address and port
            with socket(AF_INET, SOCK_STREAM) as dstSocket:
                dstSocket.connect((dstAddress, dstPort))
                socksPort = dstSocket.getsockname()[1]
                # TODO: get socksAddress and reply bound address and port to client

    def handle(self):
        # receive the AuthRequest and select an authentication method.
        version, nmethods, methods = self.getAvailableMethods(self.request)
        print(repr(methods))
        print(type(methods))
        print(type(methods[0]))
        # assert version == 5
        if version != 5:
            raise RuntimeError(
                "Socks version required 5 but received request from version {}".format(
                    version
                )
            )
        # select one method, here we choose USERNAME/PASSWORD
        if (
            self.AUTHMETHOD not in methods
        ):  # USERNAME/PASSWORD not provided, close connection
            raise RuntimeError("USERNAME/PASSWORD authentication not provided")
        # send reply
        reply = self.VERSION + self.AUTHMETHOD
        print(repr(reply))
        self.request.sendall(reply)

        # get username/password for authentication
        if not self.verifyCredential(self.connection):
            raise RuntimeError("Authentication failed, incorrect username/password")

        # receive specific request
        # here we only deal with CONNECT request
        self.processCMD(self.connection)


if __name__ == "__main__":
    with ThreadingTCPServer((servername, serverport), SocksProxyHandler) as server:
        server.serve_forever()


# # create a socket of ipv4 and streaming
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     # binde the socket to a hostname and port number
#     s.bind(("localhost", serverport))

#     # listen for incoming connections
#     s.listen(1)  # 1 is the maximum number of connections

#     # main loop

#     while True:
#         # accept connections
#         (clientSocket, address) = s.accept()
#         # do something with the new socket
#         rcvMsg = rcv(clientSocket)
#         print(rcvMsg)
#         replyMsg = "This is from localhost:1234"
#         nbytes = clientSocket.send(replyMsg.encode("utf-8"))
#         if nbytes == 0:
#             raise RuntimeError("socket connection broken")

#     quit()
