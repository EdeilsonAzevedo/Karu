import json

from auditlog.models import LogEntry
from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


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
        if isinstance(log_entry.changes, str):
            changes_dict = json.loads(log_entry.changes)
            changes = {}
            for change in changes_dict:
                for field, values in change.items():
                    changes[field] = values
        else:
            changes = log_entry.changes_dict
    except (json.JSONDecodeError, AttributeError, TypeError):
        changes = getattr(log_entry, "changes_dict", {})

    # Identificar o tipo de objeto
    object_type = identificar_tipo_objeto_detalhado(log_entry.content_type.model)

    # Se a ação for DELETAR
    if action == LogEntry.Action.DELETE:
        return formatar_exclusao_simples(object_type)

    # Se a ação for ATUALIZAR
    if action == LogEntry.Action.UPDATE:
        return formatar_alteracao_simples(changes, object_type)

    # Se a ação for CRIAR
    if action == LogEntry.Action.CREATE:
        return formatar_criacao_simples(log_entry, changes, object_type)

    return "Ação registrada no sistema."


def identificar_tipo_objeto_detalhado(model_name):
    """Identifica o tipo de objeto baseado no nome do modelo"""
    tipos = {
        # Modelos principais
        "patient": "paciente",
        "record": "prontuário",
        "dischargerecord": "alta hospitalar",
        "consultationrecord": "consulta",
        "clinicalevaluation": "avaliação clínica",
        "interdisciplinaryevaluation": "avaliação da equipe",
        "exam": "exame",
        "vaccine": "vacina",
        "followup": "acompanhamento",
        "clinicalwarningsign": "sinal de alerta clínico",
        # Modelos de usuários
        "user": "usuário do sistema",
        "gestorprofile": "perfil de gestor",
        "profissionalsaudeprofile": "perfil de profissional",
        "paisprofile": "perfil de pais/responsável",
        # Outros modelos do sistema (adicionar conforme necessário)
        "medicalhistory": "histórico médico",
        "developmentmilestone": "marco de desenvolvimento",
        "growthchart": "gráfico de crescimento",
        "medication": "medicação",
        "allergy": "alergia",
        "hospitalization": "hospitalização",
        "emergencycontact": "contato de emergência",
        "insurance": "convênio",
    }
    return tipos.get(model_name, "registro")


def formatar_exclusao_simples(object_type):
    """Formata exclusão de forma simples"""
    return f"{object_type.title()} foi excluído permanentemente."


def formatar_alteracao_simples(changes, object_type):
    """Formata alterações de forma simples e direta"""
    campos_alterados = []

    for field, (old, new) in changes.items():
        if old == new:
            continue

        # Traduz nomes de campos
        field_name = traduzir_campo_simples(field)

        # Formata valores
        old_formatted = formatar_valor_simples(old, field)
        new_formatted = formatar_valor_simples(new, field)

        # Para campo is_active, trata de forma especial
        if field == "is_active":
            if new is True:
                campos_alterados.append("Conta ativada")
            elif new is False:
                campos_alterados.append("Conta desativada")
            else:
                campos_alterados.append(f"{field_name}: {old_formatted} → {new_formatted}")
        else:
            campos_alterados.append(f"{field_name}: {old_formatted} → {new_formatted}")

    if campos_alterados:
        # Linguagem mais amigável para usuários
        if object_type == "usuário do sistema":
            if len(campos_alterados) == 1 and "Conta ativada" in campos_alterados[0]:
                return "Usuário ativado no sistema"
            elif len(campos_alterados) == 1 and "Conta desativada" in campos_alterados[0]:
                return "Usuário desativado no sistema"
            else:
                return "Usuário alterado: " + ", ".join(campos_alterados)
        else:
            return f"{object_type.title()} alterado: " + ", ".join(campos_alterados)
    else:
        if object_type == "usuário do sistema":
            return "Usuário atualizado"
        else:
            return f"{object_type.title()} atualizado"


def formatar_criacao_paciente_detalhada(changes):
    """Formata criação de paciente de forma detalhada"""
    detalhes = []

    if "first_name" in changes:
        nome = (
            changes["first_name"][1]
            if isinstance(changes["first_name"], (list, tuple))
            else changes["first_name"]
        )
        if nome:
            detalhes.append(f"Nome: {nome}")

    if "last_name" in changes:
        sobrenome = (
            changes["last_name"][1]
            if isinstance(changes["last_name"], (list, tuple))
            else changes["last_name"]
        )
        if sobrenome:
            detalhes.append(f"Sobrenome: {sobrenome}")

    if detalhes:
        return "Paciente cadastrado: " + ", ".join(detalhes)
    else:
        return "Novo paciente cadastrado"


