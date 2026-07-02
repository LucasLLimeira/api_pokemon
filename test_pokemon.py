import pytest

from pokemon import calcula_pontos_ataque, pokemon_evoluiu


@pytest.fixture
def pokemon_pikachu():
    return {"nome": "Pikachu", "forca_base": 10, "nivel": 5}


@pytest.fixture
def pokemon_bulbasaur():
    return {"nome": "Bulbasaur", "forca_base": 7, "nivel": 12}


def _para_formato_funcao(pokemon_fixture):
    return {
        "base_attack": pokemon_fixture["forca_base"],
        "level": pokemon_fixture["nivel"],
    }


def test_calcula_pontos_ataque_pikachu(pokemon_pikachu):
    pokemon = _para_formato_funcao(pokemon_pikachu)
    assert calcula_pontos_ataque(pokemon) == 50


def test_calcula_pontos_ataque_bulbasaur(pokemon_bulbasaur):
    pokemon = _para_formato_funcao(pokemon_bulbasaur)
    assert calcula_pontos_ataque(pokemon) == 84


def test_pokemon_evolui_antes_nivel(pokemon_pikachu):
    pokemon = _para_formato_funcao(pokemon_pikachu)
    assert pokemon_evoluiu(pokemon, 10) is False


def test_pokemon_evolui_no_nivel(pokemon_bulbasaur):
    pokemon = _para_formato_funcao(pokemon_bulbasaur)
    assert pokemon_evoluiu(pokemon, 12) is True


def test_pokemon_evolui_acima_nivel(pokemon_bulbasaur):
    pokemon = _para_formato_funcao(pokemon_bulbasaur)
    assert pokemon_evoluiu(pokemon, 10) is True