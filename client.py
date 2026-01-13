import socket
from protocol import *

# UI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def play_game(ip, port):
    suit_icons = {0: '♥', 1: '♦', 2: '♣', 3: '♠'}
    rank_names = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}

    try:
        # Get valid number of rounds from user
        while True:
            rounds_input = input("Enter number of rounds to play (1-10): \n")
            if rounds_input.isdigit() and 0 < int(rounds_input) <= 10:
                rounds = int(rounds_input)
                break
            print(f"{RED}Please choose between 1 and 10 rounds.{RESET}")

        # Establish TCP connection with server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((ip, port))

        # Send formatted game request
        sock.sendall(pack_request(rounds, TEAM_NAME))
        sock.sendall(b'\n')  # Requirement: send line break after packet [cite: 77]

        wins = 0
        for r in range(rounds):
            print(f"\n--- Round {r + 1} ---")
            initial_cards, total_points, dealer_points = 0, 0, 0
            first_dealer_reveal, standing = True, False

            while True:
                data = sock.recv(9)
                if not data: break

                # Unpack server payload
                _, _, res, rank, suit = struct.unpack(PAYLOAD_SERVER_FORMAT, data)

                # Check if round is over
                if res != RESULT_NOT_OVER:
                    print(f"{YELLOW}Final Scores -> You: {total_points} | Dealer: {dealer_points}{RESET}")
                    outcome_map = {RESULT_TIE: "Tie 🤝", RESULT_LOSS: "Loss ❌", RESULT_WIN: "Win 🎉"}
                    if res == RESULT_WIN: wins += 1
                    color = GREEN if res == RESULT_WIN else (RED if res == RESULT_LOSS else RESET)
                    print(f"{color}Result: {outcome_map.get(res)}{RESET}")
                    break

                # Calculate card values [cite: 25, 27, 28]
                val = 11 if rank == 1 else (10 if rank >= 11 else rank)
                r_name = rank_names.get(rank, str(rank))
                s_icon = suit_icons.get(suit, str(suit))

                # Display cards based on game stage [cite: 35, 37, 38]
                if initial_cards < 2:
                    total_points += val
                    print(f"You received: {r_name} of {s_icon} (Total: {total_points}) 🃏")
                elif initial_cards == 2:
                    print(f"Dealer's face-up card: {r_name} of {s_icon} 🕵️")
                else:
                    if not standing:
                        total_points += val
                        print(f"Hit: {r_name} of {s_icon} (Total: {total_points}) ➕")
                    else:
                        dealer_points += val
                        label = "reveals hidden card" if first_dealer_reveal else "draws"
                        print(f"Dealer {label}: {r_name} of {s_icon} 🔓")
                        first_dealer_reveal = False

                initial_cards += 1
                # Ask for player action if applicable [cite: 40, 41, 42]
                if initial_cards >= 3 and not standing and total_points <= 21:
                    while True:
                        action = input("Type 'H' to Hit or 'S' to Stand: 👉 \n").strip().lower()
                        if action in ['h', 'hit']:
                            decision = ACTION_HIT
                            break
                        elif action in ['s', 'stand']:
                            decision = ACTION_STAND
                            standing = True
                            break
                        print(f"'{action}' is not valid. Use 'H' or 'S' ❌.")

                    sock.sendall(pack_payload_client(decision))

        # Show final session statistics [cite: 81]
        win_rate = int((wins / rounds) * 100)
        print(f"{BLUE}Finished playing {rounds} rounds, win rate: {win_rate}%{RESET}")
        sock.close()
    except Exception as e:
        print(f"Connection error: {e}")


def listen_for_offers():
    # Setup UDP socket to listen for server announcements [cite: 107]
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, 'SO_REUSEPORT'):
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    udp_sock.bind(("", UDP_PORT))
    while True:
        print(f"{BLUE}****************************{RESET}")
        print(f"{BLUE}* WELCOME TO BRAZ CASINO *{RESET}")
        print(f"{BLUE}****************************{RESET}")
        print("Client started, listening for offer requests...")

        # Receive and validate offer [cite: 84, 85]
        data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        cookie, mtype, port, name = struct.unpack(OFFER_FORMAT, data[:39])

        if cookie == MAGIC_COOKIE and mtype == OFFER_TYPE:
            s_name = name.decode().strip(chr(0))
            print(f"Received offer from {s_name} at {addr[0]}")
            play_game(addr[0], port)


if __name__ == "__main__":
    listen_for_offers()
