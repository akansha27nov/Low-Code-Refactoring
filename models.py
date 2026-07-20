"""Pydantic models for meal plan validation. Relocated as-is from the notebook —
these were already well-structured, just misplaced in a monolithic cell."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator
from meal_planner_config import INGREDIENTS_PER_RECIPE


class DietaryPreference(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"


class Ingredient(BaseModel):
    """Single ingredient with quantity."""
    name: str = Field(..., description="Name of the ingredient")
    quantity: str = Field(..., description="Quantity with unit (e.g., '2 cups', '500g')")


class Recipe(BaseModel):
    """A single themed dinner recipe."""
    day: str = Field(..., description="Day of the week")
    theme: str = Field(..., description="Cuisine theme (e.g., 'Italian', 'Mexican')")
    dish_name: str = Field(..., description="Name of the dish")
    ingredients: List[Ingredient] = Field(..., description="List of 5 ingredients")
    instructions: str = Field(..., description="Brief cooking instructions")

    @field_validator('ingredients')
    @classmethod
    def validate_ingredient_count(cls, v):
        if len(v) != INGREDIENTS_PER_RECIPE:
            raise ValueError(f"Recipe must have exactly {INGREDIENTS_PER_RECIPE} ingredients, got {len(v)}")
        return v


class ShoppingItem(BaseModel):
    """Consolidated shopping list item."""
    name: str = Field(..., description="Ingredient name")
    total_quantity: str = Field(..., description="Total quantity needed")
    used_in: List[str] = Field(..., description="List of dishes using this ingredient")


class MealPlan(BaseModel):
    """Complete weekly meal plan."""
    dietary_preference: str = Field(..., description="Selected dietary preference")
    recipes: List[Recipe] = Field(..., description="List of 7 recipes for the week")
    shopping_list: List[ShoppingItem] = Field(..., description="Consolidated shopping list")

    @field_validator('recipes')
    @classmethod
    def validate_recipe_count(cls, v):
        if len(v) != 7:
            raise ValueError(f"Meal plan must have exactly 7 recipes, got {len(v)}")
        return v

    @field_validator('recipes')
    @classmethod
    def validate_unique_themes(cls, v):
        themes = [r.theme.lower() for r in v]
        if len(themes) != len(set(themes)):
            raise ValueError("All 7 themes must be unique")
        return v