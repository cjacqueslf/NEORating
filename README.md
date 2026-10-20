# NEO Rating

AplicaÃ§Ã£o desktop Windows para calcular localmente o NEO Rating com o algoritmo
oficial Digest2 do Minor Planet Center.

## Estado atual

As fases 1 a 5 estÃ£o concluÃ­das:

- ambiente Python 3.12 e Digest2 oficial validados;
- arquitetura e requisitos documentados;
- integraÃ§Ã£o cientÃ­fica isolada;
- validaÃ§Ã£o MPC de 80 colunas;
- interface PySide6 nÃ£o bloqueante.

As fases de qualidade abrangente e empacotamento ainda estÃ£o pendentes.

## Instalar no Windows

Baixe `NEORating-0.1.0-Setup.exe` na página de
[releases do GitHub](https://github.com/cjacqueslf/NEORating/releases/latest)
e execute o instalador. Não é necessário instalar Python nem ter privilégios
de administrador. Ao concluir, abra **NEO Rating** pelo atalho na área de
trabalho ou pelo menu Iniciar. Para remover, use Aplicativos instalados do Windows.
O acesso aos downloads depende das permissões do repositório.

## Executar no ambiente de desenvolvimento

No PowerShell, a partir de `D:\NEORating`:

```powershell
.venv\Scripts\python -m neo_rating
```

O cÃ¡lculo utiliza somente os arquivos homologados em
`resources\scientific`. A verificaÃ§Ã£o de atualizaÃ§Ãµes ocorre em segundo plano e
nÃ£o Ã© necessÃ¡ria para inicializar ou calcular offline. Downloads aceitos sÃ£o
validados e preparados em staging; consulte `UPDATE_POLICY.md`.

## Testes

```powershell
.venv\Scripts\python -m pytest
```

## Gerar pacote portÃ¡til Windows

O build requer Python 3.12 e as dependÃªncias de desenvolvimento instaladas:

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Os resultados ficam em `dist\NEORating-0.1.0-portable` e
`dist\NEORating-0.1.0-windows-x64.zip`. O executÃ¡vel inclui o runtime Python,
PySide6, Digest2 2.8.1 e os arquivos cientÃ­ficos homologados.
Com o NSIS 3.12 instalado, o mesmo comando tambÃ©m produz
`dist\NEORating-0.1.0-Setup.exe` e `dist\neo-rating-update.json`.
Para verificar silenciosamente o pacote completo:

```powershell
dist\NEORating-0.1.0-portable\NEORating.exe --verify-package
```

Para testar instalaÃ§Ã£o, cÃ¡lculo e desinstalaÃ§Ã£o em um diretÃ³rio temporÃ¡rio:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\test_installer.ps1
```

## Aviso cientÃ­fico

O NEO Rating corresponde a `ClassificationResult.noid.NEO`. Ã‰ uma
pseudo-probabilidade de classificaÃ§Ã£o de Ã³rbitas compatÃ­veis com uma tracklet
curta. NÃ£o confirma que o objeto seja um NEO e nÃ£o substitui determinaÃ§Ã£o
orbital ou avaliaÃ§Ã£o profissional.
