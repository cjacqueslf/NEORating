# NEO Rating — Arquitetura da versão 0.1.0

## 1. Diretrizes

A arquitetura será modular e orientada a casos de uso. PySide6 e Digest2 são
detalhes externos: nenhum deles deve determinar as regras centrais de
coordenação da aplicação.

Dependências permitidas:

```text
presentation ─────► application ◄───── infrastructure
                          │
                          ▼
                        domain
```

- `domain` não importa PySide6, Digest2 nem infraestrutura.
- `application` depende de contratos, não de widgets.
- `presentation` traduz ações do usuário em comandos de aplicação.
- `infrastructure` implementa a integração com o pacote oficial.

## 2. Componentes

### 2.1 Presentation

Responsável por:

- janela principal;
- campo de observações;
- ações Calcular, Limpar e Copiar;
- indicador de processamento;
- apresentação dos resultados e erros;
- tradução Qt;
- worker que retira o cálculo da thread gráfica.

Não pode:

- calcular pontuações;
- interpretar classes orbitais;
- acessar diretamente o pacote `digest2`;
- alterar a entrada para fazê-la passar no parser.

### 2.2 Application

Caso de uso principal: `CalculateNeoRating`.

Responsável por:

1. receber o texto original;
2. solicitar análise estrutural da entrada;
3. impedir o cálculo quando houver erros;
4. solicitar classificação das tracklets válidas;
5. montar uma resposta ordenada;
6. anexar a identidade do conjunto científico;
7. traduzir falhas de infraestrutura em categorias da aplicação.

O caso de uso não conhece widgets nem caminhos globais.

### 2.3 Domain

Conceitos previstos:

- linha de observação;
- tracklet identificada;
- problema de entrada;
- resultado de classificação;
- identidade científica.

O domínio não reproduzirá a estrutura orbital interna do Digest2. Valores
retornados pelo pacote são tratados como resultados científicos externos.

### 2.4 Infrastructure

Componentes:

- adaptador do pacote oficial Digest2;
- resolução explícita dos arquivos científicos;
- verificação SHA-256;
- leitura de metadados de versão;
- logging técnico sem astrometria completa.

O adaptador será a única parte da aplicação autorizada a importar `digest2`.

## 3. Fluxo principal

```text
Usuário cola MPC80
        │
        ▼
Presentation captura texto sem alteração
        │
        ▼
CalculateNeoRating
        │
        ├──► valida estrutura e agrupamento
        │        └── erros ──► resposta de validação
        │
        └──► Digest2Classifier
                 │
                 ├── verifica dados homologados
                 ├── parseia com parser oficial
                 ├── classifica com repeatable=True
                 └── converte ClassificationResult
        │
        ▼
Resultados ordenados por primeira aparição
        │
        ▼
Presentation exibe NEO Rating
```

## 4. Estratégia de validação MPC80

A validação terá duas camadas:

1. **Validação de envelope**, pertencente ao aplicativo:
   identifica linhas vazias relevantes, comprimento insuficiente, tipos
   desconhecidos e impossibilidade de formar tracklets.
2. **Parsing oficial**, pertencente ao Digest2:
   é a autoridade final para converter uma linha em observação.

O aplicativo não duplicará toda a gramática MPC80. Quando o parser oficial
rejeitar uma linha, a mensagem indicará que ela não é uma observação MPC80
aceita, preservando o número da linha e um trecho não sensível para diagnóstico.

Linhas com menos de 80 caracteres ou conteúdo além da coluna 80 são rejeitadas
e nunca truncadas. O caso de uso ignora somente espaços ASCII e tabulações
excedentes após a coluna 80, em uma cópia para processamento, com aviso por
linha. As primeiras 80 colunas e a entrada original permanecem intactas;
validação e classificação recebem a mesma cópia normalizada.
Linhas em branco internas são aceitas como aviso não bloqueante. Caracteres
fora de ASCII, campos fixos inválidos, linhas auxiliares órfãs e ordem temporal
regressiva são erros bloqueantes.

O parser público de arquivos do Digest2 é usado para aplicar corretamente linhas
auxiliares `s` e `v`. O adaptador cria para isso um arquivo `.obs` temporário,
sem registrar seu conteúdo, e o remove em bloco `finally` tanto no sucesso como
em falhas. A entrada original em memória nunca é alterada.

## 5. Integração Digest2

Configuração obrigatória:

