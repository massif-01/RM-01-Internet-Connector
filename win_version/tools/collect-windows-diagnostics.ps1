param(
    [string]$Label = "manual",
    [int]$Minutes = 60,
    [switch]$Interactive
)

$ErrorActionPreference = "Continue"

function New-DiagnosticsDirectory {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $desktop = [Environment]::GetFolderPath("Desktop")
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        $desktop = $PWD.Path
    }

    $safeLabel = $Label -replace '[^A-Za-z0-9_.-]', '_'
    $path = Join-Path $desktop "RM01-Diagnostics-$safeLabel-$timestamp"
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    return $path
}

function Write-Section {
    param(
        [string]$Name,
        [scriptblock]$Script
    )

    $path = Join-Path $script:OutputDir $Name
    try {
        & $Script 2>&1 | Out-String -Width 240 | Set-Content -Encoding UTF8 -Path $path
    } catch {
        "FAILED: $($_.Exception.ToString())" | Set-Content -Encoding UTF8 -Path $path
    }
}

function Export-EventLog {
    param(
        [string]$Name,
        [string]$LogName,
        [string[]]$ProviderPattern = @()
    )

    Write-Section $Name {
        $start = (Get-Date).AddMinutes(-1 * $Minutes)
        $events = Get-WinEvent -FilterHashtable @{ LogName = $LogName; StartTime = $start } -ErrorAction Stop
        if ($ProviderPattern.Count -gt 0) {
            $events = $events | Where-Object {
                $provider = $_.ProviderName
                foreach ($pattern in $ProviderPattern) {
                    if ($provider -match $pattern) { return $true }
                }
                return $false
            }
        }

        $events |
            Sort-Object TimeCreated |
            Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
            Format-List
    }
}

function Collect-Snapshot {
    param([string]$Prefix)

    Write-Section "$Prefix-00-summary.txt" {
        "Label: $Label"
        "Phase: $Prefix"
        "Time: $(Get-Date -Format o)"
        "Computer: $env:COMPUTERNAME"
        "User: $env:USERNAME"
        "PowerShell: $($PSVersionTable.PSVersion)"
        ""
        "Admin token:"
        whoami /groups
    }

    Write-Section "$Prefix-01-app-log.txt" {
        $logPath = Join-Path $env:LOCALAPPDATA "RM01InternetConnector\app.log"
        "App log path: $logPath"
        if (Test-Path $logPath) {
            Get-Content -Path $logPath -Tail 500
        } else {
            "App log not found."
        }
    }

    Write-Section "$Prefix-02-ipconfig.txt" {
        ipconfig /all
    }

    Write-Section "$Prefix-03-netsh-ip-config.txt" {
        netsh interface ip show config
    }

    Write-Section "$Prefix-04-adapters.txt" {
        "Get-NetAdapter:"
        Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue |
            Sort-Object Name |
            Format-List Name, InterfaceAlias, InterfaceDescription, Status, MacAddress, ifIndex, LinkSpeed, DriverInformation

        ""
        "Network PnP devices:"
        Get-PnpDevice -Class Net -ErrorAction SilentlyContinue |
            Sort-Object FriendlyName |
            Format-Table -AutoSize Status, Class, FriendlyName, InstanceId
    }

    Write-Section "$Prefix-05-ip-interface-route.txt" {
        "IPv4 addresses:"
        Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Sort-Object InterfaceAlias, IPAddress |
            Format-Table -AutoSize InterfaceAlias, InterfaceIndex, IPAddress, PrefixLength, PrefixOrigin, AddressState, SkipAsSource

        ""
        "IPv4 interfaces:"
        Get-NetIPInterface -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Sort-Object InterfaceAlias |
            Format-Table -AutoSize InterfaceAlias, ifIndex, ConnectionState, Dhcp, Forwarding, InterfaceMetric, NlMtu

        ""
        "IPv4 routes:"
        Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Sort-Object DestinationPrefix, RouteMetric, InterfaceMetric |
            Format-Table -AutoSize DestinationPrefix, NextHop, InterfaceAlias, RouteMetric, InterfaceMetric, PolicyStore

        ""
        "Connection profiles:"
        Get-NetConnectionProfile -ErrorAction SilentlyContinue |
            Format-List Name, InterfaceAlias, NetworkCategory, IPv4Connectivity, IPv6Connectivity
    }

    Write-Section "$Prefix-06-nat.txt" {
        "Get-NetNat:"
        Get-NetNat -ErrorAction SilentlyContinue | Format-List *

        ""
        "Get-NetNatStaticMapping:"
        Get-NetNatStaticMapping -ErrorAction SilentlyContinue | Format-List *

        ""
        "Get-NetNatSession sample:"
        Get-NetNatSession -ErrorAction SilentlyContinue |
            Where-Object { $_.InternalSourceAddress -like "10.10.99.*" -or $_.InternalDestinationAddress -like "10.10.99.*" } |
            Select-Object -First 200 |
            Format-Table -AutoSize
    }

    Write-Section "$Prefix-07-connectivity.txt" {
        "Route print:"
        route print -4

        ""
        "ARP:"
        arp -a

        ""
        "Test-NetConnection 10.10.99.98:22:"
        Test-NetConnection 10.10.99.98 -Port 22 -InformationLevel Detailed

        ""
        "Test-NetConnection 10.10.99.100:"
        Test-NetConnection 10.10.99.100 -InformationLevel Detailed
    }
}

$script:OutputDir = New-DiagnosticsDirectory

Collect-Snapshot "before"

if ($Interactive) {
    Write-Host ""
    Write-Host "Diagnostics snapshot saved to: $script:OutputDir" -ForegroundColor Cyan
    Write-Host "Now reproduce the RM-01 Connect failure, then return here and press Enter." -ForegroundColor Yellow
    Read-Host "Press Enter after the failure"
    Collect-Snapshot "after"
}

Export-EventLog "events-system-network.txt" "System" @("TCPIP", "Tcpip", "Dhcp", "NDIS", "Net", "WinNat", "WLAN")
Export-EventLog "events-network-profile.txt" "Microsoft-Windows-NetworkProfile/Operational"
Export-EventLog "events-dhcp-admin.txt" "Microsoft-Windows-Dhcp-Client/Admin"
Export-EventLog "events-dhcp-operational.txt" "Microsoft-Windows-Dhcp-Client/Operational"
Export-EventLog "events-winnat.txt" "Microsoft-Windows-WinNat/Operational"

$zipPath = "$script:OutputDir.zip"
try {
    Compress-Archive -Path (Join-Path $script:OutputDir "*") -DestinationPath $zipPath -Force
    Write-Host "Diagnostics collected: $zipPath" -ForegroundColor Green
} catch {
    Write-Host "Diagnostics collected: $script:OutputDir" -ForegroundColor Green
    Write-Host "ZIP failed: $($_.Exception.Message)" -ForegroundColor Yellow
}
