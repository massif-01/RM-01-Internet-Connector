using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Management;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace RM01InternetConnector.Win;

public interface IWindowsNetworkService
{
    Task<NetworkInterfaceInfo?> DetectAdapterAsync();
    Task EnableSharingAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken);
    Task DisableSharingAsync(NetworkInterfaceInfo? nic, CancellationToken cancellationToken);
}

public sealed class WindowsNetworkService : IWindowsNetworkService
{
    private readonly AdapterDetector _detector = new();
    private readonly NetworkConfigurator _configurator = new();
    private readonly IcsManager _ics = new();

    public Task<NetworkInterfaceInfo?> DetectAdapterAsync()
    {
        return Task.Run(() => _detector.FindFirst());
    }

    public async Task EnableSharingAsync(NetworkInterfaceInfo nic, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        await _configurator.SetStaticAsync(nic.Name, cancellationToken);

        var upstream = _detector.FindBestUpstream(nic.Name);
        if (upstream == null)
        {
            throw new InvalidOperationException("未找到可用的上游网络（如 Wi-Fi/以太网）。");
        }

        _ics.EnableSharing(upstream.Name, nic.Name);
    }

    public async Task DisableSharingAsync(NetworkInterfaceInfo? nic, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (nic != null)
        {
            _ics.DisableSharing(nic.Name);
            await _configurator.SetDhcpAsync(nic.Name, cancellationToken);
        }
    }
}

internal sealed class AdapterDetector
{
    // Only match AX88179A to avoid matching other generic USB ethernet adapters
    // This matches the macOS version behavior
    private static readonly string[] KnownIdentifiers =
    {
        "ax88179"
    };

    public NetworkInterfaceInfo? FindFirst()
    {
        return Detect().FirstOrDefault();
    }

    public NetworkInterfaceInfo? FindBestUpstream(string excludeName)
    {
        // Find the best upstream network interface (Wi-Fi, Ethernet, etc.)
        // Excludes: the target device, loopback, tunnel/VPN interfaces, and disconnected interfaces
        var candidates = NetworkInterface.GetAllNetworkInterfaces()
            .Where(n =>
                !string.Equals(n.Name, excludeName, StringComparison.OrdinalIgnoreCase) &&
                n.NetworkInterfaceType != NetworkInterfaceType.Loopback &&
                n.NetworkInterfaceType != NetworkInterfaceType.Tunnel &&
                !n.Description.Contains("Virtual", StringComparison.OrdinalIgnoreCase) &&
                !n.Description.Contains("VPN", StringComparison.OrdinalIgnoreCase) &&
                !n.Description.Contains("TAP", StringComparison.OrdinalIgnoreCase) &&
                !n.Description.Contains("TUN", StringComparison.OrdinalIgnoreCase) &&
                n.OperationalStatus == OperationalStatus.Up &&
                n.Supports(NetworkInterfaceComponent.IPv4) &&
                HasValidIPv4Address(n))
            .OrderByDescending(n => n.NetworkInterfaceType == NetworkInterfaceType.Wireless80211) // Prefer Wi-Fi
            .ThenByDescending(n => n.NetworkInterfaceType == NetworkInterfaceType.Ethernet)      // Then Ethernet
            .ThenByDescending(n => n.Speed)
            .ToList();

        var nic = candidates.FirstOrDefault();
        return nic == null ? null : ToInfo(nic, null);
    }

    private static bool HasValidIPv4Address(NetworkInterface nic)
    {
        try
        {
            var props = nic.GetIPProperties();
            return props.UnicastAddresses.Any(addr =>
                addr.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork &&
                !System.Net.IPAddress.IsLoopback(addr.Address) &&
                !addr.Address.ToString().StartsWith("169.254.")); // Exclude link-local addresses
        }
        catch
        {
            return false;
        }
    }

