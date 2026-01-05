import SwiftUI
import AppKit
import Combine

// MARK: - Utilities

/// Format network speed from bytes per second to human-readable string
func formatSpeed(_ bytesPerSecond: Double) -> String {
    if bytesPerSecond < 1024 {
        return String(format: "%.0fB/s", bytesPerSecond)
    } else if bytesPerSecond < 1024 * 1024 {
        return String(format: "%.1fKB/s", bytesPerSecond / 1024)
    } else if bytesPerSecond < 1024 * 1024 * 1024 {
        return String(format: "%.1fMB/s", bytesPerSecond / 1024 / 1024)
    } else {
        return String(format: "%.2fGB/s", bytesPerSecond / 1024 / 1024 / 1024)
    }
}

// MARK: - Localization

enum Language: String, CaseIterable {
    case english = "EN"
    case chinese = "CN"
}

@MainActor
class LocalizationManager: ObservableObject {
    static let shared = LocalizationManager()
    @Published var language: Language = .english
    
    private init() {}
    
    func localized(_ key: String) -> String {
        switch language {
        case .english: return en[key] ?? key
        case .chinese: return cn[key] ?? key
        }
    }
    
    private let en: [String: String] = [
        "windowTitle": "RM-01 Internet Connector",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "status_idle": "Ready",
        "status_connecting": "Connecting...",
        "status_disconnecting": "Disconnecting...",
        "status_connected": "Connected",
        "status_failed": "Failed",
        "interface_none": "No Device",
        "interface_found": "Device Ready",
        "hint_insert": "Please connect RM-01",
        // Menu bar items
        "menu_not_connected": "○ Not Connected",
        "menu_connected": "● Connected",
        "menu_connecting": "● Connecting...",
        "menu_failed": "● Connection Failed",
        "menu_connect": "Connect",
        "menu_disconnect": "Disconnect",
        "menu_reconnect": "Reconnect",
        "menu_open_panel": "Open Control Panel",
        "menu_quit": "Quit",
    ]
    
    private let cn: [String: String] = [
        "windowTitle": "RM-01 互联网连接助手",
        "connect": "立即连接",
        "disconnect": "断开连接",
        "status_idle": "准备就绪",
        "status_connecting": "正在连接...",
        "status_disconnecting": "正在断开...",
        "status_connected": "已连接",
        "status_failed": "连接失败",
        "interface_none": "未检测到设备",
        "interface_found": "设备已就绪",
        "hint_insert": "请连接 RM-01",
        // Menu bar items
        "menu_not_connected": "○ 未连接",
        "menu_connected": "● 已连接",
        "menu_connecting": "● 连接中...",
        "menu_failed": "● 连接失败",
        "menu_connect": "连接",
        "menu_disconnect": "断开连接",
        "menu_reconnect": "重新连接",
        "menu_open_panel": "打开控制面板",
        "menu_quit": "退出",
    ]
}

// MARK: - Network Speed Display

struct NetworkSpeedDisplay: View {
    @ObservedObject var appState: AppState
    
    var body: some View {
        if appState.connectionStatus == .connected {
            HStack(spacing: 8) {
                // Upload speed
                HStack(spacing: 4) {
                    Text("↑")
                        .font(.system(size: 14, weight: .medium))
                    Text(formatSpeed(appState.uploadSpeed))
                        .font(.system(size: 14, weight: .medium, design: .monospaced))
                }
                
                Text("|")
                    .foregroundColor(.secondary.opacity(0.5))
                
                // Download speed
                HStack(spacing: 4) {
                    Text("↓")
                        .font(.system(size: 14, weight: .medium))
                    Text(formatSpeed(appState.downloadSpeed))
                        .font(.system(size: 14, weight: .medium, design: .monospaced))
                }
            }
            .foregroundColor(.primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(Color.secondary.opacity(0.1))
            )
            .transition(.opacity.combined(with: .scale(scale: 0.95)))
        }
    }
}

// MARK: - Liquid Glass Button

struct LiquidGlassButton: View {
    let title: String
    let icon: String
    let action: () -> Void
    var isDestructive: Bool = false
    var isDisabled: Bool = false
    
