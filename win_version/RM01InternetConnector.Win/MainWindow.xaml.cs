using System;
using System.ComponentModel;
using System.Windows;

namespace RM01InternetConnector.Win;

public partial class MainWindow : Window
{
    private readonly AppState _state;
    private readonly LocalizationManager _loc;
    private readonly Action _reopenAction;
    private readonly MainViewModel _viewModel;

    public MainWindow(AppState state, LocalizationManager loc, Action reopenAction)
    {
        _state = state;
        _loc = loc;
        _reopenAction = reopenAction;

        InitializeComponent();

        _viewModel = new MainViewModel(state, loc);
        DataContext = _viewModel;
        UpdateTitle();

        _loc.PropertyChanged += (_, _) => UpdateTitle();
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        base.OnClosing(e);
        // 关闭窗口但保持托盘程序运行
        e.Cancel = true;
        Hide();
    }

    private void UpdateTitle()
    {
        Title = _viewModel.WindowTitle;
    }
}





















