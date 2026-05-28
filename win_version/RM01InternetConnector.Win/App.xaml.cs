using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;

namespace RM01InternetConnector.Win;

public partial class App : System.Windows.Application
{
    private AppState? _state;
    private TrayController? _tray;
    private MainWindow? _window;
    private bool _isQuitting;

    protected override void OnStartup(StartupEventArgs e)
    {
        RegisterExceptionHandlers();
        base.OnStartup(e);

        try
        {
            AppDiagnostics.Log($"Starting RM-01 Internet Connector from {AppContext.BaseDirectory}");

            var localization = LocalizationManager.Instance;
            var network = new WindowsNetworkService();
            _state = new AppState(network);

            ShowMainWindow();
            AppDiagnostics.Log("Startup completed");
            Dispatcher.BeginInvoke(InitializeBackgroundStartup, DispatcherPriority.ApplicationIdle);
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("Startup failed", ex);
            System.Windows.MessageBox.Show(
                $"RM-01 Internet Connector failed to start.\n\nLog: {AppDiagnostics.LogPath}\n\n{ex.Message}",
                "RM-01 Internet Connector",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            Shutdown(1);
        }
    }

    private void ShowMainWindow()
    {
        if (_state == null) return;

        if (_window == null)
        {
            _window = new MainWindow(_state, LocalizationManager.Instance, () => _tray != null);
            _window.Closed += (_, _) =>
            {
                _window = null;
            };
        }

        _window.Show();
        _window.Activate();
    }

    private void InitializeBackgroundStartup()
    {
        if (_state == null)
        {
            return;
        }

        AppDiagnostics.Log("Starting deferred tray initialization");
        try
        {
            _tray = new TrayController(
                _state,
                LocalizationManager.Instance,
                ShowMainWindow,
                QuitApplication);
            ShutdownMode = ShutdownMode.OnExplicitShutdown;
            AppDiagnostics.Log("Deferred tray initialization completed");
        }
        catch (Exception ex)
        {
            AppDiagnostics.LogException("Deferred tray initialization failed; continuing without tray", ex);
            _tray = null;
        }

        _ = _state.RefreshInterfaceAsync(checkSharing: false).ContinueWith(task =>
        {
            if (task.Exception != null)
            {
                AppDiagnostics.LogException("Deferred interface refresh failed", task.Exception);
            }
        }, TaskScheduler.Default);
    }

    private void QuitApplication()
    {
        if (_isQuitting)
            return;

        if (!Dispatcher.CheckAccess())
        {
            Dispatcher.Invoke(QuitApplication);
            return;
        }

        _isQuitting = true;

        var tray = _tray;
        _tray = null;
        tray?.Dispose();

        var state = _state;
        _state = null;
        state?.Dispose();

        Shutdown();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _state?.Dispose();
        _tray?.Dispose();
        AppDiagnostics.Log("Exited");
        base.OnExit(e);
    }

    private void RegisterExceptionHandlers()
    {
        DispatcherUnhandledException += (_, args) =>
        {
            AppDiagnostics.LogException("Dispatcher unhandled exception", args.Exception);
            System.Windows.MessageBox.Show(
                $"RM-01 Internet Connector hit an unexpected error.\n\nLog: {AppDiagnostics.LogPath}\n\n{args.Exception.Message}",
                "RM-01 Internet Connector",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            args.Handled = true;
        };

        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            if (args.ExceptionObject is Exception ex)
            {
                AppDiagnostics.LogException("AppDomain unhandled exception", ex);
            }
            else
            {
                AppDiagnostics.Log($"AppDomain unhandled exception: {args.ExceptionObject}");
            }
        };

        TaskScheduler.UnobservedTaskException += (_, args) =>
        {
            AppDiagnostics.LogException("Unobserved task exception", args.Exception);
            args.SetObserved();
        };
    }
}
