"""Módulo de renderização de templates HTML com Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateSyntaxError


def render_template(template_path, variables):
    """Renderiza um template HTML substituindo as variáveis.

    Suporta sintaxe Jinja2: {{ nome }}, {{ empresa }}, {% if ... %}, etc.

    Args:
        template_path: Caminho para o arquivo .html do template.
        variables: Dicionário com as variáveis a substituir.

    Returns:
        str: HTML renderizado com as variáveis substituídas.
    """
    path = Path(template_path)

    if not path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    env = Environment(
        loader=FileSystemLoader(str(path.parent)),
        autoescape=False,
        keep_trailing_newline=True,
    )

    try:
        template = env.get_template(path.name)
    except TemplateSyntaxError as e:
        raise ValueError(f"Erro de sintaxe no template (linha {e.lineno}): {e.message}")

    str_vars = {k: str(v) if v is not None else "" for k, v in variables.items()}
    return template.render(**str_vars)


def render_subject(subject_template, variables):
    """Renderiza o assunto do e-mail com variáveis.

    Args:
        subject_template: String do assunto com variáveis {{ }}.
        variables: Dicionário com as variáveis.

    Returns:
        str: Assunto renderizado.
    """
    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(subject_template)
    str_vars = {k: str(v) if v is not None else "" for k, v in variables.items()}
    return template.render(**str_vars)
