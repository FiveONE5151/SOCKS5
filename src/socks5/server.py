import socketserver
from ssl import SOCK_STREAM
import struct
from socket import AF_INET, socket, inet_ntoa, inet_aton
import select

serverport = 9011
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

    # def __init__(
    #     self,
    #     request: socket | tuple[bytes, socket],
    #     client_address: socketserver.Any,
    #     server: socketserver.BaseServer,
    # ) -> None:
    #     super().__init__(request, client_address, server)

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
        successMsg = struct.pack("!cB", self.VERSION, 0)
        self.connection.sendall(successMsg)
        return True

    def connectToDst(self, address, clientSocket: socket) -> socket:
        try:
            dstSocket = socket(AF_INET, SOCK_STREAM)
            dstSocket.settimeout(10)  # timeout limit: 10 sec
            dstSocket.connect(address)
            socksAddress = dstSocket.getsockname()[0]
            socksPort = dstSocket.getsockname()[1]
            replyMsg = struct.pack(
                "!cBBB4sH",
                self.VERSION,
                0,
                0,
                1,
                inet_aton(socksAddress),
                socksPort,
            )
            clientSocket.sendall(replyMsg)
            return dstSocket
        except TimeoutError:
            replyMsg = struct.pack(
                "!cBBB4sh",
                self.VERSION,
                3,
                0,
                15,
                b"\xffff",
                0,
            )
            clientSocket.sendall(replyMsg)
            return None

    def processCMD(self, clientSocket: socket):
        """
        process specific request from client, mainly focus on CMD field
        """

        version, cmd, rsv, addressType = struct.unpack("!BBBB", clientSocket.recv(4))
        assert version == 5

        match addressType:
            case 1:  # ipv4
                dstAddress = inet_ntoa(clientSocket.recv(4))
            case 3:  # domain name
                domain_length = ord(clientSocket.recv(1)[0])
                dstAddress = clientSocket.recv(domain_length)
            case 4:  # ipv6
                pass

        dstPort = struct.unpack("!H", clientSocket.recv(2))[0]

        if cmd == 1:  # CONNECT
            # establish connection with given address and port
            dstSocket = self.connectToDst((dstAddress, dstPort), clientSocket)
            return dstSocket

    def exchange_loop(self, client, remote):

        while True:

            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break

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
        dstSocket = self.processCMD(
            self.connection
        )  # getting socket connected to dst server
        if dstSocket is None:
            return

        # passing data from dst server to client
        # TODO: close dstSocket when finished
        self.exchange_loop(self.connection, dstSocket)
        dstSocket.close()


if __name__ == "__main__":
    with ThreadingTCPServer((servername, serverport), SocksProxyHandler) as server:
        server.serve_forever()
