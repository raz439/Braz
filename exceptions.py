import socket


# Base exception for all Blackjack-related errors
class BlackjackError(Exception):
    pass


# Raised when protocol rules are violated
class ProtocolError(BlackjackError):
    pass


# Raised when the connection is unexpectedly closed
class ConnectionClosedError(BlackjackError):
    pass


def handle_network_error(error):
    # Return a user-friendly message for common network errors
    if isinstance(error, socket.timeout):
        return "Error: Network timeout reached."
    elif isinstance(error, ConnectionResetError):
        return "Error: Connection was reset by peer."
    elif isinstance(error, BrokenPipeError):
        return "Error: Broken pipe - connection lost."
    else:
        return f"Unexpected network error: {error}"


def validate_payload_size(data, expected_size):
    # Ensure the received payload matches the expected size
    if len(data) < expected_size:
        raise ProtocolError(
            f"Incomplete packet received. Expected {expected_size}, got {len(data)}"
        )
