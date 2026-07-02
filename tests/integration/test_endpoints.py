def test_get_pokemons_success(client, auth_headers):
    response = client.get("/pokemons?page=1&size=20", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    assert "pagination" in payload
    assert payload["pagination"]["total"] == 1
    assert payload["data"][0]["name"] == "pikachu"


def test_get_pokemon_by_id_success(client, auth_headers):
    response = client.get("/pokemons/25", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 25
    assert payload["types"] == ["electric"]


def test_get_pokemon_by_name_success(client, auth_headers):
    response = client.get("/pokemons/name/pikachu", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "pikachu"


def test_get_pokemons_by_type_success(client, auth_headers):
    response = client.get("/pokemons/type/electric?page=1&size=20", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["page"] == 1


def test_auth_error_without_api_key(client):
    response = client.get("/pokemons")

    assert response.status_code == 401
    payload = response.json()
    assert payload["error_code"] == "INVALID_API_KEY"


def test_docs_without_api_key(client):
    response = client.get("/docs")

    assert response.status_code == 200


def test_pokemon_not_found(client, auth_headers):
    response = client.get("/pokemons/9999", headers=auth_headers)

    assert response.status_code == 404
    payload = response.json()
    assert payload["error_code"] == "POKEMON_NOT_FOUND"


def test_pagination_validation_error(client, auth_headers):
    response = client.get("/pokemons?page=0&size=20", headers=auth_headers)

    assert response.status_code == 422
