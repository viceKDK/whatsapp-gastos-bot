"""
FX utilities for currency conversion using multiple public providers.

Simple helper mirroring the dashboard app provider to keep consistency.
"""

from datetime import datetime
from typing import Dict, Optional


def _try_exchangerate_host(base: str, quote: str) -> Optional[Dict[str, any]]:
    import requests
    url = f'https://api.exchangerate.host/latest?base={base}&symbols={quote}'
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json() or {}
    rate_val = (data.get('rates') or {}).get(quote)
    if rate_val is None:
        return None
    rate = float(rate_val)
    if rate <= 0:
        return None
    return {
        'base': base,
        'quote': quote,
        'rate': rate,
        'provider': 'exchangerate.host',
        'timestamp': datetime.now().isoformat(),
    }


def _try_er_api(base: str, quote: str) -> Optional[Dict[str, any]]:
    import requests
    url = f'https://open.er-api.com/v6/latest/{base}'
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json() or {}
    if data.get('result') != 'success':
        return None
    rates = data.get('rates') or {}
    rate_val = rates.get(quote)
    if rate_val is None:
        return None
    rate = float(rate_val)
    if rate <= 0:
        return None
    return {
        'base': base,
        'quote': quote,
        'rate': rate,
        'provider': 'open.er-api.com',
        'timestamp': datetime.now().isoformat(),
    }


def _try_frankfurter(base: str, quote: str) -> Optional[Dict[str, any]]:
    import requests
    url = f'https://api.frankfurter.app/latest?from={base}&to={quote}'
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json() or {}
    rates = data.get('rates') or {}
    rate_val = rates.get(quote)
    if rate_val is None:
        return None
    rate = float(rate_val)
    if rate <= 0:
        return None
    return {
        'base': base,
        'quote': quote,
        'rate': rate,
        'provider': 'frankfurter.app',
        'timestamp': datetime.now().isoformat(),
    }


def _try_fawaz_gh_cdn(base: str, quote: str) -> Optional[Dict[str, any]]:
    import requests
    path = f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{base.lower()}/{quote.lower()}.json'
    resp = requests.get(path, timeout=8)
    resp.raise_for_status()
    data = resp.json() or {}
    rate_val = data.get(quote.lower())
    if rate_val is None:
        return None
    rate = float(rate_val)
    if rate <= 0:
        return None
    return {
        'base': base,
        'quote': quote,
        'rate': rate,
        'provider': 'cdn.jsdelivr currency-api',
        'timestamp': datetime.now().isoformat(),
    }


def get_fx_rate(base: str = 'USD', quote: str = 'UYU') -> Dict[str, any]:
    base = (base or 'USD').upper()
    quote = (quote or 'UYU').upper()
    if base == quote:
        return {'base': base, 'quote': quote, 'rate': 1.0, 'provider': 'local', 'timestamp': datetime.now().isoformat()}

    for fn in (_try_exchangerate_host, _try_er_api, _try_frankfurter, _try_fawaz_gh_cdn):
        try:
            data = fn(base, quote)
            if data:
                return data
        except Exception:
            continue
    # Fallback basico
    fallback = 40.0 if base == 'USD' and quote == 'UYU' else 1.0
    return {'base': base, 'quote': quote, 'rate': fallback, 'provider': 'fallback', 'timestamp': datetime.now().isoformat()}