    private IEnumerable<NetworkInterfaceInfo> Detect()
    {
        var all = NetworkInterface.GetAllNetworkInterfaces();
        foreach (var nic in all)
        {
            var desc = nic.Description?.ToLowerInvariant() ?? string.Empty;
            if (!KnownIdentifiers.Any(id => desc.Contains(id))) continue;

            string? pnpId = TryGetPnpId(nic.Id);
            var mac = FormatMac(nic.GetPhysicalAddress());

            yield return ToInfo(nic, pnpId ?? nic.Id, mac);
        }
    }

    private static NetworkInterfaceInfo ToInfo(NetworkInterface nic, string? idOverride, string? macOverride = null)
    {
        return new NetworkInterfaceInfo(
            nic.Name,
            nic.Description,
            idOverride ?? nic.Id,
            macOverride ?? FormatMac(nic.GetPhysicalAddress()));
    }

    private static string FormatMac(PhysicalAddress address)
    {
        var bytes = address.GetAddressBytes();
        return string.Join(":", bytes.Select(b => b.ToString("X2")));
    }

    private static string? TryGetPnpId(string interfaceId)
    {
        try
        {
            using var searcher = new ManagementObjectSearcher(
                "SELECT * FROM Win32_NetworkAdapter WHERE GUID='" + interfaceId + "'");
            foreach (var obj in searcher.Get())
            {
                return obj["PNPDeviceID"] as string;
            }
        }
        catch
        {
            // 读取失败忽略，使用 NetworkInterface.Id 作为后备
        }
        return null;
    }
}

internal sealed class NetworkConfigurator
{
    private const string StaticIp = "10.10.99.100";
    private const string Mask = "255.255.255.0";
    private const string Gateway = "10.10.99.100";
    private const string Dns = "8.8.8.8";

    public async Task SetStaticAsync(string interfaceName, CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        await Run("netsh", $"interface ip set address name=\"{interfaceName}\" static {StaticIp} {Mask} {Gateway}", token);
        await Run("netsh", $"interface ip set dns name=\"{interfaceName}\" static {Dns}", token);
    }

    public async Task SetDhcpAsync(string interfaceName, CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        
        // Restore DHCP for IP address
        await Run("netsh", $"interface ip set address name=\"{interfaceName}\" source=dhcp", token);
        
        // Clear DNS settings (restore to DHCP)
        await Run("netsh", $"interface ip set dns name=\"{interfaceName}\" source=dhcp", token);
        
        // Flush DNS cache to ensure clean state
        await Run("ipconfig", "/flushdns", token);
        
        // Release and renew DHCP to get fresh IP from RM-01
        try
        {
            await Run("ipconfig", $"/release \"{interfaceName}\"", token);
            await Task.Delay(500, token); // Brief delay for release to complete
            await Run("ipconfig", $"/renew \"{interfaceName}\"", token);
        }
        catch
        {
            // Ignore errors from release/renew as interface might not support it
        }
    }

    private static async Task Run(string fileName, string arguments, CancellationToken token)
    {
        var psi = new ProcessStartInfo
        {
            FileName = fileName,
            Arguments = arguments,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        using var process = new Process { StartInfo = psi };
        process.Start();

        await process.WaitForExitAsync(token);
        if (process.ExitCode != 0)
        {
            var error = await process.StandardError.ReadToEndAsync();
            var output = await process.StandardOutput.ReadToEndAsync();
            var message = string.IsNullOrWhiteSpace(error) ? output : error;
            throw new InvalidOperationException($"命令执行失败: {fileName} {arguments} ({message.Trim()})");
        }
    }
}

internal sealed class IcsManager
{
    public void EnableSharing(string publicInterfaceName, string privateInterfaceName)
    {
        var manager = new NetSharingManager() as INetSharingManager;
        if (manager == null || !manager.SharingInstalled)
        {
            throw new InvalidOperationException("系统未安装 Internet 连接共享组件。");
        }

        var publicConn = FindConnection(manager, publicInterfaceName);
        var privateConn = FindConnection(manager, privateInterfaceName);

        if (publicConn == null)
        {
            throw new InvalidOperationException("未找到上游网络接口：" + publicInterfaceName);
        }

        if (privateConn == null)
        {
            throw new InvalidOperationException("未找到 RM-01 适配器：" + privateInterfaceName);
        }

        var publicCfg = manager.NetSharingConfigurationForINetConnection(publicConn);
        var privateCfg = manager.NetSharingConfigurationForINetConnection(privateConn);

        // 关闭原有共享，避免冲突
        DisableExistingSharing(manager, publicInterfaceName, privateInterfaceName);

        publicCfg.EnableSharing(SHARINGCONNECTIONTYPE.ICSSHARINGTYPE_PUBLIC);
        privateCfg.EnableSharing(SHARINGCONNECTIONTYPE.ICSSHARINGTYPE_PRIVATE);
    }

