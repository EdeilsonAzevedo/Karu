"""
Growth Charts - Intergrowth-21st
Lê CSVs e formata dados para Chart.js
"""

from pathlib import Path

import pandas as pd
from django.db.models import Q

from .models import Record


def get_intergrowth_data(measurement_type, sex):
    """
    Lê CSV e retorna dados formatados

    Args:
        measurement_type: 'weight', 'head_circumference', 'length'
        sex: 'M' ou 'F'

    Returns:
        dict: {'labels': [...], 'p3': [...], 'p10': [...], 'p50': [...], 'p90': [...], 'p97': [...]}
    """

    # Caminho do CSV
    base_dir = Path(__file__).parent
    sex_folder = "boys" if sex == "M" else "girls"
    csv_path = base_dir / "data" / "growth_charts" / sex_folder / f"{measurement_type}.csv"

    print("DEBUG get_intergrowth_data:")
    print(f"  measurement_type: {measurement_type}")
    print(f"  sex: '{sex}'")
    print(f"  sex_folder: {sex_folder}")
    print(f"  csv_path: {csv_path}")
    print(f"  Arquivo existe? {csv_path.exists()}")

    # Se não existir, retornar vazio
    if not csv_path.exists():
        print("  ERRO: CSV não encontrado!")
        return {"labels": [], "p3": [], "p10": [], "p50": [], "p90": [], "p97": []}

    # Ler CSV
    df = pd.read_csv(csv_path)
    print(f"  CSV lido: {len(df)} linhas")
    print(f"  Colunas disponíveis: {df.columns.tolist()}")

    # Verificar quais colunas de percentil existem
    result = {
        "labels": df["gestational_age_weeks"].tolist()
        if "gestational_age_weeks" in df.columns
        else [],
    }

    # P3
    if "centile_3rd" in df.columns:
        result["p3"] = df["centile_3rd"].tolist()
    else:
        print("  AVISO: coluna 'centile_3rd' não encontrada")
        result["p3"] = []

    # P10 (tenta 10th, senão usa 15th como fallback)
    if "centile_10th" in df.columns:
        result["p10"] = df["centile_10th"].tolist()
    elif "centile_15th" in df.columns:
        print("  INFO: Usando 'centile_15th' como fallback para P10")
        result["p10"] = df["centile_15th"].tolist()
    else:
        print("  AVISO: nem 'centile_10th' nem 'centile_15th' encontradas")
        result["p10"] = []

    # P50
    if "centile_50th" in df.columns:
        result["p50"] = df["centile_50th"].tolist()
    else:
        print("  AVISO: coluna 'centile_50th' não encontrada")
        result["p50"] = []

    # P90 (tenta 90th, senão usa 85th como fallback)
    if "centile_90th" in df.columns:
        result["p90"] = df["centile_90th"].tolist()
    elif "centile_85th" in df.columns:
        print("  INFO: Usando 'centile_85th' como fallback para P90")
        result["p90"] = df["centile_85th"].tolist()
    else:
        print("  AVISO: nem 'centile_90th' nem 'centile_85th' encontradas")
        result["p90"] = []

    # P97
    if "centile_97th" in df.columns:
        result["p97"] = df["centile_97th"].tolist()
    else:
        print("  AVISO: coluna 'centile_97th' não encontrada")
        result["p97"] = []

    print(f"  Resultado: {len(result['labels'])} labels, {len(result['p50'])} valores P50")

    return result


