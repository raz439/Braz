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


def handle_client(conn, addr):
    """Manages the TCP game session for a client."""
    try:
        # Receive Request: Cookie(4), Type(1), Rounds(1), Name(32)
        data = conn.recv(1024)
        if len(data) < 38:
            return
        cookie, mtype, rounds, team_name = struct.unpack('!I B B 32s', data[:38])

        if cookie != MAGIC_COOKIE or mtype != REQUEST_TYPE:
            return

        for r in range(rounds):
            print(f"Starting round {r + 1} for client {addr}")
            game = BlackjackGame()
            game.deal_initial()

            # Send initial 2 player cards
            for card in game.player_hand:
                conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, 0, card[0], card[1]))

            # Send dealer's first card face-up
            d_up = game.dealer_hand[0]
            conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, 0, d_up[0], d_up[1]))

            print(f"Initial cards dealt. Waiting for player decision...")
            # Player turn loop (Moved outside the card dealing loop)
            while not game.player_bust():
                msg = conn.recv(10)
                if not msg:
                    break
                _, _, dec_bytes = struct.unpack('!I B 5s', msg)
                decision = dec_bytes.decode('utf-8').strip('\x00').lower()

                if decision == 'hittt':  # Required string
                    new_card = game.player_hit()
                    conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, 0, new_card[0], new_card[1]))
                else:
                    break  # Stand

            # Dealer turn: Reveal hidden card and draw more
            if not game.player_bust():
                # Reveal dealer's 2nd card
                d_second = game.dealer_hand[1]
                conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, 0, d_second[0], d_second[1]))

                # Draw more cards if sum < 17
                while game.hand_sum(game.dealer_hand) < 17:
                    new_card = game.deck.pop()
                    game.dealer_hand.append(new_card)
                    conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, 0, new_card[0], new_card[1]))

            # Send final result (1: Tie, 2: Loss, 3: Win)
            res = game.decide_winner()
            status = {1: "TIE 🤝", 2: "DEALER WINS 💰", 3: "PLAYER WINS 🎉"}.get(res)
            print(f"Result for {addr}: {status}")
            conn.sendall(struct.pack('!I B B H B', MAGIC_COOKIE, PAYLOAD_TYPE, res, 0, 0))
    except:
        pass
    finally:
        conn.close()


def start_server():
    """Starts the TCP server and UDP broadcaster"""
    threading.Thread(target=broadcast_offers, daemon=True).start()

    # Get local IP address for the printout
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(("", TCP_PORT))
    tcp_sock.listen()

    # Matching Example Run: "Server started, listening on IP address..."
    print(f"Server started, listening on IP address {local_ip}")

    while True:
        client_conn, addr = tcp_sock.accept()
        threading.Thread(target=handle_client, args=(client_conn, addr)).start()


if __name__ == "__main__":
    start_server()
