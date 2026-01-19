param(
    [switch]$Publish,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$projectPath = Join-Path $PSScriptRoot "RM01InternetConnector.Win"
$outputDir = Join-Path $PSScriptRoot "dist"

Write-Host "🔨 Building RM-01 Internet Connector Windows Edition..." -ForegroundColor Cyan

if ($Clean) {
    Write-Host "Cleaning previous builds..."
    dotnet clean $projectPath -c Release
    if (Test-Path $outputDir) {
        Remove-Item -Recurse -Force $outputDir
    }
}

# Restore packages
Write-Host "Restoring packages..."
dotnet restore $projectPath

if ($Publish) {
    Write-Host "Publishing release build..."
    
    # Build self-contained executable
    dotnet publish $projectPath `
        -c Release `
        -r win-x64 `
        --self-contained true `
        -p:PublishSingleFile=true `
        -p:IncludeNativeLibrariesForSelfExtract=true `
        -o "$outputDir/RM-01 Internet Connector"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Publish complete!" -ForegroundColor Green
        Write-Host "   Output: $outputDir/RM-01 Internet Connector" -ForegroundColor Yellow
        
        # Create ZIP archive
        $zipPath = Join-Path $outputDir "RM-01.Internet.Connector.Windows.zip"
        if (Test-Path $zipPath) {
            Remove-Item $zipPath
        }
        
        Compress-Archive -Path "$outputDir/RM-01 Internet Connector/*" -DestinationPath $zipPath
        Write-Host "   ZIP: $zipPath" -ForegroundColor Yellow
    }
} else {
    # Regular build
    dotnet build $projectPath -c Release
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Build complete!" -ForegroundColor Green
        Write-Host "   Output: $projectPath/bin/Release/net8.0-windows10.0.19041.0" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Done!" -ForegroundColor Cyan
