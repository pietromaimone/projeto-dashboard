"""
Neighborhood Action Dashboard - Painel Comunitário de Ocorrências
Global Solution 2026.2 - FIAP (desafio CitizenTech)

Comunidade simulada: Vila Esperança (bairro fictício), dividida nos
setores Centro, Norte e Sul.

O programa lê as ocorrências de data/dados.csv e o histórico de
data/historico.csv, valida os registros e oferece um menu textual para
listar, buscar, filtrar, cadastrar, atualizar status e ver indicadores.

Como executar:
    python src/sistema.py          -> menu interativo
    python src/sistema.py --demo   -> roteiro automático de demonstração

Usa apenas Python básico (sem bibliotecas externas).
"""

import csv
import os
import sys
from collections import deque

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO E VALORES PADRONIZADOS
# ---------------------------------------------------------------------------

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
ARQ_DADOS = os.path.join(PASTA_BASE, "..", "data", "dados.csv")
ARQ_HISTORICO = os.path.join(PASTA_BASE, "..", "data", "historico.csv")

DIA_ATUAL = 30  # "hoje" na linha do tempo simulada (dia 1 a dia 30)

# Categorias aceitas: código padronizado -> nome para exibição
CATEGORIAS = {
    "iluminacao": "Iluminação",
    "acessibilidade": "Acessibilidade",
    "limpeza": "Limpeza",
    "conservacao": "Conservação",
}

# Situações aceitas: código -> (nome para exibição, significado)
STATUS = {
    "aberta": ("Aberta", "registrada pela comunidade e ainda não examinada"),
    "em_analise": ("Em análise", "alguém já verificou o local e está acompanhando"),
    "concluida": ("Concluída", "o problema foi resolvido e o caso foi encerrado"),
}

SETORES = ["Centro", "Norte", "Sul"]

# Campos de uma ocorrência. Todos são obrigatórios.
CAMPOS_OBRIGATORIOS = ["id", "categoria", "descricao", "setor", "local",
                       "dia_abertura", "status"]

# ---------------------------------------------------------------------------
# ESTRUTURAS DE DADOS DO SISTEMA
# ---------------------------------------------------------------------------

ocorrencias = []        # LISTA: todas as ocorrências válidas, em ordem de cadastro
indice = {}             # DICIONÁRIO (tabela hash): id -> ocorrência
fila_triagem = deque()  # FILA (FIFO): ids "abertas", por ordem de registro
pilha_eventos = []      # PILHA (LIFO): eventos de status; o topo é o mais recente
rejeitados = []         # registros que falharam na validação (com o motivo)
ids_usados = set()      # todos os códigos já vistos (válidos ou rejeitados)


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def normalizar(texto):
    """Deixa o texto em minúsculas e sem acentos, para aceitar entradas como
    'Iluminação', 'iluminacao' ou 'ILUMINAÇÃO' como a mesma coisa."""
    trocas = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
              "í": "i", "ó": "o", "ô": "o", "õ": "o", "ú": "u", "ç": "c"}
    texto = texto.strip().lower()
    resultado = ""
    for letra in texto:
        resultado += trocas.get(letra, letra)
    return resultado


def interpretar_status(texto):
    """Converte o que o usuário digitou para o código padronizado do status.
    Retorna None se não reconhecer."""
    t = normalizar(texto).replace(" ", "_")
    if t in STATUS:
        return t
    elif t == "analise":
        return "em_analise"
    elif t == "concluido" or t == "resolvida":
        # 'resolvida' NÃO é aceito no arquivo (ver validar_registro), mas no
        # menu entendemos a intenção da pessoa.
        return "concluida"
    else:
        return None


def nome_categoria(cod):
    return CATEGORIAS.get(cod, cod)


def nome_status(cod):
    return STATUS[cod][0] if cod in STATUS else cod


def formatar_id(texto):
    """'7' -> '007'. Retorna None se não for número."""
    texto = texto.strip()
    if texto.isdigit() and len(texto) <= 3:
        return texto.zfill(3)
    return None


def linha(caractere="-", tamanho=78):
    print(caractere * tamanho)


def titulo(texto):
    print()
    linha("=")
    print(" " + texto.upper())
    linha("=")


# ---------------------------------------------------------------------------
# VALIDAÇÃO
# ---------------------------------------------------------------------------

