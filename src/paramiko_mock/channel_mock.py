"""
Channel mock for simulating paramiko channel behavior with exit status support.
"""


class ChannelMock:
    """
    Mock class that simulates paramiko channel behavior.
    This provides the recv_exit_status() method that real paramiko channels have.
    """

    def __init__(self, exit_status: int = 0):
        """
        Initialize the channel mock with an exit status.

        Args:
            exit_status: The exit status code to return (default: 0)
        """
        self._exit_status = exit_status
        self._closed = False

    def recv_exit_status(self) -> int:
        """
        Simulate the recv_exit_status method of paramiko channels.

        Returns:
            The exit status code
        """
        return self._exit_status

    def set_exit_status(self, exit_status: int) -> None:
        """
        Set the exit status for this channel.

        Args:
            exit_status: The exit status code to set
        """
        self._exit_status = exit_status

    def close(self) -> None:
        """Close the channel."""
        self._closed = True

    @property
    def closed(self) -> bool:
        """Check if the channel is closed."""
        return self._closed
