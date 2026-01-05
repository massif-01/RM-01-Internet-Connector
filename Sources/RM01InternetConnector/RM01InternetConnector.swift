import AppKit
import SwiftUI
import Foundation
import Darwin

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
    private let loc = LocalizationManager.shared
    private var speedMonitor: NetworkSpeedMonitor?
    
    // Menu items that need updating
    private var speedMenuItem: NSMenuItem!
    private var statusMenuItem: NSMenuItem!
    private var connectMenuItem: NSMenuItem!
    private var openPanelMenuItem: NSMenuItem!
    private var quitMenuItem: NSMenuItem!

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
        
        // Speed display item (hidden when not connected)
        speedMenuItem = NSMenuItem(title: "↑0B/s | ↓0B/s", action: #selector(doNothing), keyEquivalent: "")
        speedMenuItem.target = self
        speedMenuItem.isHidden = true
        statusMenu.addItem(speedMenuItem)
        
        // Separator after speed (hidden when not connected)
        let speedSeparator = NSMenuItem.separator()
        speedSeparator.tag = 999  // Tag to identify this separator
        statusMenu.addItem(speedSeparator)
        
        // Status display item (disabled, just for display)
        statusMenuItem = NSMenuItem(title: loc.localized("menu_not_connected"), action: nil, keyEquivalent: "")
        statusMenuItem.isEnabled = false
        statusMenu.addItem(statusMenuItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Connect/Disconnect item
        connectMenuItem = NSMenuItem(title: loc.localized("menu_connect"), action: #selector(toggleConnection), keyEquivalent: "")
        connectMenuItem.target = self
        statusMenu.addItem(connectMenuItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Open control panel
        openPanelMenuItem = NSMenuItem(title: loc.localized("menu_open_panel"), action: #selector(openControlPanel), keyEquivalent: "o")
        openPanelMenuItem.target = self
        statusMenu.addItem(openPanelMenuItem)
        
        statusMenu.addItem(NSMenuItem.separator())
        
        // Quit
        quitMenuItem = NSMenuItem(title: loc.localized("menu_quit"), action: #selector(quitApp), keyEquivalent: "q")
        quitMenuItem.target = self
        statusMenu.addItem(quitMenuItem)
        
        statusItem.menu = statusMenu
        
        // Observe app state changes
        Task { @MainActor in
            for await _ in appState.$connectionStatus.values {
                updateMenuItems()
                updateSpeedMonitoring()
            }
        }
        
        // Observe speed changes
        Task { @MainActor in
            for await _ in appState.$uploadSpeed.values {
                updateStatusBar()
            }
        }
        
        Task { @MainActor in
            for await _ in appState.$downloadSpeed.values {
                updateStatusBar()
            }
        }
        
        // Observe language changes
        Task { @MainActor in
            for await _ in loc.$language.values {
                recreateMenuItems()
            }
        }
    }
    
    private func updateSpeedMonitoring() {
        // Stop existing monitor
        speedMonitor?.stop()
        speedMonitor = nil
        
        // Start monitoring only when connected and interface is available
        if appState.connectionStatus == .connected, let interface = appState.currentInterface {
            speedMonitor = NetworkSpeedMonitor(interfaceName: interface.device) { [weak self] macUpload, macDownload in
                Task { @MainActor in
                    guard let self = self else { return }
                    // Swap: Mac's TX (upload) = RM-01's download, Mac's RX (download) = RM-01's upload
                    self.appState.uploadSpeed = macDownload    // RM-01 upload = Mac RX
                    self.appState.downloadSpeed = macUpload    // RM-01 download = Mac TX
                }
            }
            speedMonitor?.start()
        } else {
            // Clear speed display when not connected
            appState.uploadSpeed = 0
            appState.downloadSpeed = 0
        }
    }
    
    private func updateStatusBar() {
        // Find the speed separator by tag
        let speedSeparator = statusMenu.item(withTag: 999)
        
        if appState.connectionStatus == .connected {
            let uploadStr = formatSpeed(appState.uploadSpeed)
            let downloadStr = formatSpeed(appState.downloadSpeed)
            speedMenuItem.title = "↑\(uploadStr)   |   ↓\(downloadStr)"
            speedMenuItem.isHidden = false
            speedSeparator?.isHidden = false
        } else {
            speedMenuItem.isHidden = true
            speedSeparator?.isHidden = true
        }
        
        // Force menu to update while open
        statusMenu.update()
    }
    
    
    private func updateMenuItems() {
        switch appState.connectionStatus {
        case .connected:
            let text = loc.localized("menu_connected")
            statusMenuItem.title = text
            // Set green color using attributed string
            let greenDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemGreen])
            greenDot.append(NSAttributedString(string: text.dropFirst(2).trimmingCharacters(in: .whitespaces)))
            statusMenuItem.attributedTitle = greenDot
            connectMenuItem.title = loc.localized("menu_disconnect")
            connectMenuItem.isEnabled = true
        case .connecting:
            let text = loc.localized("menu_connecting")
            statusMenuItem.title = text
            let yellowDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemYellow])
            yellowDot.append(NSAttributedString(string: text.dropFirst(2).trimmingCharacters(in: .whitespaces)))
            statusMenuItem.attributedTitle = yellowDot
            connectMenuItem.title = text
            connectMenuItem.isEnabled = false
        case .failed:
            let text = loc.localized("menu_failed")
            statusMenuItem.title = text
            let redDot = NSMutableAttributedString(string: "● ", attributes: [.foregroundColor: NSColor.systemRed])
            redDot.append(NSAttributedString(string: text.dropFirst(2).trimmingCharacters(in: .whitespaces)))
            statusMenuItem.attributedTitle = redDot
            connectMenuItem.title = loc.localized("menu_reconnect")
            connectMenuItem.isEnabled = true
        case .idle:
            statusMenuItem.title = loc.localized("menu_not_connected")
            statusMenuItem.attributedTitle = nil
            connectMenuItem.title = loc.localized("menu_connect")
            connectMenuItem.isEnabled = true
        }
    }
    
    private func recreateMenuItems() {
        // Update all menu item titles when language changes
        openPanelMenuItem.title = loc.localized("menu_open_panel")
        quitMenuItem.title = loc.localized("menu_quit")
        
        // Update status-dependent items
        updateMenuItems()
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
    
    @objc private func doNothing() {
        // Empty action to make menu item appear enabled (black text)
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
        window.titleVisibility = .hidden  // Hide title text in title bar
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
        /// Custom resource bundle locator that works both in SPM development and standalone .app
        private static let resourceBundle: Bundle? = {
            let bundleName = "RM01InternetConnector_RM01InternetConnector"
            
            // Try multiple locations where the resource bundle might be
            let candidates = [
                // 1. Inside .app bundle's Resources directory
                Bundle.main.resourceURL?.appendingPathComponent("\(bundleName).bundle"),
                // 2. Next to the executable (SPM build location)
                Bundle.main.bundleURL.appendingPathComponent("\(bundleName).bundle"),
                // 3. In parent's Resources (for nested bundles)
                Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("Resources/\(bundleName).bundle"),
                // 4. Directly in Resources
                Bundle.main.resourceURL,
            ]
            
            for candidate in candidates {
                if let url = candidate, let bundle = Bundle(url: url) {
                    return bundle
                }
            }
            
            // Fallback to main bundle (resources might be directly in Resources folder)
            return Bundle.main
        }()
        
        static var statusIcon: NSImage? {
            // Create an NSImage and add all resolution variants as representations
            // This allows macOS to automatically select the right resolution
            let image = NSImage(size: NSSize(width: 18, height: 18))
            
            // Try to load from resource bundle first, then main bundle
            let bundles = [resourceBundle, Bundle.main].compactMap { $0 }
            
            for bundle in bundles {
                var foundAny = false
                
                // Load @1x (18x18)
                if let url = bundle.url(forResource: "statusIcon", withExtension: "png"),
                   let rep = NSImageRep(contentsOf: url) {
                    rep.size = NSSize(width: 18, height: 18)
                    image.addRepresentation(rep)
                    foundAny = true
                }
                
                // Load @2x (36x36)
                if let url = bundle.url(forResource: "statusIcon@2x", withExtension: "png"),
                   let rep = NSImageRep(contentsOf: url) {
                    rep.size = NSSize(width: 18, height: 18) // Point size, not pixel size
                    image.addRepresentation(rep)
                    foundAny = true
                }
                
                // Load @3x (54x54)
                if let url = bundle.url(forResource: "statusIcon@3x", withExtension: "png"),
                   let rep = NSImageRep(contentsOf: url) {
                    rep.size = NSSize(width: 18, height: 18) // Point size, not pixel size
                    image.addRepresentation(rep)
                    foundAny = true
                }
                
                if foundAny {
                    return image
                }
            }
            
            return nil
        }
        
        static var appIcon: NSImage? {
            if let bundle = resourceBundle,
               let url = bundle.url(forResource: "AppIcon", withExtension: "icns"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            if let url = Bundle.main.url(forResource: "AppIcon", withExtension: "icns"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            return nil
        }
        
        static var bodyImage: NSImage? {
            if let bundle = resourceBundle,
               let url = bundle.url(forResource: "body", withExtension: "png"),
               let image = NSImage(contentsOf: url) {
                return image
            }
            if let url = Bundle.main.url(forResource: "body", withExtension: "png"),
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
    
    // Network speed (RM-01 perspective: upload = Mac RX, download = Mac TX)
    @Published var uploadSpeed: Double = 0      // RM-01 upload (Mac RX)
    @Published var downloadSpeed: Double = 0    // RM-01 download (Mac TX)
    
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
        // networksetup requires Hardware Port name, not device name (e.g., "AX88179A 5" not "en16")
        let script = ShellScripts.enableSharing(interface: iface.hardwarePort, device: iface.device)
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
        // Save interface info before clearing it
        guard let iface = currentInterface else {
            self.statusKey = "status_idle"
            self.connectionStatus = .idle
            self.isBusy = false
            return
        }
        
        let script = ShellScripts.disableSharing(interface: iface.hardwarePort, device: iface.device)
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
    /// Known keywords that identify AX88179A USB Ethernet adapters (RM-01 uses AX88179A chip)
    /// Only match AX88179 to avoid matching other generic USB ethernet adapters
    private static let knownIdentifiers = [
        "ax88179"
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
    // Applies static IP/DNS and enables NAT for Internet Sharing (Wi-Fi -> AX88179A)
    static func enableSharing(interface: String, device: String) -> String {
        """
        IFACE="\(interface)"
        DEVICE="\(device)"
        IP="10.10.99.100"
        MASK="255.255.255.0"
        GW="10.10.99.100"
        DNS="8.8.8.8"
        NAT_CONF="/tmp/rm01_nat.conf"
        
        # Find the active internet interface (works with Wi-Fi, Ethernet, iPhone USB, etc.)
        # Excludes VPN (utun) and link-local routes, finds the physical interface with a real gateway
        INET_DEVICE=$(netstat -rn | grep "^default" | grep -v "utun" | grep -v "link#" | grep -v "$DEVICE" | head -1 | awk '{print $NF}')
        if [ -z "$INET_DEVICE" ]; then
            # Fallback to Wi-Fi
            INET_DEVICE=$(/usr/sbin/networksetup -listallhardwareports | awk '/Wi-Fi/{getline; print $2}')
        fi
        if [ -z "$INET_DEVICE" ]; then
            # Last resort fallback
            INET_DEVICE="en0"
        fi

        # Check if network service exists, if not create it
        if ! /usr/sbin/networksetup -listallnetworkservices | grep -q "^$IFACE$"; then
            /usr/sbin/networksetup -createnetworkservice "$IFACE" "$DEVICE"
        fi

        # Set static IP and DNS for the RM-01 interface
        /usr/sbin/networksetup -setmanual "$IFACE" "$IP" "$MASK" "$GW"
        /usr/sbin/networksetup -setdnsservers "$IFACE" "$DNS"

        # Enable IP forwarding
        /usr/sbin/sysctl -w net.inet.ip.forwarding=1

        # Create NAT rule file (share internet connection to AX88179A)
        echo "nat on $INET_DEVICE from $DEVICE:network to any -> ($INET_DEVICE)" > "$NAT_CONF"
        
        # Load NAT rules using pfctl
        /sbin/pfctl -d 2>/dev/null || true
        /sbin/pfctl -F all 2>/dev/null || true
        /sbin/pfctl -f "$NAT_CONF" -e 2>/dev/null
        
        # Cleanup
        rm -f "$NAT_CONF"
        """
    }

    static func disableSharing(interface: String, device: String) -> String {
        """
        IFACE="\(interface)"
        DEVICE="\(device)"
        
        # Disable IP forwarding
        /usr/sbin/sysctl -w net.inet.ip.forwarding=0
        
        # Flush NAT rules and disable pfctl
        /sbin/pfctl -d 2>/dev/null || true
        /sbin/pfctl -F all 2>/dev/null || true
        
        # Restore DHCP for the interface
        /usr/sbin/networksetup -setdhcp "$IFACE"
        
        # Clear DNS settings (empty = use DHCP)
        /usr/sbin/networksetup -setdnsservers "$IFACE" empty
        
        # Refresh the interface to trigger DHCP request
        /sbin/ifconfig "$DEVICE" down 2>/dev/null || true
        sleep 1
        /sbin/ifconfig "$DEVICE" up 2>/dev/null || true
        """
    }
}

// MARK: - Network Speed Monitor

@MainActor
class NetworkSpeedMonitor {
    private let interfaceName: String
    private var timer: Timer?
    private var lastRxBytes: UInt64 = 0
    private var lastTxBytes: UInt64 = 0
    private var lastUpdateTime: Date?
    private let callback: (Double, Double) -> Void
    
    init(interfaceName: String, callback: @escaping (Double, Double) -> Void) {
        self.interfaceName = interfaceName
        self.callback = callback
    }
    
    func start() {
        // Initial sample
        if let (rx, tx) = getInterfaceBytes() {
            lastRxBytes = rx
            lastTxBytes = tx
            lastUpdateTime = Date()
        }
        
        // Update every 1 second
        timer = Timer(timeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.update()
            }
        }
        timer?.tolerance = 0.1
        // Add to common mode so it fires even when menu is open (tracking mode)
        if let timer = timer {
            RunLoop.main.add(timer, forMode: .common)
        }
    }
    
    func stop() {
        timer?.invalidate()
        timer = nil
    }
    
    private func update() {
        guard let (currentRx, currentTx) = getInterfaceBytes(),
              let lastTime = lastUpdateTime else {
            return
        }
        
        let now = Date()
        let timeDiff = now.timeIntervalSince(lastTime)
        
        guard timeDiff > 0 else { return }
        
        // Calculate bytes per second
        let rxDiff = Double(currentRx > lastRxBytes ? currentRx - lastRxBytes : 0)
        let txDiff = Double(currentTx > lastTxBytes ? currentTx - lastTxBytes : 0)
        
        let downloadSpeed = rxDiff / timeDiff
        let uploadSpeed = txDiff / timeDiff
        
        // Update for next iteration
        lastRxBytes = currentRx
        lastTxBytes = currentTx
        lastUpdateTime = now
        
        // Callback with speeds
        callback(uploadSpeed, downloadSpeed)
    }
    
    private func getInterfaceBytes() -> (rx: UInt64, tx: UInt64)? {
        var ifaddr: UnsafeMutablePointer<ifaddrs>?
        
        guard getifaddrs(&ifaddr) == 0 else {
            return nil
        }
        
        defer { freeifaddrs(ifaddr) }
        
        var ptr = ifaddr
        while ptr != nil {
            defer { ptr = ptr?.pointee.ifa_next }
            
            guard let interface = ptr else { continue }
            let name = String(cString: interface.pointee.ifa_name)
            
            if name == interfaceName {
                // Check if this is AF_LINK (link layer address)
                if interface.pointee.ifa_addr.pointee.sa_family == UInt8(AF_LINK) {
                    // Cast to if_data structure
                    let data = interface.pointee.ifa_data.assumingMemoryBound(to: if_data.self)
                    let rxBytes = UInt64(data.pointee.ifi_ibytes)
                    let txBytes = UInt64(data.pointee.ifi_obytes)
                    return (rxBytes, txBytes)
                }
            }
        }
        
        return nil
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
