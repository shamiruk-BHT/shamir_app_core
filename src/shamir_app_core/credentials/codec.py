"""Legacy credential codec compatible with the old mmm.py helpers."""

import base64

KEY_TEXT = "JohnPaulGeorgeRingo"


class LegacyCredentialsCodec:
    """Codec preserving the legacy mmm.py credential obfuscation behavior."""

    @staticmethod
    def encrypt(key, textvalue):
        """Encrypt textvalue using the specified legacy key."""
        chars = []
        for i in range(len(textvalue)):
            keych = key[i % len(key)]
            chars.append(chr(ord(textvalue[i]) + ord(keych) % 256))
        result = "".join(chars)
        result = base64.b64encode(result.encode())
        result = result.decode()
        return result

    @staticmethod
    def decrypt(key, textvalue):
        """Decrypt textvalue using the specified legacy key."""
        chars = []
        textvalue = base64.b64decode(textvalue)
        textvalue = textvalue.decode()
        for i in range(len(textvalue)):
            keych = key[i % len(key)]
            chars.append(chr(abs(ord(textvalue[i]) - ord(keych) % 256)))
        result = "".join(chars)
        return result

    @classmethod
    def encode(cls, text):
        """Encode text using the legacy default key."""
        return cls.encrypt(KEY_TEXT, text)

    @classmethod
    def decode(cls, text):
        """Decode text using the legacy default key."""
        return cls.decrypt(KEY_TEXT, text)