def validar_registro(reg):
    """Confere um registro (dicionário) e devolve uma lista de problemas.
    Lista vazia = registro válido."""
    problemas = []

    # 1) Campos obrigatórios: nenhum pode estar ausente ou vazio
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in reg or not reg[campo].strip():
            problemas.append("campo obrigatório '" + campo + "' vazio")

    # 2) Código: 3 dígitos e sem repetição
    cod = reg.get("id", "").strip()
    if cod and (not cod.isdigit() or len(cod) != 3):
        problemas.append("código deve ter 3 dígitos (ex.: 014)")
    elif cod and cod in ids_usados:
        problemas.append("código " + cod + " já existe")

    # 3) Categoria e status só podem ter valores padronizados
    cat = reg.get("categoria", "").strip()
    if cat and cat not in CATEGORIAS:
        problemas.append("categoria desconhecida: '" + cat + "'")

    st = reg.get("status", "").strip()
    if st and st not in STATUS:
        problemas.append("status desconhecido: '" + st + "'")

    setor = reg.get("setor", "").strip()
    if setor and setor not in SETORES:
        problemas.append("setor desconhecido: '" + setor + "'")

    # 4) Dia de abertura: número entre 1 e o dia atual da simulação
    #    Expressão booleana (documentada no README):
    #    dia_valido = texto.isdigit() AND 1 <= dia <= DIA_ATUAL
    dia_txt = reg.get("dia_abertura", "").strip()
    dia_valido = dia_txt.isdigit() and 1 <= int(dia_txt) <= DIA_ATUAL
    if dia_txt and not dia_valido:
        problemas.append("dia de abertura inválido: '" + dia_txt +
                         "' (use um número de 1 a " + str(DIA_ATUAL) + ")")

    return problemas


def pode_mudar_status(atual, novo):
    """Regra de mudança de status. Retorna (True/False, mensagem)."""
    if novo not in STATUS:
        return False, "Status desconhecido. Use: aberta, em análise ou concluída."
    elif novo == atual:
        return False, "A ocorrência já está como '" + nome_status(atual) + "'."
    elif atual == "concluida" and not novo == "concluida":
        # Uma demanda encerrada não volta para trás; o certo é abrir outra.
        return False, ("Ocorrência concluída não pode ser reaberta. "
                       "Cadastre uma nova ocorrência se o problema voltou.")
    elif atual == "em_analise" and novo == "aberta":
        return False, "Uma ocorrência já examinada não volta para 'aberta'."
    else:
        return True, "Mudança permitida."


# ---------------------------------------------------------------------------
# CARGA DOS ARQUIVOS
# ---------------------------------------------------------------------------

def adicionar_ocorrencia(reg):
    """Coloca uma ocorrência já validada em todas as estruturas."""
    oc = {
        "id": reg["id"].strip(),
        "categoria": reg["categoria"].strip(),
        "descricao": reg["descricao"].strip(),
        "setor": reg["setor"].strip(),
        "local": reg["local"].strip(),
        "dia_abertura": int(reg["dia_abertura"]),
        "status": reg["status"].strip(),
        "dia_conclusao": None,
    }
    ocorrencias.append(oc)          # lista
    indice[oc["id"]] = oc           # dicionário
    ids_usados.add(oc["id"])
    if oc["status"] == "aberta":
        fila_triagem.append(oc["id"])  # entra no fim da fila
    return oc


def carregar_dados():
    with open(ARQ_DADOS, encoding="utf-8") as arq:
        leitor = csv.DictReader(arq, delimiter=";")
        for num_linha, reg in enumerate(leitor, start=2):
            problemas = validar_registro(reg)
            if problemas:
                rejeitados.append({"linha": num_linha, "registro": reg,
                                   "problemas": problemas})
                if reg.get("id", "").strip():
                    ids_usados.add(reg["id"].strip())  # código fica reservado
            else:
                adicionar_ocorrencia(reg)

    # A fila deve respeitar a ordem de registro (dia de abertura, depois código)
    ordenados = sorted(fila_triagem,
                       key=lambda i: (indice[i]["dia_abertura"], i))
    fila_triagem.clear()
    fila_triagem.extend(ordenados)


