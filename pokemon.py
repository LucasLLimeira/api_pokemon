def calcula_pontos_ataque(pokemon:dict) -> int:
    """Calcula o poder de ataque baseado na força base e nível do pokemon."""
    return pokemon["base_attack"] * pokemon["level"]

def pokemon_evoluiu(pokemon:dict, nivel_evolucao:int) -> bool:
    """Determina se o pokemon evoluiu com base no nível de evolução."""
    return pokemon["level"] >= nivel_evolucao