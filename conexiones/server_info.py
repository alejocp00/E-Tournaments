class ServerInfo:
    def __init__(self, id, multicast_port, server_port, client_port):
        self.id = id
        self.multicast_port = multicast_port
        self.server_port = server_port
        self.client_port = client_port

    def __str__(self):
        return f"ServerInfo(id={self.id}, multicast_port={self.multicast_port}, server_port={self.server_port}, client_port={self.client_port})"
