using System;
using System.ComponentModel;
using System.Drawing;
using System.Threading;
using System.Windows.Forms;

namespace RM01InternetConnector.Win;

public sealed class TrayController : IDisposable
{
    private readonly AppState _state;
    private readonly LocalizationManager _loc;
    private readonly Action _openWindow;
    private readonly Action _quit;
    private readonly SynchronizationContext? _uiContext;

    private readonly NotifyIcon _notifyIcon;
    private readonly ToolStripMenuItem _speedItem;
    private readonly ToolStripSeparator _speedSeparator;
    private readonly ToolStripMenuItem _statusItem;
    private readonly ToolStripMenuItem _connectItem;
    private readonly ToolStripMenuItem _openItem;
    private readonly ToolStripMenuItem _quitItem;
    private bool _disposed;

    public TrayController(AppState state, LocalizationManager loc, Action openWindow, Action quit)
    {
        _state = state;
        _loc = loc;
        _openWindow = openWindow;
        _quit = quit;
        _uiContext = SynchronizationContext.Current;

        _notifyIcon = new NotifyIcon
        {
            Icon = LoadIcon(),
            Visible = true,
            Text = "RM-01 Internet Connector"
        };

        var menu = new ContextMenuStrip();
        
        // Speed display (hidden when not connected)
        _speedItem = new ToolStripMenuItem 
        { 
            Enabled = false,  // Only for display
            Visible = false   // Hidden by default
        };
        _speedSeparator = new ToolStripSeparator { Visible = false };
        
        _statusItem = new ToolStripMenuItem { Enabled = false };
        _connectItem = new ToolStripMenuItem();

        _openItem = new ToolStripMenuItem
        {
            Text = _loc.Translate("tray_open")
        };
        _openItem.Click += OnOpenClicked;

        _quitItem = new ToolStripMenuItem
        {
            Text = _loc.Translate("tray_quit")
        };
        _quitItem.Click += OnQuitClicked;

        // Add menu items in order
        menu.Items.Add(_speedItem);
        menu.Items.Add(_speedSeparator);
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(_connectItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(_openItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(_quitItem);

        _notifyIcon.ContextMenuStrip = menu;
        _notifyIcon.DoubleClick += OnOpenClicked;

        _state.PropertyChanged += OnStateChanged;
        _loc.PropertyChanged += OnLocalizationChanged;

        UpdateMenu();
    }

    private void OnStateChanged(object? sender, PropertyChangedEventArgs e)
    {
        UpdateMenu();
    }

    private void OnLocalizationChanged(object? sender, PropertyChangedEventArgs e)
    {
        UpdateMenu();
    }

    private void UpdateMenu()
    {
        if (_disposed)
            return;

        if (_uiContext != null && SynchronizationContext.Current != _uiContext)
        {
            _uiContext.Post(state => UpdateMenu(), null);
            return;
        }

        // Update speed display
        if (_state.Status == ConnectionStatus.Connected)
        {
            _speedItem.Text = $"↑ {FormatSpeed(_state.UploadSpeed)}   |   ↓ {FormatSpeed(_state.DownloadSpeed)}";
            _speedItem.Visible = true;
            _speedSeparator.Visible = true;
        }
        else
        {
            _speedItem.Visible = false;
            _speedSeparator.Visible = false;
        }
        
        // Update status with colored indicator
        _statusItem.Text = StatusTitle();
        
        // Update connect/disconnect button
        _connectItem.Text = _state.IsConnected || _state.Status == ConnectionStatus.Disconnecting
            ? _loc.Translate("tray_disconnect")
            : _loc.Translate("tray_connect");
        _connectItem.Enabled = !_state.IsBusy;
        _connectItem.Click -= OnConnectClicked;
        _connectItem.Click += OnConnectClicked;

        _openItem.Text = _loc.Translate("tray_open");
        _quitItem.Text = _loc.Translate("tray_quit");
    }

    private string StatusTitle()
    {
        return _state.Status switch
        {
            ConnectionStatus.Connected => $"● {_loc.Translate("tray_status_connected")}",
            ConnectionStatus.Connecting => $"● {_loc.Translate("tray_status_connecting")}",
            ConnectionStatus.Disconnecting => $"● {_loc.Translate("status_disconnecting")}",
            ConnectionStatus.Failed => $"● {_loc.Translate("tray_status_failed")}",
            _ => $"○ {_loc.Translate("tray_status_idle")}"
        };
    }

    private void OnOpenClicked(object? sender, EventArgs e)
    {
        if (!_disposed)
            _openWindow();
    }

    private void OnQuitClicked(object? sender, EventArgs e)
    {
        if (!_disposed)
            _quit();
    }

    private async void OnConnectClicked(object? sender, EventArgs e)
    {
        if (_disposed)
            return;

        if (_state.IsConnected)
        {
            await _state.DisconnectAsync();
        }
        else
        {
            await _state.ConnectAsync();
        }
    }

    private static Icon? LoadIcon()
    {
        try
        {
            var streamInfo = System.Windows.Application.GetResourceStream(
                new Uri("pack://application:,,,/Assets/icon.ico", UriKind.Absolute));
            if (streamInfo?.Stream != null)
            {
                using var stream = streamInfo.Stream;
                return new Icon(stream);
            }
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("Loading tray icon from embedded resource failed", ex);
        }
        return SystemIcons.Application;
    }

    private static string FormatSpeed(double bytesPerSecond)
    {
        if (bytesPerSecond < 1024)
            return $"{bytesPerSecond:F0}B/s";
        else if (bytesPerSecond < 1024 * 1024)
            return $"{bytesPerSecond / 1024:F1}KB/s";
        else if (bytesPerSecond < 1024 * 1024 * 1024)
            return $"{bytesPerSecond / 1024 / 1024:F1}MB/s";
        else
            return $"{bytesPerSecond / 1024 / 1024 / 1024:F2}GB/s";
    }

    public void Dispose()
    {
        if (_disposed)
            return;

        _disposed = true;
        _state.PropertyChanged -= OnStateChanged;
        _loc.PropertyChanged -= OnLocalizationChanged;
        _notifyIcon.DoubleClick -= OnOpenClicked;
        _connectItem.Click -= OnConnectClicked;
        _openItem.Click -= OnOpenClicked;
        _quitItem.Click -= OnQuitClicked;

        _notifyIcon.Visible = false;
        _notifyIcon.ContextMenuStrip?.Dispose();
        _notifyIcon.Dispose();
    }
}

















