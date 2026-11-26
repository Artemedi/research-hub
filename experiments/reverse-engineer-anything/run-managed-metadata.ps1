param(
    [Parameter(Mandatory)][string]$Source,
    [string]$Node = 'node'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$expected = '92f332652d352e60b550567adf2399d83d8ebe78'
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
if ((git -C $sourcePath rev-parse HEAD) -ne $expected -or
    (git -C $sourcePath status --porcelain --untracked-files=no)) {
    throw 'Use a clean checkout of the pinned REA source.'
}

$scratch = New-Item -ItemType Directory -Path (
    Join-Path ([IO.Path]::GetTempPath()) ('rea-managed-' + [guid]::NewGuid())
)
$previousSdk = $env:REA_FIXTURE_SDK
$previousTelemetry = $env:DOTNET_CLI_TELEMETRY_OPTOUT
$previousCertificate = $env:DOTNET_GENERATE_ASPNET_CERTIFICATE
try {
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    $env:DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'
    $env:REA_FIXTURE_SDK = dotnet --version
    $framework = 'net' + ($env:REA_FIXTURE_SDK -split '\.')[0] + '.0'
    '<configuration><packageSources><clear /></packageSources></configuration>' |
        Set-Content (Join-Path $scratch.FullName 'NuGet.Config')
    foreach ($variant in 'oracle', 'baseline', 'second-method') {
        $project = New-Item -ItemType Directory -Path (Join-Path $scratch.FullName $variant)
        $assembly = 'ReaSynthetic'
        $outputType = 'Library'
        $file = 'Fixture.cs'
        $constants = ''
        if ($variant -eq 'oracle') {
            $assembly = 'MetadataOracle'
            $outputType = 'Exe'
            $file = 'MetadataOracle.cs'
        }
        if ($variant -eq 'second-method') {
            $constants = 'SECOND_METHOD'
        }
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $project.FullName
        @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>$framework</TargetFramework>
    <AssemblyName>$assembly</AssemblyName>
    <AssemblyVersion>2.3.4.5</AssemblyVersion>
    <DefineConstants>$constants</DefineConstants>
    <OutputType>$outputType</OutputType>
    <DebugType>none</DebugType>
    <Deterministic>true</Deterministic>
    <PathMap>$($project.FullName)=/fixture</PathMap>
  </PropertyGroup>
</Project>
"@ | Set-Content (Join-Path $project.FullName 'Fixture.csproj')
        $output = Join-Path $project.FullName 'out'
        dotnet build $project.FullName --nologo --output $output |
            ForEach-Object { [Console]::Error.WriteLine($_) }
        if ($variant -ne 'oracle') {
            $oracle = Join-Path $scratch.FullName 'oracle/out/MetadataOracle.dll'
            $fixture = Join-Path $output 'ReaSynthetic.dll'
            dotnet $oracle $fixture |
                Set-Content (Join-Path $scratch.FullName "$variant.json") -Encoding utf8NoBOM
        }
    }
    $runner = Join-Path $PSScriptRoot 'managed-metadata.mjs'
    & $Node --disable-warning=ExperimentalWarning --experimental-transform-types --permission `
        "--allow-fs-read=$sourcePath" "--allow-fs-read=$runner" `
        "--allow-fs-read=$($scratch.FullName)" $runner $sourcePath $scratch.FullName
}
finally {
    $env:REA_FIXTURE_SDK = $previousSdk
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = $previousTelemetry
    $env:DOTNET_GENERATE_ASPNET_CERTIFICATE = $previousCertificate
    $scratchPath = $scratch.FullName
    if ((Split-Path -Path $scratchPath -Parent) -eq [IO.Path]::GetTempPath().TrimEnd([IO.Path]::DirectorySeparatorChar) -and
        $scratch.Name -match '^rea-managed-[0-9a-f-]{36}$') {
        Remove-Item -LiteralPath $scratchPath -Recurse
    }
}
