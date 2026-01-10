import random


class BlackjackGame:
    """
    A simple Blackjack game engine for one player vs dealer.
    Can be imported into server.py for TCP gameplay.
    """

    def __init__(self):
        """
        Initialize the game with player name and empty hands.
        """
        self.deck = self.create_deck()        # Full 52-card deck
        self.player_hand = []                 # List of player's cards
        self.dealer_hand = []                 # List of dealer's cards

    def create_deck(self):
        """
        Creates a standard 52-card deck.
        Each card is represented as a tuple: (rank, suit)
        rank: 1-13 (Ace=1, Jack=11, Queen=12, King=13)
        suit: 0-3 (Hearts, Diamonds, Clubs, Spades)
        Returns a shuffled deck.
        """
        deck = [(rank, suit) for rank in range(1, 14) for suit in range(4)]
        random.shuffle(deck)
        return deck

    def card_value(self, card):
        """
        Returns the Blackjack value of a card.
        Ace=11, Face cards=10, Number cards=rank
        """
        rank, _ = card
        if rank == 1:       # Ace
            return 11
        elif rank >= 11:    # Jack, Queen, King
            return 10
        else:
            return rank

    def hand_sum(self, hand):
        """
        Computes the sum of a hand.
        Note: Currently Ace is always 11 (simplified rule per assignment).
        """
        return sum(self.card_value(card) for card in hand)

    def deal_initial(self):
        """
        Deals 2 cards each to player and dealer at the start of a round.
        """
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]

    def player_hit(self):
        """
        Adds a card to the player's hand from the deck.
        """
        new_card = self.deck.pop()
        self.player_hand.append(new_card)
        return new_card

    def dealer_turn(self):
        """
        Dealer reveals hidden card and draws cards until total >= 17.
        Returns True if dealer busts, False otherwise.
        """
        while self.hand_sum(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        return self.hand_sum(self.dealer_hand) > 21  # True if bust

    def player_bust(self):
        # Check if player total exceeds 21
        return self.hand_sum(self.player_hand) > 21

    def decide_winner(self):
        """
        Compares player and dealer hands and returns the result:
        "win", "loss", or "tie"
        """
        p_sum = self.hand_sum(self.player_hand)
        d_sum = self.hand_sum(self.dealer_hand)

        if p_sum > 21: return 2  # Player bust
        if d_sum > 21: return 3  # Dealer bust
        if p_sum > d_sum: return 3  # Player higher
        if d_sum > p_sum: return 2  # Dealer higher
        return 1  # Tie
