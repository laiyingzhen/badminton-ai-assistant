class NoRacketCandidateError(Exception):

    def __init__(self, budget: float):
        self.budget = budget

        super().__init__(
            f"No racket candidates found within budget {budget}."
        )


class InvalidRacketCandidateError(Exception):

    def __init__(self, racket_id: int):
        self.racket_id = racket_id

        super().__init__(
            f"Gemini selected invalid racket candidate: {racket_id}."
        )


class GeminiServiceError(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseServiceError(Exception):

    def __init__(self, message: str):
        super().__init__(message)