    @State private var isHovered = false
    @State private var isPressed = false
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .medium))
                Text(title)
                    .fontWeight(.medium)
            }
            .frame(width: 180)
            .padding(.vertical, 14)
            .background(
                ZStack {
                    // Base gradient
                    if isDestructive {
                        // Soft coral/salmon red with better light feel
                        LinearGradient(
                            colors: [
                                Color(red: 0.95, green: 0.45, blue: 0.45),
                                Color(red: 0.85, green: 0.35, blue: 0.35)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    } else {
                        // Finder Green Style
                        LinearGradient(
                            colors: [
                                Color(red: 0.18, green: 0.80, blue: 0.28), // Light green
                                Color(red: 0.14, green: 0.70, blue: 0.22)  // Slightly darker green
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    }
                    
                    // Glossy highlight at top (Liquid effect)
                    VStack(spacing: 0) {
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.4),
                                Color.white.opacity(0.1),
                                Color.clear
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                        .frame(height: 20)
                        Spacer()
                    }
                    
                    // Inner light glow from bottom
                     VStack {
                        Spacer()
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.0),
                                Color.white.opacity(0.2)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                        .frame(height: 10)
                    }

                    // Hover effect
                    if isHovered && !isDisabled {
                        Color.white.opacity(0.1)
                    }
                    
                    // Press effect
                    if isPressed {
                        Color.black.opacity(0.1)
                    }
                }
            )
            .foregroundColor(.white)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.5),
                                Color.white.opacity(0.1),
                                Color.black.opacity(0.05)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(color: isDestructive ? Color(red: 0.95, green: 0.45, blue: 0.45).opacity(0.4) : Color.green.opacity(0.3), radius: 5, x: 0, y: 3)
            .shadow(color: Color.black.opacity(0.15), radius: 10, x: 0, y: 5)
            .scaleEffect(isPressed ? 0.98 : 1.0)
            .opacity(isDisabled ? 0.6 : 1.0)
        }
        .buttonStyle(.plain)
        .disabled(isDisabled)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    if !isDisabled {
                        withAnimation(.easeInOut(duration: 0.1)) {
                            isPressed = true
                        }
                    }
                }
                .onEnded { _ in
                    withAnimation(.easeInOut(duration: 0.1)) {
                        isPressed = false
                    }
                }
        )
    }
}

// MARK: - Main Window View

struct MainView: View {
    @ObservedObject var appState: AppState
    @ObservedObject var loc = LocalizationManager.shared
    
