// swift-tools-version: 6.2
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "RM01InternetConnector",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "RM01InternetConnector",
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        )
    ]
)
