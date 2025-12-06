import SwiftUI
import AppKit
import Combine

// MARK: - Localization

enum Language: String, CaseIterable {
    case english = "EN"
    case chinese = "CN"
}

@MainActor
class LocalizationManager: ObservableObject {
    static let shared = LocalizationManager()
    @Published var language: Language = .chinese
    
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
    ]
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
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                ZStack {
                    // Base gradient
                    if isDestructive {
                        // Keep destructive style or make it red? Keeping it dark gray/reddish for disconnect
                        LinearGradient(
                            colors: [
                                Color(red: 0.8, green: 0.2, blue: 0.2),
                                Color(red: 0.6, green: 0.1, blue: 0.1)
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
            .shadow(color: isDestructive ? Color.red.opacity(0.3) : Color.green.opacity(0.3), radius: 5, x: 0, y: 3)
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
                Image(systemName: "network")
                    .font(.title2)
                    .foregroundColor(.accentColor)
                
                Text(loc.localized("windowTitle"))
                    .font(.headline)
                
                Spacer()
                
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
            }
            .padding(.horizontal)
            .padding(.top, 12)
            .padding(.bottom, 8)
            
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
                .frame(height: 12)
            
            // Copyright footer
            Text("Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.")
                .font(.system(size: 9))
                .foregroundColor(.secondary.opacity(0.6))
                .padding(.bottom, 8)
        }
        .frame(width: 315, height: 440)
    }
}

// MARK: - RM-01 Device Image

struct RM01DeviceImage: View {
    @ObservedObject var appState: AppState
    @State private var sweepOffset: CGFloat = -400
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
        let imgWidth = max(imageCache.size.width, 1)
        let imgHeight = max(imageCache.size.height, 1)
        
        ZStack {
            Image(nsImage: imageCache)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: imgWidth * 4, height: imgHeight * 4)
                .shadow(color: glowColor, radius: 15)
                .overlay(
                    GeometryReader { geo in
                        if appState.isConnected {
                            Rectangle()
                                .fill(
                                    LinearGradient(
                                        gradient: Gradient(colors: [.clear, .white.opacity(0.8), .clear]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .rotationEffect(.degrees(30))
                                .frame(width: 120, height: geo.size.height * 4)
                                .offset(x: sweepOffset, y: -geo.size.height)
                                .mask(
                                    Image(nsImage: imageCache)
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                )
                        }
                    }
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
        appState.connectionStatus == .connected ? .clear : Color.red.opacity(glowOpacity)
    }
    
    private func updateAnimations(for status: ConnectionStatus) {
        // Stop existing animations first
        withAnimation(.linear(duration: 0)) {
            sweepOffset = -400
            glowOpacity = 0
        }
        
        // Small delay to ensure reset completes
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            if status == .connected {
                withAnimation(.linear(duration: 2.0).repeatForever(autoreverses: false)) {
                    sweepOffset = 600
                }
                glowOpacity = 0
            } else {
                withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                    glowOpacity = 0.4
                }
            }
        }
    }
}
