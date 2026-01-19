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
        _statusItem.Text = StatusTitle();
        _connectItem.Text = _state.IsConnected ? _loc.Translate("tray_disconnect") : _loc.Translate("tray_connect");
        _connectItem.Enabled = !_state.IsBusy;
        _connectItem.Click -= OnConnectClicked;
        _connectItem.Click += OnConnectClicked;
    }

    private string StatusTitle()
    {
        return _state.Status switch
        {
            ConnectionStatus.Connected => _loc.Translate("tray_status_connected"),
            ConnectionStatus.Connecting => _loc.Translate("tray_status_connecting"),
            ConnectionStatus.Failed => _loc.Translate("tray_status_failed"),
            _ => _loc.Translate("tray_status_idle")
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

    public void Dispose()
    {
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
    }
}





















