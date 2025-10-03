from django import template
from auditlog.models import LogEntry

register = template.Library()

@register.filter(name="format_changes")
def format_changes(log_entry):
    """
    Filtro para formatar os detalhes do LogEntry de forma mais legível.
    """
    if not isinstance(log_entry, LogEntry):
        return ""

    action = log_entry.action
    changes = log_entry.changes_dict

    # Se a ação for DELETAR, mostre uma mensagem simples.
    if action == LogEntry.Action.DELETE:
        return f"O objeto '{log_entry.object_repr}' foi excluído."

    # Se a ação for ATUALIZAR, mostre as mudanças de -> para.
    if action == LogEntry.Action.UPDATE:
        lines = ["O objeto foi atualizado:"]
        for field, (old, new) in changes.items():
            lines.append(f'• {field}: "{old}" → "{new}"')
        return "\n".join(lines)

    # Se a ação for CRIAR, mostre apenas os valores iniciais.
    if action == LogEntry.Action.CREATE:
        lines = ["Objeto criado com os seguintes valores:"]
        # Limpamos os campos que não são úteis para o usuário final
        hidden_fields = ['id', 'created_at', 'updated_at', 'is_activate']
        
        for field, (old, new) in changes.items():
            if field in hidden_fields:
                continue # Pula campos irrelevantes
            if new: # Mostra apenas campos que foram preenchidos
                lines.append(f'• {field}: "{new}"')
        
        # Se todos os campos estiverem vazios (o que é raro), mostre uma mensagem genérica
        if len(lines) == 1:
             return f"O objeto '{log_entry.object_repr}' foi criado."

        return "\n".join(lines)

    return log_entry.changes_str # Fallback para o padrão