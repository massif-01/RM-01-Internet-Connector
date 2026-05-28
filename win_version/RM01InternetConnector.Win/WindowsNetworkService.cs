using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace RM01InternetConnector.Win;

public interface IWindowsNetworkService
{
    Task<NetworkInterfaceInfo?> DetectAdapterAsync();
    Task<bool> IsSharingEnabledAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken);
    Task EnableSharingAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken);
    Task DisableSharingAsync(NetworkInterfaceInfo? nic, CancellationToken cancellationToken);
}

public sealed class WindowsNetworkService : IWindowsNetworkService
{
    private readonly ProcessRunner _processRunner = new();
    private readonly AdapterDetector _detector;
    private readonly NetworkConfigurator _configurator;
    private readonly WindowsNatManager _nat;
    private string? _lastUpstreamInterfaceName;
    private bool _lastConnectionChangedAddress;

    public WindowsNetworkService()
    {
        _detector = new AdapterDetector(_processRunner);
        _configurator = new NetworkConfigurator(_processRunner);
        _nat = new WindowsNatManager(_processRunner);
    }

    public Task<NetworkInterfaceInfo?> DetectAdapterAsync()
    {
        return _detector.FindFirstAsync(CancellationToken.None);
    }

    public Task<bool> IsSharingEnabledAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken)
    {
        return _nat.IsSharingEnabledAsync(nic.Name, cancellationToken);
    }

    public async Task EnableSharingAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        AppDiagnostics.Log($"Enable sharing requested for RM-01 adapter '{nic.Name}'");

        var upstream = await _detector.FindBestUpstreamAsync(nic.Name, cancellationToken);
        if (upstream == null)
        {
            AppDiagnostics.Log("Enable sharing failed: no upstream adapter found");
            throw new InvalidOperationException("未找到可用的上游网络（如 Wi-Fi/以太网）。");
        }
        AppDiagnostics.Log($"Selected upstream adapter: name={upstream.Name}, description={upstream.Description}, mac={upstream.Mac}");

        var staticConfigured = false;
        try
        {
            AppDiagnostics.Log("Checking Windows NAT provider before mutating network state");
            await _nat.AssertAvailableAsync(cancellationToken);

            AppDiagnostics.Log("Cleaning existing Windows NAT/legacy ICS state before connect");
            await _nat.DisableSharingAsync(nic.Name, upstream.Name, cancellationToken);

            if (await _configurator.HasTargetAddressAsync(nic.Name, cancellationToken))
            {
                AppDiagnostics.Log("RM-01 adapter already has 10.10.99.100/24; leaving address configuration untouched");
            }
            else
            {
                AppDiagnostics.Log("Configuring RM-01 adapter static IPv4");
                staticConfigured = true;
                await _configurator.SetStaticAsync(nic.Name, cancellationToken);
            }

            AppDiagnostics.Log("Enabling Windows NAT");
            await _nat.EnableSharingAsync(upstream.Name, nic.Name, cancellationToken);
            _lastUpstreamInterfaceName = upstream.Name;
            _lastConnectionChangedAddress = staticConfigured;
            AppDiagnostics.Log("Windows NAT enabled successfully");
        }
        catch (Exception ex) when (staticConfigured)
        {
            AppDiagnostics.LogException("Enable sharing failed after static IPv4 was configured; starting rollback", ex);
            try
            {
                await _nat.DisableSharingAsync(nic.Name, upstream.Name, CancellationToken.None);
                await _configurator.SetDhcpAsync(nic.Name, CancellationToken.None);
                AppDiagnostics.Log("Rollback completed");
            }
            catch (Exception rollbackEx)
            {
                AppDiagnostics.LogException("Rollback failed", rollbackEx);
                throw new InvalidOperationException(
                    $"{ex.Message} 另外，恢复 DHCP/NAT 清理失败：{rollbackEx.Message}",
                    ex);
            }

            throw;
        }
    }

    public async Task DisableSharingAsync(NetworkInterfaceInfo? nic, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (nic == null)
        {
            return;
        }

        Exception? failure = null;

        try
        {
            AppDiagnostics.Log($"Disabling Windows NAT for RM-01 adapter '{nic.Name}'");
            await _nat.DisableSharingAsync(nic.Name, _lastUpstreamInterfaceName, cancellationToken);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            AppDiagnostics.LogException("Disabling Windows NAT failed", ex);
            failure = ex;
        }

        try
        {
            if (_lastConnectionChangedAddress)
            {
                AppDiagnostics.Log($"Restoring DHCP on RM-01 adapter '{nic.Name}'");
                await _configurator.SetDhcpAsync(nic.Name, cancellationToken);
            }
            else
            {
                AppDiagnostics.Log($"Leaving RM-01 adapter address untouched on disconnect: '{nic.Name}'");
            }
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            AppDiagnostics.LogException("Restoring DHCP failed", ex);
            failure = failure == null
                ? ex
                : new InvalidOperationException($"{failure.Message} 另外，恢复 DHCP 失败：{ex.Message}", failure);
        }

        if (failure != null)
        {
            throw failure;
        }

        _lastUpstreamInterfaceName = null;
        _lastConnectionChangedAddress = false;
    }
}

