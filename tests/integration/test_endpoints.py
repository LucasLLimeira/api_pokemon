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


def test_create_local_pokemon_success(crud_client, auth_headers):
    payload = {
        "name": "testmon",
        "height": 11,
        "weight": 99,
        "types": ["normal"],
        "sprites": {
            "front_default": "https://img/testmon-front.png",
            "back_default": "https://img/testmon-back.png",
        },
    }

    response = crud_client.post("/pokemons", json=payload, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "testmon"


def test_list_local_pokemons_success(crud_client, auth_headers):
    crud_client.post(
        "/pokemons",
        json={
            "name": "testmon",
            "height": 11,
            "weight": 99,
            "types": ["normal"],
            "sprites": {"front_default": None, "back_default": None},
        },
        headers=auth_headers,
    )

    response = crud_client.get("/pokemons/local?page=1&size=20", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["data"][0]["name"] == "testmon"


def test_update_local_pokemon_success(crud_client, auth_headers):
    created = crud_client.post(
        "/pokemons",
        json={
            "name": "testmon",
            "height": 11,
            "weight": 99,
            "types": ["normal"],
            "sprites": {"front_default": None, "back_default": None},
        },
        headers=auth_headers,
    )

    pokemon_id = created.json()["id"]
    response = crud_client.put(
        f"/pokemons/{pokemon_id}",
        json={"name": "testmon-updated", "weight": 150},
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "testmon-updated"
    assert payload["weight"] == 150


def test_delete_local_pokemon_success(crud_client, auth_headers):
    created = crud_client.post(
        "/pokemons",
        json={
            "name": "testmon",
            "height": 11,
            "weight": 99,
            "types": ["normal"],
            "sprites": {"front_default": None, "back_default": None},
        },
        headers=auth_headers,
    )

    pokemon_id = created.json()["id"]
    response = crud_client.delete(f"/pokemons/{pokemon_id}", headers=auth_headers)

    assert response.status_code == 204

    list_response = crud_client.get("/pokemons/local?page=1&size=20", headers=auth_headers)
    assert list_response.json()["pagination"]["total"] == 0