- `model_path` explícito;
- `config_path` explícito;
- `obscodes_path` explícito;
- `repeatable=True`;
- `no_threshold=False`;
- `collect_orbits=False`.

O adaptador retornará apenas os campos necessários:

- pontuações Raw;
- pontuações NOID;
- RMS;
- RMS Prime;
- designação;
- classe NOID predominante.

O NEO Rating será obtido diretamente de `result.noid.NEO`.

## 6. Concorrência

O caso de uso será executado em worker Qt.

Regras:

- widgets acessados somente pela thread gráfica;
- entrada copiada antes do início do worker;
- um cálculo ativo por janela;
- cancelamento visual não interromperá o núcleo C de forma insegura;
- fechamento da janela aguardará ou descartará com segurança o resultado;
- exceções do worker serão convertidas em resposta, nunca propagadas ao loop Qt.

A Fase 5 adotou `QThreadPool` com `QRunnable`. O worker recebe uma cópia
imutável da solicitação, executa o caso de uso fora da thread gráfica e retorna
uma resposta completa por signal. Teste automatizado compara o identificador da
thread de execução com o da GUI. Widgets são atualizados exclusivamente pelos
slots da janela principal.

Durante o processamento, a entrada fica somente leitura e disparos duplicados
são impedidos. Uma edição posterior ao sucesso invalida imediatamente o
resultado anterior.

## 6.1 Estados da interface

| Estado | Comportamento |
|---|---|
| `EMPTY` | aguarda entrada; cálculo desabilitado |
| `READY` | entrada alterada; resultado anterior removido |
| `PROCESSING` | entrada bloqueada; cálculo executado no worker |
| `SUCCESS` | resultados e ação de cópia disponíveis |
| `ERROR` | problemas traduzidos exibidos por linha |

Mensagens visíveis são criadas com `tr()`. Códigos estáveis permanecem
disponíveis como informação técnica, separados da explicação apresentada ao
usuário.

## 7. Dados científicos

Os três arquivos científicos serão recursos somente leitura da distribuição:

- `digest2.model.csv` ou modelo binário homologado;
- `MPC.config`;
- `digest2.obscodes`.

Na inicialização:

1. resolver caminhos;
2. verificar existência e leitura;
3. calcular hashes;
4. comparar com o manifesto homologado;
5. impedir cálculo em caso de divergência;
6. mostrar diagnóstico sem tentar download.

O binário derivado `digest2.model` não será criado dentro de `site-packages` em
tempo de execução. A Fase 3 confirmou que o Digest2 tenta gerá-lo ao lado do CSV
quando ele está ausente. A distribuição conterá o CSV oficial e o binário
pré-gerado e homologado para Windows x64. Ambos serão verificados por SHA-256.
O adaptador continuará fornecendo o caminho do CSV oficial; a presença do
binário irmão evita escrita em execução e preserva o comportamento de seleção
do próprio Digest2.

Medições exploratórias em sete processos novos apresentaram médias de 484 ms
com o caminho CSV e 537 ms com o caminho binário explícito, incluindo a
inicialização do Python. A diferença não justifica desviar do caminho oficial
CSV. O benefício do binário pré-gerado é impedir escrita em recursos instalados,
não estabelecer uma otimização de desempenho contratual.

## 8. Contratos

### 8.1 Comando de cálculo

`CalculateNeoRatingRequest`

| Campo | Tipo conceitual | Regra |
|---|---|---|
| `source_text` | texto | obrigatório e preservado |
| `correlation_id` | identificador | criado pela apresentação |

### 8.2 Problema de entrada

`InputProblem`

| Campo | Conteúdo |
|---|---|
| `code` | código estável |
| `severity` | erro ou aviso |
| `line_number` | linha 1-based, quando aplicável |
| `message_key` | chave traduzível |
| `details` | dados técnicos sem observação completa |

### 8.3 Resultado por tracklet

`TrackletRating`

| Campo | Conteúdo |
|---|---|
| `designation` | designação preservada/normalizada pelo parser |
| `observation_count` | número de observações principais |
| `neo_rating` | `noid.NEO` integral |
| `raw_neo_score` | `raw.NEO` integral |
| `rms_arcsec` | RMS integral |
| `rms_prime_arcsec` | RMS Prime integral |
| `top_noid_class` | abreviação oficial |
| `noid_scores` | mapa das classes oficiais |
| `raw_scores` | mapa das classes oficiais |

### 8.4 Resposta do caso de uso

