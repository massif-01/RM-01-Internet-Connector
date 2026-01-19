using System.Windows;

namespace RM01InternetConnector.Win;

public partial class App : Application
{
    private AppState? _state;
    private TrayController? _tray;
    private MainWindow? _window;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        var localization = LocalizationManager.Instance;
        var network = new WindowsNetworkService();
        _state = new AppState(network);

        _tray = new TrayController(
            _state,
            localization,
            ShowMainWindow,
            QuitApplication);

        _ = _state.RefreshInterfaceAsync();
        ShowMainWindow();
        
        // Note: Admin privileges are now requested via app.manifest
        // The app will automatically prompt for elevation when started
    }

    private void ShowMainWindow()
    {
        if (_state == null) return;

        if (_window == null)
        {
            _window = new MainWindow(_state, LocalizationManager.Instance, ShowMainWindow);
            _window.Closed += (_, _) =>
            {
                // 保持托盘驻留，窗口关闭时不退出
                Current.ShutdownMode = ShutdownMode.OnExplicitShutdown;
            };
        }

        _window.Show();
        _window.Activate();
    }

    private void QuitApplication()
    {
        _tray?.Dispose();
        Shutdown();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _tray?.Dispose();
        base.OnExit(e);
    }
}




