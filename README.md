# Neighborhood Action Dashboard – Vila Esperança

**Global Solution 2026.2 – FIAP | Desafio CitizenTech**

Painel comunitário, em modo texto, para registrar, organizar e acompanhar pedidos de melhoria em um bairro: iluminação, acessibilidade, limpeza e conservação de espaços coletivos.

---

## 1. Equipe

**Nome da equipe:** _[preencher]_

| Integrante | RM |
|---|---|
| Pietro Maimone | RM _[preencher]_ |

---

## 2. O bairro, o problema e quem se beneficia

**Vila Esperança** é um bairro fictício dividido em três setores: **Centro**, **Norte** e **Sul**. Lá tem praça, parquinho, quadra comunitária, escola municipal e uma passarela sobre o córrego.

**O problema:** os moradores percebem postes apagados, calçadas sem rampa, lixo acumulado e brinquedos quebrados, mas esses relatos ficam espalhados em grupos de mensagem e conversas. Ninguém sabe direito o que já foi visto, o que está parado e qual tipo de problema aparece mais.

**Quem se beneficia:** a associação de moradores, quem organiza mutirões e os próprios moradores, que passam a ver em que pé está cada pedido. O sistema **não** se conecta à prefeitura e **não** promete que os pedidos serão atendidos. Ele só organiza a informação.

---

## 3. Como executar

Precisa apenas de Python 3 (não usa nenhuma biblioteca externa).

```bash
python src/sistema.py          # menu interativo
python src/sistema.py --demo   # roteiro automático com o exemplo do enunciado
```

### Estrutura do repositório

```
├── README.md
├── src/
│   └── sistema.py        # programa principal, comentado
├── data/
│   ├── dados.csv         # 14 ocorrências (12 válidas + 2 com erro de propósito)
│   └── historico.csv     # 10 atualizações de status
└── docs/
    ├── relatorio.pdf     # relatório técnico
    ├── link_video.txt    # link do vídeo no YouTube
    └── uso_ia.md         # como a IA foi usada
```

### Formato dos dados

Os dados ficam em arquivos CSV separados por **ponto e vírgula** (`;`), porque as descrições podem ter vírgulas.

**`data/dados.csv`** – uma ocorrência por linha:

| Campo | Obrigatório | Exemplo | Regra |
|---|---|---|---|
| `id` | sim | `004` | 3 dígitos, sem repetir |
| `categoria` | sim | `iluminacao` | `iluminacao`, `acessibilidade`, `limpeza` ou `conservacao` |
| `descricao` | sim | `Lâmpada do poste piscando` | texto curto, sem dados pessoais |
| `setor` | sim | `Norte` | `Centro`, `Norte` ou `Sul` |
| `local` | sim | `Rua dos Ipês` | local genérico (praça, rua, quadra) |
| `dia_abertura` | sim | `5` | número de 1 a 30 |
| `status` | sim | `aberta` | `aberta`, `em_analise` ou `concluida` |

**`data/historico.csv`** – `id;dia;status_anterior;status_novo;observacao`

O tempo é simulado em **dias de 1 a 30**. O "hoje" da simulação é o **dia 30**.

### Significado de cada status

| Status | Significado |
|---|---|
| **Aberta** | registrada pela comunidade e ainda não examinada |
| **Em análise** | alguém já verificou o local e está acompanhando |
| **Concluída** | o problema foi resolvido e o caso foi encerrado |

Caminho permitido: **Aberta → Em análise → Concluída** (também pode ir direto de Aberta para Concluída). Não dá para voltar.

### Menu

```
  1 - Listar todas as ocorrências
  2 - Buscar por código
  3 - Filtrar por categoria e/ou status
  4 - Cadastrar nova ocorrência
  5 - Atualizar status
  6 - Fila de triagem (examinar a próxima)
  7 - Últimas atualizações
  8 - Ver por setor e categoria
  9 - Painel de indicadores
 10 - Registros rejeitados
 11 - Ajuda e significado dos status
  0 - Sair
```

