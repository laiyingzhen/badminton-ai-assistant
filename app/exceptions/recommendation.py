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

class NoEquipmentCandidateError(Exception):

    def __init__(
        self,
        equipment_type: str,
        budget: float,
    ):
        self.equipment_type = equipment_type
        self.budget = budget

        super().__init__(
            f"No {equipment_type} candidates found "
            f"within budget {budget}."
        )


class InvalidEquipmentCandidateError(Exception):

    def __init__(
        self,
        equipment_type: str,
        equipment_id: int,
    ):
        self.equipment_type = equipment_type
        self.equipment_id = equipment_id

        super().__init__(
            f"Gemini selected invalid "
            f"{equipment_type} candidate: {equipment_id}."
        )        