import SwiftUI
import PhotosUI

struct SolveView: View {
    let onCreated: (String) -> Void

    @Environment(AppEnvironment.self) private var env
    @State private var selectedItem: PhotosPickerItem?
    @State private var imageData: Data?
    @State private var caption: String = ""
    @State private var textInput: String = ""
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        Form {
            Section("Фото задачи") {
                PhotosPicker(selection: $selectedItem, matching: .images) {
                    Label(imageData == nil ? "Выбрать фото" : "Фото выбрано ✓", systemImage: "photo")
                }
                .onChange(of: selectedItem) { _, newValue in
                    Task { imageData = try? await newValue?.loadTransferable(type: Data.self) }
                }
                TextField("Подсказка (необязательно)", text: $caption, axis: .vertical)
                    .lineLimit(2...4)
                Button("Отправить фото", action: submitImage)
                    .disabled(imageData == nil || busy)
            }

            Section("Или введите задачу текстом") {
                TextField("Условие", text: $textInput, axis: .vertical)
                    .lineLimit(4...10)
                Button("Решить текст", action: submitText)
                    .disabled(textInput.isEmpty || busy)
            }

            if busy { ProgressView() }
            if let error { Text(error).foregroundStyle(.red) }
        }
        .navigationTitle("Новая задача")
    }

    private func submitImage() {
        guard let data = imageData else { return }
        Task {
            busy = true; error = nil
            do {
                let id = try await env.taskRepo.submitImage(data: data, caption: caption.isEmpty ? nil : caption)
                onCreated(id)
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func submitText() {
        Task {
            busy = true; error = nil
            do {
                let id = try await env.taskRepo.submitText(text: textInput)
                onCreated(id)
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }
}