# Atualize a função formatar_criacao_simples para usar a nova função
def formatar_criacao_simples(log_entry, changes, object_type):
    """Formata criação de forma simples"""

    if object_type == "paciente":
        return formatar_criacao_paciente_detalhada(changes)
    elif object_type == "usuário do sistema":
        return formatar_criacao_usuario_detalhada(changes)
    elif object_type == "perfil de gestor":
        return formatar_criacao_perfil_gestor(changes)
    elif object_type == "perfil de profissional":
        return formatar_criacao_perfil_profissional(changes)
    elif object_type == "perfil de pais/responsável":
        return formatar_criacao_perfil_pais(changes)
    elif object_type == "consulta":
        return "Nova consulta registrada"
    elif object_type == "alta hospitalar":
        return "Alta hospitalar registrada"
    elif object_type == "prontuário":
        return "Prontuário criado"
    elif object_type == "avaliação clínica":
        return "Avaliação clínica registrada"
    elif object_type == "avaliação da equipe":
        return "Avaliação da equipe registrada"
    elif object_type == "exame":
        return "Exame registrado"
    elif object_type == "vacina":
        return "Vacina registrada"
    elif object_type == "sinal de alerta clínico":
        return "Sinal de alerta registrado"
    else:
        return f"Novo {object_type} criado"


def formatar_criacao_paciente_simples(changes):
    """Formata criação de paciente de forma simples"""
    nome = ""

    # Extrai nome do paciente
    if "first_name" in changes:
        nome = (
            changes["first_name"][1]
            if isinstance(changes["first_name"], (list, tuple))
            else changes["first_name"]
        )

    if "last_name" in changes:
        sobrenome = (
            changes["last_name"][1]
            if isinstance(changes["last_name"], (list, tuple))
            else changes["last_name"]
        )
        if nome and sobrenome:
            nome = f"{nome} {sobrenome}"

    if nome:
        return f"Paciente cadastrado: {nome}"
    else:
        return "Novo paciente cadastrado"


def formatar_criacao_usuario_detalhada(changes):
    """Formata criação de usuário de forma detalhada"""
    detalhes = []

    # Informações básicas do usuário
    if "username" in changes:
        cpf = (
            changes["username"][1]
            if isinstance(changes["username"], (list, tuple))
            else changes["username"]
        )
        detalhes.append(f"CPF: {formatar_valor_simples(cpf, 'cpf')}")

    if detalhes:
        return "Usuário criado: " + ", ".join(detalhes)
    else:
        return "Novo usuário criado"


def formatar_criacao_perfil_gestor(changes):
    """Formata criação de perfil de gestor"""
    detalhes = []

    if "unidade" in changes:
        unidade = (
            changes["unidade"][1]
            if isinstance(changes["unidade"], (list, tuple))
            else changes["unidade"]
        )
        if unidade:
            detalhes.append(f"Unidade: {unidade}")

    if "cargo" in changes:
        cargo = (
            changes["cargo"][1] if isinstance(changes["cargo"], (list, tuple)) else changes["cargo"]
        )
        if cargo:
            detalhes.append(f"Cargo: {cargo}")

    return "Perfil de gestor criado" + (": " + ", ".join(detalhes) if detalhes else "")


def formatar_criacao_perfil_profissional(changes):
    """Formata criação de perfil de profissional"""
    detalhes = []

    if "categoria" in changes:
        categoria = (
            changes["categoria"][1]
            if isinstance(changes["categoria"], (list, tuple))
            else changes["categoria"]
        )
        if categoria:
            detalhes.append(f"Categoria: {categoria}")

    if "unidade" in changes:
        unidade = (
            changes["unidade"][1]
            if isinstance(changes["unidade"], (list, tuple))
            else changes["unidade"]
        )
        if unidade:
            detalhes.append(f"Unidade: {unidade}")

    return "Perfil de profissional criado" + (": " + ", ".join(detalhes) if detalhes else "")


def formatar_criacao_perfil_pais(changes):
    """Formata criação de perfil de pais/responsável"""
    detalhes = []

    if "telefone" in changes:
        telefone = (
            changes["telefone"][1]
            if isinstance(changes["telefone"], (list, tuple))
            else changes["telefone"]
        )
        if telefone:
            detalhes.append(f"Telefone: {telefone}")

    return "Perfil de pais/responsável criado" + (": " + ", ".join(detalhes) if detalhes else "")


