"""Gradio interface for the meal planner. Wrapped in a main() so importing
this module (e.g. for testing format_shopping_list) doesn't launch a server
or require live credentials — matches the lab's 'no module-level side effects
on import' checkpoint.
"""

import time as pytime

import gradio as gr

from .meal_plan_generator import MealPlanGenerator
from .email_utils import send_meal_plan_email
from path2.dataset_evaluation import run_basic_validation


def format_shopping_list(meal_plan: dict) -> str:
    """Format shopping list section."""
    lines = ["## Shopping List\n"]
    for item in meal_plan["shopping_list"]:
        lines.append(f"- {item['total_quantity']} **{item['name']}**")
    return "\n".join(lines)


def format_single_recipe(recipe: dict) -> str:
    """Format a single recipe compactly."""
    ingredients = ", ".join([f"{ing['quantity']} {ing['name']}" for ing in recipe["ingredients"]])
    return f"**{recipe['day']}** | {recipe['theme']} | *{recipe['dish_name']}*\n{ingredients}\n"


def build_generate_plan_streaming(generator: MealPlanGenerator):
    """
    Returns a Gradio-callback closure over `generator`, so the UI functions
    don't rely on a module-level global (the original notebook referenced
    `generator` as a bare global from the enclosing scope).
    """

    def generate_plan_streaming(dietary_pref, theme_requests, additional_prefs):
        """Generate meal plan with streaming output."""
        yield "Generating your meal plan..."

        result = generator.generate(
            dietary_preference=dietary_pref,
            theme_requests=theme_requests if theme_requests.strip() else "random",
            additional_preferences=additional_prefs if additional_prefs.strip() else "none",
        )

        if not result["success"]:
            yield f"Error: {result['error']}"
            return

        meal_plan = result["meal_plan"]
        output = f"## Weekly {meal_plan['dietary_preference'].title()} Meal Plan\n\n"
        output += format_shopping_list(meal_plan) + "\n\n---\n\n## Recipes\n\n"
        yield output
        pytime.sleep(0.1)

        for recipe in meal_plan["recipes"]:
            output += format_single_recipe(recipe) + "\n"
            yield output
            pytime.sleep(0.05)

        validation = run_basic_validation(result)
        status = "All checks passed" if validation["passed"] else f"Issues: {', '.join(validation['errors'])}"
        output += f"---\n*Generated in {result['generation_time']}s | {status}*"
        yield output

    return generate_plan_streaming


def build_send_email_ui(generator: MealPlanGenerator):
    """Returns a Gradio-callback closure over `generator`."""

    def send_email_ui(email, dietary_pref, theme_requests, additional_prefs):
        """Generate and send meal plan via email."""
        if not email or "@" not in email:
            return "Enter a valid email address."

        result = generator.generate(
            dietary_preference=dietary_pref,
            theme_requests=theme_requests if theme_requests.strip() else "random",
            additional_preferences=additional_prefs if additional_prefs.strip() else "none",
        )

        if not result["success"]:
            return f"Generation failed: {result['error']}"

        email_result = send_meal_plan_email(email, result["meal_plan"])
        return email_result["message"]

    return send_email_ui


def build_app(generator: MealPlanGenerator) -> gr.Blocks:
    """Construct the Gradio Blocks app, wired to the given generator instance."""
    generate_plan_streaming = build_generate_plan_streaming(generator)
    send_email_ui = build_send_email_ui(generator)

    with gr.Blocks(title="Weekly Meal Planner") as app:
        gr.Markdown("# Weekly Meal Planner\nGenerate 7 themed dinners with a consolidated shopping list.")

        with gr.Row():
            with gr.Column(scale=1):
                dietary_dropdown = gr.Dropdown(
                    choices=["omnivore", "vegetarian", "vegan", "keto"],
                    value="omnivore", label="Diet"
                )
                theme_input = gr.Textbox(label="Themes (optional)", placeholder="Italian, Mexican...", lines=1)
                additional_input = gr.Textbox(label="Preferences (optional)", placeholder="no nuts, quick meals...", lines=1)
                generate_btn = gr.Button("Generate", variant="primary")

                gr.Markdown("---")
                email_input = gr.Textbox(label="Email", placeholder="you@example.com")
                send_btn = gr.Button("Email Plan")
                email_status = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=2):
                output_display = gr.Markdown("Click **Generate** to start.")

        generate_btn.click(
            fn=generate_plan_streaming,
            inputs=[dietary_dropdown, theme_input, additional_input],
            outputs=[output_display],
        )
        send_btn.click(
            fn=send_email_ui,
            inputs=[email_input, dietary_dropdown, theme_input, additional_input],
            outputs=[email_status],
        )

    return app


def main():
    """Entrypoint: build a generator, build the app, launch it."""
    from meal_planner_config import validate_config
    validate_config(require_email=True)  # email feature needs these; langsmith not required to launch

    generator = MealPlanGenerator()
    app = build_app(generator)
    app.launch(share=True)


if __name__ == "__main__":
    main()