internal sealed class AdapterDetector
{
    private readonly ProcessRunner _processRunner;

    public AdapterDetector(ProcessRunner processRunner)
    {
        _processRunner = processRunner;
    }

    public async Task<NetworkInterfaceInfo?> FindFirstAsync(CancellationToken token)
    {
        var output = await _processRunner.RunPowerShellAsync(
            """
            $adapter = $null
            if (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue) {
                $adapter = Get-NetAdapter -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.InterfaceDescription -match '(?i)ax88179' -or
                        $_.Name -match '(?i)ax88179'
                    } |
                    Sort-Object @{ Expression = { if ($_.Status -eq 'Up') { 0 } else { 1 } } }, Name |
                    Select-Object -First 1
            }

            if ($null -ne $adapter) {
                [pscustomobject]@{
                    Name = $adapter.Name
                    Description = $adapter.InterfaceDescription
                    MacAddress = $adapter.MacAddress
                } | ConvertTo-Json -Compress
                return
            }

            $cimAdapter = Get-CimInstance Win32_NetworkAdapter -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.NetConnectionID -and (
                        $_.Name -match '(?i)ax88179' -or
                        $_.Description -match '(?i)ax88179' -or
                        $_.PNPDeviceID -match '(?i)ax88179'
                    )
                } |
                Sort-Object NetConnectionID |
                Select-Object -First 1

            if ($null -ne $cimAdapter) {
                [pscustomobject]@{
                    Name = $cimAdapter.NetConnectionID
                    Description = $cimAdapter.Description
                    MacAddress = $cimAdapter.MACAddress
                } | ConvertTo-Json -Compress
            }
            """,
            TimeSpan.FromSeconds(15),
            token);

        return NetworkInterfaceFromJson(output, "AX88179A USB Ethernet Adapter");
    }

