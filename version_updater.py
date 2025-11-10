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

# Configurações
VERSION_FILE = "hype_maps"  # Arquivo onde a versão será salva
REPO_PATH = r"C:\Users\Administrator\Documents\GitHub\Hype-Creative-2025\resources\[maps]"  # Caminho do repositório a ser monitorado
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

def commit_and_push(version_string):
    """Faz commit e push das alterações no repositório atual"""
    # Obtém o diretório atual (onde está o script e o arquivo de versão)
    current_dir = os.getcwd()
    
    # Verifica se há mudanças para commitar
    status_result, _, _ = run_git_command("git status --porcelain", check=False, cwd=current_dir)
    if not status_result or VERSION_FILE not in status_result:
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
    add_result, add_code, _ = run_git_command(f"git add {VERSION_FILE}", check=False, cwd=current_dir)
    if add_result is None or add_code != 0:
        print("Aviso: Problema ao adicionar arquivo ao staging")
    
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
            # Se o hash já é o mesmo, não precisa atualizar
            if current_file_hash == current_repo_hash:
                print(f"Versão já está atualizada. Hash: {current_repo_hash}")
                return True
    
    # Verifica atualizações (para log)
    has_updates, commit_hash = check_git_updates()
    
    # Usa o hash atual do repositório
    commit_hash = current_repo_hash
    
    date_str = get_commit_date()
    version_string = create_version_string(commit_hash, date_str)
    
    print(f"\nNova versão gerada: {version_string}")
    
    # Atualiza o arquivo de versão (só atualiza se for diferente)
    file_changed = update_version_file(version_string)
    
    if not file_changed:
        print("Arquivo não foi alterado (versão já está atualizada).")
        return True
    
    # Faz commit e push apenas se houve mudança
    commit_success = commit_and_push(version_string)
    
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