    public void DisableSharing(string interfaceName)
    {
        var manager = new NetSharingManager() as INetSharingManager;
        if (manager == null || !manager.SharingInstalled) return;

        var connection = FindConnection(manager, interfaceName);
        if (connection == null) return;

        var cfg = manager.NetSharingConfigurationForINetConnection(connection);
        if (cfg.SharingEnabled)
        {
            cfg.DisableSharing();
        }
    }

    private static void DisableExistingSharing(INetSharingManager manager, string currentPublic, string currentPrivate)
    {
        foreach (INetConnection conn in manager.EnumEveryConnection)
        {
            var props = manager.NetConnectionProps(conn);
            var cfg = manager.NetSharingConfigurationForINetConnection(conn);
            if (!cfg.SharingEnabled) continue;

            if (!string.Equals(props.Name, currentPublic, StringComparison.OrdinalIgnoreCase) &&
                !string.Equals(props.Name, currentPrivate, StringComparison.OrdinalIgnoreCase))
            {
                cfg.DisableSharing();
            }
        }
    }

    private static INetConnection? FindConnection(INetSharingManager manager, string name)
    {
        foreach (INetConnection conn in manager.EnumEveryConnection)
        {
            var props = manager.NetConnectionProps(conn);
            if (string.Equals(props.Name, name, StringComparison.OrdinalIgnoreCase))
            {
                return conn;
            }
        }
        return null;
    }
}

// ICS COM interop definitions

[ComImport]
[Guid("5C63C1AD-3956-4FF8-8486-40034758315B")]
internal class NetSharingManager
{
}

internal enum SHARINGCONNECTIONTYPE
{
    ICSSHARINGTYPE_PUBLIC = 0,
    ICSSHARINGTYPE_PRIVATE = 1
}

internal enum NETCON_STATUS
{
    NCS_DISCONNECTED = 0,
    NCS_CONNECTING = 1,
    NCS_CONNECTED = 2
}

[ComImport]
[Guid("C08956B7-1CD3-11D1-B1C5-00805FC1270E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INetSharingManager
{
    bool SharingInstalled { get; }

    INetSharingEveryConnectionCollection EnumEveryConnection { get; }

    INetConnectionProps NetConnectionProps([In] INetConnection pNetConnection);

    INetSharingConfiguration NetSharingConfigurationForINetConnection([In] INetConnection pNetConnection);
}

[ComImport]
[Guid("C08956B1-1CD3-11D1-B1C5-00805FC1270E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INetConnection
{
}

[ComImport]
[Guid("C08956B3-1CD3-11D1-B1C5-00805FC1270E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INetConnectionProps
{
    string Guid { get; }
    string Name { get; }
    string DeviceName { get; }
    NETCON_STATUS Status { get; }
}

[ComImport]
[Guid("C08956B4-1CD3-11D1-B1C5-00805FC1270E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INetSharingConfiguration
{
    bool SharingEnabled { get; }

    SHARINGCONNECTIONTYPE SharingConnectionType { get; }

    void DisableSharing();

    void EnableSharing(SHARINGCONNECTIONTYPE type);
}

[ComImport]
[Guid("C08956B6-1CD3-11D1-B1C5-00805FC1270E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INetSharingEveryConnectionCollection : IEnumerable
{
    [return: MarshalAs(UnmanagedType.Interface)]
    new IEnumerator GetEnumerator();
}




