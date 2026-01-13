"""
utils.py
Shared utilities for UI, colors, and formatting.
"""

# ANSI Color Codes
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# Card Mappings
SUIT_ICONS = {
    0: '♥',  # Hearts
    1: '♦',  # Diamonds
    2: '♣',  # Clubs
    3: '♠'   # Spades
}

RANK_NAMES = {
    1: 'Ace',
    11: 'Jack',
    12: 'Queen',
    13: 'King'
}

def get_card_display(rank, suit):
    """
    Returns a formatted string for a card (e.g., 'Ace of Spades ♠').
    """
    r_name = RANK_NAMES.get(rank, str(rank))
    s_icon = SUIT_ICONS.get(suit, '?')
    return f"{r_name} of {s_icon}"

def print_banner():
    """
    Prints the welcome banner.
    """
    print(f"{Colors.BLUE}****************************{Colors.RESET}")
    print(f"{Colors.BLUE}* WELCOME TO BRAZ CASINO  *{Colors.RESET}")
    print(f"{Colors.BLUE}****************************{Colors.RESET}")