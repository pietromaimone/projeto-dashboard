# ============================================================
# Neighborhood Action Dashboard - Jardim Primavera
# Global Solution 2026.2 - FIAP
#
# Etapa 3: ler as ocorrências do arquivo e mostrar uma tabela
# Como executar (a partir da pasta principal do projeto):
#     python src/sistema.py
# ============================================================

ARQUIVO_DADOS = "data/dados.csv"

# Dicionários que traduzem o código padronizado para o nome bonito
NOMES_CATEGORIA = {
    "iluminacao": "Iluminação",
    "acessibilidade": "Acessibilidade",
    "limpeza": "Limpeza",
    "conservacao": "Conservação",
}

NOMES_STATUS = {
    "aberta": "Aberta",
    "em_analise": "Em análise",
    "concluida": "Concluída",
}


def ler_dados(caminho):
    """Lê o arquivo CSV e devolve uma LISTA de ocorrências.
    Cada ocorrência é um DICIONÁRIO, por exemplo:
    {"id": "004", "categoria": "conservacao", ..., "status": "aberta"}
    """
    ocorrencias = []

    with open(caminho, "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()

    # A primeira linha é o cabeçalho: id;categoria;descricao;...
    cabecalho = linhas[0].strip().split(";")

    # As outras linhas são as ocorrências
    for linha in linhas[1:]:
        linha = linha.strip()
        if linha == "":
            continue  # pula linhas vazias

        valores = linha.split(";")

        # Junta cada nome do cabeçalho com o valor da mesma posição
        ocorrencia = {}
        for i in range(len(cabecalho)):
            ocorrencia[cabecalho[i]] = valores[i]

        ocorrencias.append(ocorrencia)

    return ocorrencias


def mostrar_tabela(ocorrencias):
    """Mostra as ocorrências em formato de tabela."""
    print("CÓDIGO".ljust(8) + "CATEGORIA".ljust(16) + "SETOR".ljust(8) +
          "LOCAL".ljust(36) + "STATUS")
    print("-" * 80)

    for oc in ocorrencias:
        categoria = NOMES_CATEGORIA.get(oc["categoria"], oc["categoria"])
        status = NOMES_STATUS.get(oc["status"], oc["status"])
        print(oc["id"].ljust(8) + categoria.ljust(16) + oc["setor"].ljust(8) +
              oc["local"].ljust(36) + status)

    print("-" * 80)
    print("Total:", len(ocorrencias), "ocorrência(s)")


# ---------------- programa principal ----------------
ocorrencias = ler_dados(ARQUIVO_DADOS)
mostrar_tabela(ocorrencias)