def carregar_historico():
    with open(ARQ_HISTORICO, encoding="utf-8") as arq:
        leitor = csv.DictReader(arq, delimiter=";")
        eventos = sorted(leitor, key=lambda e: int(e["dia"]))
    for ev in eventos:
        if ev["id"] not in indice:
            continue  # evento de ocorrência inexistente/rejeitada é ignorado
        evento = {"id": ev["id"], "dia": int(ev["dia"]),
                  "de": ev["status_anterior"], "para": ev["status_novo"],
                  "obs": ev["observacao"]}
        pilha_eventos.append(evento)  # empilha: o último fica no topo
        if evento["para"] == "concluida":
            indice[ev["id"]]["dia_conclusao"] = evento["dia"]


# ---------------------------------------------------------------------------
# EXIBIÇÃO
# ---------------------------------------------------------------------------

def mostrar_tabela(lista):
    if not lista:
        print("Nenhuma ocorrência para mostrar.")
        return
    print("CÓDIGO".ljust(8) + "CATEGORIA".ljust(16) + "SETOR".ljust(8) +
          "LOCAL".ljust(36) + "STATUS")
    linha()
    for oc in lista:
        print(oc["id"].ljust(8) + nome_categoria(oc["categoria"]).ljust(16) +
              oc["setor"].ljust(8) + oc["local"][:34].ljust(36) +
              nome_status(oc["status"]))
    linha()
    print("Total:", len(lista), "ocorrência(s)")


def mostrar_detalhes(oc):
    print("Código ........:", oc["id"])
    print("Categoria .....:", nome_categoria(oc["categoria"]))
    print("Descrição .....:", oc["descricao"])
    print("Local .........:", oc["local"], "(setor " + oc["setor"] + ")")
    print("Aberta no dia .:", oc["dia_abertura"])
    print("Status ........:", nome_status(oc["status"]), "-",
          STATUS[oc["status"]][1])
    eventos = [e for e in pilha_eventos if e["id"] == oc["id"]]
    if eventos:
        print("Histórico .....:")
        for e in eventos:
            print("   dia", str(e["dia"]).rjust(2), ":", nome_status(e["de"]),
                  "->", nome_status(e["para"]), "|", e["obs"])
    else:
        print("Histórico .....: nenhuma atualização ainda")


# ---------------------------------------------------------------------------
# FUNCIONALIDADES DO MENU
# ---------------------------------------------------------------------------

def listar_todas():
    titulo("Todas as ocorrências")
    mostrar_tabela(ocorrencias)  # percorre a lista


def buscar_por_codigo(texto):
    """Busca direta no dicionário: não precisa percorrer a lista."""
    cod = formatar_id(texto)
    if cod is None:
        print("Código inválido. Digite apenas números, por exemplo 7 ou 007.")
        return None
    if cod in indice:
        return indice[cod]
    elif cod in ids_usados:
        print("O código", cod, "existe no arquivo, mas foi rejeitado na "
              "validação (veja a opção 10).")
    else:
        print("Ocorrência", cod, "não encontrada.")
    return None


def filtrar(categoria=None, status=None):
    """Busca sequencial na lista com condições combinadas.
    Expressão: (categoria vazia OR categoria igual) AND (status vazio OR status igual)
    """
    resultado = []
    for oc in ocorrencias:
        cat_ok = categoria is None or oc["categoria"] == categoria
        st_ok = status is None or oc["status"] == status
        if cat_ok and st_ok:
            resultado.append(oc)
    return resultado


def proximo_id():
    maior = 0
    for cod in ids_usados:
        if cod.isdigit() and int(cod) > maior:
            maior = int(cod)
    return str(maior + 1).zfill(3)


def cadastrar(dados):
    """Recebe um dicionário com os campos, valida e cadastra.
    Retorna a ocorrência criada ou None."""
    problemas = validar_registro(dados)
    if problemas:
        print("Não foi possível cadastrar. Corrija os itens abaixo:")
        for p in problemas:
            print("  -", p)
        return None
    oc = adicionar_ocorrencia(dados)
    print("Ocorrência", oc["id"], "cadastrada com sucesso como '" +
          nome_status(oc["status"]) + "'.")
    if oc["status"] == "aberta":
        print("Ela entrou no fim da fila de triagem (posição",
              str(len(fila_triagem)) + ").")
    return oc


