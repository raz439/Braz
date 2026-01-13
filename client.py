import socket
from protocol import *
import utils  # Import the new utils module


def play_game(ip, port):
    try:
        # Get valid number of rounds from user
        while True:
            rounds_input = input(f"Enter number of rounds to play (1-10): \n")
            if rounds_input.isdigit() and 0 < int(rounds_input) <= 10:
                rounds = int(rounds_input)
                break
            print(f"{utils.Colors.RED}Please choose between 1 and 10 rounds.{utils.Colors.RESET}")

        # Establish TCP connection with server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((ip, port))

        # Send formatted game request
        sock.sendall(pack_request(rounds, TEAM_NAME))
        sock.sendall(b'\n')

        wins = 0
        for r in range(rounds):
            print(f"\n{utils.Colors.BOLD}--- Round {r + 1} ---{utils.Colors.RESET}")
            initial_cards, total_points, dealer_points = 0, 0, 0
            first_dealer_reveal, standing = True, False

            while True:
                data = sock.recv(9)
                if not data: break

                # Unpack server payload
                _, _, res, rank, suit = struct.unpack(PAYLOAD_SERVER_FORMAT, data)

                # Check if round is over
                if res != RESULT_NOT_OVER:
                    print(
                        f"{utils.Colors.YELLOW}Final Scores -> You: {total_points} | Dealer: {dealer_points}{utils.Colors.RESET}")

                    outcome_map = {RESULT_TIE: "Tie 🤝", RESULT_LOSS: "Loss ❌", RESULT_WIN: "Win 🎉"}
                    if res == RESULT_WIN: wins += 1

                    # Determine color based on result
                    color = utils.Colors.GREEN if res == RESULT_WIN else (
                        utils.Colors.RED if res == RESULT_LOSS else utils.Colors.RESET)
                    print(f"{color}Result: {outcome_map.get(res)}{utils.Colors.RESET}")
                    break

                # Calculate card numeric value for score tracking
                val = 11 if rank == 1 else (10 if rank >= 11 else rank)

                # Get pretty string using utils
                card_display = utils.get_card_display(rank, suit)

                # Display cards based on game stage
                if initial_cards < 2:
                    total_points += val
                    print(f"You received: {card_display} (Total: {total_points}) 🃏")
                elif initial_cards == 2:
                    print(f"Dealer's face-up card: {card_display} 🕵️")
                else:
                    if not standing:
                        total_points += val
                        print(f"Hit: {card_display} (Total: {total_points}) ➕")
                    else:
                        dealer_points += val
                        label = "reveals hidden card" if first_dealer_reveal else "draws"
                        print(f"Dealer {label}: {card_display} 🔓")
                        first_dealer_reveal = False

                initial_cards += 1

                # Ask for player action if applicable
                if initial_cards >= 3 and not standing and total_points <= 21:
                    while True:
                        action = input(
                            f"Type '{utils.Colors.CYAN}H{utils.Colors.RESET}' to Hit or '{utils.Colors.CYAN}S{utils.Colors.RESET}' to Stand: 👉 \n").strip().lower()
                        if action in ['h', 'hit']:
                            decision = ACTION_HIT
                            break
                        elif action in ['s', 'stand']:
                            decision = ACTION_STAND
                            standing = True
                            break
                        print(f"'{action}' is not valid. Use 'H' or 'S' ❌.")

                    sock.sendall(pack_payload_client(decision))

        # Show final session statistics
        if rounds > 0:
            win_rate = int((wins / rounds) * 100)
            print(f"{utils.Colors.BLUE}Finished playing {rounds} rounds, win rate: {win_rate}%{utils.Colors.RESET}")

        sock.close()
    except Exception as e:
        print(f"{utils.Colors.RED}Connection error: {e}{utils.Colors.RESET}")


def listen_for_offers():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, 'SO_REUSEPORT'):
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    udp_sock.bind(("", UDP_PORT))

    while True:
        utils.print_banner()  # Use the banner from utils
        print("Client started, listening for offer requests...")

        # Receive and validate offer
        try:
            data, addr = udp_sock.recvfrom(BUFFER_SIZE)
            if len(data) >= 39:  # Basic length check
                cookie, mtype, port, name = struct.unpack(OFFER_FORMAT, data[:39])

                if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
                    s_name = name.decode('utf-8').strip('\x00')
                    print(f"Received offer from {s_name} at {addr[0]}")
                    play_game(addr[0], port)
        except Exception as e:
            print(f"Error receiving offer: {e}")


if __name__ == "__main__":
    listen_for_offers()