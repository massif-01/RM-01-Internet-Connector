using System;
using System.Linq;
using System.Net.NetworkInformation;
using System.Threading;

namespace RM01InternetConnector.Win;

/// <summary>
/// Monitors network interface speed in real-time
/// Measures upload and download speeds from RM-01's perspective
/// </summary>
public sealed class NetworkSpeedMonitor : IDisposable
{
    private readonly string _interfaceName;
    private readonly Action<double, double> _callback;
    private Timer? _timer;
    private long _lastRxBytes;
    private long _lastTxBytes;
    private DateTime _lastUpdateTime;
    private bool _disposed;

    /// <summary>
    /// Create a network speed monitor for the specified interface
    /// </summary>
    /// <param name="interfaceName">Network interface name to monitor</param>
    /// <param name="callback">Callback (uploadSpeed, downloadSpeed) in bytes per second</param>
    public NetworkSpeedMonitor(string interfaceName, Action<double, double> callback)
    {
        _interfaceName = interfaceName ?? throw new ArgumentNullException(nameof(interfaceName));
        _callback = callback ?? throw new ArgumentNullException(nameof(callback));
    }

    /// <summary>
    /// Start monitoring network speed
    /// </summary>
    public void Start()
    {
        if (_disposed)
            throw new ObjectDisposedException(nameof(NetworkSpeedMonitor));

        if (_timer != null)
            return; // Already started

        // Get initial sample
        var (rx, tx) = GetInterfaceBytes();
        if (rx >= 0 && tx >= 0)
        {
            _lastRxBytes = rx;
            _lastTxBytes = tx;
            _lastUpdateTime = DateTime.Now;
        }

        // Update every 1 second
        _timer = new Timer(Update, null, TimeSpan.FromSeconds(1), TimeSpan.FromSeconds(1));
    }

    /// <summary>
    /// Stop monitoring network speed
    /// </summary>
    public void Stop()
    {
        _timer?.Dispose();
        _timer = null;
    }

    private void Update(object? state)
    {
        try
        {
            var (currentRx, currentTx) = GetInterfaceBytes();
            if (currentRx < 0 || currentTx < 0)
                return; // Interface not found or error

            var now = DateTime.Now;
            var timeDiff = (now - _lastUpdateTime).TotalSeconds;

            if (timeDiff <= 0)
                return;

            // Calculate bytes per second
            var rxDiff = currentRx > _lastRxBytes ? currentRx - _lastRxBytes : 0;
            var txDiff = currentTx > _lastTxBytes ? currentTx - _lastTxBytes : 0;

            var downloadSpeed = rxDiff / timeDiff;  // Computer RX
            var uploadSpeed = txDiff / timeDiff;    // Computer TX

            // From RM-01's perspective:
            // - RM-01 upload = Computer's RX (data coming from RM-01)
            // - RM-01 download = Computer's TX (data going to RM-01)
            // So we swap them for the callback
            _callback(downloadSpeed, uploadSpeed);  // RM-01 upload, RM-01 download

            // Update for next iteration
            _lastRxBytes = currentRx;
            _lastTxBytes = currentTx;
            _lastUpdateTime = now;
        }
        catch
        {
            // Ignore errors in background monitoring
        }
    }

    /// <summary>
    /// Get total bytes received and transmitted for the interface
    /// </summary>
    /// <returns>Tuple of (rxBytes, txBytes), or (-1, -1) if interface not found</returns>
    private (long rxBytes, long txBytes) GetInterfaceBytes()
    {
        try
        {
            var nic = NetworkInterface.GetAllNetworkInterfaces()
                .FirstOrDefault(n => string.Equals(n.Name, _interfaceName, StringComparison.OrdinalIgnoreCase));

            if (nic == null)
                return (-1, -1);

            var stats = nic.GetIPv4Statistics();
            return (stats.BytesReceived, stats.BytesSent);
        }
        catch
        {
            return (-1, -1);
        }
    }

    public void Dispose()
    {
        if (_disposed)
            return;

        _disposed = true;
        Stop();
    }
}
