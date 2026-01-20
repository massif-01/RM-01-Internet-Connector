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
    Connected,
    Failed
}

public sealed class AppState : INotifyPropertyChanged
{
    private readonly IWindowsNetworkService _networkService;
    private ConnectionStatus _status = ConnectionStatus.Idle;
    private NetworkInterfaceInfo? _currentInterface;
    private string _statusKey = "status_idle";
    private bool _isBusy;
    private Exception? _lastError;
    private double _uploadSpeed;
    private double _downloadSpeed;
    private NetworkSpeedMonitor? _speedMonitor;

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
    }

    public async Task RefreshInterfaceAsync()
    {
        var nic = await _networkService.DetectAdapterAsync();
        CurrentInterface = nic;
        StatusKey = nic == null ? "interface_none" : "interface_found";
    }

    public async Task ConnectAsync()
    {
        if (IsBusy) return;
        IsBusy = true;
        LastError = null;
        Status = ConnectionStatus.Connecting;
        StatusKey = "status_connecting";

        try
        {
            var nic = await _networkService.DetectAdapterAsync();
            if (nic == null)
            {
                Status = ConnectionStatus.Failed;
                StatusKey = "interface_none";
                LastError = new InvalidOperationException("未检测到 AX88179A 适配器");
                return;
            }

            CurrentInterface = nic;
            await _networkService.EnableSharingAsync(nic, CancellationToken.None);

            Status = ConnectionStatus.Connected;
            StatusKey = "status_connected";
            
            // Start speed monitoring
            StartSpeedMonitoring();
        }
        catch (OperationCanceledException)
        {
            Status = ConnectionStatus.Idle;
            StatusKey = "status_idle";
        }
        catch (Exception ex)
        {
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
        IsBusy = true;
        LastError = null;
        Status = ConnectionStatus.Connecting;
        StatusKey = "status_disconnecting";

        try
        {
            // Stop speed monitoring
            StopSpeedMonitoring();
            
            await _networkService.DisableSharingAsync(CurrentInterface, CancellationToken.None);
            Status = ConnectionStatus.Idle;
            StatusKey = "status_idle";
            CurrentInterface = null;
        }
        catch (OperationCanceledException)
        {
            Status = ConnectionStatus.Connected;
            StatusKey = "status_connected";
        }
        catch (Exception ex)
        {
            LastError = ex;
            Status = ConnectionStatus.Failed;
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
        UploadSpeed = uploadSpeed;
        DownloadSpeed = downloadSpeed;
    }
}





















