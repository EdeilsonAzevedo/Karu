from auditlog.models import LogEntry
from django import template

register = template.Library()


@register.filter(name="format_changes")
def format_changes(log_entry):
    """
    Filtro para formatar os detalhes do LogEntry de forma mais legível em português.
    """
    if not isinstance(log_entry, LogEntry):
        return ""

    action = log_entry.action
    changes = log_entry.changes_dict

    # Se a ação for DELETAR, mostre uma mensagem simples.
    if action == LogEntry.Action.DELETE:
        return f"O registro '{log_entry.object_repr}' foi excluído permanentemente."

    # Se a ação for ATUALIZAR, mostre apenas os campos que realmente mudaram
    if action == LogEntry.Action.UPDATE:
        lines = ["Foram realizadas as seguintes alterações:"]
        changes_count = 0

        for field, (old, new) in changes.items():
            # Pula campos técnicos e que não mudaram realmente
            if field in ["id", "created_at", "updated_at", "is_activate", "last_login"]:
                continue
            if old == new:
                continue

            # Traduz nomes de campos comuns
            field_name = traduzir_campo(field)

            lines.append(f'• {field_name}: de "{formatar_valor(old)}" para "{formatar_valor(new)}"')
            changes_count += 1

        if changes_count == 0:
            return "Foram feitas alterações menores no registro."

        return "\n".join(lines)

    # Se a ação for CRIAR, mostre informações resumidas
    if action == LogEntry.Action.CREATE:
        # Tenta identificar o tipo de objeto para mensagem personalizada
        object_type = identificar_tipo_objeto(log_entry.object_repr)

        if object_type == "usuário":
            return formatar_criacao_usuario(log_entry, changes)
        elif object_type == "paciente":
            return formatar_criacao_paciente(log_entry, changes)
        else:
            return formatar_criacao_generica(log_entry, changes)

    return "Ação registrada no sistema."  # Fallback genérico


def traduzir_campo(field_name):
    """Traduz nomes de campos técnicos para português amigável"""
    traducoes = {
        "first_name": "Nome",
        "last_name": "Sobrenome",
        "full_name": "Nome completo",
        "name": "Nome",
        "email": "E-mail",
        "username": "Usuário",
        "cpf": "CPF",
        "phone": "Telefone",
        "birth_date": "Data de nascimento",
        "address": "Endereço",
        "is_active": "Status",
        "password": "Senha",
        "user": "Usuário vinculado",
        "created_at": "Data de criação",
        "updated_at": "Última atualização",
    }
    return traducoes.get(field_name, field_name.replace("_", " ").title())


def formatar_valor(valor):
    """Formata valores para exibição mais amigável"""
    if valor is None or valor == "":
        return "não informado"
    elif valor is True:
        return "Ativo"
    elif valor is False:
        return "Inativo"
    elif isinstance(valor, str) and len(valor) > 50:
        return f"{valor[:50]}..."
    return valor


def identificar_tipo_objeto(object_repr):
    """Identifica o tipo de objeto baseado na representação"""
    repr_lower = object_repr.lower()
    if "user" in repr_lower or "usuário" in repr_lower or "@" in repr_lower:
        return "usuário"
    elif "patient" in repr_lower or "paciente" in repr_lower:
        return "paciente"
    return "registro"


def formatar_criacao_usuario(log_entry, changes):
    """Formata criação de usuário de forma amigável"""
    nome = changes.get("first_name", ("", ""))[1] or changes.get("name", ("", ""))[1]
    email = changes.get("email", ("", ""))[1]
    username = changes.get("username", ("", ""))[1]

    if nome and email:
        return f"Usuário criado: {nome} ({email})"
    elif nome:
        return f"Usuário criado: {nome}"
    elif email:
        return f"Usuário criado: {email}"
    elif username:
        return f"Usuário criado: {username}"
    else:
        return "Novo usuário criado no sistema"


def formatar_criacao_paciente(log_entry, changes):
    """Formata criação de paciente de forma amigável"""
    nome = (
        changes.get("first_name", ("", ""))[1]
        or changes.get("name", ("", ""))[1]
        or changes.get("full_name", ("", ""))[1]
    )
    cpf = changes.get("cpf", ("", ""))[1]

    if nome and cpf:
        return f"Paciente cadastrado: {nome} (CPF: {cpf})"
    elif nome:
        return f"Paciente cadastrado: {nome}"
    elif cpf:
        return f"Paciente cadastrado com CPF: {cpf}"
    else:
        return "Novo paciente cadastrado no sistema"


def formatar_criacao_generica(log_entry, changes):
    """Formata criação genérica de forma amigável"""
    # Tenta encontrar um campo de nome para personalizar a mensagem
    for field in ["name", "first_name", "full_name", "title", "description"]:
        if field in changes and changes[field][1]:
            nome = changes[field][1]
            if len(str(nome)) < 100:  # Não usar campos muito longos
                return f"Registro criado: {nome}"

    return f"Novo registro criado: {log_entry.object_repr}"
