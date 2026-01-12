import socket
import struct

# Protocol Constants
UDP_PORT = 13122
MAGIC_COOKIE = 0xabcddcba
OFFER_TYPE = 0x2
REQUEST_TYPE = 0x3
PAYLOAD_TYPE = 0x4

# Colors for visualization
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def play_game(ip, port):
    """Connects to server and plays rounds."""
    suit_icons = {0: '♥', 1: '♦', 2: '♣', 3: '♠'}
    rank_names = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}

    try:
        while True:
            rounds_input = input("Enter number of rounds to play (1-10): \n")
            if rounds_input.isdigit():
                val = int(rounds_input)
                if 0 < val <= 10:
                    rounds = val
                    break
                else:
                    print(f"{RED}Please choose between 1 and 10 rounds.{RESET}")
            else:
                print(f"{RED}Invalid input! Please enter a number.{RESET}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        # Send Request
        name = b"BrazTeam".ljust(32, b'\x00')
        sock.sendall(struct.pack('!I B B 32s', MAGIC_COOKIE, REQUEST_TYPE, rounds, name))
        # Send line break after the packet
        sock.sendall(b'\n')

        wins = 0
        for r in range(rounds):
            print(f"\n--- Round {r + 1} ---")
            initial_cards = 0
            total_points = 0
            dealer_points = 0
            first_dealer_reveal = True
            standing = False

            while True:
                data = sock.recv(9)
                if not data:
                    break
                _, _, res, rank, suit = struct.unpack('!I B B H B', data)

                if res != 0:
                    # Final summary before showing result
                    print(f"{YELLOW}Final Scores -> You: {total_points} | Dealer: {dealer_points}{RESET}")
                    outcome_map = {1: "Tie 🤝", 2: "Loss ❌", 3: "Win 🎉"}
                    color = GREEN if res == 3 else (RED if res == 2 else RESET)
                    if res == 3: wins += 1
                    print(f"{color}Result: {outcome_map.get(res)}{RESET}")
                    break

                # Calculate value
                val = 11 if rank == 1 else (10 if rank >= 11 else rank)
                r_name = rank_names.get(rank, str(rank))
                s_icon = suit_icons.get(suit, str(suit))

                # logic to distinguish between player and dealer cards
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
                        # Logic for Dealer's turn
                        dealer_points += val
                        if first_dealer_reveal:
                            print(f"Dealer reveals hidden card: {r_name} of {s_icon} 🔓")
                            first_dealer_reveal = False
                        else:
                            print(f"Dealer draws: {r_name} of {s_icon} ⏳")

                initial_cards += 1
                # Only ask for input if we have 3 cards, haven't stood, and haven't busted
                if initial_cards >= 3 and not standing and total_points <= 21:
                    while True:
                        action = input("Type 'H' to Hit or 'S' to Stand: 👉 \n").strip().lower()
                        # Check for specific valid inputs only
                        if action in ['h', 'hit', 'hittt']:
                            decision = b"Hittt"
                            break
                        elif action in ['s', 'stand']:
                            decision = b"Stand"
                            standing = True
                            break
                        else:
                            # Feedback for invalid input to make it fun to read
                            print(f"'{action}' is not a valid move. Please use 'H' or 'S' ❌.")
                    sock.sendall(struct.pack('!I B 5s', MAGIC_COOKIE, PAYLOAD_TYPE, decision.ljust(5, b'\x00')))
                    if decision == b"Stand":
                        standing = True

        # Final statistics
        win_rate = int((wins / rounds) * 100)
        print(f"{BLUE}Finished playing {rounds} rounds, win rate: {win_rate}%{RESET}")
        sock.close()
    except Exception as e:
        print(f"Connection error: {e}")


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
