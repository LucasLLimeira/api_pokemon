from app.models.pagination import PaginationResponse


def test_pagination_next_previous_first_page() -> None:
    pagination = PaginationResponse(
        total=100,
        page=1,
        size=20,
        next="/pokemons?page=2&size=20",
        previous=None,
    )

    assert pagination.page == 1
    assert pagination.next == "/pokemons?page=2&size=20"
    assert pagination.previous is None
