from shamir_app_core.credentials.codec import KEY_TEXT, LegacyCredentialsCodec


def test_encode_decode_ascii_roundtrip():
    text = "plain ASCII credentials 123"

    encoded = LegacyCredentialsCodec.encode(text)

    assert LegacyCredentialsCodec.decode(encoded) == text


def test_encode_known_values():
    assert LegacyCredentialsCodec.encode("") == ""
    assert LegacyCredentialsCodec.encode("A") == "wos="
    assert LegacyCredentialsCodec.encode("abc") == "wqvDkcOL"
    assert LegacyCredentialsCodec.encode("annapurna") == "wqvDncOWw4/DgMOWw6fDmsKo"
    assert LegacyCredentialsCodec.encode("hawkstone") == "wrLDkMOfw5nDg8OVw6TDmsKs"


def test_decode_known_values():
    assert LegacyCredentialsCodec.decode("") == ""
    assert LegacyCredentialsCodec.decode("wos=") == "A"
    assert LegacyCredentialsCodec.decode("wqvDkcOL") == "abc"
    assert LegacyCredentialsCodec.decode("wqvDncOWw4/DgMOWw6fDmsKo") == "annapurna"


def test_encrypt_decrypt_with_custom_key():
    encoded = LegacyCredentialsCodec.encrypt("key", "abc")

    assert encoded == "w4zDh8Oc"
    assert LegacyCredentialsCodec.decrypt("key", encoded) == "abc"


def test_default_key_matches_legacy_mmm_key():
    assert KEY_TEXT == "JohnPaulGeorgeRingo"
