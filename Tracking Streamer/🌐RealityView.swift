import WebKit
import SwiftUI
import RealityKit
import ARKit

struct 🌐RealityView: View {
    var model: 🥽AppModel
    var body: some View {

        RealityView { content, attachments in

            // create and configure x axis entity
            let xAxisMesh = MeshResource.generateBox(size: [0.5, 0.01, 0.01])
            let xAxisMaterial = SimpleMaterial(color: .red, isMetallic: true)
            let xAxisEntity = ModelEntity(mesh: xAxisMesh, materials: [xAxisMaterial])
            xAxisEntity.position = [0.25, 0, 0] // move the entity to the right
            // create y axis entity
            let yAxisMesh = MeshResource.generateBox(size: [0.01, 0.01, 0.5])
            let yAxisMaterial = SimpleMaterial(color: .green, isMetallic: true)
            let yAxisEntity = ModelEntity(mesh: yAxisMesh, materials: [yAxisMaterial])
            yAxisEntity.position = [0, 0, -0.25] // move the entity to the front
            // create z axis entity
            let zAxisMesh = MeshResource.generateBox(size: [0.01, 0.5, 0.01])
            let zAxisMaterial = SimpleMaterial(color: .blue, isMetallic: true)
            let zAxisEntity = ModelEntity(mesh: zAxisMesh, materials: [zAxisMaterial])
            zAxisEntity.position = [0, 0.25, 0] // move the entity to the top
            // add the axis entities to the scene content
            content.add(xAxisEntity)
            content.add(yAxisEntity)
            content.add(zAxisEntity)


            let resultLabelEntity = attachments.entity(for: Self.attachmentID)!
            resultLabelEntity.components.set(🧑HeadTrackingComponent())
            resultLabelEntity.name = 🧩Name.resultLabel

            // get and configure webViewEntity
            let webViewEntity = attachments.entity(for: Self.webViewAttachmentID)!
            webViewEntity.position = [0, 1.0, -1.5] // move the entity to the front

            // comment out the following line if you do not need first person view
            content.add(webViewEntity)

        } attachments: {
            Attachment(id: Self.attachmentID) {
            }
            Attachment(id: Self.webViewAttachmentID) {
                // this web link should be changed to your server address
                WebView(url: URL(string: "https://192.168.11.214:8012/?ws=wss://192.168.11.214:8012")!)
                .frame(width: 1500, height: 1200)
            }
        }
        .gesture(
            TapGesture()
                .targetedToAnyEntity()
        )
        .task { self.model.run() }
        .task { await self.model.processDeviceAnchorUpdates() }
        .task { self.model.startserver() }
        .task(priority: .low) { await self.model.processReconstructionUpdates() }
        // these tasks are the core things that send information

    }
    static let attachmentID: String = "resultLabel"
    static let webViewAttachmentID: String = "webViewAttachment"

}

struct WebView: UIViewRepresentable {
    var url: URL

    func makeUIView(context: Context) -> some UIView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsPictureInPictureMediaPlayback = true
        configuration.allowsInlinePredictions = true
        configuration.allowsInlineMediaPlayback = true
        configuration.allowsAirPlayForMediaPlayback = true
        
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.load(URLRequest(url: url))
        
        return webView
    }
    
    func updateUIView(_ uiView: UIViewType, context: Context) {
        
    }
}

