# NEO Rating — Requisitos da versão 0.1.0

## 1. Propósito

O NEO Rating é uma aplicação desktop para Windows destinada a calcular
localmente a classificação Digest2 de observações astrométricas no formato
MPC de 80 colunas.

O produto integra o pacote oficial `digest2` publicado pelo Minor Planet
Center. O NEO Rating não implementa, reproduz ou aproxima o algoritmo
científico do Digest2.

## 2. Público e ambiente

- Uso profissional em busca e acompanhamento de objetos próximos da Terra.
- Execução em Windows de 64 bits.
- Cálculo local sem serviço em nuvem, telemetria ou dependência de rede.
- A rede é opcional e usada somente pelo atualizador controlado.
- Interface e mensagens em inglês.

## 3. Definição do resultado principal

O valor denominado **NEO Rating** na interface corresponde exclusivamente a:

`ClassificationResult.noid.NEO`

O valor:

- pertence ao intervalo de 0 a 100;
- é uma pseudo-probabilidade de classificação;
- não confirma que o objeto é um NEO;
- não substitui determinação orbital nem avaliação humana;
- será exibido como inteiro arredondado segundo a apresentação oficial do
  Digest2, mantendo-se o valor integral retornado pela API para diagnóstico.

Além do NEO Rating, a versão 0.1.0 apresentará:

- designação da tracklet;
- número de observações aceitas;
- RMS de ajuste em grande círculo, quando aplicável;
- classe NOID com maior pontuação;
- versão do Digest2 e identificação dos dados científicos;
- avisos ou erros associados à entrada.

## 4. Escopo funcional

### RF-001 — Inserção de observações

O usuário deve poder colar texto contendo observações MPC de 80 colunas em
uma área monoespaçada.

### RF-002 — Preservação da entrada

O aplicativo não deve corrigir, completar, reformatar ou remover silenciosamente
caracteres das linhas fornecidas. Espaços iniciais, intermediários e finais são
significativos.

### RF-003 — Validação estrutural

Antes do cálculo, o aplicativo deve validar no mínimo:

- existência de conteúdo;
- comprimento mínimo necessário;
- tipo de linha reconhecido pelo parser oficial;
- designação;
- data;
- ascensão reta;
- declinação;
- magnitude, quando informada;
- código de observatório;
- mínimo de duas observações válidas por tracklet.

Cada erro bloqueante deve identificar a linha original usando numeração iniciada
em 1. Linhas vazias internas geram aviso não bloqueante. Linhas com comprimento
diferente de 80 e caracteres fora de ASCII são rejeitadas sem correção.

### RF-004 — Múltiplas tracklets

Quando o texto contiver mais de uma designação, o aplicativo deve agrupá-las
segundo as mesmas regras do parser oficial e produzir um resultado independente
para cada tracklet válida.

### RF-005 — Linhas auxiliares

Linhas complementares MPC80 de observadores móveis ou espaciais devem ser
preservadas e entregues ao parser oficial. A versão 0.1.0 não criará nem
modificará essas linhas.

### RF-006 — Cálculo

O cálculo deve utilizar:

- Python 3.12 de 64 bits;
- PySide6 6.11.1;
- pacote oficial `digest2` na versão fixada pelo projeto;
- `repeatable=True`;
- caminhos explícitos para o modelo, configuração e códigos de observatórios;
- pontuação NOID retornada diretamente pela API oficial.

### RF-007 — Execução não bloqueante

O cálculo não deve bloquear a thread da interface. Enquanto houver cálculo em
andamento, a interface deve indicar processamento e impedir disparos duplicados.

### RF-008 — Apresentação do resultado

Para cada tracklet calculada, a interface deve mostrar o NEO Rating em destaque,
sem apresentá-lo como confirmação científica.

### RF-009 — Invalidação

Qualquer alteração na entrada depois de um cálculo deve marcar o resultado
anterior como desatualizado ou removê-lo.

### RF-010 — Ações básicas

O usuário deve poder:

- calcular;
- limpar entrada e resultados;
- copiar um resultado;
- consultar informações de versão.

A consulta de informações deve apresentar a versão da aplicação, versão do
Digest2, modo repetível e hashes do conjunto científico utilizado no último
cálculo bem-sucedido.

