import json

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

    # Tentar parsear as mudanças do campo changes
    try:
        # Para registros manuais, o campo changes pode ser uma string JSON
        if isinstance(log_entry.changes, str):
            changes_dict = json.loads(log_entry.changes)
            # Converter para o formato esperado pelo código existente
            changes = {}
            for change in changes_dict:
                for field, values in change.items():
                    changes[field] = values
        else:
            # Para registros automáticos, usar changes_dict normal
            changes = log_entry.changes_dict
    except (json.JSONDecodeError, AttributeError, TypeError):
        # Fallback para changes_dict normal
        changes = getattr(log_entry, "changes_dict", {})

    # Se a ação for DELETAR, mostre uma mensagem simples.
    if action == LogEntry.Action.DELETE:
        return f"O registro '{log_entry.object_repr}' foi excluído permanentemente."

    # Se a ação for ATUALIZAR, mostre apenas os campos que realmente mudaram
    if action == LogEntry.Action.UPDATE:
        lines = []
        changes_count = 0

        for field, (old, new) in changes.items():
            # Pula campos que não mudaram realmente
            if old == new:
                continue

            # Mensagem especial para ativação/desativação
            if field == "is_active":
                # Usar o object_repr diretamente como nome
                usuario_nome = log_entry.object_repr

                if new is True or str(new).lower() == "true":
                    lines.append(
                        f"• A conta de {usuario_nome} foi ativada (acesso restaurado ao sistema)"
                    )
                else:
                    lines.append(
                        f"• A conta de {usuario_nome} foi desativada (acesso ao sistema removido)"
                    )
                changes_count += 1
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
    elif valor is True or str(valor).lower() == "true":
        return "Ativo"
    elif valor is False or str(valor).lower() == "false":
        return "Inativo"
    elif isinstance(valor, str) and len(valor) > 50:
        return f"{valor[:50]}..."
    return str(valor)


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
    nome = (
        changes.get("first_name", ("", ""))[1]
        if isinstance(changes.get("first_name"), (list, tuple))
        else changes.get("first_name", "")
    )
    email = (
        changes.get("email", ("", ""))[1]
        if isinstance(changes.get("email"), (list, tuple))
        else changes.get("email", "")
    )
    username = (
        changes.get("username", ("", ""))[1]
        if isinstance(changes.get("username"), (list, tuple))
        else changes.get("username", "")
    )

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
    nome = ""
    if "first_name" in changes:
        nome = (
            changes["first_name"][1]
            if isinstance(changes["first_name"], (list, tuple))
            else changes["first_name"]
        )
    elif "name" in changes:
        nome = changes["name"][1] if isinstance(changes["name"], (list, tuple)) else changes["name"]
    elif "full_name" in changes:
        nome = (
            changes["full_name"][1]
            if isinstance(changes["full_name"], (list, tuple))
            else changes["full_name"]
        )

    cpf = (
        changes.get("cpf", ("", ""))[1]
        if isinstance(changes.get("cpf"), (list, tuple))
        else changes.get("cpf", "")
    )

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
        if field in changes:
            nome = (
                changes[field][1] if isinstance(changes[field], (list, tuple)) else changes[field]
            )
            if nome and len(str(nome)) < 100:
                return f"Registro criado: {nome}"

    return f"Novo registro criado: {log_entry.object_repr}"