    public async Task<NetworkInterfaceInfo?> FindBestUpstreamAsync(string excludeName, CancellationToken token)
    {
        var output = await _processRunner.RunPowerShellAsync(
            $$"""
            $exclude = {{PowerShellText.Quote(excludeName)}}

            function Test-UsableAdapter($adapter) {
                if ($null -eq $adapter) { return $false }
                if ($adapter.Name -ieq $exclude) { return $false }
                if ($adapter.Status -ne 'Up') { return $false }

                $text = (($adapter.Name, $adapter.InterfaceDescription) -join ' ')
                if ($text -match '(?i)vpn|virtual|tap|tun|vmware|virtualbox|loopback|hyper-v') {
                    return $false
                }

                $ipv4 = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                    Where-Object { $_.IPAddress -notlike '169.254.*' } |
                    Select-Object -First 1
                return $null -ne $ipv4
            }

            $candidate = $null
            if ((Get-Command Get-NetRoute -ErrorAction SilentlyContinue) -and
                (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {
                $routes = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
                    Where-Object { $_.NextHop -and $_.NextHop -ne '0.0.0.0' } |
                    Sort-Object RouteMetric, InterfaceMetric

                foreach ($route in $routes) {
                    $adapter = Get-NetAdapter -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue
                    if (Test-UsableAdapter $adapter) {
                        $candidate = $adapter
                        break
                    }
                }
            }

            if ($null -eq $candidate -and (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {
                foreach ($adapter in (Get-NetAdapter -ErrorAction SilentlyContinue |
                    Sort-Object @{
                        Expression = {
                            if ($_.InterfaceDescription -match '(?i)wi-?fi|wireless|802\.11') { 0 }
                            elseif ($_.InterfaceDescription -match '(?i)ethernet|gigabit') { 1 }
                            else { 2 }
                        }
                    }, Name)) {
                    if (Test-UsableAdapter $adapter) {
                        $candidate = $adapter
                        break
                    }
                }
            }

            if ($null -ne $candidate) {
                [pscustomobject]@{
                    Name = $candidate.Name
                    Description = $candidate.InterfaceDescription
                    MacAddress = $candidate.MacAddress
                } | ConvertTo-Json -Compress
            }
            """,
            TimeSpan.FromSeconds(15),
            token);

        return NetworkInterfaceFromJson(output, "Upstream Network");
    }

    private static NetworkInterfaceInfo? NetworkInterfaceFromJson(string output, string fallbackDescription)
    {
        var root = JsonHelpers.ParseRoot(output);
        if (root == null)
        {
            return null;
        }

        var name = JsonHelpers.GetString(root.Value, "Name");
        if (string.IsNullOrWhiteSpace(name))
        {
            return null;
        }

        var description = JsonHelpers.GetString(root.Value, "Description");
        var mac = JsonHelpers.GetString(root.Value, "MacAddress");
        return new NetworkInterfaceInfo(
            name,
            string.IsNullOrWhiteSpace(description) ? fallbackDescription : description,
            name,
            NormalizeMac(mac) ?? "N/A");
    }

    private static string? NormalizeMac(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        var compact = value.Replace("-", string.Empty).Replace(":", string.Empty);
        if (compact.Length != 12)
        {
            return null;
        }

        var parts = new List<string>();
        for (var i = 0; i < compact.Length; i += 2)
        {
            parts.Add(compact.Substring(i, 2).ToUpperInvariant());
        }

        return string.Join(":", parts);
    }
}

internal sealed class NetworkConfigurator
{
    private const string StaticIp = "10.10.99.100";
    private const string Mask = "255.255.255.0";
    private const string Dns = "8.8.8.8";

    private readonly ProcessRunner _processRunner;

    public NetworkConfigurator(ProcessRunner processRunner)
    {
        _processRunner = processRunner;
    }

    public async Task<bool> HasTargetAddressAsync(string interfaceName, CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        var output = await _processRunner.RunPowerShellAsync(
            $$"""
            $name = {{PowerShellText.Quote(interfaceName)}}
            $ip = Get-NetIPAddress -InterfaceAlias $name -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                Where-Object { $_.IPAddress -eq {{PowerShellText.Quote(StaticIp)}} -and [int]$_.PrefixLength -eq 24 } |
                Select-Object -First 1

            [pscustomobject]@{
                HasTargetAddress = ($null -ne $ip)
            } | ConvertTo-Json -Compress
            """,
            TimeSpan.FromSeconds(10),
            token);

        var root = JsonHelpers.ParseRoot(output);
        return root != null && JsonHelpers.GetBool(root.Value, "HasTargetAddress");
    }