def atualizar_status(cod, novo, dia, obs):
    oc = indice.get(cod)
    if oc is None:
        print("Ocorrência", cod, "não encontrada.")
        return False

    permitido, msg = pode_mudar_status(oc["status"], novo)
    if not permitido:
        print("Atualização recusada:", msg)
        return False

    dia_ok = dia >= oc["dia_abertura"] and dia <= DIA_ATUAL
    if not dia_ok:
        print("Atualização recusada: o dia precisa estar entre",
              oc["dia_abertura"], "(abertura) e", DIA_ATUAL, "(hoje).")
        return False

    anterior = oc["status"]
    oc["status"] = novo
    if novo == "concluida":
        oc["dia_conclusao"] = dia
    # Se saiu de "aberta", não precisa mais esperar na fila de triagem
    if anterior == "aberta" and cod in fila_triagem:
        fila_triagem.remove(cod)

    pilha_eventos.append({"id": cod, "dia": dia, "de": anterior,
                          "para": novo, "obs": obs or "Atualização pelo painel"})
    print("Ocorrência", cod + ":", nome_status(anterior), "->",
          nome_status(novo), "(registrado no histórico, dia " + str(dia) + ")")
    return True


def examinar_proxima():
    """Tira a primeira da fila (a mais antiga) e passa para 'em análise'."""
    if not fila_triagem:
        print("A fila de triagem está vazia. Nenhuma ocorrência aguardando.")
        return
    cod = fila_triagem[0]
    print("Próxima da fila (registrada há mais tempo):")
    mostrar_detalhes(indice[cod])
    atualizar_status(cod, "em_analise", DIA_ATUAL, "Examinada pela fila de triagem")


def mostrar_fila():
    titulo("Fila de triagem (abertas, por ordem de registro)")
    if not fila_triagem:
        print("Fila vazia.")
        return
    for pos, cod in enumerate(fila_triagem, start=1):
        oc = indice[cod]
        print(str(pos).rjust(2) + "º", cod, "| dia", str(oc["dia_abertura"]).rjust(2),
              "|", nome_categoria(oc["categoria"]).ljust(15), "|", oc["local"])


def mostrar_ultimas(qtd=5):
    titulo("Últimas atualizações (topo da pilha primeiro)")
    if not pilha_eventos:
        print("Nenhuma atualização registrada.")
        return
    # Percorre do topo para baixo, sem retirar da pilha
    for i in range(len(pilha_eventos) - 1, max(-1, len(pilha_eventos) - 1 - qtd), -1):
        e = pilha_eventos[i]
        print("dia", str(e["dia"]).rjust(2), "| ocorrência", e["id"], "|",
              nome_status(e["de"]), "->", nome_status(e["para"]), "|", e["obs"])
    print("(", len(pilha_eventos), "eventos no histórico )")


def montar_hierarquia():
    """Árvore simples: bairro -> setor -> categoria -> lista de códigos."""
    arvore = {}
    for oc in ocorrencias:
        if oc["setor"] not in arvore:
            arvore[oc["setor"]] = {}
        if oc["categoria"] not in arvore[oc["setor"]]:
            arvore[oc["setor"]][oc["categoria"]] = []
        arvore[oc["setor"]][oc["categoria"]].append(oc["id"])
    return arvore


def mostrar_hierarquia():
    titulo("Hierarquia: Vila Esperança > setor > categoria > ocorrências")
    arvore = montar_hierarquia()
    print("Vila Esperança")
    for setor in SETORES:
        if setor not in arvore:
            continue
        total = sum(len(v) for v in arvore[setor].values())
        print("  +-- Setor", setor, "(" + str(total) + ")")
        for cat in CATEGORIAS:
            if cat in arvore[setor]:
                ids = arvore[setor][cat]
                print("  |     +--", nome_categoria(cat).ljust(15), ":",
                      ", ".join(ids))


def montar_matriz():
    """Matriz (lista de listas): linhas = categorias, colunas = status."""
    cats = list(CATEGORIAS.keys())
    sts = list(STATUS.keys())
    matriz = [[0] * len(sts) for _ in cats]
    for oc in ocorrencias:
        i = cats.index(oc["categoria"])
        j = sts.index(oc["status"])
        matriz[i][j] += 1
    return cats, sts, matriz


def porcentagem(parte, total):
    if total == 0:
        return 0.0
    return parte / total * 100


