import AppKit
import SwiftUI
import Foundation

@main
@MainActor
final class RM01InternetConnectorApp: NSObject, NSApplicationDelegate, NSWindowDelegate {
    static func main() {
        let app = NSApplication.shared
        let delegate = RM01InternetConnectorApp()
        app.delegate = delegate
        app.run()
    }

    private var statusItem: NSStatusItem!
    private var statusMenu: NSMenu!
    private var window: NSWindow?
    private let appState = AppState()
    
    // Menu items that need updating
    private var statusMenuItem: NSMenuItem!
    private var connectMenuItem: NSMenuItem!

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Setup main menu for keyboard shortcuts
        setupMainMenu()
        
        // Start as regular app (shows in Dock for proper minimize)
        NSApp.setActivationPolicy(.regular)
        
        // Setup App State
        appState.refreshInterface()
        
        // Setup Status Bar with Menu
        setupStatusBar()
        
        // Setup Main Window
        setupWindow()
        
        // Show window on launch
        showMainWindow()
    }
    
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false
    }
    
    private func setupMainMenu() {
        let mainMenu = NSMenu()
        
        // App menu
        let appMenuItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(NSMenuItem(title: "关于 RM-01 Internet Connector", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: ""))
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(NSMenuItem(title: "隐藏 RM-01", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h"))
        let hideOthersItem = NSMenuItem(title: "隐藏其他", action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
        hideOthersItem.keyEquivalentModifierMask = [.command, .option]
        appMenu.addItem(hideOthersItem)
        appMenu.addItem(NSMenuItem(title: "显示全部", action: #selector(NSApplication.unhideAllApplications(_:)), keyEquivalent: ""))
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(NSMenuItem(title: "退出 RM-01", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        appMenuItem.submenu = appMenu
        mainMenu.addItem(appMenuItem)
        
        // Window menu
        let windowMenuItem = NSMenuItem()
        let windowMenu = NSMenu(title: "窗口")
        windowMenu.addItem(NSMenuItem(title: "关闭窗口", action: #selector(closeWindow), keyEquivalent: "w"))
        windowMenu.addItem(NSMenuItem(title: "最小化", action: #selector(minimizeWindow), keyEquivalent: "m"))
        windowMenuItem.submenu = windowMenu
        mainMenu.addItem(windowMenuItem)
        
        NSApp.mainMenu = mainMenu
    }
    
    @objc private func closeWindow() {
        window?.close()
    }
    
    @objc private func minimizeWindow() {
        window?.miniaturize(nil)
    }

    private func setupStatusBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            if let image = Asset.statusIcon {
                image.isTemplate = true
                image.size = NSSize(width: 16, height: 16)
                button.image = image
            } else {
                button.image = NSImage(systemSymbolName: "network", accessibilityDescription: "RM-01")
            }
        }
        
        // Create native menu (like Shadowrocket)
        statusMenu = NSMenu()
        
        // Status display item (disabled, just for display)
        statusMenuItem = NSMenuItem(title: "○ 未连接", action: nil, keyEquivalent: "")
        statusMenuItem.isEnabled = false
        statusMenu.addItem(statusMenuItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Connect/Disconnect item
        connectMenuItem = NSMenuItem(title: "连接", action: #selector(toggleConnection), keyEquivalent: "")
        connectMenuItem.target = self
        statusMenu.addItem(connectMenuItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Open control panel
        let openItem = NSMenuItem(title: "打开控制面板", action: #selector(openControlPanel), keyEquivalent: "o")
        openItem.target = self
        statusMenu.addItem(openItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Quit
        let quitItem = NSMenuItem(title: "退出", action: #selector(quitApp), keyEquivalent: "q")
        quitItem.target = self
        statusMenu.addItem(quitItem)
        
        statusItem.menu = statusMenu
        
        // Observe app state changes
        Task { @MainActor in
            for await _ in appState.$connectionStatus.values {
                updateMenuItems()
            }
        }
    }
    
    private func updateMenuItems() {
        switch appState.connectionStatus {
        case .connected:
            statusMenuItem.title = "● 已连接"
            // Set green color using attributed string
            let greenDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemGreen])
            greenDot.append(NSAttributedString(string: "已连接"))
            statusMenuItem.attributedTitle = greenDot
            connectMenuItem.title = "断开连接"
            connectMenuItem.isEnabled = true
        case .connecting:
            statusMenuItem.title = "● 连接中..."
            let yellowDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemYellow])
            yellowDot.append(NSAttributedString(string: "连接中..."))
            statusMenuItem.attributedTitle = yellowDot
            connectMenuItem.title = "连接中..."
            connectMenuItem.isEnabled = false
        case .failed:
            statusMenuItem.title = "● 连接失败"
            let redDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemRed])
            redDot.append(NSAttributedString(string: "连接失败"))
            statusMenuItem.attributedTitle = redDot
            connectMenuItem.title = "重新连接"
            connectMenuItem.isEnabled = true
        case .idle:
            statusMenuItem.title = "○ 未连接"
            statusMenuItem.attributedTitle = nil
            connectMenuItem.title = "连接"
            connectMenuItem.isEnabled = true
        }
    }
    
    @objc private func toggleConnection() {
        if appState.isConnected {
            appState.disconnect()
        } else {
            appState.connect()
        }
    }
    
    @objc private func openControlPanel() {
        showMainWindow()
    }
    
    @objc private func quitApp() {
        NSApp.terminate(nil)
    }

    private func setupWindow() {
        // Create standard macOS window with normal title bar
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 315, height: 440),
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "RM-01 Internet Connector"
        window.isReleasedWhenClosed = false
        window.delegate = self
        
        // Set SwiftUI Content
        window.contentView = NSHostingView(rootView: MainView(appState: appState))
        
        self.window = window
    }
    
    // MARK: - NSWindowDelegate
    
    func windowWillClose(_ notification: Notification) {
        // Hide from Dock when window closes, but stay in menu bar
        NSApp.setActivationPolicy(.accessory)
    }

    private func showMainWindow() {
        guard let window = window else { return }
        // Show in Dock when window is visible (for proper minimize animation)
        NSApp.setActivationPolicy(.regular)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    
    // MARK: - Assets
    enum Asset {
        static var statusIcon: NSImage? {
            if let url = Bundle.module.url(forResource: "statusIcon", withExtension: "png"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            return nil
        }
        
        static var appIcon: NSImage? {
            if let url = Bundle.module.url(forResource: "AppIcon", withExtension: "icns"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            return nil
        }
        
        static var bodyImage: NSImage? {
            if let url = Bundle.module.url(forResource: "body", withExtension: "png"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            return nil
        }
    }
}

// MARK: - App State & Logic

enum ConnectionStatus: Equatable {
    case idle
    case connecting
    case connected
    case failed
}

/// Custom error types for better error handling
enum RM01Error: LocalizedError {
    case noInterfaceFound
    case scriptExecutionFailed(String)
    case userCancelled
    
    var errorDescription: String? {
        switch self {
        case .noInterfaceFound:
            return "No AX88179A interface found"
        case .scriptExecutionFailed(let message):
            return "Script failed: \(message)"
        case .userCancelled:
            return "User cancelled the operation"
        }
    }
}

@MainActor
class AppState: ObservableObject {
    @Published var connectionStatus: ConnectionStatus = .idle
    @Published var currentInterface: NetworkInterface?
    @Published var statusKey: String = "status_idle"
    @Published var isBusy: Bool = false
    @Published var lastError: Error?
    
    var isConnected: Bool {
        connectionStatus == .connected
    }
    
    func connect() {
        guard !isBusy else { return }
        isBusy = true
        lastError = nil
        connectionStatus = .connecting
        statusKey = "status_connecting"
        
        Task {
            await performConnect()
        }
    }
    
    func disconnect() {
        guard !isBusy else { return }
        isBusy = true
        lastError = nil
        statusKey = "status_disconnecting"
        connectionStatus = .connecting // Show visual feedback
        
        Task {
            await performDisconnect()
        }
    }
    
    func refreshInterface() {
        Task {
            let interfaces = await Task.detached {
                InterfaceDetector.detectAX88179A()
            }.value
            currentInterface = interfaces.first
        }
    }
    
    private func performConnect() async {
        // Detect interfaces on background thread
        let interfaces = await Task.detached(priority: .userInitiated) {
            InterfaceDetector.detectAX88179A()
        }.value
        
        guard let iface = interfaces.first else {
            self.statusKey = "interface_none"
            self.connectionStatus = .failed
            self.lastError = RM01Error.noInterfaceFound
            self.isBusy = false
            return
        }
        
        self.currentInterface = iface
        
        // Run privileged script on background thread
        let script = ShellScripts.enableSharing(interface: iface.device)
        let result = await Task.detached(priority: .userInitiated) {
            self.runPrivileged(script: script)
        }.value
        
        switch result {
        case .success:
            self.statusKey = "status_connected"
            self.connectionStatus = .connected
        case .failure(let error):
            self.lastError = error
            // Check if user cancelled
            if (error as NSError).code == -128 {
                self.statusKey = "status_idle"
                self.connectionStatus = .idle
            } else {
                self.statusKey = "status_failed"
                self.connectionStatus = .failed
            }
        }
        self.isBusy = false
    }
    
    private func performDisconnect() async {
        let script = ShellScripts.disableSharing()
        let result = await Task.detached(priority: .userInitiated) {
            self.runPrivileged(script: script)
        }.value
        
        switch result {
        case .success:
            self.statusKey = "status_idle"
            self.connectionStatus = .idle
            self.currentInterface = nil
        case .failure(let error):
            self.lastError = error
            // Check if user cancelled
            if (error as NSError).code == -128 {
                // Keep current status
                self.statusKey = "status_connected"
                self.connectionStatus = .connected
            } else {
                self.statusKey = "status_failed"
                self.connectionStatus = .failed
            }
        }
        self.isBusy = false
    }
    
    private nonisolated func runPrivileged(script: String) -> Result<Void, Error> {
        let escapedScript = script.escapingForAppleScript()
        let appleScript = """
        do shell script "\(escapedScript)" with administrator privileges
        """

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", appleScript]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            process.waitUntilExit()
            
            if process.terminationStatus == 0 {
                return .success(())
            } else {
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                let message = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? "Unknown error"
                return .failure(NSError(
                    domain: "RM01",
                    code: Int(process.terminationStatus),
                    userInfo: [NSLocalizedDescriptionKey: message]
                ))
            }
        } catch {
            return .failure(error)
        }
    }
}

// MARK: - Interface Detection

struct NetworkInterface: Equatable, Sendable {
    let hardwarePort: String
    let device: String
    let mac: String
}

enum InterfaceDetector {
    /// Known keywords that identify AX88179A USB Ethernet adapters
    private static let knownIdentifiers = [
        "ax88179",
        "usb 10/100/1000 lan",
        "usb ethernet",
        "usb gigabit ethernet"
    ]
    
    /// Detects AX88179A USB Ethernet adapters
    static func detectAX88179A() -> [NetworkInterface] {
        let result = runCommand(["/usr/sbin/networksetup", "-listallhardwareports"])
        guard case let .success(output) = result else { return [] }

        var interfaces: [NetworkInterface] = []
        var currentPort: String?
        var currentDevice: String?
        var currentMac: String?

        let lines = output.components(separatedBy: .newlines)
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            if trimmed.hasPrefix("Hardware Port:") {
                // Save previous interface if complete
                if let port = currentPort, let device = currentDevice {
                    if isAX88179A(port: port) {
                        interfaces.append(NetworkInterface(
                            hardwarePort: port,
                            device: device,
                            mac: currentMac ?? "N/A"
                        ))
                    }
                }
                
                currentPort = trimmed
                    .replacingOccurrences(of: "Hardware Port:", with: "")
                    .trimmingCharacters(in: .whitespaces)
                currentDevice = nil
                currentMac = nil
                
            } else if trimmed.hasPrefix("Device:") {
                currentDevice = trimmed
                    .replacingOccurrences(of: "Device:", with: "")
                    .trimmingCharacters(in: .whitespaces)
                
            } else if trimmed.hasPrefix("Ethernet Address:") {
                currentMac = trimmed
                    .replacingOccurrences(of: "Ethernet Address:", with: "")
                    .trimmingCharacters(in: .whitespaces)
            }
        }
        
        // Don't forget the last interface
        if let port = currentPort, let device = currentDevice {
            if isAX88179A(port: port) {
                interfaces.append(NetworkInterface(
                    hardwarePort: port,
                    device: device,
                    mac: currentMac ?? "N/A"
                ))
            }
        }

        return interfaces
    }
    
    /// Checks if the hardware port name matches known AX88179A identifiers
    private static func isAX88179A(port: String) -> Bool {
        let lowercased = port.lowercased()
        return knownIdentifiers.contains { lowercased.contains($0) }
    }

    private static func runCommand(_ arguments: [String]) -> Result<String, Error> {
        guard !arguments.isEmpty else {
            return .failure(NSError(domain: "RM01", code: -1, userInfo: [NSLocalizedDescriptionKey: "Empty command"]))
        }
        
        let process = Process()
        process.executableURL = URL(fileURLWithPath: arguments[0])
        process.arguments = Array(arguments.dropFirst())
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            process.waitUntilExit()
            
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let output = String(data: data, encoding: .utf8) ?? ""
            
            if process.terminationStatus == 0 {
                return .success(output)
            } else {
                return .failure(NSError(
                    domain: "RM01",
                    code: Int(process.terminationStatus),
                    userInfo: [NSLocalizedDescriptionKey: output.isEmpty ? "Command failed" : output]
                ))
            }
        } catch {
            return .failure(error)
        }
    }
}

// MARK: - Shell scripts

enum ShellScripts {
    // Applies static IP/DNS and toggles Internet Sharing restart.
    static func enableSharing(interface: String) -> String {
        """
        IFACE="\(interface)"
        IP="10.10.99.100"
        MASK="255.255.255.0"
        GW="10.10.99.100"
        DNS="8.8.8.8"

        /usr/sbin/networksetup -setmanual "$IFACE" "$IP" "$MASK" "$GW"
        /usr/sbin/networksetup -setdnsservers "$IFACE" "$DNS"

        # Configure Internet Sharing (Wi-Fi -> AX88179A)
        /bin/launchctl unload /System/Library/LaunchDaemons/com.apple.InternetSharing.plist 2>/dev/null || true
        /usr/bin/defaults write /Library/Preferences/SystemConfiguration/com.apple.nat NAT -dict Enabled -int 1
        /usr/bin/defaults write /Library/Preferences/SystemConfiguration/com.apple.nat SharingNetworkNumberStart "$IP"
        /usr/bin/defaults write /Library/Preferences/SystemConfiguration/com.apple.nat SharingNetworkMask "$MASK"

        # Minimal preferences.plist toggles; may vary by macOS version.
        /usr/libexec/PlistBuddy -c "Set :sharing:InternetSharing:InternetSharingEnabled 1" /Library/Preferences/SystemConfiguration/preferences.plist 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :sharing:InternetSharing:devices:0 $IFACE" /Library/Preferences/SystemConfiguration/preferences.plist 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :sharing:InternetSharing:sharefrom:0 Wi-Fi" /Library/Preferences/SystemConfiguration/preferences.plist 2>/dev/null || true

        /bin/launchctl load /System/Library/LaunchDaemons/com.apple.InternetSharing.plist
        """
    }

    static func disableSharing() -> String {
        """
        /bin/launchctl unload /System/Library/LaunchDaemons/com.apple.InternetSharing.plist 2>/dev/null || true
        /usr/bin/defaults write /Library/Preferences/SystemConfiguration/com.apple.nat NAT -dict Enabled -int 0
        """
    }
}

// MARK: - Utilities

private extension String {
    func escapingForAppleScript() -> String {
        self
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: "\\\n")
    }
}