def get_growth_chart_data(patient):
    """
    Prepara dados dos gráficos de crescimento usando curvas Intergrowth-21 reais
    """

    # Buscar dados Intergrowth baseado no sexo do paciente
    intergrowth_weight = get_intergrowth_data("weight", patient.sex)
    intergrowth_length = get_intergrowth_data("length", patient.sex)
    intergrowth_head = get_intergrowth_data("head_circumference", patient.sex)

    # Dados de idade gestacional do paciente ao nascer
    gestational_weeks_at_birth = patient.gestational_age_weeks
    gestational_days_at_birth = patient.gestational_age_days or 0
    date_of_birth = patient.date_of_birth

    # Converter idade gestacional ao nascer para dias totais
    gestational_age_at_birth_in_days = (gestational_weeks_at_birth * 7) + gestational_days_at_birth

    # Buscar registros com medições do paciente
    records_for_chart = (
        Record.objects.filter(
            Q(consultation_details__isnull=False) | Q(discharge__isnull=False), patient=patient
        )
        .order_by("date")
        .distinct()
    )

    # O Intergrowth começa em 24 semanas (168 dias)
    INTERGROWTH_START_DAYS = 24 * 7  # 168 dias
    INTERGROWTH_END_DAYS = 42 * 7 + 6  # 300 dias (42 semanas e 6 dias)

    # Criar array com tamanho do Intergrowth (168 a 300 = 133 posições)
    total_intergrowth_positions = INTERGROWTH_END_DAYS - INTERGROWTH_START_DAYS + 1

    # Inicializar arrays para dados do paciente com None
    patient_weight_mapped = [None] * total_intergrowth_positions
    patient_length_mapped = [None] * total_intergrowth_positions
    patient_head_mapped = [None] * total_intergrowth_positions

    for rec in records_for_chart:
        # Calcular idade cronológica em dias desde o nascimento
        chronological_age_days = (rec.date - date_of_birth).days

        # Calcular idade gestacional corrigida em dias
        # Idade gestacional corrigida = idade gestacional ao nascer + idade cronológica
        corrected_gestational_age_days = gestational_age_at_birth_in_days + chronological_age_days

        # Calcular o índice no array Intergrowth
        # Se a idade gestacional corrigida for 24 semanas (168 dias) → índice 0
        # Se for 24 semanas e 1 dia (169 dias) → índice 1
        # E assim por diante...
        intergrowth_index = corrected_gestational_age_days - INTERGROWTH_START_DAYS

        # Verificar se o índice está dentro do range válido do Intergrowth
        if 0 <= intergrowth_index < total_intergrowth_positions:
            # Extrair dados da consulta ou alta
            data_source = getattr(rec, "consultation_details", None) or getattr(
                rec, "discharge", None
            )

            if data_source:
                print(
                    f"Record {rec.id} - Idade gestacional corrigida: {corrected_gestational_age_days} dias ({corrected_gestational_age_days // 7}s{corrected_gestational_age_days % 7}d) - Índice: {intergrowth_index}"
                )
                print(
                    f"  W={data_source.weight}, L={data_source.length}, H={data_source.head_circumference}"
                )

                patient_weight_mapped[intergrowth_index] = (
                    float(data_source.weight) / 1000 if data_source.weight else None
                )
                patient_length_mapped[intergrowth_index] = (
                    float(data_source.length) if data_source.length else None
                )
                patient_head_mapped[intergrowth_index] = (
                    float(data_source.head_circumference)
                    if data_source.head_circumference
                    else None
                )
        else:
            print(
                f"Record {rec.id} - Idade gestacional corrigida {corrected_gestational_age_days} dias está fora do range Intergrowth (168-300 dias)"
            )

    # Labels do Intergrowth (assumindo que sejam baseados em dias ou semanas)
    intergrowth_labels = intergrowth_weight.get("labels", [])

    return {
        "chart_labels": intergrowth_labels,
        "weight_data": {
            "patient": patient_weight_mapped,
            "p3": intergrowth_weight.get("p3", []),
            "p10": intergrowth_weight.get("p10", []),
            "p50": intergrowth_weight.get("p50", []),
            "p90": intergrowth_weight.get("p90", []),
            "p97": intergrowth_weight.get("p97", []),
        },
        "length_data": {
            "patient": patient_length_mapped,
            "p3": intergrowth_length.get("p3", []),
            "p10": intergrowth_length.get("p10", []),
            "p50": intergrowth_length.get("p50", []),
            "p90": intergrowth_length.get("p90", []),
            "p97": intergrowth_length.get("p97", []),
        },
        "head_data": {
            "patient": patient_head_mapped,
            "p3": intergrowth_head.get("p3", []),
            "p10": intergrowth_head.get("p10", []),
            "p50": intergrowth_head.get("p50", []),
            "p90": intergrowth_head.get("p90", []),
            "p97": intergrowth_head.get("p97", []),
        },
    }
