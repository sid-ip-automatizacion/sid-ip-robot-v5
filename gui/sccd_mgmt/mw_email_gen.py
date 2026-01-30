"""
Maintenance Window Email Generator Module.

This module provides functionality for generating HTML emails for
maintenance window notifications from structured text input using
Jinja2 templates.
"""

import re
from jinja2 import Template


def parse_text_to_dict(text: str) -> dict:
    """
    Parse structured text into a dictionary.

    Extracts key-value pairs for RFC, status, start/end dates, and details
    from formatted text input.

    Args:
        text: Structured text with key: value format

    Returns:
        dict: Dictionary with extracted values for rfc, status,
              start_date, end_date, and details
    """
    # Define the expected keys
    keys = ["rfc", "status", "start_date", "end_date", "details"]

    # Use regex to find keys and values
    pattern = r"(rfc|status|start_date|end_date|details):\s*((?:.|\n)*?)(?=(rfc|status|start_date|end_date|details|$))"
    matches = re.findall(pattern, text)

    # Create dictionary with extracted values
    result_dict = {}
    for match in matches:
        key, value = match[0], match[1].strip()  # Remove extra whitespace from values

        # For "details" key, replace newlines with spaces
        if key == "details":
            value = value.replace("\n", " ")

        result_dict[key] = value

    return result_dict


def generate_html_from_template(template_file: str, output_file: str, replacements: dict) -> None:
    """
    Generate an HTML file from a Jinja2 template.

    Args:
        template_file: Path to the Jinja2 template file
        output_file: Path where the rendered HTML will be saved
        replacements: Dictionary of values to substitute in the template
    """
    # Read the template
    with open(template_file, 'r', encoding='utf-8') as file:
        template = Template(file.read())

    # Render the template with dictionary values
    html_content = template.render(replacements)

    # Save the new HTML file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)


def generate_MW_email(text: str) -> None:
    """
    Generate a maintenance window email HTML file.

    Parses the input text for MW details and generates an HTML email
    using the email template.

    Args:
        text: Structured text containing MW information (rfc, status,
              start_date, end_date, details)
    """
    mw_dic = parse_text_to_dict(text)
    print(mw_dic)
    print('outputs/MW_' + mw_dic['rfc'] + '.html')
    generate_html_from_template(
        'resources/states/email.html',
        'outputs/MW_' + mw_dic['rfc'] + '_' + mw_dic['status'] + '.html',
        mw_dic
    )


# Sample text for testing
text_sample = """
rfc: RFC15265
status: text_state
start_date: 2024-08-10 14:30:00
end_date: 2024-08-11 18:45:00
details: This is a detail
with multiple lines of information
that can continue.
"""

# generate_MW_email(text_sample)