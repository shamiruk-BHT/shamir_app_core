"""Minimal mmm.py compatibility surface for Milestone 1.1."""

from shamir_app_core.credentials.codec import KEY_TEXT, LegacyCredentialsCodec

__version__ = "1.08.00"


def encrypt(key, textvalue):
    """Encrypt textvalue using the specified legacy key."""
    return LegacyCredentialsCodec.encrypt(key, textvalue)


def decrypt(key, textvalue):
    """Decrypt textvalue using the specified legacy key."""
    return LegacyCredentialsCodec.decrypt(key, textvalue)


def encode(text):
    """Encode text using the legacy default key."""
    return LegacyCredentialsCodec.encode(text)


def decode(text):
    """Decode text using the legacy default key."""
    return LegacyCredentialsCodec.decode(text)


def getlist(csv):
    """Split comma-separated text, trimming whitespace and dropping empty items."""
    the_list = csv.split(",")
    the_list = [item.strip() for item in the_list]
    while the_list.count("") > 0:
        the_list.remove("")
    return the_list


__all__ = [
    "__version__",
    "KEY_TEXT",
    "encrypt",
    "decrypt",
    "encode",
    "decode",
    "getlist",
]
