import re
from jinja2 import Template

def parse_text_to_dict(text):
    # Definir las claves que esperamos
    keys = ["rfc", "status", "start_date", "end_date", "details"]

    # Usar una expresión regular para encontrar las claves y valores
    pattern = r"(rfc|status|start_date|end_date|details):\s*((?:.|\n)*?)(?=(rfc|status|start_date|end_date|details|$))"
    matches = re.findall(pattern, text)

    # Crear el diccionario con los valores obtenidos
    result_dict = {}
    for match in matches:
        key, value = match[0], match[1].strip()  # Eliminar espacios extra en los valores

        # Si la clave es "details", eliminar los saltos de línea en su valor
        if key == "details":
            value = value.replace("\n", " ")  # Reemplaza saltos de línea por espacios en blanco

        result_dict[key] = value

    return result_dict

# Ejemplo de uso




def generate_html_from_template(template_file, output_file, replacements):
    # Leer la plantilla
    with open(template_file, 'r', encoding='utf-8') as file:
        template = Template(file.read())

    # Renderizar la plantilla con los valores del diccionario
    html_content = template.render(replacements)

    # Guardar el nuevo archivo HTML
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)


def generate_MW_email(text):
    mw_dic=parse_text_to_dict(text)
    print(mw_dic)
    print('outputs/MW_'+mw_dic['rfc']+'.html')
    generate_html_from_template('resources/states/email.html', 'outputs/MW_'+mw_dic['rfc']+'_'+mw_dic['status']+'.html',mw_dic)


text_sample="""
rfc: RFC15265
status: text_state
start_date: 2024-08-10 14:30:00
end_date: 2024-08-11 18:45:00
details: Este es un detalle
con varias líneas de información
que puede continuar.
"""

#generate_MW_email(text_sample) 