    var body: some View {
        VStack(spacing: 0) {
            // Header with language toggle
            HStack {
                Button(action: {
                    loc.language = loc.language == .english ? .chinese : .english
                }) {
                    Text(loc.language.rawValue)
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.accentColor.opacity(0.1))
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
                
                Spacer()
                
                Image(systemName: "network")
                    .font(.title2)
                    .foregroundColor(.accentColor)
                
                Text(loc.localized("windowTitle"))
                    .font(.headline)
                
                Spacer()
                
                // Invisible placeholder to balance the layout
                Text(loc.language.rawValue)
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .opacity(0)
            }
            .padding(.horizontal)
            .padding(.top, 16)
            .padding(.bottom, 12)
            
            Divider()
                .padding(.horizontal)
            
            // Spacer for vertical centering logic - Top Buffer
            Spacer()
                .frame(height: 15)
            
            // Status text
            VStack(spacing: 4) {
                Text(loc.localized(appState.statusKey))
                    .font(.title2)
                    .fontWeight(.medium)
                
                // Device info
                if let interface = appState.currentInterface {
                    HStack(spacing: 4) {
                        Image(systemName: "cable.connector")
                            .font(.caption)
                        Text(interface.device)
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                } else {
                    Text(loc.localized("hint_insert"))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .frame(height: 50) // Fixed height block
            
            // Gap 1: Reduced
            Spacer()
                .frame(height: 20)
            
            // RM-01 device image
            RM01DeviceImage(appState: appState)
            
            // Gap 2: Reduced
            Spacer()
                .frame(height: 20)
            
            // Network speed display (only when connected)
            NetworkSpeedDisplay(appState: appState)
            
            // Gap 3: Small spacing before button
            Spacer()
                .frame(height: 12)
            
            // Liquid Glass Action Button
            LiquidGlassButton(
                title: appState.isConnected ? loc.localized("disconnect") : loc.localized("connect"),
                icon: appState.isConnected ? "power" : "network",
                action: {
                    if appState.isConnected {
                        appState.disconnect()
                    } else {
                        appState.connect()
                    }
                },
                isDestructive: appState.isConnected,
                isDisabled: appState.isBusy
            )
            .padding(.horizontal, 30)
            
            Spacer()
                .frame(height: 16)
            
            // Copyright footer
            Text("Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.")
                .font(.system(size: 9))
                .foregroundColor(.secondary.opacity(0.6))
                .padding(.bottom, 12)
        }
        .frame(width: 315, height: 440)
    }
}

// MARK: - RM-01 Device Image

struct RM01DeviceImage: View {
    @ObservedObject var appState: AppState
    @State private var sweepOffset: CGFloat = -120
    @State private var glowOpacity: Double = 0.0
    @State private var isAnimating: Bool = false
    
    private let imageCache: NSImage = {
        let bundleName = "RM01InternetConnector_RM01InternetConnector"
        
        // Try multiple locations where the resource bundle might be
        let candidates: [URL?] = [
            Bundle.main.resourceURL?.appendingPathComponent("\(bundleName).bundle"),
            Bundle.main.bundleURL.appendingPathComponent("\(bundleName).bundle"),
            Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("Resources/\(bundleName).bundle"),
        ]
        
        // Try resource bundle first
        for candidate in candidates {
            if let url = candidate,
               let bundle = Bundle(url: url),
               let imageUrl = bundle.url(forResource: "body", withExtension: "png"),
               let image = NSImage(contentsOf: imageUrl) {
                return image
            }
        }
        
        // Try main bundle's Resources directly
        if let url = Bundle.main.url(forResource: "body", withExtension: "png"),
           let image = NSImage(contentsOf: url) {
            return image
        }
        
        // Fallback: create placeholder image
        let placeholder = NSImage(size: NSSize(width: 50, height: 70))
        placeholder.lockFocus()
        NSColor.gray.withAlphaComponent(0.3).setFill()
        NSBezierPath(roundedRect: NSRect(x: 0, y: 0, width: 50, height: 70), xRadius: 5, yRadius: 5).fill()
        placeholder.unlockFocus()
        return placeholder
    }()
    
    var body: some View {
        // Fixed display size: original image was 100x178
        // High-res image (300x534) provides 3x clarity at this display size
        let displayWidth: CGFloat = 100
        let displayHeight: CGFloat = 178
        
        ZStack {
            Image(nsImage: imageCache)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: displayWidth, height: displayHeight)
                .shadow(color: glowColor, radius: 15)
                .overlay(
                    ZStack {
                        if appState.isConnected && isAnimating {
                            Rectangle()
                                .fill(
                                    LinearGradient(
                                        gradient: Gradient(colors: [.clear, .white.opacity(0.5), .white.opacity(0.95), .white.opacity(0.5), .clear]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .frame(width: 80, height: displayHeight * 3)
                                .blur(radius: 15)
                                .rotationEffect(.degrees(25))
                                .offset(x: sweepOffset)
                        }
                    }
                    .frame(width: displayWidth, height: displayHeight)
                    .mask(
                        Image(nsImage: imageCache)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                    )
                )
        }
        .onAppear {
            updateAnimations(for: appState.connectionStatus)
        }
        .onReceive(appState.$connectionStatus) { newStatus in
            updateAnimations(for: newStatus)
        }
    }
    
    private var glowColor: Color {
        if appState.connectionStatus == .connected {
            return Color.green.opacity(glowOpacity)
        } else {
            return Color.red.opacity(glowOpacity)
        }
    }
    
    private func updateAnimations(for status: ConnectionStatus) {
        // Stop existing animations first
        withAnimation(.linear(duration: 0)) {
            sweepOffset = -120
            glowOpacity = 0
            isAnimating = false
        }
        
        // Small delay to ensure reset completes
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            if status == .connected {
                isAnimating = true
                withAnimation(.easeInOut(duration: 1.4)) {
                    sweepOffset = 120
                }
                // After sweep completes, start green glow
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) {
                    isAnimating = false
                    withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                        glowOpacity = 0.4
                    }
                }
            } else {
                withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                    glowOpacity = 0.4
                }
            }
        }
    }
}