    public async Task SetStaticAsync(string interfaceName, CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        AppDiagnostics.Log($"netsh set static IPv4: interface='{interfaceName}', ip={StaticIp}, mask={Mask}, gateway=none");
        await _processRunner.RunAsync(
            "netsh",
            new[]
            {
                "interface", "ip", "set", "address",
                $"name={interfaceName}", "source=static",
                $"addr={StaticIp}", $"mask={Mask}", "gateway=none"
            },
            TimeSpan.FromSeconds(30),
            token);
        AppDiagnostics.Log($"netsh set static DNS: interface='{interfaceName}', dns={Dns}");
        await _processRunner.RunAsync(
            "netsh",
            new[]
            {
                "interface", "ip", "set", "dns",
                $"name={interfaceName}", "source=static", $"addr={Dns}"
            },
            TimeSpan.FromSeconds(30),
            token);
    }

    public async Task SetDhcpAsync(string interfaceName, CancellationToken token)
    {
        token.ThrowIfCancellationRequested();

        AppDiagnostics.Log($"netsh restore DHCP IPv4: interface='{interfaceName}'");
        await _processRunner.RunAsync(
            "netsh",
            new[] { "interface", "ip", "set", "address", $"name={interfaceName}", "source=dhcp" },
            TimeSpan.FromSeconds(30),
            token);
        AppDiagnostics.Log($"netsh restore DHCP DNS: interface='{interfaceName}'");
        await _processRunner.RunAsync(
            "netsh",
            new[] { "interface", "ip", "set", "dns", $"name={interfaceName}", "source=dhcp" },
            TimeSpan.FromSeconds(30),
            token);

        AppDiagnostics.Log("Flushing DNS cache");
        await _processRunner.RunAsync("ipconfig", new[] { "/flushdns" }, TimeSpan.FromSeconds(15), token);

        try
        {
            AppDiagnostics.Log($"ipconfig release/renew: interface='{interfaceName}'");
            await _processRunner.RunAsync("ipconfig", new[] { "/release", interfaceName }, TimeSpan.FromSeconds(20), token);
            await Task.Delay(500, token);
            await _processRunner.RunAsync("ipconfig", new[] { "/renew", interfaceName }, TimeSpan.FromSeconds(20), token);
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("ipconfig release/renew failed after DHCP restore; continuing", ex);
        }
    }
}

internal sealed class WindowsNatManager
{
    private const string NatName = "RM01InternetConnector";
    private const string PrivatePrefix = "10.10.99.0/24";
    private const string StaticIp = "10.10.99.100";

    private readonly ProcessRunner _processRunner;

    public WindowsNatManager(ProcessRunner processRunner)
    {
        _processRunner = processRunner;
    }

    public Task AssertAvailableAsync(CancellationToken token)
    {
        return _processRunner.RunPowerShellAsync(
            NatCommonScript + """
            Assert-NatCommands
            Assert-NatProvider
            "OK"
            """,
            TimeSpan.FromSeconds(10),
            token);
    }