def traduzir_campo_simples(field_name):
    """Traduz nomes de campos de forma simples"""
    traducoes = {
        # Campos de usuário
        "first_name": "Nome",
        "last_name": "Sobrenome",
        "name": "Nome",
        "email": "E-mail",
        "username": "CPF",
        "cpf": "CPF",
        "contact_phone": "Telefone",
        "is_active": "Status da conta",
        "user_type": "Tipo de Usuário",
        # Campos de paciente
        "date_of_birth": "Data de nascimento",
        "birth_weight": "Peso ao nascer",
        "gestational_age_weeks": "Idade gestacional (semanas)",
        "birth_certificate_number": "Número da certidão de nascimento",
        "mother_name": "Nome da mãe",
        "father_name": "Nome do pai",
        "address_street": "Logradouro",
        "address_number": "Número",
        "address_complement": "Complemento",
        "address_neighborhood": "Bairro",
        "address_city": "Cidade",
        "address_state": "Estado",
        "address_zipcode": "CEP",
        # Campos médicos/antropométricos
        "weight": "Peso",
        "length": "Comprimento",
        "head_circumference": "Perímetro cefálico",
        "feeding_type": "Tipo de alimentação",
        "birth_height": "Altura ao nascer",
        # Campos de consulta/prontuário
        "date": "Data",
        "professional": "Profissional",
        "location": "Local",
        "status": "Status",
        "type": "Tipo",
        "result": "Resultado",
        "observations": "Observações",
        "notes": "Anotações",
        "next_appointment_date": "Data da próxima consulta",
        "appointment_type": "Tipo de consulta",
        # Campos de exames
        "exam_type": "Tipo de exame",
        "exam_date": "Data do exame",
        "requesting_professional": "Profissional solicitante",
        "laboratory": "Laboratório",
        # Campos de vacinas
        "vaccine_name": "Nome da vacina",
        "vaccine_date": "Data da vacina",
        "dose": "Dose",
        "batch_number": "Número do lote",
        # Campos de sinais de alerta
        "warning_type": "Tipo de sinal",
        "is_present": "Está presente",
        "severity": "Gravidade",
        "description": "Descrição",
        # Campos de perfis
        "unidade": "Unidade",
        "cargo": "Cargo",
        "categoria": "Categoria",
        "especialidade": "Especialidade",
        "conselho": "Conselho",
        "numero_registro": "Número de Registro",
        "telefone": "Telefone",
        "departamento": "Departamento",
        # Campos gerais do sistema
        "created_at": "Data de criação",
        "updated_at": "Data de atualização",
        "is_completed": "Está concluído",
        "is_approved": "Está aprovado",
        "reason": "Motivo",
        "comments": "Comentários",
        "diagnosis": "Diagnóstico",
        "treatment": "Tratamento",
        "prescription": "Prescrição",
        "recommendations": "Recomendações",
    }

    # Para campos não mapeados, tenta traduzir palavras comuns
    if field_name not in traducoes:
        field_lower = field_name.lower()
        if "date" in field_lower:
            return "Data"
        elif "time" in field_lower:
            return "Hora"
        elif "name" in field_lower:
            return "Nome"
        elif "description" in field_lower:
            return "Descrição"
        elif "number" in field_lower or "num" in field_lower:
            return "Número"
        elif "value" in field_lower:
            return "Valor"
        elif "type" in field_lower:
            return "Tipo"
        elif "category" in field_lower:
            return "Categoria"
        elif "status" in field_lower:
            return "Status"
        elif "active" in field_lower:
            return "Ativo"
        elif "created" in field_lower:
            return "Criado em"
        elif "updated" in field_lower:
            return "Atualizado em"

    return traducoes.get(field_name, field_name.replace("_", " ").title())


def formatar_valor_simples(valor, field_name):
    """Formata valores de forma simples"""
    if valor is None or valor == "":
        return "não informado"
    elif valor is True:
        if field_name == "is_active":
            return "Ativo"
        elif field_name == "is_present":
            return "Presente"
        elif field_name == "is_completed":
            return "Concluído"
        elif field_name == "is_approved":
            return "Aprovado"
        return "Sim"
    elif valor is False:
        if field_name == "is_active":
            return "Inativo"
        elif field_name == "is_present":
            return "Ausente"
        elif field_name == "is_completed":
            return "Pendente"
        elif field_name == "is_approved":
            return "Reprovado"
        return "Não"
    elif field_name == "cpf" and valor and len(str(valor)) == 11:
        cpf_str = str(valor)
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    elif field_name == "username" and valor and len(str(valor)) == 11:
        # Formata CPF também quando vem do campo username
        cpf_str = str(valor)
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    elif field_name in ["address_zipcode", "zipcode"] and valor and len(str(valor)) == 8:
        cep_str = str(valor)
        return f"{cep_str[:5]}-{cep_str[5:]}"
    elif isinstance(valor, str) and len(valor) > 30:
        return f"{valor[:30]}..."

    # Traduz valores específicos de campos enum
    if field_name == "feeding_type" and valor:
        alimentacao_traduzida = {
            "breastfeeding": "Aleitamento materno",
            "formula": "Fórmula infantil",
            "mixed": "Misto",
            "complementary": "Alimentação complementar",
        }
        return alimentacao_traduzida.get(valor, valor)

    if field_name == "gender" and valor:
        genero_traduzido = {
            "M": "Masculino",
            "F": "Feminino",
            "O": "Outro",
        }
        return genero_traduzido.get(valor, valor)

    return str(valor)
