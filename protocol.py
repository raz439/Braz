import struct

# --- Protocol Constants ---
UDP_PORT = 13122
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4

# --- Network Settings ---
DEFAULT_TCP_PORT = 12345
BROADCAST_IP = '255.255.255.255'
BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 10.0

# --- Struct Formats ---
# ! = Network Endian (Big Endian)
# I = Unsigned Int (4 bytes)
# B = Unsigned Char (1 byte)
# H = Unsigned Short (2 bytes)
# s = String/Char array (byte size follows)

# Format: Cookie(4), Type(1), Port(2), Name(32) -> Total 39 bytes
OFFER_FORMAT = '!I B H 32s'

# Format: Cookie(4), Type(1), Rounds(1), Name(32) -> Total 38 bytes
REQUEST_FORMAT = '!I B B 32s'

# Format: Cookie(4), Type(1), Decision(5) -> Total 10 bytes
PAYLOAD_CLIENT_FORMAT = '!I B 5s'

# Format: Cookie(4), Type(1), Result(1), Data1(2), Data2(1) -> Total 9 bytes
PAYLOAD_SERVER_FORMAT = '!I B B H B'

# --- Game Results ---
RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# --- Logic Constants ---
TEAM_NAME = "BrazTeam"
ACTION_HIT = "Hittt"   # 5 chars matches 5s in struct
ACTION_STAND = "Stand" # 5 chars matches 5s in struct


def pack_offer(port: int, server_name: str) -> bytes:
    """
    Packs the server offer message.
    Ensures server_name is exactly 32 bytes via padding or truncation.
    """
    # Encode to bytes, pad with null bytes to 32, and slice to ensure max length
    name_bytes = server_name.encode('utf-8').ljust(32, b'\x00')[:32]
    return struct.pack(OFFER_FORMAT, MAGIC_COOKIE, OFFER_TYPE, port, name_bytes)


def pack_request(rounds: int, team_name: str) -> bytes:
    """
    Packs the client request message.
    """
    name_bytes = team_name.encode('utf-8').ljust(32, b'\x00')[:32]
    return struct.pack(REQUEST_FORMAT, MAGIC_COOKIE, REQUEST_TYPE, rounds, name_bytes)


def pack_payload_client(decision: str) -> bytes:
    """
    Packs the client payload (game move).
    Decision must be 'Hittt' or 'Stand'.
    """
    decision_bytes = decision.encode('utf-8').ljust(5, b'\x00')[:5]
    return struct.pack(PAYLOAD_CLIENT_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, decision_bytes)


def pack_payload_server(result: int, val1: int, val2: int) -> bytes:
    """
    Packs the server payload.
    Based on PAYLOAD_SERVER_FORMAT: '!I B B H B'
    """
    return struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, result, val1, val2)