### RF-011 — Diagnóstico de dados científicos

A aplicação deve informar claramente quando qualquer arquivo científico estiver
ausente, ilegível, incompatível ou com hash diferente do conjunto homologado.

### RF-012 — Operação offline e atualização controlada

Inicialização e cálculo devem funcionar com acesso à rede indisponível. Quando
houver rede, um worker separado deve verificar automaticamente o canal público
homologado, validar manifesto, tamanho e SHA-256 e preparar a atualização sem
bloquear a interface. Falhas do atualizador não podem impedir cálculos.

## 5. Requisitos não funcionais

### RNF-001 — Fidelidade científica

Nenhuma regra de pontuação, classificação orbital ou geração de órbitas do
Digest2 será reproduzida no código do aplicativo.

### RNF-002 — Reprodutibilidade

A mesma entrada, executada com a mesma versão do pacote e dos dados, deve
produzir resultados idênticos.

### RNF-003 — Rastreabilidade

Cada resultado deve estar associado internamente a:

- versão do NEO Rating;
- versão do `digest2`;
- hash do modelo populacional;
- hash do `MPC.config`;
- hash do arquivo de observatórios;
- modo repetível habilitado.

### RNF-004 — Desempenho

Uma tracklet comum deve iniciar o cálculo sem atraso perceptível de interface.
Não é estabelecido nesta versão um SLA científico de duração, pois o espaço de
soluções depende da tracklet.

### RNF-005 — Segurança

- Não executar conteúdo da área de observações.
- Não enviar observações para serviços externos.
- Não registrar observações completas em logs comuns.
- Não incluir caminhos específicos da máquina em dados portáveis.

### RNF-006 — Usabilidade

- Fluxo principal composto por colar, calcular e visualizar.
- Mensagens em linguagem clara.
- Detalhes técnicos separados da mensagem principal.
- Suporte à escala de exibição do Windows.
- Navegação básica por teclado.

### RNF-007 — Tradução

Todo texto visível deve passar pelo mecanismo traduzível do Qt.

### RNF-008 — Empacotamento

A distribuição final deve funcionar em Windows x64 sem Python previamente
instalado e sem compilador C.

## 6. Fora do escopo da versão 0.1.0

- ADES XML como entrada de usuário;
- importação de arquivos;
- banco de dados ou histórico permanente;
- atualização direta de arquivos científicos sem uma release homologada;
- acesso ao NEOCP;
- submissão de observações ao MPC;
- filtros adicionais `NEOCP_filters`;
- gráficos ou análise das órbitas de tentativa;
- `collect_orbits=True`;
- edição assistida de linhas MPC80;
- determinação orbital;
- suporte oficial a outros sistemas operacionais;
- personalização extensiva de temas;
- processamento automatizado de diretórios.

## 7. Dados científicos homologados inicialmente

O conjunto validado na Fase 1 é:

| Componente | Versão ou SHA-256 |
|---|---|
| Python | 3.12.10 x64 |
| Digest2 | 2.8.1 |
| `digest2.model.csv` | `2b9d9d2a6d8ab16d3a2dbb835b30d3aa172431f27c3cb7c159675d7686668c45` |
| `digest2.model` derivado para Windows x64 | `77a7ce32d15f6e363d5dca03bba87916302c29f76d499ca4e70f655a2356e9f8` |
| `MPC.config` | `5c623453f790db741a924f08a75d451385c15cde4be479660d480cbd2c7d2121` |
| `digest2.obscodes` | `c64569ee2d9d58da6c1ca032f484bdd2188c869be56f0ef077cb624c3dfb9406` |

Mudanças em qualquer item exigem nova homologação científica.

## 8. Critérios globais de aceitação

A versão 0.1.0 estará aceita quando:

1. calcular o exemplo oficial com o conjunto homologado;
2. repetir o mesmo resultado em execuções consecutivas;
3. funcionar com rede bloqueada;
4. rejeitar entradas inválidas com indicação da linha e do problema;
5. processar múltiplas tracklets sem misturar resultados;
6. manter a interface responsiva;
7. apresentar `noid.NEO` como NEO Rating;
8. identificar integralmente o conjunto científico utilizado;
9. executar em uma instalação limpa do Windows sem Python;
10. não conter implementação alternativa do algoritmo Digest2.
