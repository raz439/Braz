from protocol import *
from utils import *
from blackjack_game import *
from exceptions import *


def play_game(ip, port):
    # Main game loop that connects to the server and plays multiple rounds
    try:
        # Ask the user for number of rounds (1–10)
        while True:
            rounds_input = input(f"{Colors.CYAN}Enter number of rounds to play (1-10): {Colors.RESET}\n")
            if rounds_input.isdigit() and 0 < int(rounds_input) <= 10:
                rounds = int(rounds_input)
                break
            print(f"{Colors.RED}Please choose between 1 and 10 rounds.{Colors.RESET}")

        # Create and configure TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((ip, port))

        # Send game request to the server
        sock.sendall(pack_request(rounds, TEAM_NAME))

        wins = 0
        # Play the specified number of rounds
        for r in range(rounds):
            print(f"\n{Colors.BOLD}--- Round {r + 1} ---{Colors.RESET}")
            initial_cards, total_points, dealer_points = 0, 0, 0
            first_dealer_reveal, standing = True, False

            # Receive server payloads until round ends
            while True:
                data = sock.recv(9)
                if not data:
                    break

                # Validate and unpack server payload
                validate_payload_size(data, 9)
                _, _, res, rank, suit = struct.unpack(PAYLOAD_SERVER_FORMAT, data)

                # Handle end-of-round result
                if res != RESULT_NOT_OVER:
                    print(f"{Colors.YELLOW}Final Scores -> You: {total_points} | Dealer: {dealer_points}{Colors.RESET}")
                    outcome_map = {RESULT_TIE: "Tie 🤝", RESULT_LOSS: "Loss ❌", RESULT_WIN: "Win 🎉"}
                    if res == RESULT_WIN:
                        wins += 1
                    color = Colors.GREEN if res == RESULT_WIN else (Colors.RED if res == RESULT_LOSS else Colors.RESET)
                    print(f"{color}Result: {outcome_map.get(res)}{Colors.RESET}")
                    break

                # Calculate card value and display string
                val = BlackjackGame.card_value((rank, suit))
                card_str = get_card_display(rank, suit)

                # Handle initial deal and subsequent card logic
                if initial_cards < 2:
                    total_points += val
                    print(f"You received: {card_str} (Total: {total_points}) 🃏")
                elif initial_cards == 2:
                    dealer_points += val
                    print(f"Dealer's face-up card: {card_str} 🕵️")
                else:
                    if not standing:
                        total_points += val
                        print(f"Hit: {card_str} (Total: {total_points}) ➕")
                    else:
                        dealer_points += val
                        label = "reveals hidden card" if first_dealer_reveal else "draws"
                        print(f"Dealer {label}: {card_str} (Total: {dealer_points}) 🔓")
                        first_dealer_reveal = False

                initial_cards += 1

                # Ask player for action once allowed
                if initial_cards >= 3 and not standing and total_points <= 21:
                    while True:
                        action = input(
                            f"{Colors.CYAN}Type 'H' to Hit or 'S' to Stand: {Colors.RESET}👉 \n"
                        ).strip().lower()
                        if action in ['h', 'hit']:
                            decision = ACTION_HIT
                            break
                        elif action in ['s', 'stand']:
                            decision = ACTION_STAND
                            standing = True
                            break
                        print(f"{Colors.RED}'{action}' is not valid. Use 'H' or 'S' ❌.{Colors.RESET}")

                    # Send player's decision to the server
                    sock.sendall(pack_payload_client(decision))

        # Print final statistics
        win_rate = int((wins / rounds) * 100)
        print(f"{Colors.BLUE}Finished playing {rounds} rounds, win rate: {win_rate}%{Colors.RESET}")
        sock.close()

    # Handle network and protocol-related errors
    except Exception as e:
        print(f"{Colors.RED}{handle_network_error(e)}{Colors.RESET}")


def listen_for_offers():
    # Listen for UDP broadcast offers from servers
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, 'SO_REUSEPORT'):
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    udp_sock.bind(("", UDP_PORT))

    while True:
        print_banner()
        print("Client started, listening for offer requests...")

        # Receive offer packet
        data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        try:
            # Validate and unpack offer
            validate_payload_size(data, 39)
            cookie, mtype, port, name = struct.unpack(OFFER_FORMAT, data[:39])

            # Check offer validity and start game
            if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
                s_name = name.decode().strip(chr(0))
                print(f"Received offer from {s_name} at {addr[0]}")
                play_game(addr[0], port)
        except Exception:
            # Ignore invalid packets
            continue


# Entry point of the client application
if __name__ == "__main__":
    listen_for_offers()
