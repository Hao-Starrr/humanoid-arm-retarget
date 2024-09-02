import SwiftUI

@main
struct VisionProTeleopApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowResizability(.contentSize)
        ImmersiveSpace(id: "immersiveSpace") {
            🌐RealityView(model: 🥽AppModel())
        }

    }
    init() {
        🧑HeadTrackingComponent.registerComponent()
        🧑HeadTrackingSystem.registerSystem()
    }
}

// Park, Y. Teleopeation System using Apple Vision Pro (Version 0.1.0) [Computer software]. https://github.com/Improbable-AI/VisionProTeleop