import time
import threading
from blackjack_game import *
from protocol import *
from exceptions import *
from utils import *


def broadcast_offers():
    # Periodically broadcast server offers via UDP
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    packet = pack_offer(DEFAULT_TCP_PORT, TEAM_NAME)

    while True:
        try:
            udp_sock.sendto(packet, (BROADCAST_IP, UDP_PORT))
            time.sleep(1)
        except Exception:
            # Ignore transient broadcast errors
            continue


def handle_client(conn, addr):
    # Handle a single connected client session
    try:
        conn.settimeout(SOCKET_TIMEOUT)
        data = conn.recv(BUFFER_SIZE)
        validate_payload_size(data, 38)

        # Unpack and validate client request
        cookie, mtype, rounds, team_name = struct.unpack(REQUEST_FORMAT, data[:38])
        if cookie != MAGIC_COOKIE or mtype != REQUEST_TYPE:
            return

        client_name = team_name.decode('utf-8').strip('\x00')
        print(f"{Colors.GREEN}Starting {rounds} rounds with {client_name} ({addr[0]}){Colors.RESET}")

        # Play the requested number of rounds
        for _ in range(rounds):
            game = BlackjackGame()
            game.deal_initial()

            # Send player's initial cards
            for card in game.player_hand:
                conn.sendall(pack_payload_server(RESULT_NOT_OVER, card[0], card[1]))

            # Send dealer's face-up card
            conn.sendall(
                pack_payload_server(
                    RESULT_NOT_OVER,
                    game.dealer_hand[0][0],
                    game.dealer_hand[0][1]
                )
            )

            # Handle player's turn
            while not game.player_bust():
                msg = conn.recv(BUFFER_SIZE)
                if not msg:
                    break

                validate_payload_size(msg, 10)
                _, _, dec_bytes = struct.unpack(PAYLOAD_CLIENT_FORMAT, msg[:10])
                decision = dec_bytes.decode('utf-8').strip('\x00').lower()

                if "hittt" in decision:
                    new_card = game.player_hit()
                    conn.sendall(pack_payload_server(RESULT_NOT_OVER, new_card[0], new_card[1]))
                else:
                    break

            # Handle dealer's turn if player did not bust
            if not game.player_bust():
                conn.sendall(
                    pack_payload_server(
                        RESULT_NOT_OVER,
                        game.dealer_hand[1][0],
                        game.dealer_hand[1][1]
                    )
                )
                while game.hand_sum(game.dealer_hand) < 17:
                    new_card = game.deck.pop()
                    game.dealer_hand.append(new_card)
                    conn.sendall(pack_payload_server(RESULT_NOT_OVER, new_card[0], new_card[1]))

            # Send final game result
            conn.sendall(pack_payload_server(game.decide_winner(), 0, 0))

    except Exception as e:
        # Handle connection and protocol errors
        print(f"{Colors.RED}{handle_network_error(e)}{Colors.RESET}")
    finally:
        # Always close the client connection
        conn.close()


def start_server():
    # Initialize server networking and start accepting clients
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Start UDP offer broadcasting in background thread
    threading.Thread(target=broadcast_offers, daemon=True).start()

    # Set up TCP server socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(("", DEFAULT_TCP_PORT))
    tcp_sock.listen(5)

    print(f"{Colors.BLUE}Server started on IP {local_ip}, port {DEFAULT_TCP_PORT}{Colors.RESET}")

    # Accept and handle incoming client connections
    while True:
        try:
            client_conn, addr = tcp_sock.accept()
            threading.Thread(
                target=handle_client,
                args=(client_conn, addr)
            ).start()
        except Exception:
            # Ignore accept errors and continue serving
            continue


# Entry point of the server application
if __name__ == "__main__":
    start_server()