def painel_indicadores():
    titulo("Painel de indicadores - Vila Esperança (dia " + str(DIA_ATUAL) + ")")
    total = len(ocorrencias)
    cats, sts, matriz = montar_matriz()

    # Matriz categoria x status, com totais de linha e coluna
    print("1) Quantidade por categoria e por status (matriz)")
    print("   Fórmula da proporção: % = quantidade / total x 100")
    print()
    cab = "CATEGORIA".ljust(16)
    for s in sts:
        cab += nome_status(s).rjust(12)
    cab += "TOTAL".rjust(8) + "%".rjust(8)
    print(cab)
    linha()
    for i, c in enumerate(cats):
        soma_linha = sum(matriz[i])
        txt = nome_categoria(c).ljust(16)
        for j in range(len(sts)):
            txt += str(matriz[i][j]).rjust(12)
        txt += str(soma_linha).rjust(8)
        txt += ("%.1f" % porcentagem(soma_linha, total)).rjust(8)
        print(txt)
    linha()
    txt = "TOTAL".ljust(16)
    totais_status = []
    for j in range(len(sts)):
        soma_col = 0
        for i in range(len(cats)):
            soma_col += matriz[i][j]
        totais_status.append(soma_col)
        txt += str(soma_col).rjust(12)
    txt += str(total).rjust(8) + "100.0".rjust(8)
    print(txt)
    txt = "%".ljust(16)
    for v in totais_status:
        txt += ("%.1f" % porcentagem(v, total)).rjust(12)
    print(txt)

    # Tempo médio até a conclusão
    print()
    print("2) Tempo médio simulado entre abertura e conclusão")
    print("   Fórmula: soma(dia_conclusao - dia_abertura) / nº de concluídas")
    soma, n = 0, 0
    for oc in ocorrencias:
        if oc["status"] == "concluida" and oc["dia_conclusao"] is not None:
            dias = oc["dia_conclusao"] - oc["dia_abertura"]
            print("   ", oc["id"], ": dia", oc["dia_abertura"], "-> dia",
                  oc["dia_conclusao"], "=", dias, "dias")
            soma += dias
            n += 1
    media_conclusao = soma / n if n > 0 else 0
    if n > 0:
        print("   Resultado:", soma, "/", n, "=", "%.1f dias" % media_conclusao)
    else:
        print("   Ainda não há ocorrências concluídas.")

    # Pendências
    print()
    print("3) Pendências (abertas + em análise) e tempo médio de espera")
    print("   Fórmula: soma(dia_atual - dia_abertura) / nº de pendentes")
    pendentes = [oc for oc in ocorrencias if not oc["status"] == "concluida"]
    espera = 0
    mais_antiga = None
    for oc in pendentes:
        espera += DIA_ATUAL - oc["dia_abertura"]
        if mais_antiga is None or oc["dia_abertura"] < mais_antiga["dia_abertura"]:
            mais_antiga = oc
    media_espera = espera / len(pendentes) if pendentes else 0
    print("   Pendentes:", len(pendentes), "de", total,
          "(%.1f%%)" % porcentagem(len(pendentes), total))
    if pendentes:
        print("   Espera média:", espera, "/", len(pendentes), "=",
              "%.1f dias" % media_espera)
        print("   Pendência mais antiga:", mais_antiga["id"], "-",
              mais_antiga["descricao"], "(aberta no dia",
              str(mais_antiga["dia_abertura"]) + ")")

    # Interpretação automática
    print()
    print("4) O que os números sugerem")
    maior_i = 0
    for i in range(len(cats)):
        if sum(matriz[i]) > sum(matriz[maior_i]):
            maior_i = i
    print("   - A categoria mais frequente é", nome_categoria(cats[maior_i]),
          "com", sum(matriz[maior_i]), "registro(s); merece atenção primeiro.")
    pend_por_cat = []
    for i in range(len(cats)):
        pend_por_cat.append(matriz[i][0] + matriz[i][1])
    maior_p = pend_por_cat.index(max(pend_por_cat))
    print("   - Mais pendências em", nome_categoria(cats[maior_p]),
          "(" + str(pend_por_cat[maior_p]) + " sem solução).")
    if porcentagem(len(pendentes), total) > 50:
        print("   - Mais da metade das demandas segue sem solução: o ritmo de",
              "conclusão está abaixo do ritmo de novos registros.")
    else:
        print("   - Menos da metade está pendente: o acompanhamento está em dia.")
    print("   - Lembrete: são dados simulados; servem para treinar a",
          "organização, não para tirar conclusões sobre um bairro real.")
    if rejeitados:
        print("   - Ficaram fora do cálculo", len(rejeitados),
              "registro(s) inválido(s) (opção 10).")


