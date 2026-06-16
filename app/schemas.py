from pydantic import BaseModel


class IngredientIn(BaseModel):
    raw_text: str
    quantity: str | None = None
    unit: str | None = None
    name: str | None = None


class StepIn(BaseModel):
    text: str


class RecipeIn(BaseModel):
    title: str
    description: str | None = None
    servings: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    ingredients: list[IngredientIn] = []
    steps: list[StepIn] = []
