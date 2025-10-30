import pytest

try:
    from interface.web import get_dashboard_app
    HAS_FLASK = True
except Exception:
    HAS_FLASK = False


pytestmark = pytest.mark.skipif(not HAS_FLASK, reason="Flask not installed")


def _client():
    app = get_dashboard_app().app
    app.testing = True
    return app.test_client()


def test_balance_endpoint():
    client = _client()
    resp = client.get('/api/v2/balance')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'balance_total' in data['data']
    assert 'cambio_porcentual' in data['data']


def test_spending_endpoint():
    client = _client()
    resp = client.get('/api/v2/spending')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    s = data['data']
    assert 'total_gastado' in s
    assert 'limite_mensual' in s
    assert 'porcentaje_usado' in s


def test_search_endpoint():
    client = _client()
    resp = client.get('/api/v2/search?query=comida&limit=5')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'count' in data
    assert isinstance(data['data'], list)


def test_month_comparison_endpoint():
    client = _client()
    resp = client.get('/api/v2/month-comparison')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    mc = data['data']
    assert 'mes_actual' in mc
    assert 'mes_anterior' in mc
    assert 'cambios' in mc


def test_trends_endpoint():
    client = _client()
    resp = client.get('/api/v2/trends?days=30')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    tr = data['data']
    assert 'timeline' in tr
    assert 'top_categorias' in tr

