import struct

# Network and protocol constants
UDP_PORT = 13122
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4

# Default configuration values
DEFAULT_TCP_PORT = 12345
BROADCAST_IP = '255.255.255.255'
BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 10.0

# Struct formats for different message types
OFFER_FORMAT = '!I B H 32s'
REQUEST_FORMAT = '!I B B 32s'
PAYLOAD_CLIENT_FORMAT = '!I B 5s'
PAYLOAD_SERVER_FORMAT = '!I B B H B'

# Game result codes
RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Game-related constants
TEAM_NAME = "BrazTeam"
ACTION_HIT = "Hittt"
ACTION_STAND = "Stand"


def pack_offer(port, server_name):
    # Pack a server offer message
    name_bytes = server_name.encode('utf-8').ljust(32, b'\x00')[:32]
    return struct.pack(OFFER_FORMAT, MAGIC_COOKIE, OFFER_TYPE, port, name_bytes)


def pack_request(rounds, team_name):
    # Pack a client request message
    name_bytes = team_name.encode('utf-8').ljust(32, b'\x00')[:32]
    return struct.pack(REQUEST_FORMAT, MAGIC_COOKIE, REQUEST_TYPE, rounds, name_bytes)


def pack_payload_client(decision):
    # Pack a client payload with the player's decision
    decision_bytes = decision.encode('utf-8').ljust(5, b'\x00')[:5]
    return struct.pack(PAYLOAD_CLIENT_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, decision_bytes)


def pack_payload_server(result, rank, suit):
    # Pack a server payload with game result and card data
    return struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, result, rank, suit)
