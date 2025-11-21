Param(
    [string]$VersionRepoPath = "D:\GitHub\versions",
    [string]$FxManifestPath = "D:\GitHub\HypeMapas2025\[hype-maps]\hype_maps_updater\fxmanifest.lua"
)

$ErrorActionPreference = "Stop"

try {
    $timestamp = Get-Date -Format "vyyyy.MM.dd-HHmmss"
    Write-Host "Nova versão gerada: $timestamp"

    # Atualiza arquivo de versão hype_maps
    $versionFilePath = Join-Path $VersionRepoPath "hype_maps"
    Write-Host "Atualizando arquivo de versão: $versionFilePath"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($versionFilePath, $timestamp, $utf8NoBom)

    # Commit e push no repositório de versões, se for um repo git
    if (Test-Path (Join-Path $VersionRepoPath ".git")) {
        Write-Host "Repositório Git detectado em $VersionRepoPath. Enviando atualização para o GitHub..."
        Push-Location $VersionRepoPath
        try {
            git add "hype_maps"
            git commit -m "Update version to $timestamp"
            git push
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Warning "Diretório $VersionRepoPath não contém um repositório Git (.git não encontrado). Pulando etapa de push."
    }

    # Atualiza fxmanifest.lua
    if (-not [System.IO.File]::Exists($FxManifestPath)) {
        throw "fxmanifest.lua não encontrado em $FxManifestPath"
    }

    Write-Host "Atualizando fxmanifest: $FxManifestPath"
    $content = [System.IO.File]::ReadAllLines($FxManifestPath)

    $updated = $false
    $newContent = foreach ($line in $content) {
        if (-not $updated -and $line -match '^\s*version\s+') {
            $updated = $true
            "version '$timestamp'"
        }
        else {
            $line
        }
    }

    if (-not $updated) {
        Write-Warning "Nenhuma linha 'version' encontrada em fxmanifest.lua. Adicionando no final do arquivo."
        $newContent += "version '$timestamp'"
    }

    # Grava o fxmanifest.lua em UTF-8 sem BOM para evitar erro de caractere oculto no FiveM
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($FxManifestPath, $newContent, $utf8NoBom)

    # Commit e push do fxmanifest.lua na branch 'development', se estiver em um repositório Git
    $fxDir = [System.IO.Path]::GetDirectoryName($FxManifestPath)
    if (-not [System.IO.Directory]::Exists($fxDir)) {
        Write-Warning "Diretório $fxDir não existe. Pulando commit/push do fxmanifest.lua."
    }
    else {
        Push-Location -LiteralPath $fxDir
        try {
            git rev-parse --is-inside-work-tree > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Repositório Git detectado em $fxDir. Enviando fxmanifest.lua para a branch 'development'..."

                $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
                if ($currentBranch -ne "development") {
                    Write-Host "Trocando para a branch 'development'..."
                    git checkout development
                }

                $status = git status --porcelain "fxmanifest.lua"
                if ($status) {
                    git add "fxmanifest.lua"
                    git commit -m "feat(hype_maps_updater): update version"
                    git push origin development
                }
                else {
                    Write-Host "Nenhuma alteração em fxmanifest.lua para commitar."
                }
            }
            else {
                Write-Warning "Diretório $fxDir não está dentro de um repositório Git. Pulando commit/push do fxmanifest.lua."
            }
        }
        finally {
            Pop-Location
        }
    }

    Write-Host "Concluído com sucesso. Versão atual: $timestamp"
}
catch {
    Write-Error "Erro ao atualizar versão: $_"
    exit 1
}
