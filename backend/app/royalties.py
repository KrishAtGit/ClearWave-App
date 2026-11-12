from typing import Optional

PAYOUT_SOURCE = (
    "Average Spotify payout per stream, as widely reported by artists and industry analysts "
    "(roughly $0.003 to $0.005). Real payouts vary by country, subscription type and deal."
)

def estimate_value(streams: Optional(int), share_percent: Optional(float), payout_per_stream: float) -> Optional(float): # type: ignore
    if streams is None or share_percent is None:
        return None
    return round(streams * payout_per_stream * share_percent / 100, 2)
