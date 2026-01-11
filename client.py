import socket
import struct

# Protocol Constants
UDP_PORT = 13122
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4


def play_game(ip, port):
    pass


def listen_for_offers():
    """Listens for UDP server announcements."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Important for running multiple clients on same PC
    if hasattr(socket, 'SO_REUSEPORT'):
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    udp_sock.bind(("", UDP_PORT))
    while True:
        print(f"{BLUE}****************************{RESET}")
        print(f"{BLUE}* WELCOME TO BRAZ CASINO *{RESET}")
        print(f"{BLUE}****************************{RESET}")
        print("Client started, listening for offer requests...")
        data, addr = udp_sock.recvfrom(1024)
        cookie, mtype, port, name = struct.unpack('!I B H 32s', data[:39])
        if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
            s_name = name.decode().strip(chr(0))
            print(f"Received offer from {s_name} at {addr[0]}")
            play_game(addr[0], port)


if __name__ == "__main__":
    listen_for_offers()
