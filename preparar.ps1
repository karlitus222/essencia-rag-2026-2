$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar o Docker Compose.' }
    docker compose exec -T ollama ollama pull qwen3-embedding:0.6b
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao baixar o modelo de embeddings.' }
    docker compose exec -T ollama ollama pull qwen3:1.7b
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao baixar o modelo de texto.' }
    python rag.py indexar
    if ($LASTEXITCODE -ne 0) { throw 'Falha na indexação. Verifique os serviços e tente novamente.' }
    Write-Host 'Base pronta. Execute: python -m streamlit run app.py'
} finally {
    Pop-Location
}
