# Script de Atualização de Versão

Este script verifica automaticamente se há atualizações no repositório Git e atualiza um arquivo de versão com informações do commit.

## Funcionalidades

- ✅ Verifica se há atualizações no repositório Git (comparando com origin)
- ✅ Gera versão no formato: `HYPE-DD.MM-HH.MM-COMMIT` (ex: `HYPE-07.11-00.00-8d56e500`)
- ✅ Atualiza arquivo `version.txt` com a nova versão
- ✅ Faz commit automático com o nome da versão
- ✅ Faz push automático para o repositório remoto

## Como Usar

### Execução Manual

```bash
python version_updater.py
```

### Execução Automatizada

Você pode configurar este script para rodar automaticamente usando:

1. **Cron (Linux/Mac)**: Configure para rodar periodicamente
2. **Task Scheduler (Windows)**: Configure uma tarefa agendada
3. **Git Hooks**: Configure um hook pós-commit ou pós-merge
4. **CI/CD**: Adicione como etapa no seu pipeline

## Formato da Versão

O formato da versão é: `HYPE-DD.MM-HH.MM-COMMIT`

- `HYPE`: Prefixo fixo
- `DD.MM`: Dia e mês do commit
- `HH.MM`: Hora e minuto do commit
- `COMMIT`: Primeiros 8 caracteres do hash do commit

Exemplo: `HYPE-07.11-00.00-8d56e500`

## Configuração

Você pode modificar as seguintes variáveis no script:

- `VERSION_FILE`: Nome do arquivo de versão (padrão: `version.txt`)
- `REPO_PATH`: Caminho do repositório (padrão: `.`)

## Requisitos

- Python 3.6 ou superior
- Git instalado e configurado
- Repositório Git inicializado
- Acesso ao repositório remoto (origin)

## Notas

- O script verifica atualizações comparando o commit local com o remoto
- Se não houver atualizações, o script não faz nada
- O arquivo `version.txt` será criado automaticamente se não existir

