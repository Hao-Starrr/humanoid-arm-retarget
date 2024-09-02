import RealityKit
import ARKit
import SwiftUI

struct 🧑HeadTrackingComponent: Component, Codable {
    init() {}
}

struct 🧑HeadTrackingSystem: System {
    private static let query = EntityQuery(where: .has(🧑HeadTrackingComponent.self))
    
    private let session = ARKitSession()
    private let provider = WorldTrackingProvider()
    
    init(scene: RealityKit.Scene) {
        self.setUpSession()
    }
    
    private func setUpSession() {
        Task {
            do {
                try await self.session.run([self.provider])
            } catch {
                assertionFailure()
            }
        }
    }
    
    func update(context: SceneUpdateContext) {
        let entities = context.scene.performQuery(Self.query).map { $0 }
        
        guard !entities.isEmpty,
                let deviceAnchor = self.provider.queryDeviceAnchor(atTimestamp: CACurrentMediaTime()) else { return }
        
        let cameraTransform = Transform(matrix: deviceAnchor.originFromAnchorTransform)

        // Calculate the position 1 meter in front
        let forwardVector = cameraTransform.matrix.columns.2 // Z direction vector
        let forwardOffset = simd_make_float3(forwardVector.x, forwardVector.y, forwardVector.z) * -1.0 // Reverse direction
        let targetPosition = cameraTransform.translation + forwardOffset // Position 1 meter in front
        
        for entity in entities {
            // set the position of new entity
            entity.setPosition(targetPosition, relativeTo: nil)
            
            // make the entity face the camera
            entity.look(at: cameraTransform.translation,
                    from: targetPosition,
                    relativeTo: nil,
                    forward: .positiveZ)
            
            // entity.look(at: cameraTransform.translation,
            //             from: entity.position(relativeTo: nil),
            //             relativeTo: nil,
            //             forward: .positiveZ)
        }
    }
}

