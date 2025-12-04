"""
Enhanced stderr mock that combines BytesIO functionality with channel support.
"""
from io import BytesIO
from .channel_mock import ChannelMock


class StderrMock(BytesIO):
    """
    Enhanced stderr mock that extends BytesIO and adds channel functionality.
    This simulates the behavior of paramiko's stderr which has both read() capabilities
    and a channel with recv_exit_status() method.
    """

    def __init__(self, initial_bytes: bytes = b'', exit_status: int = 0):
        """
        Initialize the stderr mock with initial data and exit status.

        Args:
            initial_bytes: Initial bytes for the stderr content
            exit_status: The exit status code for the channel
        """
        super().__init__(initial_bytes)
        self.channel = ChannelMock(exit_status)

    def set_exit_status(self, exit_status: int) -> None:
        """
        Set the exit status for the channel.

        Args:
            exit_status: The exit status code to set
        """
        self.channel.set_exit_status(exit_status)

    def get_exit_status(self) -> int:
        """
        Get the current exit status.

        Returns:
            The current exit status code
        """
        return self.channel.recv_exit_status()
