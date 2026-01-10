import socket
import time
import struct
import threading
from blackjack_game import BlackjackGame

# Protocol Constants
UDP_PORT = 13122
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4
SERVER_NAME = "Braz"
TCP_PORT = 12345


def broadcast_offers():
    """Broadcasts server availability via UDP"""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Pack offer: Cookie(4), Type(1), Port(2), Name(32)
    name_bytes = SERVER_NAME.encode('utf-8').ljust(32, b'\x00')
    packet = struct.pack('!I B H 32s', MAGIC_COOKIE, OFFER_TYPE, TCP_PORT, name_bytes)
    while True:
        try:
            udp_sock.sendto(packet, ('255.255.255.255', UDP_PORT))
            time.sleep(1)
        except:
            pass
