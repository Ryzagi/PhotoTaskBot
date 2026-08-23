import SwiftUI
import AVFoundation
import PhotosUI
import UIKit

struct SolveView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    @Environment(\.dismiss) private var dismiss
    let onCreated: (String) -> Void

    @State private var camera = CameraController()
    @State private var mode = "photo"                 // photo | text
    @State private var problemText = ""
    @State private var busy = false
    @State private var error: String?
    @State private var pendingImage: Data?
    @State private var caption = ""
    @State private var pickerItem: PhotosPickerItem?

    private let vfDeep = Color(red: 0.13, green: 0.12, blue: 0.10)

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 0) {
                ZStack {
                    RadialGradient(colors: [Color(red: 0.23, green: 0.21, blue: 0.18), vfDeep],
                                   center: .center, startRadius: 10, endRadius: 500)
                    if mode == "text" {
                        textCard
                    } else if camera.authorized {
                        CameraPreview(session: camera.session).ignoresSafeArea(edges: .top)
                    } else {
                        permissionAsk
                    }
                    if mode == "photo" && camera.authorized {
                        VStack {
                            Spacer()
                            Text(t.cameraAim).font(caveat(20, .bold)).foregroundStyle(.white)
                                .padding(.horizontal, 16).padding(.vertical, 6)
                                .background(Capsule().fill(.black.opacity(0.32)))
                                .padding(.bottom, 24)
                        }
                    }
                    topBar
                }
                controls
            }
            if let data = pendingImage { previewOverlay(data) }
            if busy { solvingOverlay }
        }
        .task { await camera.start() }
        .onDisappear { camera.stop() }
        .onChange(of: pickerItem) {
            guard let item = pickerItem else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self) { pendingImage = data }
                pickerItem = nil
            }
        }
    }

    private var textCard: some View {
        VStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(t.solveProblemLabel).font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
                TextEditor(text: $problemText)
                    .font(nunito(16, .semibold)).foregroundStyle(c.ink)
                    .scrollContentBackground(.hidden)
                    .overlay(alignment: .topLeading) {
                        if problemText.isEmpty {
                            Text(t.solveTextPlaceholder).font(nunito(16, .semibold)).foregroundStyle(c.inkFaint)
                                .padding(.top, 8).padding(.leading, 4).allowsHitTesting(false)
                        }
                    }
            }
            .padding(18)
            .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
            .padding(.horizontal, 24).padding(.top, 100).padding(.bottom, 24)
        }
    }

    private var permissionAsk: some View {
        VStack(spacing: 10) {
            Text(t.cameraPermTitle).font(caveat(24, .bold)).foregroundStyle(.white)
            Text(t.cameraPermSubtitle).font(nunito(13, .semibold)).foregroundStyle(.white.opacity(0.7))
            CandyButton(text: t.cameraPermAllow) {
                if AVCaptureDevice.authorizationStatus(for: .video) == .denied {
                    // Permanently denied: the system dialog won't reappear —
                    // send the user to the app's Settings page instead.
                    if let url = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(url)
                    }
                } else {
                    Task { await camera.start() }
                }
            }
            .frame(width: 220).padding(.top, 10)
            Text(t.cameraOrType).font(caveat(17, .semibold)).foregroundStyle(c.lav)
                .onTapGesture { mode = "text" }.padding(.top, 4)
        }
        .padding(32)
    }

    private var topBar: some View {
        VStack {
            HStack {
                roundBtn { dismiss() } label: { Image(systemName: "xmark").font(.system(size: 15, weight: .bold)) }
                Spacer()
                HStack(spacing: 8) {
                    Circle().fill(c.mint).frame(width: 7, height: 7)
                    Text(t.cameraReady).font(nunito(12, .heavy)).foregroundStyle(.white)
                }
                .padding(.horizontal, 14).padding(.vertical, 7)
                .background(Capsule().fill(c.mint.opacity(0.22)))
                .overlay(Capsule().stroke(c.mint, lineWidth: 1.5))
                Spacer()
                roundBtn(active: camera.torchOn) { camera.toggleTorch() } label: { Text("⚡").font(.system(size: 16)) }
            }
            .padding(.horizontal, 22).padding(.top, 8)
            Spacer()
        }
    }

    private func roundBtn(active: Bool = false, _ action: @escaping () -> Void, label: () -> some View) -> some View {
        Button(action: action) {
            label().foregroundStyle(active ? c.ink : .white)
                .frame(width: 40, height: 40)
                .background(Circle().fill(active ? c.butter : .white.opacity(0.16)))
        }
    }

    private var controls: some View {
        HStack {
            VStack(alignment: .leading, spacing: 7) {
                Text(t.modeText).font(nunito(11, .heavy))
                    .foregroundStyle(mode == "text" ? c.mint : .white.opacity(0.5))
                    .onTapGesture { mode = "text" }
                Text(t.modePhoto).font(nunito(11, .heavy))
                    .foregroundStyle(mode == "photo" ? c.mint : .white.opacity(0.5))
                    .onTapGesture { mode = "photo" }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            Button {
                if mode == "text" { submitText() } else { capture() }
            } label: {
                ZStack {
                    Circle().fill(.white).frame(width: 80, height: 80)
                    Circle().fill(LinearGradient(colors: [c.mint, c.sky], startPoint: .topLeading, endPoint: .bottomTrailing))
                        .frame(width: 64, height: 64)
                    Image(systemName: mode == "text" ? "checkmark" : "camera.fill")
                        .font(.system(size: 24, weight: .semibold)).foregroundStyle(.white)
                }
            }
            .disabled(busy || (mode == "text" && problemText.isEmpty))
            PhotosPicker(selection: $pickerItem, matching: .images) {
                Image(systemName: "photo.fill").font(.system(size: 20)).foregroundStyle(.white)
                    .frame(width: 50, height: 50)
                    .background(RoundedRectangle(cornerRadius: 14)
                        .fill(LinearGradient(colors: [c.lav, c.pink], startPoint: .topLeading, endPoint: .bottomTrailing)))
            }
            .frame(maxWidth: .infinity, alignment: .trailing)
        }
        .padding(.horizontal, 30).padding(.top, 20).padding(.bottom, 24)
        .background(Color.black)
    }

    private func previewOverlay(_ data: Data) -> some View {
        VStack(spacing: 0) {
            ZStack(alignment: .topLeading) {
                Color.black.ignoresSafeArea()
                if let ui = UIImage(data: data) {
                    Image(uiImage: ui).resizable().scaledToFit().frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                roundBtn { pendingImage = nil; caption = "" } label: { Image(systemName: "xmark").font(.system(size: 15, weight: .bold)) }
                    .padding(.leading, 20).padding(.top, 8)
            }
            HStack(spacing: 12) {
                TextField(t.captionPlaceholder, text: $caption)
                    .font(nunito(15, .semibold)).foregroundStyle(.white)
                    .padding(.horizontal, 16).padding(.vertical, 12)
                    .background(Capsule().fill(.white.opacity(0.14)))
                Button { submitImage(data) } label: {
                    Image(systemName: "paperplane.fill").font(.system(size: 20)).foregroundStyle(.white)
                        .frame(width: 52, height: 52)
                        .background(Circle().fill(LinearGradient(colors: [c.mint, c.sky], startPoint: .topLeading, endPoint: .bottomTrailing)))
                }
                .disabled(busy)
            }
            .padding(16)
            .background(Color.black)
        }
    }

    private var solvingOverlay: some View {
        ZStack {
            Color.black.opacity(0.6).ignoresSafeArea()
            VStack(spacing: 14) {
                ProgressView().tint(c.mint).scaleEffect(1.4)
                Text(t.solvingPanda).font(caveat(22, .bold)).foregroundStyle(.white)
            }
        }
    }

    private func capture() {
        camera.capture { data in
            if let data { pendingImage = data }
        }
    }

    private func submitText() {
        busy = true; error = nil
        Task {
            do { onCreated(try await env.taskRepo.submitText(text: problemText)) }
            catch { self.error = String(describing: error) }
            busy = false
        }
    }

    private func submitImage(_ data: Data) {
        busy = true; error = nil
        let cap = caption.trimmingCharacters(in: .whitespaces)
        pendingImage = nil; caption = ""
        Task {
            do { onCreated(try await env.taskRepo.submitImage(data: data, caption: cap.isEmpty ? nil : cap)) }
            catch { self.error = String(describing: error) }
            busy = false
        }
    }
}

// MARK: - AVFoundation camera plumbing

@Observable @MainActor final class CameraController: NSObject, AVCapturePhotoCaptureDelegate {
    let session = AVCaptureSession()
    var authorized = false
    var torchOn = false
    private let output = AVCapturePhotoOutput()
    private var device: AVCaptureDevice?
    private var onCapture: ((Data?) -> Void)?

    func start() async {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        if status == .notDetermined { authorized = await AVCaptureDevice.requestAccess(for: .video) }
        else { authorized = status == .authorized }
        guard authorized, !session.isRunning else { return }
        session.beginConfiguration()
        session.sessionPreset = .photo
        if let dev = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
           let input = try? AVCaptureDeviceInput(device: dev), session.canAddInput(input) {
            session.addInput(input); device = dev
        }
        if session.canAddOutput(output) { session.addOutput(output) }
        session.commitConfiguration()
        let s = session
        Task.detached { s.startRunning() }
    }

    func stop() { let s = session; Task.detached { if s.isRunning { s.stopRunning() } } }

    func toggleTorch() {
        guard let device, device.hasTorch else { return }
        try? device.lockForConfiguration()
        device.torchMode = torchOn ? .off : .on
        torchOn.toggle()
        device.unlockForConfiguration()
    }

    func capture(_ done: @escaping (Data?) -> Void) {
        onCapture = done
        let settings = AVCapturePhotoSettings()
        output.capturePhoto(with: settings, delegate: self)
    }

    nonisolated func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        let data = photo.fileDataRepresentation()
        Task { @MainActor in self.onCapture?(data); self.onCapture = nil }
    }
}

struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession
    func makeUIView(context: Context) -> PreviewHost {
        let v = PreviewHost()
        v.videoPreviewLayer.session = session
        v.videoPreviewLayer.videoGravity = .resizeAspectFill
        return v
    }
    func updateUIView(_ uiView: PreviewHost, context: Context) {}
    final class PreviewHost: UIView {
        override static var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var videoPreviewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }
}