    public async Task EnableSharingAsync(string publicInterfaceName, string privateInterfaceName, CancellationToken token)
    {
        AppDiagnostics.Log($"PowerShell enable Windows NAT: public='{publicInterfaceName}', private='{privateInterfaceName}', prefix={PrivatePrefix}, nat={NatName}");
        await _processRunner.RunPowerShellAsync(
            NatCommonScript + $$"""
            $publicName = {{PowerShellText.Quote(publicInterfaceName)}}
            $privateName = {{PowerShellText.Quote(privateInterfaceName)}}
            $natName = {{PowerShellText.Quote(NatName)}}
            $prefix = {{PowerShellText.Quote(PrivatePrefix)}}

            Assert-NatCommands
            Assert-NatProvider

            $publicAdapter = Get-NetAdapter -Name $publicName -ErrorAction SilentlyContinue
            $privateAdapter = Get-NetAdapter -Name $privateName -ErrorAction SilentlyContinue
            if ($null -eq $publicAdapter) { throw "Upstream interface not found: $publicName" }
            if ($null -eq $privateAdapter) { throw "RM-01 interface not found: $privateName" }

            Get-NetNat -Name $natName -ErrorAction SilentlyContinue | Remove-NetNat -Confirm:$false
            Get-NetNat -ErrorAction SilentlyContinue |
                Where-Object { $_.InternalIPInterfaceAddressPrefix -eq $prefix -and $_.Name -ne $natName } |
                Remove-NetNat -Confirm:$false

            Set-NetIPInterface -InterfaceAlias $privateName -AddressFamily IPv4 -Forwarding Enabled
            Set-NetIPInterface -InterfaceAlias $publicName -AddressFamily IPv4 -Forwarding Enabled
            New-NetNat -Name $natName -InternalIPInterfaceAddressPrefix $prefix | Out-Null

            "OK"
            """,
            TimeSpan.FromSeconds(30),
            token);
    }

    public async Task DisableSharingAsync(string privateInterfaceName, string? publicInterfaceName, CancellationToken token)
    {
        AppDiagnostics.Log($"PowerShell disable Windows NAT/legacy ICS: private='{privateInterfaceName}', public='{publicInterfaceName ?? string.Empty}', prefix={PrivatePrefix}, nat={NatName}");
        await _processRunner.RunPowerShellAsync(
            NatCommonScript + LegacyIcsCommonScript + $$"""
            $privateName = {{PowerShellText.Quote(privateInterfaceName)}}
            $publicName = {{PowerShellText.Quote(publicInterfaceName ?? string.Empty)}}
            $natName = {{PowerShellText.Quote(NatName)}}
            $prefix = {{PowerShellText.Quote(PrivatePrefix)}}

            if (Get-Command Get-NetNat -ErrorAction SilentlyContinue) {
                Get-NetNat -Name $natName -ErrorAction SilentlyContinue | Remove-NetNat -Confirm:$false
                Get-NetNat -ErrorAction SilentlyContinue |
                    Where-Object { $_.InternalIPInterfaceAddressPrefix -eq $prefix -and $_.Name -ne $natName } |
                    Remove-NetNat -Confirm:$false
            }

            if ((Get-Command Set-NetIPInterface -ErrorAction SilentlyContinue) -and
                (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {
                foreach ($name in @($privateName, $publicName)) {
                    if ([string]::IsNullOrWhiteSpace($name)) { continue }
                    $adapter = Get-NetAdapter -Name $name -ErrorAction SilentlyContinue
                    if ($null -ne $adapter) {
                        Set-NetIPInterface -InterfaceAlias $name -AddressFamily IPv4 -Forwarding Disabled -ErrorAction SilentlyContinue
                    }
                }
            }

            Disable-LegacyIcsSharing $privateName $publicName

            "OK"
            """,
            TimeSpan.FromSeconds(30),
            token);
    }

    public async Task<bool> IsSharingEnabledAsync(string privateInterfaceName, CancellationToken token)
    {
        var output = await _processRunner.RunPowerShellAsync(
            NatCommonScript + $$"""
            $privateName = {{PowerShellText.Quote(privateInterfaceName)}}
            $natName = {{PowerShellText.Quote(NatName)}}
            $staticIp = {{PowerShellText.Quote(StaticIp)}}

            if (-not (Get-Command Get-NetNat -ErrorAction SilentlyContinue) -or
                -not (Get-Command Get-NetIPAddress -ErrorAction SilentlyContinue)) {
                [pscustomobject]@{ SharingEnabled = $false } | ConvertTo-Json -Compress
                return
            }

            $nat = Get-NetNat -Name $natName -ErrorAction SilentlyContinue
            $ip = Get-NetIPAddress -InterfaceAlias $privateName -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                Where-Object { $_.IPAddress -eq $staticIp } |
                Select-Object -First 1
            $forwarding = $null
            if (Get-Command Get-NetIPInterface -ErrorAction SilentlyContinue) {
                $forwarding = Get-NetIPInterface -InterfaceAlias $privateName -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                    Select-Object -First 1
            }

            $forwardingEnabled = ($null -ne $forwarding -and [string]$forwarding.Forwarding -eq 'Enabled')

            [pscustomobject]@{
                SharingEnabled = ($null -ne $nat -and $null -ne $ip -and $forwardingEnabled)
            } | ConvertTo-Json -Compress
            """,
            TimeSpan.FromSeconds(15),
            token);

        var root = JsonHelpers.ParseRoot(output);
        return root != null && JsonHelpers.GetBool(root.Value, "SharingEnabled");
    }

