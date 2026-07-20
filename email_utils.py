"""Email formatting and sending, with narrowed exception handling.

Previously: send_meal_plan_email() caught all exceptions identically —
an SMTP auth failure and a network timeout looked the same to the caller.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from meal_planner_config import EMAIL_SENDER, EMAIL_PASSWORD


def format_meal_plan_email(meal_plan: dict) -> str:
    """Format meal plan as readable email content (shopping list first)."""
    lines = ["=" * 40, f"WEEKLY MEAL PLAN ({meal_plan['dietary_preference'].upper()})",
              "=" * 40, ""]
    lines.append("SHOPPING LIST")
    lines.append("-" * 20)
    for item in meal_plan['shopping_list']:
        lines.append(f"- {item['total_quantity']} {item['name']}")
    lines.append("")
    lines.append("=" * 40)
    lines.append("RECIPES")
    lines.append("=" * 40)
    for recipe in meal_plan['recipes']:
        lines.append(f"\n{recipe['day'].upper()} - {recipe['theme']}")
        lines.append(f"{recipe['dish_name']}")
        ingredients = ", ".join([f"{ing['quantity']} {ing['name']}" for ing in recipe['ingredients']])
        lines.append(f"Ingredients: {ingredients}")
        lines.append(f"Instructions: {recipe['instructions']}")
    return "\n".join(lines)


def send_meal_plan_email(recipient_email: str, meal_plan: dict) -> dict:
    """
    Send meal plan via email.

    Returns:
        dict with 'success' bool and 'message' string. Different failure types
        produce distinguishable messages instead of one generic catch-all.
    """
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient_email
    msg['Subject'] = "Your Weekly Meal Plan"
    msg.attach(MIMEText(format_meal_plan_email(meal_plan), 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return {"success": True, "message": f"Email sent to {recipient_email}"}

    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "message": f"[send_meal_plan_email] SMTPAuthenticationError: {e}\n"
                       f"Suggestion: check EMAIL_SENDER/EMAIL_PASSWORD — Gmail requires an App Password, not your regular password."
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message": f"[send_meal_plan_email] {type(e).__name__}: {e}\n"
                       f"Suggestion: check recipient address '{recipient_email}' and SMTP server status."
        }
    except OSError as e:
        return {
            "success": False,
            "message": f"[send_meal_plan_email] {type(e).__name__}: {e}\n"
                       f"Suggestion: check network connection to smtp.gmail.com:587."
        }