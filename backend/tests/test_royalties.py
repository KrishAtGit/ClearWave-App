from app.royalties import estimate_value

def test_estimate_multiplies_streams_rate_and_share() -> None:
    # 2.1 billion streams x $0.004 x 25% = $2,100,000
    assert estimate_value(2_100_000_000, 25, 0.004) == 2_100_000.0


def test_estimate_rounds_to_cents() -> None:
    assert estimate_value(333, 33.3, 0.0037) == 0.41


def test_estimate_is_empty_until_both_inputs_are_given() -> None:
    assert estimate_value(None, 25, 0.004) is None
    assert estimate_value(1000, None, 0.004) is None