    private const string NatCommonScript =
        """
        function Assert-NatCommands {
            foreach ($command in @('Get-NetNat', 'New-NetNat', 'Remove-NetNat', 'Set-NetIPInterface', 'Get-NetAdapter')) {
                if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
                    throw "Windows NAT command is not available: $command"
                }
            }
        }

        function Assert-NatProvider {
            try {
                Get-CimClass -Namespace root/StandardCimv2 -ClassName MSFT_NetNat -ErrorAction Stop | Out-Null
            } catch {
                throw "Windows NAT provider is not available: MSFT_NetNat cannot be loaded. $($_.Exception.Message)"
            }
        }
        """;

    private const string LegacyIcsCommonScript =
        """
        function Get-ConnectionByName($manager, [string]$name) {
            foreach ($conn in @($manager.EnumEveryConnection)) {
                $props = $manager.NetConnectionProps($conn)
                if ($props.Name -ieq $name) {
                    return $conn
                }
            }
            return $null
        }

        function Get-SharingConfig($manager, $connection) {
            try {
                return $manager.INetSharingConfigurationForINetConnection($connection)
            } catch {
                return $manager.NetSharingConfigurationForINetConnection($connection)
            }
        }

        function Disable-LegacyIcsSharing([string]$privateName, [string]$publicName) {
            try {
                $manager = New-Object -ComObject HNetCfg.HNetShare
            } catch {
                return
            }
            if (-not $manager.SharingInstalled) {
                return
            }

            $disabledPrivate = $false
            $privateConn = Get-ConnectionByName $manager $privateName
            if ($null -ne $privateConn) {
                $privateCfg = Get-SharingConfig $manager $privateConn
                if ($privateCfg.SharingEnabled) {
                    $privateCfg.DisableSharing()
                    $disabledPrivate = $true
                }
            }

            if (-not [string]::IsNullOrWhiteSpace($publicName)) {
                $publicConn = Get-ConnectionByName $manager $publicName
                if ($null -ne $publicConn) {
                    $publicCfg = Get-SharingConfig $manager $publicConn
                    if ($publicCfg.SharingEnabled) {
                        $publicCfg.DisableSharing()
                    }
                }
            } elseif ($disabledPrivate) {
                foreach ($conn in @($manager.EnumEveryConnection)) {
                    $cfg = Get-SharingConfig $manager $conn
                    if ($cfg.SharingEnabled -and ([int]$cfg.SharingConnectionType -eq 0)) {
                        $cfg.DisableSharing()
                    }
                }
            }
        }
        """;
}

internal sealed class ProcessRunner
{
    public Task<string> RunPowerShellAsync(string script, TimeSpan timeout, CancellationToken token)
    {
        var wrapped = string.Join(
            " ",
            "$ErrorActionPreference = 'Stop';",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;",
            script);

        return RunAsync(
            "powershell.exe",
            new[] { "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", wrapped },
            timeout,
            token);
    }

