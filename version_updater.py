#!/usr/bin/env python3
"""
Script de Atualização de Versão
Verifica atualizações no repositório Git e atualiza arquivo de versão
"""

import subprocess
import os
from datetime import datetime
import sys
import time
import re

# Configurações
VERSION_FILE = "hype_maps"  # Arquivo onde a versão será salva
REPO_PATH = r"C:\Users\Administrator\Documents\GitHub\Hype-Creative-2025\resources\[maps]"  # Caminho do repositório a ser monitorado
FXMANIFEST_PATH = r"C:\Users\Administrator\Documents\GitHub\Hype-Studio-2025\resources\[maps]\[hype-maps]\hype_maps_updater\fxmanifest.lua"  # Caminho do fxmanifest.lua
REFERENCE_BRANCH = "development"  # Branch de referência para geração do hash
CHECK_INTERVAL = 10  # Intervalo em segundos entre verificações

def run_git_command(command, check=True, cwd=None):
    """Executa um comando Git e retorna o resultado (stdout, returncode, stderr)"""
    if cwd is None:
        cwd = REPO_PATH
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check,
            cwd=cwd
        )
        return result.stdout.strip(), result.returncode, result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando Git: {e}")
        if e.stderr:
            print(f"Erro detalhado: {e.stderr}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        return None, e.returncode, e.stderr.strip() if e.stderr else ""

def check_git_updates():
    """Verifica se há atualizações no repositório remoto"""
    print(f"Verificando atualizações no repositório (branch: {REFERENCE_BRANCH})...")
    
    # Busca atualizações do remoto
    run_git_command("git fetch origin", check=False)
    
    # Compara branch de referência local com remoto
    local_commit, _, _ = run_git_command(f"git rev-parse {REFERENCE_BRANCH}")
    remote_commit, _, _ = run_git_command(f"git rev-parse origin/{REFERENCE_BRANCH}")
    
    if local_commit and remote_commit:
        if local_commit != remote_commit:
            print(f"Atualizações encontradas!")
            print(f"Local:  {local_commit[:8]}")
            print(f"Remoto: {remote_commit[:8]}")
            return True, remote_commit
        else:
            print("Nenhuma atualização encontrada.")
            return False, None
    else:
        # Se não conseguir comparar, verifica se há commits novos localmente
        # ou se o repositório está inicializado
        if not local_commit:
            print("Erro: Não é um repositório Git válido.")
            return False, None
        
        # Tenta pegar o último commit local
        return True, local_commit

def get_commit_hash():
    """Obtém o hash do último commit da branch de referência"""
    # Tenta pegar da branch remota primeiro, depois local
    commit_hash, _, _ = run_git_command(f"git rev-parse origin/{REFERENCE_BRANCH}")
    if not commit_hash:
        # Se não encontrar no remoto, tenta local
        commit_hash, _, _ = run_git_command(f"git rev-parse {REFERENCE_BRANCH}")
    if commit_hash:
        # Retorna primeiros 7 caracteres em maiúsculas
        return commit_hash[:7].upper()
    return None

def get_commit_date():
    """Obtém a data do último commit da branch de referência"""
    # Tenta pegar da branch remota primeiro, depois local
    date_str, _, _ = run_git_command(f"git log -1 origin/{REFERENCE_BRANCH} --format=%cd --date=format:%d.%m-%H.%M")
    if not date_str:
        # Se não encontrar no remoto, tenta local
        date_str, _, _ = run_git_command(f"git log -1 {REFERENCE_BRANCH} --format=%cd --date=format:%d.%m-%H.%M")
    return date_str if date_str else datetime.now().strftime("%d.%m-%H.%M")

def create_version_string(commit_hash, date_str):
    """Cria a string de versão no formato: HYPE-DD.MM-HH.MM-COMMIT"""
    return f"HYPE-{date_str}-{commit_hash}"

def get_current_version():
    """Lê a versão atual do arquivo"""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        print(f"Erro ao ler arquivo de versão: {e}")
        return None

def update_version_file(version_string):
    """Atualiza o arquivo de versão e retorna True se houve mudança"""
    try:
        # Verifica se a versão já é a mesma
        current_version = get_current_version()
        if current_version == version_string:
            print(f"Versão já está atualizada: {version_string}")
            return False  # Não houve mudança
        
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(version_string)
        print(f"Arquivo {VERSION_FILE} atualizado com: {version_string}")
        return True  # Houve mudança
    except Exception as e:
        print(f"Erro ao atualizar arquivo de versão: {e}")
        return False

def update_fxmanifest(version_string):
    """Atualiza a versão no arquivo fxmanifest.lua e retorna True se houve mudança"""
    try:
        if not os.path.exists(FXMANIFEST_PATH):
            print(f"Aviso: Arquivo fxmanifest.lua não encontrado em {FXMANIFEST_PATH}")
            return False
        
        # Lê o arquivo
        with open(FXMANIFEST_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Procura pela linha com version e atualiza
        updated = False
        old_version = None
        for i, line in enumerate(lines):
            # Procura por padrões como: version 'HYPE-...' ou version "HYPE-..."
            # Padrão para encontrar version 'HYPE-...' ou version "HYPE-..."
            pattern = r"(version\s+['\"])(HYPE-[^'\"]+)(['\"])"
            match = re.search(pattern, line)
            if match:
                old_version = match.group(2)
                # Verifica se a versão já é a mesma
                if old_version == version_string:
                    print(f"Versão no fxmanifest.lua já está atualizada: {version_string}")
                    return False
                quote_char = match.group(1)[-1]  # Pega a aspas usada
                # Substitui apenas a versão, mantendo as aspas
                new_line = re.sub(pattern, f"version {quote_char}{version_string}{quote_char}", line)
                if new_line != line:
                    lines[i] = new_line
                    updated = True
                    print(f"Arquivo fxmanifest.lua atualizado: {old_version} -> {version_string}")
                    break
        
        if updated:
            # Salva o arquivo
            with open(FXMANIFEST_PATH, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        else:
            if old_version is None:
                print(f"Aviso: Não foi possível encontrar a linha 'version' no fxmanifest.lua")
            return False
            
    except Exception as e:
        print(f"Erro ao atualizar fxmanifest.lua: {e}")
        return False

def diagnose_auth_issue(current_dir):
    """Diagnostica problemas de autenticação do Git"""
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO DE AUTENTICAÇÃO")
    print("=" * 50)
    
    # Verifica configuração do remote
    remote_result, _, _ = run_git_command("git remote -v", check=False, cwd=current_dir)
    print(f"\nRemote configurado:")
    print(remote_result if remote_result else "Nenhum remote encontrado")
    
    # Verifica usuário Git configurado
    user_result, _, _ = run_git_command("git config user.name", check=False, cwd=current_dir)
    email_result, _, _ = run_git_command("git config user.email", check=False, cwd=current_dir)
    print(f"\nUsuário Git configurado:")
    print(f"  Nome: {user_result if user_result else 'Não configurado'}")
    print(f"  Email: {email_result if email_result else 'Não configurado'}")
    
    # Verifica se está usando HTTPS ou SSH
    if remote_result and "https://" in remote_result:
        print(f"\n⚠️  Usando HTTPS - Pode precisar de:")
        print("  1. Token de Acesso Pessoal (PAT) do GitHub")
        print("  2. Atualizar credenciais no Gerenciador de Credenciais do Windows")
        print("  3. Ou configurar SSH ao invés de HTTPS")
    elif remote_result and "git@" in remote_result:
        print(f"\n✓ Usando SSH - Verifique se a chave SSH está configurada")
    
    print("\n" + "=" * 50)

def is_main_at_or_ahead_of_development():
    """Verifica se a branch main está na mesma ou acima da branch development"""
    try:
        # Busca atualizações do remoto
        run_git_command("git fetch origin", check=False, cwd=REPO_PATH)
        
        # Obtém os commits das branches main e development
        main_commit, _, _ = run_git_command("git rev-parse origin/main", check=False, cwd=REPO_PATH)
        if not main_commit:
            # Tenta local
            main_commit, _, _ = run_git_command("git rev-parse main", check=False, cwd=REPO_PATH)
        
        dev_commit, _, _ = run_git_command(f"git rev-parse origin/{REFERENCE_BRANCH}", check=False, cwd=REPO_PATH)
        if not dev_commit:
            # Tenta local
            dev_commit, _, _ = run_git_command(f"git rev-parse {REFERENCE_BRANCH}", check=False, cwd=REPO_PATH)
        
        if not main_commit or not dev_commit:
            print("Aviso: Não foi possível obter os commits das branches main e development")
            return False
        
        # Se os commits são iguais, main está na mesma que development
        if main_commit.strip() == dev_commit.strip():
            print("Branch main está na mesma versão que development")
            return True
        
        # Verifica se main está à frente de development
        # Conta quantos commits main tem que development não tem
        ahead_result, ahead_code, _ = run_git_command(
            f"git rev-list --count {dev_commit}..{main_commit}",
            check=False,
            cwd=REPO_PATH
        )
        
        if ahead_code == 0 and ahead_result:
            ahead_count = int(ahead_result.strip()) if ahead_result.strip().isdigit() else 0
            if ahead_count > 0:
                print(f"Branch main está {ahead_count} commit(s) à frente de development")
                return True
            else:
                # Se ahead_count é 0, verifica se development está à frente
                behind_result, behind_code, _ = run_git_command(
                    f"git rev-list --count {main_commit}..{dev_commit}",
                    check=False,
                    cwd=REPO_PATH
                )
                if behind_code == 0 and behind_result:
                    behind_count = int(behind_result.strip()) if behind_result.strip().isdigit() else 0
                    if behind_count > 0:
                        print(f"Branch main está {behind_count} commit(s) atrás de development")
                        return False
                print("Branch main está na mesma versão que development")
                return True
        else:
            # Se não conseguir contar, verifica usando merge-base
            merge_base, _, _ = run_git_command(
                f"git merge-base {main_commit} {dev_commit}",
                check=False,
                cwd=REPO_PATH
            )
            if merge_base:
                merge_base = merge_base.strip()
                # Se o merge-base for igual ao dev_commit, main está à frente
                if merge_base == dev_commit.strip():
                    print("Branch main está à frente de development")
                    return True
                # Se o merge-base for igual ao main_commit, development está à frente
                elif merge_base == main_commit.strip():
                    print("Branch main está atrás de development")
                    return False
                # Se o merge-base for diferente de ambos, as branches divergiram
                # Neste caso, verificamos se main tem o commit de development
                _, is_ancestor_code, _ = run_git_command(
                    f"git merge-base --is-ancestor {dev_commit} {main_commit}",
                    check=False,
                    cwd=REPO_PATH
                )
                if is_ancestor_code == 0:  # Código 0 significa que dev é ancestral de main
                    print("Branch main contém todos os commits de development")
                    return True
            print("Branch main não está na mesma ou acima de development")
            return False
            
    except Exception as e:
        print(f"Erro ao verificar se main está na mesma ou acima de development: {e}")
        return False

def commit_fxmanifest_in_repo(version_string):
    """Faz commit e push do fxmanifest.lua no repositório monitorado na branch main"""
    current_branch = None
    try:
        # Verifica se o fxmanifest.lua está no repositório monitorado
        if not os.path.exists(FXMANIFEST_PATH):
            print("Aviso: fxmanifest.lua não encontrado, pulando commit no repositório monitorado")
            return False
        
        # Obtém o caminho relativo do fxmanifest.lua em relação ao REPO_PATH
        fxmanifest_rel_path = os.path.relpath(FXMANIFEST_PATH, REPO_PATH)
        
        # Verifica se o arquivo está dentro do repositório monitorado
        if fxmanifest_rel_path.startswith('..'):
            print("Aviso: fxmanifest.lua não está dentro do repositório monitorado")
            return False
        
        print(f"\nFazendo commit do fxmanifest.lua no repositório monitorado (branch: main)...")
        
        # Salva a branch atual antes de mudar
        current_branch, _, _ = run_git_command("git branch --show-current", check=False, cwd=REPO_PATH)
        if not current_branch:
            current_branch, _, _ = run_git_command("git rev-parse --abbrev-ref HEAD", check=False, cwd=REPO_PATH)
        
        # Faz checkout para a branch main
        print("Alterando para a branch main...")
        checkout_result, checkout_code, checkout_stderr = run_git_command(
            "git checkout main",
            check=False,
            cwd=REPO_PATH
        )
        
        if checkout_code != 0:
            print(f"Erro ao fazer checkout para branch main: {checkout_stderr}")
            # Tenta criar a branch main se não existir
            print("Tentando criar branch main...")
            checkout_result, checkout_code, checkout_stderr = run_git_command(
                "git checkout -b main",
                check=False,
                cwd=REPO_PATH
            )
            if checkout_code != 0:
                print(f"Erro ao criar branch main: {checkout_stderr}")
                return False
        
        print("Branch main selecionada com sucesso!")
        
        # Verifica se há mudanças no fxmanifest.lua
        status_result, _, _ = run_git_command("git status --porcelain", check=False, cwd=REPO_PATH)
        normalized_status = status_result.replace('\\', '/') if status_result else ""
        normalized_path = fxmanifest_rel_path.replace('\\', '/')
        
        # Verifica se o arquivo foi modificado (pode estar modificado mesmo que a versão seja a mesma)
        has_changes = status_result and normalized_path in normalized_status
        
        if not has_changes:
            # Verifica se o arquivo existe e se precisa ser adicionado ao git
            # Mesmo sem mudanças detectadas, se main está na mesma ou acima, fazemos o commit
            print("Verificando se fxmanifest.lua precisa ser commitado na branch main...")
            # Verifica se o arquivo está sendo rastreado pelo git
            ls_result, _, _ = run_git_command(
                f"git ls-files --error-unmatch \"{fxmanifest_rel_path}\"",
                check=False,
                cwd=REPO_PATH
            )
            if ls_result is None:
                # Arquivo não está sendo rastreado, precisa ser adicionado
                print("fxmanifest.lua não está sendo rastreado, será adicionado ao git")
            else:
                print("Nenhuma mudança detectada no fxmanifest.lua, mas fazendo commit na branch main mesmo assim")
                # Mesmo sem mudanças, vamos garantir que está na branch main
                # Não retorna False, continua para fazer o commit
        
        # Identifica a alteração (versão antiga vs nova)
        old_version = None
        try:
            # Tenta obter a versão antiga do arquivo no HEAD (antes da modificação)
            show_result, _, _ = run_git_command(
                f"git show HEAD:\"{fxmanifest_rel_path}\"",
                check=False,
                cwd=REPO_PATH
            )
            if show_result:
                # Extrai a versão antiga do conteúdo do arquivo no HEAD
                old_match = re.search(r"version\s+['\"](HYPE-[^'\"]+)['\"]", show_result)
                if old_match:
                    old_version = old_match.group(1)
            
            # Se não encontrou no HEAD, tenta no diff
            if not old_version:
                diff_result, _, _ = run_git_command(
                    f"git diff HEAD -- \"{fxmanifest_rel_path}\"",
                    check=False,
                    cwd=REPO_PATH
                )
                if diff_result:
                    # Extrai a versão antiga do diff (linha com -)
                    old_match = re.search(r"-\s*version\s+['\"](HYPE-[^'\"]+)['\"]", diff_result)
                    if old_match:
                        old_version = old_match.group(1)
        except:
            pass
        
        # Adiciona o arquivo (mesmo que não tenha mudanças, adiciona para garantir)
        add_result, add_code, _ = run_git_command(f"git add \"{fxmanifest_rel_path}\"", check=False, cwd=REPO_PATH)
        if add_result is None or add_code != 0:
            print("Aviso: Problema ao adicionar fxmanifest.lua ao staging no repositório monitorado")
            # Volta para a branch original em caso de erro
            if current_branch and current_branch != "main":
                run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
            return False
        
        # Verifica se há algo para commitar após adicionar
        status_after_add, _, _ = run_git_command("git status --porcelain", check=False, cwd=REPO_PATH)
        has_staged_changes = status_after_add and any(
            line.strip().startswith(('M', 'A', 'D')) and normalized_path in line
            for line in status_after_add.split('\n')
        ) if status_after_add else False
        
        # Cria mensagem de commit com comentário sobre a alteração
        if old_version:
            commit_message = f"{old_version} -> {version_string}"
        else:
            commit_message = f"{version_string}"
        
        if has_staged_changes:
            print(f"Alteração identificada: {old_version if old_version else 'Nova versão'} -> {version_string}")
        else:
            print(f"Versão já está correta: {version_string}, mas fazendo commit na branch main mesmo assim")
        
        print(f"Fazendo commit na branch main...")
        
        # Faz o commit na branch main
        commit_result, commit_code, commit_stderr = run_git_command(
            f'git commit -m "{commit_message}"',
            check=False,
            cwd=REPO_PATH
        )
        
        if commit_result is None or commit_code != 0:
            # Se falhou porque não há mudanças, isso é aceitável quando main está na mesma versão
            if "nothing to commit" in (commit_stderr or "").lower() or "no changes" in (commit_stderr or "").lower():
                print("Nenhuma mudança para commitar (arquivo já está atualizado na branch main)")
                # Mesmo sem commit, consideramos sucesso pois o arquivo já está correto
                # Volta para a branch original
                if current_branch and current_branch != "main":
                    run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
                return True  # Retorna True porque não há erro, apenas não há mudanças
            else:
                print("Aviso: Problema ao fazer commit do fxmanifest.lua na branch main")
                if commit_stderr:
                    print(f"Detalhes: {commit_stderr}")
                # Volta para a branch original em caso de erro
                if current_branch and current_branch != "main":
                    run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
                return False
        
        print("Commit do fxmanifest.lua realizado com sucesso na branch main!")
        
        # Faz o push apenas para a branch main
        print("Fazendo push do fxmanifest.lua para origin/main (apenas branch main)...")
        push_result, push_code, push_stderr = run_git_command(
            "git push origin main",
            check=False,
            cwd=REPO_PATH
        )
        
        if push_result is None or push_code != 0:
            print(f"Aviso: Problema ao fazer push do fxmanifest.lua (código: {push_code})")
            if push_stderr:
                print(f"Erro detalhado: {push_stderr}")
            # Volta para a branch original em caso de erro
            if current_branch and current_branch != "main":
                run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
            return False
        
        print("Push do fxmanifest.lua realizado com sucesso na branch main!")
        print("✓ Alteração commitada e enviada apenas para a branch main")
        
        # Volta para a branch original se necessário
        if current_branch and current_branch != "main":
            print(f"Voltando para a branch original: {current_branch}")
            run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
        
        return True
        
    except Exception as e:
        print(f"Erro ao fazer commit do fxmanifest.lua no repositório monitorado: {e}")
        # Tenta voltar para a branch original em caso de erro
        try:
            if current_branch and current_branch != "main":
                run_git_command(f"git checkout {current_branch}", check=False, cwd=REPO_PATH)
        except:
            pass
        return False

def commit_and_push(version_string):
    """Faz commit e push das alterações no repositório atual"""
    # Obtém o diretório atual (onde está o script e o arquivo de versão)
    current_dir = os.getcwd()
    
    # Verifica se há mudanças para commitar
    status_result, _, _ = run_git_command("git status --porcelain", check=False, cwd=current_dir)
    
    # Verifica se há mudanças no arquivo de versão
    has_version_file = status_result and VERSION_FILE in status_result
    
    # Verifica se o fxmanifest.lua está no repositório e foi modificado
    has_fxmanifest = False
    fxmanifest_rel_path = None
    
    if os.path.exists(FXMANIFEST_PATH):
        try:
            # Tenta obter o caminho relativo do fxmanifest.lua em relação ao repositório atual
            fxmanifest_rel_path = os.path.relpath(FXMANIFEST_PATH, current_dir)
            # Verifica se o arquivo está dentro do repositório atual (não contém ..)
            if not fxmanifest_rel_path.startswith('..') and os.path.exists(os.path.join(current_dir, fxmanifest_rel_path)):
                # Verifica se o arquivo aparece no status do git
                if status_result:
                    # Normaliza os separadores de caminho para comparação
                    normalized_status = status_result.replace('\\', '/')
                    normalized_path = fxmanifest_rel_path.replace('\\', '/')
                    # Verifica se o caminho aparece no status (pode ter M, A, etc. no início)
                    has_fxmanifest = any(normalized_path in line for line in normalized_status.split('\n'))
        except ValueError:
            # Se não conseguir fazer relpath, o arquivo não está no mesmo diretório
            pass
    
    if not has_version_file and not has_fxmanifest:
        print("Nenhuma mudança detectada para commitar.")
        return False
    
    print(f"Fazendo commit com mensagem: {version_string}")
    
    # Obtém o nome da branch atual
    branch_result, _, _ = run_git_command("git branch --show-current", check=False, cwd=current_dir)
    if not branch_result:
        # Tenta método alternativo
        branch_result, _, _ = run_git_command("git rev-parse --abbrev-ref HEAD", check=False, cwd=current_dir)
    
    branch_name = branch_result if branch_result else "main"
    print(f"Branch atual: {branch_name}")
    
    # Adiciona o arquivo de versão
    if has_version_file:
        add_result, add_code, _ = run_git_command(f"git add {VERSION_FILE}", check=False, cwd=current_dir)
        if add_result is None or add_code != 0:
            print("Aviso: Problema ao adicionar arquivo ao staging")
    
    # Adiciona o fxmanifest.lua se estiver no repositório
    if has_fxmanifest:
        fxmanifest_rel_path = os.path.relpath(FXMANIFEST_PATH, current_dir)
        add_result, add_code, _ = run_git_command(f"git add \"{fxmanifest_rel_path}\"", check=False, cwd=current_dir)
        if add_result is None or add_code != 0:
            print(f"Aviso: Problema ao adicionar fxmanifest.lua ao staging")
        else:
            print(f"fxmanifest.lua adicionado ao staging")
    
    # Faz o commit
    commit_result, commit_code, commit_stderr = run_git_command(
        f'git commit -m "{version_string}"',
        check=False,
        cwd=current_dir
    )
    
    if commit_result is None or commit_code != 0:
        print("Aviso: Problema ao fazer commit (pode ser que não haja mudanças)")
        if commit_stderr:
            print(f"Detalhes: {commit_stderr}")
        # Verifica se realmente houve erro ou se não havia mudanças
        if commit_code == 0:
            print("Commit realizado com sucesso!")
        else:
            return False
    else:
        print("Commit realizado com sucesso!")
    
    # Faz o push - tenta múltiplas vezes se necessário
    print("Fazendo push para o repositório remoto...")
    push_result, push_code, push_stderr = run_git_command(f"git push origin {branch_name}", check=False, cwd=current_dir)
    
    if push_result is None or push_code != 0:
        print(f"Erro ao fazer push (código: {push_code})")
        if push_stderr:
            print(f"Erro detalhado: {push_stderr}")
        if push_result:
            print(f"Saída: {push_result}")
        print("Tentando push simples...")
        # Tenta push simples
        push_result, push_code, push_stderr = run_git_command("git push", check=False, cwd=current_dir)
        if push_result is None or push_code != 0:
            print(f"Erro: Não foi possível fazer push (código: {push_code})")
            if push_stderr:
                print(f"Erro detalhado: {push_stderr}")
            if push_result:
                print(f"Saída: {push_result}")
            
            # Se for erro 403 (Permission denied), faz diagnóstico
            error_text = (push_stderr or "") + " " + (push_result or "")
            if push_code == 128 and ("403" in error_text or "Permission" in error_text or "denied" in error_text.lower()):
                print("\n⚠️  ERRO 403 - PERMISSÃO NEGADA")
                print("O usuário configurado não tem permissão para fazer push neste repositório.")
                diagnose_auth_issue(current_dir)
                print("\nSOLUÇÕES POSSÍVEIS:")
                print("1. Atualizar credenciais do Git:")
                print("   - Abra: Painel de Controle > Gerenciador de Credenciais")
                print("   - Procure por 'git:https://github.com'")
                print("   - Remova e adicione novamente com credenciais corretas")
                print("\n2. Usar Token de Acesso Pessoal (PAT):")
                print("   - GitHub > Settings > Developer settings > Personal access tokens")
                print("   - Crie um token com permissão 'repo'")
                print("   - Use o token como senha ao fazer push")
                print("\n3. Configurar SSH (recomendado):")
                print("   git remote set-url origin git@github.com:dylakkj/versions.git")
                print("   (Depois configure sua chave SSH no GitHub)")
            else:
                print("\nVerifique:")
                print("  - Conexão com o servidor remoto")
                print("  - Permissões de acesso")
                print("  - Configuração do remote (git remote -v)")
                print("  - Autenticação (credenciais ou SSH)")
            return False
        else:
            print("Push realizado com sucesso!")
            if push_result:
                print(f"Saída: {push_result}")
            return True
    else:
        print("Push realizado com sucesso!")
        if push_result:
            print(f"Saída: {push_result}")
        return True

def run_check():
    """Executa uma verificação de atualização"""
    # Verifica se o repositório Git existe
    git_path = os.path.join(REPO_PATH, ".git")
    if not os.path.exists(git_path):
        print(f"Erro: O diretório {REPO_PATH} não é um repositório Git!")
        return False
    
    # Verifica periodicamente se main está na mesma ou acima de development
    print("Verificando se branch main está na mesma ou acima de development...")
    main_at_or_ahead = is_main_at_or_ahead_of_development()
    if main_at_or_ahead:
        print("✓ Branch main está na mesma ou acima de development")
    else:
        print("⚠ Branch main está atrás de development")
    print("-" * 50)
    
    # Obtém o hash do commit atual do repositório monitorado
    current_repo_hash = get_commit_hash()
    if not current_repo_hash:
        print("Erro: Não foi possível obter o hash do commit")
        return False
    
    # Formata o hash para 7 caracteres em maiúsculas
    current_repo_hash = current_repo_hash[:7].upper()
    
    # Obtém a versão atual do arquivo
    current_file_version = get_current_version()
    
    # Se o arquivo existe, extrai o hash da versão atual
    if current_file_version:
        # Formato: HYPE-DD.MM-HH.MM-HASH
        parts = current_file_version.split('-')
        if len(parts) >= 4:
            current_file_hash = parts[-1].upper()
            # Se o hash já é o mesmo, não precisa atualizar hype_maps
            # MAS ainda verifica fxmanifest.lua independentemente
            if current_file_hash == current_repo_hash:
                print(f"Versão no hype_maps já está atualizada. Hash: {current_repo_hash}")
                print("Continuando para verificar fxmanifest.lua independentemente...")
                # Não retorna True aqui, continua para verificar fxmanifest.lua
    
    # Verifica atualizações (para log)
    has_updates, commit_hash = check_git_updates()
    
    # Usa o hash atual do repositório
    commit_hash = current_repo_hash
    
    date_str = get_commit_date()
    version_string = create_version_string(commit_hash, date_str)
    
    print(f"\nNova versão gerada: {version_string}")
    
    # Inicializa commit_success como False por padrão
    commit_success = False
    
    # PRIMEIRO: Atualiza o arquivo hype_maps com a hash gerada (se necessário)
    print("1. Verificando e atualizando arquivo hype_maps com a hash gerada...")
    file_changed = update_version_file(version_string)
    
    if file_changed:
        print("✓ Arquivo hype_maps atualizado com sucesso!")
        # Faz commit e push do arquivo hype_maps no repositório atual
        print("\n2. Fazendo commit e push do hype_maps...")
        commit_success = commit_and_push(version_string)
        if not commit_success:
            print("Aviso: Problema ao fazer commit do hype_maps, mas continuando...")
    else:
        print("Arquivo hype_maps não foi alterado (versão já está atualizada).")
        print("Continuando para verificar fxmanifest.lua independentemente...")
        # Não houve commit porque não havia mudanças, mas isso é OK
        commit_success = True  # Considera sucesso pois não havia mudanças para commitar
    
    # DEPOIS: Atualiza o fxmanifest.lua na branch main independentemente do hype_maps
    # Isso acontece periodicamente sempre que main estiver na mesma ou acima de development
    if main_at_or_ahead:
        print("\n3. Verificando e atualizando fxmanifest.lua na branch main (independente do hype_maps)...")
        # Atualiza o fxmanifest.lua com a hash e informações da versão (mesma que foi usada no hype_maps)
        fxmanifest_changed = update_fxmanifest(version_string)
        if fxmanifest_changed:
            print("✓ fxmanifest.lua atualizado com sucesso!")
        else:
            # Mesmo que a versão já esteja atualizada, verifica se precisa fazer commit na branch main
            print("Versão no fxmanifest.lua já está correta, mas verificando se precisa commit na branch main...")
            # Força a verificação e commit na branch main mesmo se a versão já estiver correta
            fxmanifest_changed = True  # Marca como alterado para forçar o commit
        
        # Faz commit do fxmanifest.lua na branch main (independente do hype_maps)
        print("\n4. Fazendo commit do fxmanifest.lua na branch main...")
        commit_fxmanifest_in_repo(version_string)
    else:
        print("fxmanifest.lua não será atualizado: branch main está atrás de development")
    
    if commit_success:
        print("\n" + "=" * 50)
        print("Processo concluído com sucesso!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("Processo concluído (sem mudanças para commitar)")
        print("=" * 50)
    
    return True

def main():
    """Função principal com loop periódico"""
    print("=" * 50)
    print("Script de Atualização de Versão")
    print(f"Verificando a cada {CHECK_INTERVAL} segundos")
    print("Pressione Ctrl+C para parar")
    print("=" * 50)
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Iniciando verificação...")
            print("-" * 50)
            
            run_check()
            
            print(f"\nAguardando {CHECK_INTERVAL} segundos até a próxima verificação...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("Script interrompido pelo usuário.")
        print("=" * 50)
        sys.exit(0)

if __name__ == "__main__":
    main()

