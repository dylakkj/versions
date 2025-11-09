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
REPO_PATH = r"D:\GitHub\HypeMapas2025"  # Caminho do repositório a ser monitorado
CHECK_INTERVAL = 10  # Intervalo em segundos entre verificações

def run_git_command(command, check=True, cwd=None):
    """Executa um comando Git e retorna o resultado"""
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
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando Git: {e}")
        if e.stderr:
            print(f"Erro detalhado: {e.stderr}")
        return None

def check_git_updates():
    """Verifica se há atualizações no repositório remoto"""
    print("Verificando atualizações no repositório...")
    
    # Busca atualizações do remoto
    run_git_command("git fetch origin", check=False)
    
    # Compara branch local com remoto
    local_commit = run_git_command("git rev-parse HEAD")
    remote_commit = run_git_command("git rev-parse origin/$(git branch --show-current)")
    
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
    """Obtém o hash do último commit"""
    commit_hash = run_git_command("git rev-parse HEAD")
    if commit_hash:
        # Retorna primeiros 7 caracteres em maiúsculas
        return commit_hash[:7].upper()
    return None

def get_commit_date():
    """Obtém a data do último commit"""
    date_str = run_git_command("git log -1 --format=%cd --date=format:%d.%m-%H.%M")
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

def commit_and_push(version_string):
    """Faz commit e push das alterações no repositório atual"""
    # Obtém o diretório atual (onde está o script e o arquivo de versão)
    current_dir = os.getcwd()
    
    # Verifica se há mudanças para commitar
    status_result = run_git_command("git status --porcelain", check=False, cwd=current_dir)
    if not status_result or VERSION_FILE not in status_result:
        print("Nenhuma mudança detectada para commitar.")
        return False
    
    print(f"Fazendo commit com mensagem: {version_string}")
    
    # Obtém o nome da branch atual
    branch_result = run_git_command("git branch --show-current", check=False, cwd=current_dir)
    if not branch_result:
        # Tenta método alternativo
        branch_result = run_git_command("git rev-parse --abbrev-ref HEAD", check=False, cwd=current_dir)
    
    branch_name = branch_result if branch_result else "main"
    print(f"Branch atual: {branch_name}")
    
    # Adiciona o arquivo de versão
    add_result = run_git_command(f"git add {VERSION_FILE}", check=False, cwd=current_dir)
    if add_result is None:
        print("Aviso: Problema ao adicionar arquivo ao staging")
    
    # Faz o commit
    commit_result = run_git_command(
        f'git commit -m "{version_string}"',
        check=False,
        cwd=current_dir
    )
    
    if commit_result is None:
        print("Aviso: Problema ao fazer commit (pode ser que não haja mudanças)")
        return False
    else:
        print("Commit realizado com sucesso!")
    
    # Faz o push
    print("Fazendo push para o repositório remoto...")
    push_result = run_git_command(f"git push origin {branch_name}", check=False, cwd=current_dir)
    
    if push_result is None:
        print("Aviso: Problema ao fazer push")
        print("Tentando push novamente...")
        # Tenta push simples
        push_result = run_git_command("git push", check=False, cwd=current_dir)
        if push_result is None:
            print("Erro: Não foi possível fazer push. Verifique a conexão e as permissões.")
            return False
        else:
            print("Push realizado com sucesso!")
            return True
    else:
        print("Push realizado com sucesso!")
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