def mostrar_rejeitados():
    titulo("Registros rejeitados na validação")
    if not rejeitados:
        print("Nenhum registro rejeitado.")
        return
    for r in rejeitados:
        reg = r["registro"]
        print("Linha", r["linha"], "do arquivo | código",
              reg.get("id") or "(sem código)", "|", reg.get("descricao", ""))
        for p in r["problemas"]:
            print("   motivo:", p)
    print()
    print("Esses registros não entram na lista nem nos indicadores.")
    print("Para aproveitá-los, cadastre de novo pela opção 4 com os dados corretos.")


def mostrar_ajuda():
    titulo("Ajuda")
    print("Este painel organiza pedidos de melhoria da Vila Esperança.")
    print("Use os números do menu e aperte Enter. Acentos são opcionais.")
    print()
    print("Categorias aceitas:", ", ".join(CATEGORIAS.values()))
    print("Setores aceitos:   ", ", ".join(SETORES))
    print()
    print("Significado de cada status:")
    for cod in STATUS:
        print("  -", STATUS[cod][0].ljust(11), ":", STATUS[cod][1])
    print()
    print("Caminho normal: Aberta -> Em análise -> Concluída.")
    print("Privacidade: não informe nomes, telefones ou endereços de pessoas.")
    print("Use locais genéricos, como 'Praça Central' ou 'Rua das Palmeiras'.")


# ---------------------------------------------------------------------------
# ENTRADAS DO USUÁRIO (MENU)
# ---------------------------------------------------------------------------

def perguntar(texto):
    try:
        return input(texto)
    except EOFError:
        return "0"


def escolher_categoria(permitir_vazio):
    txt = perguntar("Categoria (iluminação, acessibilidade, limpeza, conservação)"
                    + (" [Enter = todas]" if permitir_vazio else "") + ": ")
    if permitir_vazio and not txt.strip():
        return None, True
    cod = normalizar(txt)
    if cod in CATEGORIAS:
        return cod, True
    print("Categoria não reconhecida:", txt)
    return None, False


def menu_buscar():
    oc = buscar_por_codigo(perguntar("Código da ocorrência: "))
    if oc:
        titulo("Ocorrência " + oc["id"])
        mostrar_detalhes(oc)


def menu_filtrar():
    cat, ok = escolher_categoria(permitir_vazio=True)
    if not ok:
        return
    st_txt = perguntar("Status (aberta, em análise, concluída) [Enter = todos]: ")
    st = None
    if st_txt.strip():
        st = interpretar_status(st_txt)
        if st is None:
            print("Status não reconhecido:", st_txt)
            return
    titulo("Resultado do filtro")
    print("Categoria:", nome_categoria(cat) if cat else "todas",
          "| Status:", nome_status(st) if st else "todos")
    mostrar_tabela(filtrar(cat, st))


def menu_cadastrar():
    titulo("Cadastrar nova ocorrência")
    print("Não use dados pessoais. Todos os campos são obrigatórios.")
    sugestao = proximo_id()
    cod_txt = perguntar("Código [Enter = " + sugestao + "]: ")
    cod = sugestao if not cod_txt.strip() else (formatar_id(cod_txt) or cod_txt.strip())
    cat_txt = perguntar("Categoria (iluminação, acessibilidade, limpeza, conservação): ")
    setor_txt = perguntar("Setor (Centro, Norte, Sul): ")
    dados = {
        "id": cod,
        "categoria": normalizar(cat_txt),
        "descricao": perguntar("Descrição breve: "),
        "setor": setor_txt.strip().capitalize(),
        "local": perguntar("Local genérico (ex.: Praça Central): "),
        "dia_abertura": perguntar("Dia de abertura [Enter = " + str(DIA_ATUAL) + "]: ")
                        or str(DIA_ATUAL),
        "status": "aberta",
    }
    cadastrar(dados)