`CalculateNeoRatingResponse`

| Campo | Conteúdo |
|---|---|
| `status` | sucesso, validação ou falha |
| `ratings` | resultados ordenados |
| `problems` | erros e avisos |
| `scientific_identity` | versões e hashes |
| `correlation_id` | correlação da solicitação |

## 9. Catálogo inicial de erros

| Código | Condição | Efeito |
|---|---|---|
| `INPUT_EMPTY` | entrada sem conteúdo | impede cálculo |
| `LINE_TOO_SHORT` | menos de 80 caracteres | impede a tracklet |
| `LINE_TOO_LONG` | mais de 80 caracteres | impede a tracklet |
| `LINE_EMPTY` | linha interna vazia | aviso; não impede cálculo |
| `LINE_NON_ASCII` | caractere fora de ASCII | impede a tracklet |
| `LINE_UNSUPPORTED` | tipo MPC80 não aceito | impede a tracklet |
| `LINE_PARSE_FAILED` | parser oficial rejeitou | impede a tracklet |
| `LINE_FIELD_DESIGNATION` | designação ausente | impede a tracklet |
| `LINE_FIELD_DATE` | data inválida | impede a tracklet |
| `LINE_FIELD_RA` | ascensão reta inválida | impede a tracklet |
| `LINE_FIELD_DEC` | declinação inválida | impede a tracklet |
| `LINE_FIELD_MAGNITUDE` | magnitude inválida | impede a tracklet |
| `LINE_FIELD_OBSCODE` | código de observatório ausente | impede a tracklet |
| `ORPHAN_AUXILIARY_LINE` | linha auxiliar sem principal | impede a tracklet |
| `AUXILIARY_PARSE_FAILED` | parser oficial rejeitou linha auxiliar | impede a tracklet |
| `TRACKLET_TOO_SHORT` | menos de duas observações | impede a tracklet |
| `TRACKLET_TIME_ORDER` | ordem temporal inválida | impede a tracklet |
| `SCIENTIFIC_FILE_MISSING` | arquivo obrigatório ausente | impede todos |
| `SCIENTIFIC_FILE_HASH` | hash não homologado | impede todos |
| `DIGEST2_INIT_FAILED` | inicialização do pacote falhou | impede todos |
| `DIGEST2_CLASSIFY_FAILED` | cálculo falhou | falha da tracklet |
| `UNEXPECTED_FAILURE` | falha não classificada | mensagem genérica e log técnico |

Os textos exibidos serão traduzíveis e não serão formados por concatenação.

## 10. Logging e privacidade

Eventos técnicos poderão registrar:

- correlação;
- versão da aplicação;
- versão e hashes científicos;
- número de linhas;
- número de tracklets;
- duração;
- código do erro;
- stack trace em arquivo técnico local quando necessário.

Não serão registrados por padrão:

- texto integral das observações;
- coordenadas;
- magnitudes;
- conteúdo completo da área de entrada.

## 11. Testabilidade

- `application` será testada com um classificador falso.
- O adaptador Digest2 terá testes de integração com dados oficiais.
- A validação terá testes por linha e por tracklet.
- A GUI terá testes focados em estados e sinais, não em ciência.
- Testes offline substituirão qualquer acesso de rede por falha imediata.
- Testes de empacotamento executarão em ambiente sem Python instalado.

## 12. Decisões adiadas

Não são decisões da Fase 2:

- ferramenta final de empacotamento;
- aparência visual definitiva;
- formato de atualização manual dos dados;
- suporte ADES;
- persistência de histórico;
- distribuição pública ou interna.

Esses pontos não alteram o núcleo da versão 0.1.0.

## 13. Atualização automática controlada

O código-fonte permanece em repositório privado. Releases binárias e seus
manifestos são publicadas em `cjacqueslf/NEORating-Releases`, que não contém
código-fonte nem dados do usuário.

O fluxo de atualização depende de `UpdateSource` e `UpdateStager`, implementados
na infraestrutura. A apresentação dispara `CheckAndStageUpdate` em worker
separado após abrir a janela. Indisponibilidade de rede é silenciosamente
degradada e nunca altera o estado do cálculo.

O pacote é aceito somente após correspondência entre tag, manifesto e asset,
limite de tamanho e SHA-256 integral. O staging usa arquivo temporário e
substituição atômica. Instalação e rollback serão executados por helper externo
depois que o layout final do pacote Windows for definido na Fase 7.
