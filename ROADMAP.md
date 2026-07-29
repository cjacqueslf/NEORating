# NEO Rating — Roadmap

## Visão geral

O desenvolvimento da versão 0.1.0 está dividido em sete fases com portões de
aceitação. Uma fase só avança quando o resultado anterior é verificável.

## Fase 1 — Prova científica e técnica

**Estado:** concluída em 29/07/2026.

Resultados:

- Python 3.12.10 x64 instalado isoladamente;
- Digest2 2.8.1 instalado por wheel oficial;
- arquivos científicos identificados por SHA-256;
- exemplo oficial MPC80 processado;
- repetibilidade confirmada em cinco execuções;
- cálculo offline confirmado;
- 98 testes centrais oficiais aprovados;
- 69 testes condicionais pulados;
- nenhuma falha nos testes executados.

## Fase 2 — Especificação e arquitetura

**Estado:** concluída em 29/07/2026.

Entregas:

- escopo fechado da versão 0.1.0;
- definição formal do NEO Rating como `noid.NEO`;
- requisitos funcionais e não funcionais;
- limites entre camadas;
- contratos de entrada e saída;
- catálogo inicial de erros;
- critérios globais de aceitação;
- decisões adiadas registradas.

Portão:

- documentação revisada sem implementação científica alternativa;
- todos os arquivos científicos tratados como dependências versionadas;
- funcionamento offline obrigatório desde o desenho.

## Fase 3 — Integração científica isolada

**Estado:** concluída em 29/07/2026.

Objetivos:

- criar a estrutura mínima do projeto;
- implementar contratos de domínio e aplicação;
- implementar o adaptador exclusivo do Digest2;
- localizar e verificar dados científicos;
- receber texto sem depender da GUI;
- retornar resultados estruturados;
- testar exemplo oficial, repetibilidade e ausência de rede;
- decidir o tratamento do modelo binário derivado.

Resultados:

- estrutura modular criada sem PySide6;
- contratos de domínio e aplicação implementados;
- único adaptador autorizado a importar `digest2`;
- dados científicos copiados e verificados por manifesto SHA-256;
- CSV e modelo binário derivado homologados;
- cálculo do exemplo oficial aprovado;
- repetibilidade e ausência de rede cobertas por testes.

Portão:

- cálculo correto sem PySide6;
- testes críticos aprovados;
- nenhuma tentativa de rede.

## Fase 4 — Validação MPC80

**Estado:** concluída em 29/07/2026.

Objetivos:

- validar envelope de linhas;
- preservar espaços;
- associar linhas auxiliares;
- agrupar tracklets;
- manter números originais das linhas;
- emitir erros estáveis e traduzíveis;
- cobrir limites com testes.

Resultados:

- validação exata de 80 colunas e ASCII;
- validação de designação, data, ascensão reta, declinação, magnitude e código
  de observatório;
- confirmação de cada linha principal pelo parser oficial;
- associação e confirmação oficial de linhas auxiliares `s` e `v`;
- detecção de linha auxiliar órfã;
- agrupamento independente por designação;
- detecção de ordem temporal regressiva;
- mínimo de duas observações por tracklet;
- erros com número original da linha;
- linhas vazias tratadas como aviso não bloqueante;
- cálculo impedido quando existe qualquer erro de validação.

Portão:

- nenhuma entrada inválida é ignorada silenciosamente;
- nenhuma observação válida é alterada;
- múltiplas tracklets permanecem isoladas.

## Fase 5 — Interface PySide6

**Estado:** concluída em 29/07/2026.

Objetivos:

- construir janela principal;
- implementar colar, calcular, limpar e copiar;
- exibir NEO Rating e detalhes;
- executar o cálculo fora da thread gráfica;
- implementar estados vazio, pronto, processando, sucesso e erro;
- preparar todos os textos para tradução.

Resultados:

- PySide6 6.11.1 fixado;
- janela principal responsiva e escalável;
- área monoespaçada sem quebra de linhas;
- estados vazio, pronto, processando, sucesso e erro;
- worker `QThreadPool`/`QRunnable`;
- cálculo comprovadamente fora da thread gráfica;
- suporte visual a múltiplas tracklets;
- mensagens humanas com códigos técnicos separados;
- copiar e limpar;
- invalidação do resultado após edição;
- consulta de versões e hashes científicos;
- captura offscreen e cálculo real do exemplo oficial aprovados.

Portão:

- fluxo completo utilizável;
- interface responsiva;
- apresentação não confunde rating com confirmação orbital.

## Fase 6 — Qualidade e validação

**Estado:** em andamento.

Objetivos:

- ampliar testes unitários e de integração;
- testar múltiplas tracklets e linhas auxiliares;
- testar arquivos ausentes ou adulterados;
- testar caminhos com espaços;
- medir desempenho;
- validar ausência de rede;
- revisar logs e privacidade;
- executar análise estática aplicável.
- validar o canal automático de atualização sem depender de rede nos testes;
- rejeitar manifesto, tamanho ou hash incompatível;

Portão:

- suíte crítica aprovada;
- sem falha conhecida que altere pontuação;
- rastreabilidade científica completa.

## Fase 7 — Empacotamento e lançamento

**Estado:** em andamento.

Objetivos:

- escolher ferramenta de empacotamento por prova prática;
- criar distribuição Windows x64;
- incorporar runtime e dados homologados;
- incluir licenças;
- testar em Windows limpo e offline;
- gerar hashes do produto;
- publicar notas e limitações da versão 0.1.0.
- empacotar o helper externo de instalação atômica e rollback;
- publicar manifesto e pacote no canal público de releases;

Resultados parciais:

- PyInstaller 6.21.0 selecionado e fixado;
- configuração `onedir` reproduzível criada para Windows x64;
- runtime, extensão nativa Digest2 e arquivos científicos incorporados;
- hashes científicos preservados no pacote;
- modo interno `--verify-package` criado para validar o cálculo empacotado;
- NSIS 3.12 selecionado para evitar obrigação de licença comercial da
  ferramenta de instalação;
- instalador por usuário com atalhos e desinstalação criado;
- manifesto de atualização com tamanho e SHA-256 gerado automaticamente;
- ciclo de instalação, cálculo e desinstalação validado localmente;

Portão:

- instalação sem Python ou compilador;
- execução totalmente offline;
- resultado igual ao ambiente de desenvolvimento;
- versão 0.1.0 identificável e reproduzível.

## Pós-0.1.0

Somente após avaliação da versão inicial poderão ser considerados:

- ADES XML;
- abertura de arquivos;
- histórico local;
- atualização manual auditada dos dados;
- processamento em lote;
- exportação;
- filtros NEOCP;
- diagnósticos científicos avançados.
