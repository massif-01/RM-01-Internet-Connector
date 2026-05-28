using System;
using System.IO;

namespace RM01InternetConnector.Win;

internal static class AppDiagnostics
{
    private static readonly object Gate = new();

    public static string LogPath { get; } = ResolveLogPath();

    public static void Log(string message)
    {
        Write(message);
    }

    public static void LogException(string context, Exception exception)
    {
        Write($"{context}: {exception}");
    }

    private static void Write(string message)
    {
        try
        {
            lock (Gate)
            {
                Directory.CreateDirectory(Path.GetDirectoryName(LogPath)!);
                File.AppendAllText(
                    LogPath,
                    $"[{DateTimeOffset.Now:yyyy-MM-dd HH:mm:ss zzz}] {message}{Environment.NewLine}");
            }
        }
        catch
        {
            // Logging must never prevent startup.
        }
    }

    private static string ResolveLogPath()
    {
        try
        {
            var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            if (!string.IsNullOrWhiteSpace(localAppData))
            {
                return Path.Combine(localAppData, "RM01InternetConnector", "app.log");
            }
        }
        catch
        {
            // Fall back below.
        }

        return Path.Combine(AppContext.BaseDirectory, "RM01InternetConnector.log");
    }
}
