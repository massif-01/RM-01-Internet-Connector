using System;
using System.ComponentModel;
using System.Windows;

namespace RM01InternetConnector.Win;

public partial class MainWindow : Window
{
    private readonly AppState _state;
    private readonly LocalizationManager _loc;
    private readonly Func<bool> _hasTray;
    private readonly MainViewModel _viewModel;
    private Exception? _lastShownError;

    public MainWindow(AppState state, LocalizationManager loc, Func<bool> hasTray)
    {
        _state = state;
        _loc = loc;
        _hasTray = hasTray;

        InitializeComponent();

        _viewModel = new MainViewModel(state, loc);
        DataContext = _viewModel;
        UpdateTitle();

        _loc.PropertyChanged += (_, _) => UpdateTitle();
        _state.PropertyChanged += OnStatePropertyChanged;
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        base.OnClosing(e);
        if (_hasTray())
        {
            // 关闭窗口但保持托盘程序运行
            e.Cancel = true;
            Hide();
        }
    }

    private void UpdateTitle()
    {
        Title = _viewModel.WindowTitle;
    }

    private void OnStatePropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName != nameof(AppState.LastError))
            return;

        var error = _state.LastError;
        if (error == null || ReferenceEquals(error, _lastShownError))
            return;

        _lastShownError = error;
        if (!Dispatcher.CheckAccess())
        {
            Dispatcher.InvokeAsync(() => ShowConnectionError(error));
            return;
        }

        ShowConnectionError(error);
    }

    private void ShowConnectionError(Exception error)
    {
        var helpKey = IsWindowsNatUnavailable(error)
            ? "winnat_unavailable_help"
            : "generic_connection_error_help";
        var message = string.Join(
            Environment.NewLine,
            _loc.Translate(helpKey),
            AppDiagnostics.LogPath,
            string.Empty,
            error.Message);

        var title = _loc.Translate("connection_error_title");
        if (IsVisible)
        {
            System.Windows.MessageBox.Show(
                this,
                message,
                title,
                System.Windows.MessageBoxButton.OK,
                System.Windows.MessageBoxImage.Error);
            return;
        }

        System.Windows.MessageBox.Show(
            message,
            title,
            System.Windows.MessageBoxButton.OK,
            System.Windows.MessageBoxImage.Error);
    }

    private static bool IsWindowsNatUnavailable(Exception error)
    {
        var text = error.ToString();
        return ContainsIgnoreCase(text, "Windows NAT provider is not available")
            || ContainsIgnoreCase(text, "Windows NAT command is not available")
            || ContainsIgnoreCase(text, "MSFT_NetNat")
            || ContainsIgnoreCase(text, "New-NetNat")
            || ContainsIgnoreCase(text, "Get-NetNat")
            || ContainsIgnoreCase(text, "0x80041010");
    }

    private static bool ContainsIgnoreCase(string text, string value)
    {
        return text.IndexOf(value, StringComparison.OrdinalIgnoreCase) >= 0;
    }
}



