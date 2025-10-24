import json
import unicodedata

# Copie o dicionário CIDADE_PARA_REGIAO da Etapa 1 para cá
REGIOES_SAUDE_AL = {
    '1ª Macro': {
        '1ª Região': ['Maceió', 'Barra de Santo Antônio', 'Barra de São Miguel', 'Coqueiro Seco', 'Flexeiras', 'Marechal Deodoro', 'Messias', 'Paripueira', 'Pilar', 'Rio Largo', 'Santa Luzia do Norte', 'Satuba'],
        '2ª Região': ['Maragogi', 'Jacuípe', 'Japaratinga', 'Matriz de Camaragibe', 'Passo de Camaragibe', 'Porto Calvo', 'Porto de Pedras', 'São Luiz do Quitunde', 'São Miguel dos Milagres'],
        '3ª Região': ['União dos Palmares', 'Branquinha', 'Campestre', 'Colônia Leopoldina', 'Ibateguara', 'Joaquim Gomes', 'Jundiá', 'Novo Lino', 'Santana do Mundaú', 'São José da Laje'],
        '4ª Região': ['Viçosa', 'Atalaia', 'Cajueiro', 'Capela', 'Chã Preta', 'Mar Vermelho', 'Paulo Jacinto', 'Pindoba', 'Quebrangulo'],
        '5ª Região': ['São Miguel dos Campos', 'Anadia', 'Boca da Mata', 'Campo Alegre', 'Junqueiro', 'Roteiro', 'Teotônio Vilela'],
        '6ª Região': ['Penedo', 'Coruripe', 'Feliz Deserto', 'Igreja Nova', 'Jequiá da Praia', 'Piaçabuçu', 'Porto Real do Colégio', 'São Brás'],
    },
    '2ª Macro': {
        '7ª Região': ['Arapiraca', 'Batalha', 'Belo Monte', 'Campo Grande', 'Coité do Nóia', 'Craíbas', 'Feira Grande', 'Girau do Ponciano', 'Jacaré dos Homens', 'Jaramataia', 'Lagoa da Canoa', 'Limoeiro de Anadia', 'Monteirópolis', 'Olho d\'Água Grande', 'São Sebastião', 'Taquarana', 'Traipu'],
        '8ª Região': ['Palmeira dos Índios', 'Belém', 'Cacimbinhas', 'Estrela de Alagoas', 'Igaci', 'Major Isidoro', 'Minador do Negrão', 'Tanque d\'Arca'],
        '9ª Região': ['Santana do Ipanema', 'Canapi', 'Carneiros', 'Dois Riachos', 'Maravilha', 'Olho d\'Água das Flores', 'Olivença', 'Ouro Branco', 'Palestina', 'Pão de Açúcar', 'Poço das Trincheiras', 'São José da Tapera', 'Senador Rui Palmeira'],
        '10ª Região': ['Delmiro Gouveia', 'Água Branca', 'Inhapi', 'Mata Grande', 'Pariconha', 'Piranhas'],
    }
}

# Criar um mapa reverso (Cidade -> Regiões) para busca rápida
CIDADE_PARA_REGIAO = {}
for macro, regioes in REGIOES_SAUDE_AL.items():
    for regiao, cidades in regioes.items():
        for cidade in cidades:
            # Normalizar nomes para evitar problemas com acentos (embora o ideal seja garantir que os dados batam)
            cidade_norm = cidade.upper().strip() 
            CIDADE_PARA_REGIAO[cidade_norm] = {
                'micro_regiao': regiao,
                'macro_regiao': macro
            }

# Função para normalizar nomes (remover acentos, maiúsculas)
def normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')\
                   .upper().strip()

# Caminho para seus arquivos
geojson_original = 'alagoas_municipios.geojson' # <-- SEU ARQUIVO DE ENTRADA
geojson_modificado = 'alagoas_municipios_com_regioes.geojson' # <-- NOME DO NOVO ARQUIVO

with open(geojson_original, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Itera sobre cada "feature" (município) no GeoJSON
for feature in data['features']:
    props = feature['properties']
    
    # Pega o nome do município. No seu karu_map.js, vi que você usa 'NM_MUN'.
    # Ajuste se for diferente.
    nome_mun_original = props.get('NM_MUN') 
    
    if nome_mun_original:
        nome_mun_norm = normalize(nome_mun_original)
        
        # Busca no nosso mapa
        regioes = CIDADE_PARA_REGIAO.get(nome_mun_norm)
        
        if regioes:
            # Adiciona as novas propriedades!
            props['MICRO_REGIAO'] = regioes['micro_regiao']
            props['MACRO_REGIAO'] = regioes['macro_regiao']
        else:
            print(f"AVISO: Município não mapeado: {nome_mun_original} ({nome_mun_norm})")
            props['MICRO_REGIAO'] = 'N/A'
            props['MACRO_REGIAO'] = 'N/A'

# Salva o novo arquivo GeoJSON
with open(geojson_modificado, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Arquivo '{geojson_modificado}' criado com sucesso!")