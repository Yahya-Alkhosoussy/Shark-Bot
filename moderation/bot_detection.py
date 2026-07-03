from collections import deque  # noqa
from hashlib import md5  # noqa
from datetime import datetime
from _hashlib import HASH
from exceptions.exceptions import FormatError


class message:
    def __init__(
        self,
        message_id: int,
        timestamp: datetime,
        content: str,
        user_id: int,
        image_hashes: set[HASH] | None = None,
        image_binaries: set[bytes] | None = None,
    ):
        self.message_id = message_id
        self.timestamp = timestamp
        self.content = content
        self.image_hashes = image_hashes
        self.image_binaries = image_binaries
        self.user_id = user_id

        if not self.image_binaries and not self.image_hashes:
            raise FormatError("Provide a set of image binaries or the hashed image binaries.", 2000)
        if not self.image_hashes and self.image_binaries:
            self.image_hashes = set()
            for binary in self.image_binaries:
                self.image_hashes.add(md5(binary))

    def __str__(self) -> str:
        return (
            f"A User with the ID of {self.user_id} sent a message with the "
            f"content of {self.content} at {self.timestamp.strftime(r'%m/%d %H:%M:%S')}."
        )

    def __repr__(self) -> str:
        return (
            f"A User with the ID of {self.user_id} sent a message with the content of "
            f"{self.content} at {self.timestamp.strftime(r'%m/%d %H:%M:%S')} and the following "
            f"image hashes: {self.image_hashes}"
        )
