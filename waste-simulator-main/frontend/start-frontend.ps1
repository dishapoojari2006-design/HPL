# Starts SWMS frontend using the bundled Codex runtime when pnpm is not on PATH.
$pnpm = 'C:\Users\Siri\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd'
if (Test-Path $pnpm) {
    & $pnpm dev
    exit $LASTEXITCODE
}

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm dev
    exit $LASTEXITCODE
}

Write-Error 'pnpm was not found. Install Node.js LTS, then run: corepack enable; corepack prepare pnpm@latest --activate'
exit 1
