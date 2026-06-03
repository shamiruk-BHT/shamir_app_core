from shamir_app_core.compat import mmm
from shamir_app_core.credentials.codec import KEY_TEXT, LegacyCredentialsCodec


def test_mmm_exports_version_and_key_text():
    assert mmm.__version__ == "1.08.00"
    assert mmm.KEY_TEXT == KEY_TEXT


def test_mmm_codec_wrappers_match_legacy_codec():
    text = "annapurna"
    encoded = "wqvDncOWw4/DgMOWw6fDmsKo"

    assert mmm.encode(text) == LegacyCredentialsCodec.encode(text)
    assert mmm.encode(text) == encoded
    assert mmm.decode(encoded) == text
    assert mmm.encrypt(KEY_TEXT, text) == encoded
    assert mmm.decrypt(KEY_TEXT, encoded) == text


def test_getlist_trims_whitespace():
    assert mmm.getlist(" alpha, beta ,gamma ") == ["alpha", "beta", "gamma"]


def test_getlist_drops_empty_items():
    assert mmm.getlist("alpha,, , beta,") == ["alpha", "beta"]


def test_getlist_empty_string_returns_empty_list():
    assert mmm.getlist("") == []
