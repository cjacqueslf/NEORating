# NEO Rating

Aplicação desktop Windows para calcular localmente o NEO Rating com o algoritmo
oficial Digest2 do Minor Planet Center.

## Estado atual

As fases 1 a 5 estão concluídas:

- ambiente Python 3.12 e Digest2 oficial validados;
- arquitetura e requisitos documentados;
- integração científica isolada;
- validação MPC de 80 colunas;
- interface PySide6 não bloqueante.

As fases de qualidade abrangente e empacotamento ainda estão pendentes.

## Executar no ambiente de desenvolvimento

No PowerShell, a partir de `D:\NEORating`:

```powershell
.venv\Scripts\python -m neo_rating
```

O cálculo utiliza somente os arquivos homologados em
`resources\scientific`. A verificação de atualizações ocorre em segundo plano e
não é necessária para inicializar ou calcular offline. Downloads aceitos são
validados e preparados em staging; consulte `UPDATE_POLICY.md`.

## Testes

```powershell
.venv\Scripts\python -m pytest
```

## Aviso científico

O NEO Rating corresponde a `ClassificationResult.noid.NEO`. É uma
pseudo-probabilidade de classificação de órbitas compatíveis com uma tracklet
curta. Não confirma que o objeto seja um NEO e não substitui determinação
orbital ou avaliação profissional.
