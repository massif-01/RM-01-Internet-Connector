using System;
using System.ComponentModel;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace RM01InternetConnector.Win;

public sealed class TrayController : IDisposable
{
    private readonly AppState _state;
    private readonly LocalizationManager _loc;
    private readonly Action _openWindow;
    private readonly Action _quit;

    private readonly NotifyIcon _notifyIcon;
    private readonly ToolStripMenuItem _speedItem;
    private readonly ToolStripSeparator _speedSeparator;
    private readonly ToolStripMenuItem _statusItem;
    private readonly ToolStripMenuItem _connectItem;

    public TrayController(AppState state, LocalizationManager loc, Action openWindow, Action quit)
    {
        _state = state;
        _loc = loc;
        _openWindow = openWindow;
        _quit = quit;

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

        var openItem = new ToolStripMenuItem
        {
            Text = _loc.Translate("tray_open")
        };
        openItem.Click += (_, _) => _openWindow();

        var quitItem = new ToolStripMenuItem
        {
            Text = _loc.Translate("tray_quit")
        };
        quitItem.Click += (_, _) => _quit();

        // Add menu items in order
        menu.Items.Add(_speedItem);
        menu.Items.Add(_speedSeparator);
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(_connectItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(openItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(quitItem);

        _notifyIcon.ContextMenuStrip = menu;
        _notifyIcon.DoubleClick += (_, _) => _openWindow();

        _state.PropertyChanged += OnStateChanged;
        _loc.PropertyChanged += (_, _) => UpdateMenu();

        UpdateMenu();
    }

    private void OnStateChanged(object? sender, PropertyChangedEventArgs e)
    {
        UpdateMenu();
    }

    private void UpdateMenu()
    {
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
        _connectItem.Text = _state.IsConnected ? _loc.Translate("tray_disconnect") : _loc.Translate("tray_connect");
        _connectItem.Enabled = !_state.IsBusy;
        _connectItem.Click -= OnConnectClicked;
        _connectItem.Click += OnConnectClicked;
    }

    private string StatusTitle()
    {
        return _state.Status switch
        {
            ConnectionStatus.Connected => $"● {_loc.Translate("tray_status_connected")}",
            ConnectionStatus.Connecting => $"● {_loc.Translate("tray_status_connecting")}",
            ConnectionStatus.Failed => $"● {_loc.Translate("tray_status_failed")}",
            _ => $"○ {_loc.Translate("tray_status_idle")}"
        };
    }

    private async void OnConnectClicked(object? sender, EventArgs e)
    {
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
            var path = Path.Combine(AppContext.BaseDirectory, "Assets", "icon.png");
            if (File.Exists(path))
            {
                using var bmp = new Bitmap(path);
                return Icon.FromHandle(bmp.GetHicon());
            }
        }
        catch
        {
            // ignore and fallback
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
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
    }
}





















