using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace RM01InternetConnector.Win;

public enum Language
{
    English,
    Chinese
}

public sealed class LocalizationManager : INotifyPropertyChanged
{
    private static readonly Lazy<LocalizationManager> Lazy = new(() => new LocalizationManager());
    public static LocalizationManager Instance => Lazy.Value;

    private Language _language = Language.English;

    public event PropertyChangedEventHandler? PropertyChanged;

    public Language CurrentLanguage
    {
        get => _language;
        set
        {
            if (_language == value) return;
            _language = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(CurrentLanguage)));
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(LanguageLabel)));
        }
    }

    public string LanguageLabel => CurrentLanguage == Language.English ? "EN" : "CN";

    public string Translate(string key)
    {
        return CurrentLanguage switch
        {
            Language.English => En.TryGetValue(key, out var vEn) ? vEn : key,
            Language.Chinese => Cn.TryGetValue(key, out var vCn) ? vCn : key,
            _ => key
        };
    }

    private LocalizationManager() { }

    private static readonly Dictionary<string, string> En = new(StringComparer.OrdinalIgnoreCase)
    {
        { "windowTitle", "RM-01 Internet Connector" },
        { "connect", "Connect" },
        { "disconnect", "Disconnect" },
        { "status_idle", "Ready" },
        { "status_connecting", "Connecting..." },
        { "status_disconnecting", "Disconnecting..." },
        { "status_connected", "Connected" },
        { "status_failed", "Failed" },
        { "interface_none", "No Device" },
        { "interface_found", "Device Ready" },
        { "hint_insert", "Please connect RM-01" },
        { "tray_open", "Open Control Panel" },
        { "tray_quit", "Quit" },
        { "tray_connect", "Connect" },
        { "tray_disconnect", "Disconnect" },
        { "tray_status_connected", "● Connected" },
        { "tray_status_connecting", "● Connecting..." },
        { "tray_status_failed", "● Failed" },
        { "tray_status_idle", "○ Idle" },
    };

    private static readonly Dictionary<string, string> Cn = new(StringComparer.OrdinalIgnoreCase)
    {
        { "windowTitle", "RM-01 互联网连接助手" },
        { "connect", "立即连接" },
        { "disconnect", "断开连接" },
        { "status_idle", "准备就绪" },
        { "status_connecting", "正在连接..." },
        { "status_disconnecting", "正在断开..." },
        { "status_connected", "已连接" },
        { "status_failed", "连接失败" },
        { "interface_none", "未检测到设备" },
        { "interface_found", "设备已就绪" },
        { "hint_insert", "请连接 RM-01" },
        { "tray_open", "打开控制面板" },
        { "tray_quit", "退出" },
        { "tray_connect", "连接" },
        { "tray_disconnect", "断开连接" },
        { "tray_status_connected", "● 已连接" },
        { "tray_status_connecting", "● 连接中..." },
        { "tray_status_failed", "● 连接失败" },
        { "tray_status_idle", "○ 未连接" },
    };
}





