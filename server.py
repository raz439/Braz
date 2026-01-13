import socket
import time
import threading
from blackjack_game import BlackjackGame
from protocol import *


def broadcast_offers():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Pack offer message using protocol helper
    packet = pack_offer(DEFAULT_TCP_PORT, TEAM_NAME)

    while True:
        try:
            udp_sock.sendto(packet, (BROADCAST_IP, UDP_PORT))
            time.sleep(1)
        except:
            pass


def handle_client(conn, addr):
    try:
        # Receive and unpack initial request
        data = conn.recv(BUFFER_SIZE)
        if len(data) < 38:
            return

        cookie, mtype, rounds, team_name = struct.unpack(REQUEST_FORMAT, data[:38])
        if cookie != MAGIC_COOKIE or mtype != REQUEST_TYPE:
            return

        for r in range(rounds):
            print(f"Starting round {r + 1} for client {addr}")
            game = BlackjackGame()
            game.deal_initial()

            # Send player's starting cards
            for card in game.player_hand:
                conn.sendall(
                    struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, RESULT_NOT_OVER, card[0], card[1]))

            # Send dealer's visible card
            d_up = game.dealer_hand[0]
            conn.sendall(
                struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, RESULT_NOT_OVER, d_up[0], d_up[1]))

            # Process player decisions
            while not game.player_bust():
                msg = conn.recv(10)
                if not msg:
                    break
                _, _, dec_bytes = struct.unpack(PAYLOAD_CLIENT_FORMAT, msg)
                decision = dec_bytes.decode('utf-8').strip('\x00').lower()

                if decision == ACTION_HIT.lower():
                    new_card = game.player_hit()
                    conn.sendall(
                        struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, RESULT_NOT_OVER, new_card[0],
                                    new_card[1]))
                else:
                    break

            # Dealer plays if player is still in game
            if not game.player_bust():
                d_second = game.dealer_hand[1]
                conn.sendall(
                    struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, RESULT_NOT_OVER, d_second[0],
                                d_second[1]))

                while game.hand_sum(game.dealer_hand) < 17:
                    new_card = game.deck.pop()
                    game.dealer_hand.append(new_card)
                    conn.sendall(
                        struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, RESULT_NOT_OVER, new_card[0],
                                    new_card[1]))

            # Determine and send final result
            res = game.decide_winner()
            conn.sendall(struct.pack(PAYLOAD_SERVER_FORMAT, MAGIC_COOKIE, PAYLOAD_TYPE, res, 0, 0))
    except:
        pass
    finally:
        conn.close()


def start_server():
    # Start background UDP broadcast thread
    threading.Thread(target=broadcast_offers, daemon=True).start()

    # Get local IP and setup TCP socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(("", DEFAULT_TCP_PORT))
    tcp_sock.listen()

    print(f"Server started, listening on IP address {local_ip}")

    while True:
        client_conn, addr = tcp_sock.accept()
        threading.Thread(target=handle_client, args=(client_conn, addr)).start()


if __name__ == "__main__":
    start_server()
