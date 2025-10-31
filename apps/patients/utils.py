def convert_days_to_age_components(total_days: int) -> dict:
    """
    Converte um número total de dias (positivo ou negativo) em um
    dicionário estruturado contendo meses, semanas e dias.
    """
    # 1. Determina se o período é negativo e guarda essa informação.
    is_negative = total_days < 0

    # 2. Trabalha com o valor absoluto para todos os cálculos.
    #    Isso simplifica a lógica e evita repetição de código.
    effective_days = abs(total_days)

    # 3. Realiza os cálculos de conversão.
    #    Aproximação: 1 mês = 30 dias
    months = effective_days // 30
    remaining_days_after_months = effective_days % 30

    weeks = remaining_days_after_months // 7
    days = remaining_days_after_months % 7

    # 4. Retorna a estrutura de dados completa.
    return {
        "is_negative": is_negative,
        "total_days": total_days,  # Mantém o valor original para referência
        "months": months,
        "weeks": weeks,
        "days": days,
    }
