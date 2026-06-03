// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AgentWatchMenuBar",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "AgentWatchMenuBar",
            path: "Sources/AgentWatchMenuBar"
        )
    ]
)
