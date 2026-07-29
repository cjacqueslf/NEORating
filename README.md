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

## Gerar pacote portátil Windows

O build requer Python 3.12 e as dependências de desenvolvimento instaladas:

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Os resultados ficam em `dist\NEORating-0.1.0-portable` e
`dist\NEORating-0.1.0-windows-x64.zip`. O executável inclui o runtime Python,
PySide6, Digest2 2.8.1 e os arquivos científicos homologados.
Com o NSIS 3.12 instalado, o mesmo comando também produz
`dist\NEORating-0.1.0-Setup.exe` e `dist\neo-rating-update.json`.
Para verificar silenciosamente o pacote completo:

```powershell
dist\NEORating-0.1.0-portable\NEORating.exe --verify-package
```

Para testar instalação, cálculo e desinstalação em um diretório temporário:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\test_installer.ps1
```

## Aviso científico

O NEO Rating corresponde a `ClassificationResult.noid.NEO`. É uma
pseudo-probabilidade de classificação de órbitas compatíveis com uma tracklet
curta. Não confirma que o objeto seja um NEO e não substitui determinação
orbital ou avaliação profissional.