    public async Task<string> RunAsync(string fileName, IReadOnlyList<string> arguments, TimeSpan timeout, CancellationToken token)
    {
        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(token);
        timeoutCts.CancelAfter(timeout);
        var command = FormatCommand(fileName, arguments);
        var started = Stopwatch.StartNew();
        AppDiagnostics.Log($"Running command: {command}");

        var psi = new ProcessStartInfo
        {
            FileName = fileName,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        foreach (var argument in arguments)
        {
            psi.ArgumentList.Add(argument);
        }

        using var process = new Process { StartInfo = psi };
        process.Start();

        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();

        try
        {
            await process.WaitForExitAsync(timeoutCts.Token);
        }
        catch (OperationCanceledException) when (!token.IsCancellationRequested)
        {
            KillProcess(process);
            AppDiagnostics.Log($"Command timed out after {timeout.TotalSeconds:N0}s: {command}");
            throw new TimeoutException($"{fileName} timed out after {timeout.TotalSeconds:N0}s.");
        }
        catch (OperationCanceledException)
        {
            KillProcess(process);
            AppDiagnostics.Log($"Command cancelled: {command}");
            throw;
        }

        var stdout = await stdoutTask;
        var stderr = await stderrTask;
        started.Stop();
        AppDiagnostics.Log(
            $"Command exited {process.ExitCode} after {started.ElapsedMilliseconds}ms: {command}\n" +
            $"stdout: {TruncateForLog(stdout)}\n" +
            $"stderr: {TruncateForLog(stderr)}");
        if (process.ExitCode != 0)
        {
            var message = string.IsNullOrWhiteSpace(stderr) ? stdout : stderr;
            throw new InvalidOperationException($"{fileName} failed: {NormalizeError(message)}");
        }

        return stdout.Trim();
    }

    private static string FormatCommand(string fileName, IReadOnlyList<string> arguments)
    {
        var builder = new StringBuilder(fileName);
        foreach (var argument in arguments)
        {
            builder.Append(' ');
            builder.Append(argument.Contains(' ') ? $"\"{argument}\"" : argument);
        }

        return builder.ToString();
    }

    private static string TruncateForLog(string value)
    {
        var text = string.IsNullOrWhiteSpace(value) ? "<empty>" : value.Trim();
        const int maxLength = 4000;
        return text.Length <= maxLength ? text : text[..maxLength] + "...<truncated>";
    }

    private static void KillProcess(Process process)
    {
        try
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }
        }
        catch
        {
            // Process may have exited between timeout and kill.
        }
    }

    private static string NormalizeError(string message)
    {
        var trimmed = message.Trim();
        if (string.IsNullOrWhiteSpace(trimmed))
        {
            return "unknown error";
        }

        var lower = trimmed.ToLowerInvariant();
        if (lower.Contains("access is denied") ||
            lower.Contains("administrator") ||
            lower.Contains("elevated") ||
            lower.Contains("permission") ||
            trimmed.Contains("权限") ||
            trimmed.Contains("拒绝访问"))
        {
            return "Permission denied. Please run as Administrator.";
        }

        return trimmed;
    }
}

internal static class JsonHelpers
{
    public static JsonElement? ParseRoot(string output)
    {
        if (string.IsNullOrWhiteSpace(output))
        {
            return null;
        }

        using var document = JsonDocument.Parse(output);
        var root = document.RootElement;
        if (root.ValueKind == JsonValueKind.Array)
        {
            if (root.GetArrayLength() == 0)
            {
                return null;
            }

            root = root[0];
        }

        return root.Clone();
    }

    public static string? GetString(JsonElement root, string propertyName)
    {
        return root.TryGetProperty(propertyName, out var property) && property.ValueKind == JsonValueKind.String
            ? property.GetString()
            : null;
    }

    public static bool GetBool(JsonElement root, string propertyName)
    {
        return root.TryGetProperty(propertyName, out var property) &&
            property.ValueKind == JsonValueKind.True;
    }
}

internal static class PowerShellText
{
    public static string Quote(string value)
    {
        return "'" + value.Replace("'", "''") + "'";
    }
}
