using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;

namespace RM01InternetConnector.Win;

public sealed class MainViewModel : INotifyPropertyChanged
{
    private readonly AppState _state;
    private readonly LocalizationManager _loc;

    public event PropertyChangedEventHandler? PropertyChanged;

    public ICommand ToggleLanguageCommand { get; }
    public ICommand ConnectCommand { get; }

    public MainViewModel(AppState state, LocalizationManager loc)
    {
        _state = state;
        _loc = loc;

        _state.PropertyChanged += (_, _) => Refresh();
        _loc.PropertyChanged += (_, _) => Refresh();

        ToggleLanguageCommand = new RelayCommand(() =>
        {
            _loc.CurrentLanguage = _loc.CurrentLanguage == Language.English
                ? Language.Chinese
                : Language.English;
        });

        ConnectCommand = new RelayCommand(async () => await ToggleConnectAsync(), () => !_state.IsBusy);
    }

    public string WindowTitle => _loc.Translate("windowTitle");
    public string StatusText => _loc.Translate(_state.StatusKey);
    public string InterfaceText => _state.CurrentInterface?.Name ?? _loc.Translate("hint_insert");
    public string DeviceDescription => _state.CurrentInterface?.Description ?? string.Empty;
    public string ButtonText => _state.IsConnected ? _loc.Translate("disconnect") : _loc.Translate("connect");
    public string LanguageLabel => _loc.LanguageLabel;
    public bool IsBusy => _state.IsBusy;
    public bool IsConnected => _state.IsConnected;

    private async Task ToggleConnectAsync()
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

    private void Refresh([CallerMemberName] string? _ = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(StatusText)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(InterfaceText)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(DeviceDescription)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(ButtonText)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(LanguageLabel)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(WindowTitle)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(IsBusy)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(IsConnected)));
        if (ConnectCommand is RelayCommand cmd)
        {
            cmd.RaiseCanExecuteChanged();
        }
    }
}





















