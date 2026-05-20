import yfinance as yf
from fastapi import APIRouter, HTTPException
from app.services.cache import get_cache, set_cache

router = APIRouter()

# Preset screener queries — these are valid yfinance EquityQuery presets
PRESETS = {
    "most_active":       "most_actives",
    "day_gainers":       "day_gainers",
    "day_losers":        "day_losers",
    "52w_highs":         "52_wk_high",
    "52w_lows":          "52_wk_low",
    "growth_tech":       "growth_technology_stocks",
    "undervalued_large": "undervalued_large_caps",
}


def safe_val(v):
    """Convert non-serialisable types to plain Python."""
    try:
        if v is None or (isinstance(v, float) and v != v):  # NaN check
            return None
        return round(float(v), 2) if isinstance(v, float) else v
    except Exception:
        return None


@router.get("/{preset}")
async def screen(preset: str, limit: int = 10):
    if preset not in PRESETS:
        raise HTTPException(400, f"preset must be one of {list(PRESETS.keys())}")

    cache_key = f"screener:{preset}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    try:
        result = yf.screen(PRESETS[preset], count=limit)
        quotes = result.get("quotes", [])
        data = [
            {
                "ticker":      q.get("symbol"),
                "name":        q.get("shortName"),
                "price":       safe_val(q.get("regularMarketPrice")),
                "change_pct":  safe_val(q.get("regularMarketChangePercent")),
                "volume":      q.get("regularMarketVolume"),
                "market_cap":  q.get("marketCap"),
                "sector":      q.get("sector"),
            }
            for q in quotes
        ]
        await set_cache(cache_key, data, ttl_seconds=3600)  # 1h cache
        return data
    except Exception as e:
        raise HTTPException(500, str(e))