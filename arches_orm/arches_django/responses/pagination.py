

class PaginationResponse:

    _current_page = 0;
    _limit = 30;

    def __init__(self, currentPage: int):
        self._current_page = currentPage