"""Technical analysis service powered by IndiaQuant modules."""

import os
import sys
from typing import Any, Dict
import pandas as pd

# Add vendor path to access IndiaQuant MCP modules
_VENDOR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vendor", "indiaquant-mcp"))
if _VENDOR_PATH not in sys.path:
    sys.path.insert(0, _VENDOR_PATH)

try:
    from modules.signals import (
        calculate_rsi as _iq_calculate_rsi,
        calculate_macd as _iq_calculate_macd,
        calculate_bollinger_bands as _iq_calculate_bollinger_bands,
        generate_signal as _iq_generate_signal,
    )
except ImportError:
    _iq_calculate_rsi = None
    _iq_calculate_macd = None
    _iq_calculate_bollinger_bands = None
    _iq_generate_signal = None


def calculate_rsi(closes: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI) using IndiaQuant."""
    if _iq_calculate_rsi is not None:
        return _iq_calculate_rsi(closes, period=period)

    # Fallback calculation if module unavailable
    try:
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]), 2)
    except Exception:
        return 50.0


def calculate_macd(closes: pd.Series) -> Dict[str, float]:
    """Calculate MACD (Moving Average Convergence Divergence) using IndiaQuant."""
    if _iq_calculate_macd is not None:
        return _iq_calculate_macd(closes)

    # Fallback calculation
    try:
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal_line
        return {
            "macd": round(float(macd_line.iloc[-1]), 4),
            "signal": round(float(signal_line.iloc[-1]), 4),
            "histogram": round(float(hist.iloc[-1]), 4),
        }
    except Exception:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}


def calculate_bollinger_bands(closes: pd.Series, period: int = 20) -> Dict[str, float]:
    """Calculate Bollinger Bands using IndiaQuant."""
    if _iq_calculate_bollinger_bands is not None:
        return _iq_calculate_bollinger_bands(closes, period=period)

    try:
        sma = closes.rolling(window=period).mean().iloc[-1]
        std = closes.rolling(window=period).std().iloc[-1]
        return {
            "upper": round(float(sma + 2 * std), 2),
            "middle": round(float(sma), 2),
            "lower": round(float(sma - 2 * std), 2),
        }
    except Exception:
        return {"upper": 0.0, "middle": 0.0, "lower": 0.0}


def generate_trade_signal(symbol: str, closes: pd.Series = None, timeframe: str = "1d") -> Dict[str, Any]:
    """Generate trade signals (BUY/SELL/HOLD).

    For Indian stocks (.NS / .BO), uses IndiaQuant's native multi-factor generator.
    For US / global equities, evaluates IndiaQuant technical indicators (RSI & MACD).
    """
    clean = symbol.strip().upper()
    is_indian = clean.endswith(".NS") or clean.endswith(".BO") or clean in ["NIFTY", "BANKNIFTY", "SENSEX"]

    if is_indian and _iq_generate_signal is not None:
        try:
            return _iq_generate_signal(clean, timeframe=timeframe)
        except Exception:
            pass

    # Global / general equity signal synthesis based on IndiaQuant RSI & MACD
    if closes is not None and len(closes) >= 14:
        rsi = calculate_rsi(closes)
        macd = calculate_macd(closes)

        score = 0
        reasons = []

        if rsi < 30:
            score += 2
            reasons.append(f"RSI {rsi:.1f} indicates oversold territory (potential upward bounce)")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI {rsi:.1f} indicates overbought territory (potential pullback)")
        else:
            reasons.append(f"RSI {rsi:.1f} is in neutral range")

        if macd["histogram"] > 0:
            score += 1
            reasons.append(f"MACD histogram positive ({macd['histogram']:.2f}) - bullish momentum")
        else:
            score -= 1
            reasons.append(f"MACD histogram negative ({macd['histogram']:.2f}) - bearish momentum")

        if score >= 2:
            signal = "BUY"
            confidence = min(0.6 + score * 0.1, 0.95)
        elif score <= -2:
            signal = "SELL"
            confidence = min(0.6 + abs(score) * 0.1, 0.95)
        else:
            signal = "HOLD"
            confidence = 0.5

        return {
            "symbol": clean,
            "signal": signal,
            "confidence": round(confidence, 2),
            "rsi": rsi,
            "macd": macd,
            "reasons": reasons,
        }

    return {
        "symbol": clean,
        "signal": "HOLD",
        "confidence": 0.5,
        "reasons": ["Insufficient data points for signal generation"],
    }