---

## 4. Estruturas de dados e por que cada uma

| Estrutura | No código | Para que serve | Por que essa e não outra |
|---|---|---|---|
| **Lista** | `ocorrencias` | guarda todas as ocorrências válidas na ordem em que entraram | é o jeito mais simples de percorrer tudo para listar, filtrar e somar indicadores |
| **Dicionário (tabela hash)** | `indice` | acha uma ocorrência pelo código | buscar `indice["007"]` é imediato; numa lista teria que olhar item por item |
| **Fila (FIFO)** | `fila_triagem` (`deque`) | ocorrências **abertas** esperando alguém examinar, da mais antiga para a mais nova | quem pediu primeiro é atendido primeiro – é justo e fácil de explicar para a comunidade |
| **Pilha (LIFO)** | `pilha_eventos` | histórico de mudanças de status | o que interessa ver primeiro é o que aconteceu por último; o topo da pilha é sempre o evento mais recente |
| **Hierarquia (árvore com dicionários aninhados)** | `montar_hierarquia()` | Vila Esperança → setor → categoria → códigos | mostra *onde* os problemas se concentram (ex.: no Sul, quase tudo é iluminação e limpeza) |
| **Matriz (lista de listas)** | `montar_matriz()` | linhas = categorias, colunas = status, cada célula = quantidade | dá para somar uma linha (total da categoria) ou uma coluna (total do status) com laços simples |
| **Conjunto** | `ids_usados` | todos os códigos já vistos, inclusive os rejeitados | evita cadastrar um código repetido |

Exemplo da fila funcionando: a opção 6 mostra a fila e "examina" a primeira (a mais antiga), que passa para **Em análise** e sai da fila. Uma ocorrência nova entra no **fim** da fila.

---

## 5. Regras lógicas

### Validação de um registro (`validar_registro`)

Um registro é recusado se:

1. algum campo obrigatório estiver vazio;
2. o código não tiver 3 dígitos **ou** já existir;
3. a categoria, o status ou o setor não estiverem na lista de valores aceitos;
4. o dia de abertura não for um número de 1 a 30.

Os registros recusados não somem: vão para a lista `rejeitados`, com o motivo, e podem ser vistos na opção 10. Eles ficam fora dos indicadores.

No arquivo de dados há **dois registros com erro de propósito**:

| Linha | Código | Problema | Tratamento |
|---|---|---|---|
| 14 | 013 | categoria vazia | rejeitado: "campo obrigatório 'categoria' vazio" |
| 15 | 015 | status `resolvida` e dia `abc` | rejeitado com os dois motivos |

### Mudança de status (`pode_mudar_status`)

```python
if novo not in STATUS:                         -> recusa: status desconhecido
elif novo == atual:                            -> recusa: já está nesse status
elif atual == "concluida" and not novo == "concluida":
                                               -> recusa: concluída não reabre
elif atual == "em_analise" and novo == "aberta":
                                               -> recusa: não volta para aberta
else:                                          -> permite e grava no histórico
```

Além disso, o dia da atualização precisa estar entre o dia de abertura e o dia 30.

### Expressões booleanas (AND, OR, NOT)

| Onde | Expressão | O que faz |
|---|---|---|
| validação do dia | `dia_txt.isdigit() and 1 <= int(dia_txt) <= DIA_ATUAL` | só aceita número dentro da simulação |
| validação do código | `cod and (not cod.isdigit() or len(cod) != 3)` | acusa código com letra **ou** tamanho errado |
| filtro | `(categoria is None or oc["categoria"] == categoria) and (status is None or oc["status"] == status)` | campo deixado em branco no filtro significa "todos" |
| regra de status | `atual == "concluida" and not novo == "concluida"` | impede reabrir uma concluída |
| pendências | `not oc["status"] == "concluida"` | pendente = tudo que não foi concluído |
| atualização | `dia >= oc["dia_abertura"] and dia <= DIA_ATUAL` | o dia da mudança precisa fazer sentido |

