import pytest

from webapp.models import UserCreate, UserUpdate


def test_service_crud(user_service):
    user = user_service.create(UserCreate(name='Ada', email='ada@example.com'))
    assert user.id == 1
    assert user_service.get(1) == user
    assert user_service.list() == [user]

    updated = user_service.update(1, UserUpdate(name='Ada L.'))
    assert updated.name == 'Ada L.'
    assert updated.email == 'ada@example.com'

    assert user_service.delete(1) is True
    assert user_service.delete(1) is False
    assert user_service.get(1) is None
    assert user_service.update(1, UserUpdate(name='x')) is None


def test_service_ids_increment(user_service):
    first = user_service.create(UserCreate(name='A', email='a@example.com'))
    second = user_service.create(UserCreate(name='B', email='b@example.com'))
    assert (first.id, second.id) == (1, 2)


def test_create_user(client):
    response = client.post('/users', json={'name': 'Ada', 'email': 'ada@example.com'})

    assert response.status_code == 201
    body = response.json()
    assert body['id'] == 1
    assert body['name'] == 'Ada'
    assert 'created_at' in body


def test_list_and_get_user(client):
    client.post('/users', json={'name': 'Ada', 'email': 'ada@example.com'})

    assert client.get('/users').json()['total'] == 1
    assert client.get('/users/1').json()['email'] == 'ada@example.com'


def _make_users(client, n):
    for i in range(n):
        client.post('/users', json={'name': f'U{i}', 'email': f'u{i}@example.com'})


def test_list_defaults(client):
    _make_users(client, 3)

    body = client.get('/users').json()

    assert [u['name'] for u in body['items']] == ['U0', 'U1', 'U2']
    assert {k: body[k] for k in ('total', 'page', 'page_size', 'total_pages')} == {
        'total': 3, 'page': 1, 'page_size': 20, 'total_pages': 1}


def test_list_second_page_and_rounding(client):
    _make_users(client, 5)

    body = client.get('/users', params={'page': 2, 'page_size': 2}).json()

    assert [u['name'] for u in body['items']] == ['U2', 'U3']
    assert body['total'] == 5
    assert body['page'] == 2
    assert body['page_size'] == 2
    assert body['total_pages'] == 3


def test_list_last_partial_page(client):
    _make_users(client, 5)

    body = client.get('/users', params={'page': 3, 'page_size': 2}).json()

    assert [u['name'] for u in body['items']] == ['U4']


def test_list_exact_multiple(client):
    _make_users(client, 4)

    assert client.get('/users', params={'page_size': 2}).json()['total_pages'] == 2


def test_list_empty(client):
    body = client.get('/users').json()

    assert body == {'items': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0}


def test_list_page_beyond_last(client):
    _make_users(client, 2)

    response = client.get('/users', params={'page': 9, 'page_size': 2})

    assert response.status_code == 200
    assert response.json()['items'] == []
    assert response.json()['total_pages'] == 1


@pytest.mark.parametrize('params', [
    {'page': 0}, {'page': -1}, {'page_size': 0}, {'page_size': 101},
    {'page': 'abc'}, {'page_size': 'x'},
])
def test_list_invalid_pagination(client, params):
    assert client.get('/users', params=params).status_code == 422


def test_list_page_size_max_allowed(client):
    assert client.get('/users', params={'page_size': 100}).status_code == 200


def test_openapi_documents_pagination(client):
    spec = client.get('/openapi.json').json()

    op = spec['paths']['/users']['get']
    assert {p['name'] for p in op['parameters']} == {'page', 'page_size'}
    ref = op['responses']['200']['content']['application/json']['schema']['$ref']
    schema = spec['components']['schemas'][ref.split('/')[-1]]
    assert set(schema['properties']) == {'items', 'total', 'page', 'page_size', 'total_pages'}


def test_update_user_partial(client):
    client.post('/users', json={'name': 'Ada', 'email': 'ada@example.com'})

    response = client.put('/users/1', json={'name': 'Grace'})

    assert response.status_code == 200
    assert response.json()['name'] == 'Grace'
    assert response.json()['email'] == 'ada@example.com'


def test_delete_user(client):
    client.post('/users', json={'name': 'Ada', 'email': 'ada@example.com'})

    assert client.delete('/users/1').status_code == 204
    assert client.get('/users/1').status_code == 404


@pytest.mark.parametrize('method', ['get', 'delete'])
def test_missing_user_returns_404(client, method):
    assert getattr(client, method)('/users/99').status_code == 404


def test_update_missing_user_returns_404(client):
    assert client.put('/users/99', json={'name': 'x'}).status_code == 404


@pytest.mark.parametrize('payload', [
    {'name': 'Ada'},
    {'name': 'Ada', 'email': 'not-an-email'},
])
def test_create_invalid_payload_returns_422(client, payload):
    assert client.post('/users', json=payload).status_code == 422


def test_ping_still_works(client):
    assert client.get('/ping').json() == {'status': 'ok'}
