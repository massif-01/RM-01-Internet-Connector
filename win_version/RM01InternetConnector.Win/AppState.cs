using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace RM01InternetConnector.Win;

public enum ConnectionStatus
{
    Idle,
    Connecting,
    Disconnecting,
    Connected,
    Failed
}

public sealed class AppState : INotifyPropertyChanged, IDisposable
{
    private readonly IWindowsNetworkService _networkService;
    private readonly SynchronizationContext? _stateContext;
    private readonly CancellationTokenSource _lifetimeCts = new();
    private ConnectionStatus _status = ConnectionStatus.Idle;
    private NetworkInterfaceInfo? _currentInterface;
    private string _statusKey = "status_idle";
    private bool _isBusy;
    private Exception? _lastError;
    private double _uploadSpeed;
    private double _downloadSpeed;
    private NetworkSpeedMonitor? _speedMonitor;
    private bool _disposed;

    public event PropertyChangedEventHandler? PropertyChanged;

    public ConnectionStatus Status
    {
        get => _status;
        private set => SetProperty(ref _status, value);
    }

    public NetworkInterfaceInfo? CurrentInterface
    {
        get => _currentInterface;
        private set => SetProperty(ref _currentInterface, value);
    }

    public string StatusKey
    {
        get => _statusKey;
        private set => SetProperty(ref _statusKey, value);
    }

    public bool IsBusy
    {
        get => _isBusy;
        private set => SetProperty(ref _isBusy, value);
    }

    public Exception? LastError
    {
        get => _lastError;
        private set => SetProperty(ref _lastError, value);
    }

    public bool IsConnected => Status == ConnectionStatus.Connected;

    public double UploadSpeed
    {
        get => _uploadSpeed;
        private set => SetProperty(ref _uploadSpeed, value);
    }

    public double DownloadSpeed
    {
        get => _downloadSpeed;
        private set => SetProperty(ref _downloadSpeed, value);
    }

    public AppState(IWindowsNetworkService networkService)
    {
        _networkService = networkService;
        _stateContext = SynchronizationContext.Current;
    }

    public async Task RefreshInterfaceAsync(bool checkSharing = false)
    {
        try
        {
            var nic = await _networkService.DetectAdapterAsync();
            if (!CanApplyRefreshResult())
                return;

            CurrentInterface = nic;
            LastError = null;
            if (nic == null)
            {
                StopSpeedMonitoring();
                Status = ConnectionStatus.Idle;
                StatusKey = "interface_none";
                return;
            }

            if (checkSharing && await _networkService.IsSharingEnabledAsync(nic, _lifetimeCts.Token))
            {
                if (!CanApplyRefreshResult())
                    return;

                Status = ConnectionStatus.Connected;
                StatusKey = "status_connected";
                StartSpeedMonitoring();
                return;
            }

            StopSpeedMonitoring();
            Status = ConnectionStatus.Idle;
            StatusKey = "interface_found";
        }
        catch (OperationCanceledException)
        {
            // The app is shutting down.
        }
        catch (Exception ex)
        {
            if (!CanApplyRefreshResult())
                return;

            LastError = ex;
            Status = ConnectionStatus.Failed;
            StatusKey = "status_failed";
        }
    }

    public async Task ConnectAsync()
    {
        if (IsBusy) return;
        AppDiagnostics.Log("Connect requested");
        IsBusy = true;
        LastError = null;
        Status = ConnectionStatus.Connecting;
        StatusKey = "status_connecting";

        try
        {
            var nic = await _networkService.DetectAdapterAsync();
            if (nic == null)
            {
                AppDiagnostics.Log("Connect failed: AX88179A adapter not detected");
                Status = ConnectionStatus.Failed;
                StatusKey = "interface_none";
                LastError = new InvalidOperationException("未检测到 AX88179A 适配器");
                return;
            }

            CurrentInterface = nic;
            AppDiagnostics.Log($"Connect using adapter: name={nic.Name}, description={nic.Description}, mac={nic.Mac}");
            await _networkService.EnableSharingAsync(nic, _lifetimeCts.Token);

            Status = ConnectionStatus.Connected;
            StatusKey = "status_connected";
            AppDiagnostics.Log("Connect completed");
            
            // Start speed monitoring
            StartSpeedMonitoring();
        }
        catch (OperationCanceledException)
        {
            AppDiagnostics.Log("Connect cancelled");
            Status = ConnectionStatus.Idle;
            StatusKey = "status_idle";
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("Connect failed", ex);
            LastError = ex;
            Status = ConnectionStatus.Failed;
            StatusKey = "status_failed";
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task DisconnectAsync()
    {
        if (IsBusy) return;
        AppDiagnostics.Log("Disconnect requested");
        IsBusy = true;
        LastError = null;
        Status = ConnectionStatus.Disconnecting;
        StatusKey = "status_disconnecting";

        try
        {
            var nic = CurrentInterface ?? await _networkService.DetectAdapterAsync();
            if (nic == null)
            {
                AppDiagnostics.Log("Disconnect skipped: AX88179A adapter not detected");
                StopSpeedMonitoring();
                Status = ConnectionStatus.Idle;
                StatusKey = "interface_none";
                CurrentInterface = null;
                return;
            }

            CurrentInterface = nic;
            AppDiagnostics.Log($"Disconnect using adapter: name={nic.Name}, description={nic.Description}, mac={nic.Mac}");
            await _networkService.DisableSharingAsync(nic, _lifetimeCts.Token);
            StopSpeedMonitoring();
            Status = ConnectionStatus.Idle;
            StatusKey = "status_idle";
            CurrentInterface = null;
            AppDiagnostics.Log("Disconnect completed");
        }
        catch (OperationCanceledException)
        {
            AppDiagnostics.Log("Disconnect cancelled");
            Status = ConnectionStatus.Connected;
            StatusKey = "status_connected";
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("Disconnect failed", ex);
            LastError = ex;
            Status = CurrentInterface == null ? ConnectionStatus.Failed : ConnectionStatus.Connected;
            StatusKey = "status_failed";
        }
        finally
        {
            IsBusy = false;
        }
    }

    private void SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (Equals(field, value)) return;
        field = value;
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    private void StartSpeedMonitoring()
    {
        if (_disposed)
            return;

        if (CurrentInterface == null || Status != ConnectionStatus.Connected)
            return;

        StopSpeedMonitoring(); // Stop any existing monitor

        _speedMonitor = new NetworkSpeedMonitor(CurrentInterface.Name, OnSpeedUpdated);
        _speedMonitor.Start();
    }

    private void StopSpeedMonitoring()
    {
        if (_speedMonitor != null)
        {
            _speedMonitor.Dispose();
            _speedMonitor = null;
        }

        UploadSpeed = 0;
        DownloadSpeed = 0;
    }

    private void OnSpeedUpdated(double uploadSpeed, double downloadSpeed)
    {
        if (_disposed)
            return;

        RunOnStateContext(() =>
        {
            if (_disposed)
                return;

            UploadSpeed = uploadSpeed;
            DownloadSpeed = downloadSpeed;
        });
    }

    private bool CanApplyRefreshResult()
    {
        return !_disposed && !IsBusy && Status == ConnectionStatus.Idle;
    }

    private void RunOnStateContext(Action action)
    {
        if (_stateContext == null || SynchronizationContext.Current == _stateContext)
        {
            action();
            return;
        }

        _stateContext.Post(_ => action(), null);
    }

    public void Dispose()
    {
        if (_disposed)
            return;

        _disposed = true;
        _lifetimeCts.Cancel();
        StopSpeedMonitoring();
        _lifetimeCts.Dispose();
    }
}
