**Expressão documentada em detalhe – o filtro:**

```
mostrar = (C = vazio OU categoria = C) E (S = vazio OU status = S)
```

- Se a pessoa digita só a categoria "iluminação" e deixa o status em branco, a segunda parte é sempre verdadeira, então aparecem todas as de iluminação.
- Se digita "iluminação" e "aberta", as duas partes precisam ser verdadeiras: aparecem só as abertas de iluminação (004 e 012).
- Se deixa os dois em branco, tudo é verdadeiro e aparecem todas.

### Entradas do usuário

- Acentos e maiúsculas são opcionais: `Iluminação`, `iluminacao` e `ILUMINAÇÃO` viram o mesmo código (`normalizar`).
- Para status, também são aceitos `em analise`, `analise` e `concluido`.
- Código pode ser digitado como `7` ou `007`.
- Se a ocorrência não existe, o sistema diz "Ocorrência 099 não encontrada". Se o código existe mas foi rejeitado, ele avisa isso também.

---

## 6. Indicadores

Todos calculados com laços e contas simples, só com as ocorrências válidas.

| Indicador | Fórmula |
|---|---|
| Total por categoria e por status | contagem na matriz categoria × status |
| Proporção | `quantidade / total × 100` |
| Tempo médio até a conclusão | `soma(dia_conclusao − dia_abertura) / nº de concluídas` |
| Pendências | `nº de ocorrências com status diferente de concluída` |
| Espera média das pendentes | `soma(30 − dia_abertura) / nº de pendentes` |

### Resultado com os dados iniciais (12 ocorrências)

| Categoria | Aberta | Em análise | Concluída | Total | % |
|---|---|---|---|---|---|
| Iluminação | 2 | 1 | 1 | 4 | 33,3 |
| Acessibilidade | 1 | 1 | 1 | 3 | 25,0 |
| Limpeza | 1 | 1 | 1 | 3 | 25,0 |
| Conservação | 1 | 1 | 0 | 2 | 16,7 |
| **Total** | **5** | **4** | **3** | **12** | 100 |
| **%** | 41,7 | 33,3 | 25,0 | | |

- **Tempo médio até concluir:** 001 (7 dias) + 003 (10) + 007 (10) = 27 / 3 = **9,0 dias**
- **Pendências:** 9 de 12 (**75%**), esperando em média 170 / 9 = **18,9 dias**
- **Pendência mais antiga:** 002 – calçada sem rampa, aberta no dia 3

### Interpretação

- **Iluminação** é o problema mais comum (1 em cada 3 pedidos) e é também a categoria com mais pendências. Faz sentido priorizar uma ronda noturna para mapear os pontos escuros.
- **Três em cada quatro pedidos** ainda estão sem solução, e eles esperam em média o dobro do tempo que os concluídos levaram. Os pedidos estão chegando mais rápido do que estão sendo resolvidos.
- A pendência mais antiga é de **acessibilidade** (calçada sem rampa). Esse tipo de problema afeta mais quem já tem dificuldade de circular, então merece atenção mesmo não sendo a categoria mais frequente.
- **Cuidado:** são 12 registros inventados. Os números servem para mostrar como o painel funciona, não para dizer algo sobre um bairro de verdade.

---

## 7. Exemplo de uso

Saída real de `python src/sistema.py --demo` (trechos):

**Registros com erro detectados na carga**
```
Linha 14 do arquivo | código 013 | Mato alto no canteiro
   motivo: campo obrigatório 'categoria' vazio
Linha 15 do arquivo | código 015 | Lixeira pública quebrada
   motivo: status desconhecido: 'resolvida'
   motivo: dia de abertura inválido: 'abc' (use um número de 1 a 30)
```

**Consulta: abertas de iluminação**
```
CÓDIGO  CATEGORIA       SETOR   LOCAL                               STATUS
------------------------------------------------------------------------------
004     Iluminação      Norte   Rua dos Ipês                        Aberta
012     Iluminação      Sul     Quadra Comunitária                  Aberta
------------------------------------------------------------------------------
Total: 2 ocorrência(s)
```