def menu_atualizar():
    oc = buscar_por_codigo(perguntar("Código da ocorrência: "))
    if not oc:
        return
    print("Status atual:", nome_status(oc["status"]))
    novo_txt = perguntar("Novo status (em análise / concluída): ")
    novo = interpretar_status(novo_txt)
    if novo is None:
        print("Status desconhecido:", novo_txt, "- nada foi alterado.")
        return
    dia_txt = perguntar("Dia da atualização [Enter = " + str(DIA_ATUAL) + "]: ")
    if not dia_txt.strip():
        dia = DIA_ATUAL
    elif dia_txt.strip().isdigit():
        dia = int(dia_txt)
    else:
        print("Dia inválido - nada foi alterado.")
        return
    obs = perguntar("Observação (opcional): ")
    atualizar_status(oc["id"], novo, dia, obs.strip())


def menu_fila():
    mostrar_fila()
    if fila_triagem:
        resp = normalizar(perguntar("Examinar a próxima agora? (s/n): "))
        if resp == "s" or resp == "sim":
            examinar_proxima()


def menu():
    opcoes = {
        "1": ("Listar todas as ocorrências", listar_todas),
        "2": ("Buscar por código", menu_buscar),
        "3": ("Filtrar por categoria e/ou status", menu_filtrar),
        "4": ("Cadastrar nova ocorrência", menu_cadastrar),
        "5": ("Atualizar status", menu_atualizar),
        "6": ("Fila de triagem (examinar a próxima)", menu_fila),
        "7": ("Últimas atualizações", mostrar_ultimas),
        "8": ("Ver por setor e categoria", mostrar_hierarquia),
        "9": ("Painel de indicadores", painel_indicadores),
        "10": ("Registros rejeitados", mostrar_rejeitados),
        "11": ("Ajuda e significado dos status", mostrar_ajuda),
    }
    while True:
        titulo("Neighborhood Action Dashboard - Vila Esperança")
        print("Ocorrências válidas:", len(ocorrencias), "| Na fila:",
              len(fila_triagem), "| Dia atual:", DIA_ATUAL)
        linha()
        for chave in opcoes:
            print(chave.rjust(3), "-", opcoes[chave][0])
        print("  0 - Sair")
        escolha = perguntar("Escolha uma opção: ").strip()
        if escolha == "0":
            print("Até logo!")
            break
        elif escolha in opcoes:
            opcoes[escolha][1]()
            perguntar("\nAperte Enter para voltar ao menu...")
        else:
            print("Opção inválida. Digite um número de 0 a 11.")


# ---------------------------------------------------------------------------
# ROTEIRO DE DEMONSTRAÇÃO (o mesmo exemplo do enunciado)
# ---------------------------------------------------------------------------

def demo():
    titulo("Demonstração automática")
    print("Registros carregados:", len(ocorrencias), "válidos,",
          len(rejeitados), "rejeitados")
    resumo = []
    for st in STATUS:
        resumo.append(nome_status(st) + ": " + str(len(filtrar(None, st))))
    print("Situação inicial ->", " | ".join(resumo))
    mostrar_rejeitados()

    titulo("Consulta: ocorrências abertas da categoria Iluminação")
    mostrar_tabela(filtrar("iluminacao", "aberta"))

    titulo("Ação 1a: tentativa de cadastro inválido (sem categoria)")
    cadastrar({"id": "014", "categoria": "", "descricao": "Poste sem luz",
               "setor": "Centro", "local": "Praça Central",
               "dia_abertura": "30", "status": "aberta"})

    titulo("Ação 1b: cadastro válido da ocorrência 014")
    cadastrar({"id": "014", "categoria": "iluminacao",
               "descricao": "Poste apagado ao lado do coreto",
               "setor": "Centro", "local": "Praça Central",
               "dia_abertura": "30", "status": "aberta"})

    titulo("Ação 2: alterar a ocorrência 014 para 'em análise'")
    atualizar_status("014", "em_analise", 30, "Verificado pelo mutirão")
    print()
    print("Tentativa de status desconhecido:")
    atualizar_status("014", "resolvendo", 30, "")
    print("Tentativa de reabrir uma concluída:")
    atualizar_status("001", "aberta", 30, "")

    titulo("Busca por código 014")
    mostrar_detalhes(indice["014"])
    print()
    buscar_por_codigo("099")

    mostrar_fila()
    mostrar_ultimas()
    mostrar_hierarquia()

    print()
    print("Ação 3: indicadores atualizados")
    painel_indicadores()


# ---------------------------------------------------------------------------

def main():
    carregar_dados()
    carregar_historico()
    if "--demo" in sys.argv:
        demo()
    else:
        menu()


if __name__ == "__main__":
    main()
