"""LLM prompt templates and model getter for the meal planner.
Relocated from the notebook — updated to strongly enforce structure."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .meal_planner_config import OPENAI_MODEL, TEMPERATURE

def get_llm() -> ChatOpenAI:
    """Get the configured LLM instance."""
    return ChatOpenAI(model=OPENAI_MODEL, temperature=TEMPERATURE)

EXAMPLE_OUTPUT = """
Example of the EXACT structure required (do not copy content, only structure):
{{
  "dietary_preference": "omnivore",
  "recipes": [
    {{
      "day": "Monday",
      "theme": "Italian",
      "dish_name": "Chicken Parmesan",
      "ingredients": [
        {{"name": "chicken breast", "quantity": "500g"}},
        {{"name": "parmesan cheese", "quantity": "100g"}}
      ],
      "instructions": "Bread chicken, bake, top with sauce and cheese."
    }}
  ],
  "shopping_list": [
    {{"name": "chicken breast", "total_quantity": "500g", "used_in": ["Chicken Parmesan"]}}
  ]
}}
"""

MEAL_PLAN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional meal planner. Generate a weekly meal plan with EXACTLY 7 themed dinners.

CRITICAL JSON RULES - YOU MUST FOLLOW THESE OR THE SYSTEM WILL CRASH:
1. NEVER wrap the output in a "MealPlan" key. Start directly with {{ "dietary_preference": ... }}
2. NEVER use days like "Monday" as dictionary keys. Days MUST be values inside a list of "recipes".
3. "ingredients" MUST be a list of objects containing "name" and "quantity".
4. You MUST include "dietary_preference", "recipes" (list of 7), and "shopping_list" (list).
5. Each recipe MUST have exactly 5 main ingredients.

Dietary Guidelines:
- Omnivore: Any ingredients allowed
- Vegetarian: No meat/fish
- Vegan: No animal products
- Keto: Low carb, high fat

{example_output}

Output valid JSON matching this exact structure:
{{format_instructions}}"""),
    ("human", """Create a weekly meal plan:
- Diet: {dietary_preference}
- Theme requests: {theme_requests}
- Preferences: {additional_preferences}

Generate 7 unique themed dinners for Monday-Sunday.""")
]).partial(example_output=EXAMPLE_OUTPUT)

SHOPPING_LIST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a shopping list organizer. Consolidate ingredients from multiple recipes into a single shopping list.

RULES:
1. Combine same ingredients and sum their quantities
2. List which dishes use each ingredient
3. Output valid JSON matching this structure:
{format_instructions}"""),
    ("human", """Consolidate the shopping list from these recipes:
{recipes_json}""")
])