**Cadastro (primeiro inválido, depois válido)**
```
Não foi possível cadastrar. Corrija os itens abaixo:
  - campo obrigatório 'categoria' vazio

Ocorrência 014 cadastrada com sucesso como 'Aberta'.
Ela entrou no fim da fila de triagem (posição 6).
```

**Alteração de status**
```
Ocorrência 014: Aberta -> Em análise (registrado no histórico, dia 30)

Tentativa de status desconhecido:
Atualização recusada: Status desconhecido. Use: aberta, em análise ou concluída.
Tentativa de reabrir uma concluída:
Atualização recusada: Ocorrência concluída não pode ser reaberta. Cadastre uma nova ocorrência se o problema voltou.
```

**Últimas atualizações (pilha)**
```
dia 30 | ocorrência 014 | Aberta -> Em análise | Verificado pelo mutirão
dia 20 | ocorrência 010 | Aberta -> Em análise | Volume de entulho estimado
dia 19 | ocorrência 007 | Em análise -> Concluída | Piso tátil recolocado
```

**Hierarquia**
```
Vila Esperança
  +-- Setor Centro (5)
  |     +-- Iluminação      : 001, 014
  |     +-- Acessibilidade  : 002, 007
  |     +-- Conservação     : 005
  +-- Setor Norte (4)
  ...
```

**Indicadores atualizados depois do cadastro da 014**
```
CATEGORIA             Aberta  Em análise   Concluída   TOTAL       %
------------------------------------------------------------------------------
Iluminação                 2           2           1       5    38.5
Acessibilidade             1           1           1       3    23.1
Limpeza                    1           1           1       3    23.1
Conservação                1           1           0       2    15.4
------------------------------------------------------------------------------
TOTAL                      5           5           3      13   100.0
```

---

## 8. Acessibilidade, inclusão e privacidade

- **Linguagem simples** em todas as mensagens, e o significado de cada status sempre disponível (opção 11).
- **Acentos e maiúsculas opcionais** na digitação, para não travar quem digita rápido ou usa teclado sem acento.
- **Mensagens de erro dizem o que corrigir**, e não só "erro".
- **Nada depende de cor**: tudo é texto, funciona com leitor de tela e em qualquer terminal.
- **Menu numerado e curto**, sempre com o caminho de volta.
- **Privacidade:** nenhum campo pede nome, telefone ou endereço de pessoa. O local é genérico (praça, rua, quadra). O próprio sistema lembra disso na ajuda e no cadastro. Todos os dados são inventados.
- **Inclusão:** os dados incluem problemas que afetam mais quem tem mobilidade reduzida (rampa, piso tátil, faixa de pedestre perto da escola), e a interpretação dos indicadores chama atenção para eles.

---

## 9. Vídeo

Link: _[colar aqui o link do YouTube (Não Listado)]_

---

## 10. Conclusões, limitações e aprendizados

**Conclusões.** Com estruturas simples dá para transformar relatos soltos em informação útil: a lista guarda tudo, o dicionário acha rápido, a fila organiza a ordem de atendimento, a pilha mostra o que mudou por último e a matriz resume tudo numa tabela.

**Limitações.**
- Os dados são inventados e poucos (12 registros), então os indicadores não representam um bairro real.
- As alterações feitas no menu ficam só na memória; ao fechar o programa, os arquivos voltam ao estado original.
- O tempo é simulado em dias (1 a 30), sem datas reais.
- Não há login: qualquer pessoa com acesso ao terminal pode alterar status.
- Não há ligação com prefeitura ou outro órgão; o sistema só organiza a informação.

**Aprendizados.** Escolher a estrutura certa simplifica o código: buscar por código no dicionário é uma linha, enquanto na lista seria um laço. Também ficou claro que validar os dados logo na entrada evita indicadores errados lá na frente, e que escrever as regras de status antes de programar evitou situações estranhas, como reabrir algo já concluído.
