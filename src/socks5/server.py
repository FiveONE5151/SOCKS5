import socketserver
import struct

serverport = 1234
servername = "localhost"


# Create a TCP server
class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


# create a handler
class SocksProxy(socketserver.StreamRequestHandler):
    """handler class for socks proxy"""

    VERSION = b"\x05"
    AUTHMETHOD = b"\x02"  # authentication method is USER/PASSWORD

    def rcv(self, clientSocket):
        version = int.from_bytes(clientSocket.recv(1), "big")
        nmethods = int.from_bytes(clientSocket.recv(1), "big")

        format = "!" + "c" * nmethods
        methods = struct.unpack(format, clientSocket.recv(nmethods))
        return (version, nmethods, methods)

    def handle(self):
        # receive the AuthRequest and select an authentication method.
        version, nmethods, methods = self.rcv(self.request)
        print(repr(methods))
        print(type(methods))
        print(type(methods[0]))
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


if __name__ == "__main__":
    with ThreadingTCPServer((servername, serverport), SocksProxy) as server:
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
