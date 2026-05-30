import SwiftUI

struct SettingsView: View {
    @Environment(AppEnvironment.self) private var env
    @State private var linkCode: String?
    @State private var telegramLinked = false
    @State private var error: String?

    var body: some View {
        Form {
            Section("Аккаунт") {
                if telegramLinked {
                    Label("Telegram привязан", systemImage: "checkmark.circle")
                } else {
                    HStack {
                        Text(linkCode ?? "Привязать Telegram")
                        Spacer()
                        Button("Получить код", action: issueLink)
                    }
                }
                Button("Выйти", role: .destructive) {
                    Task { try? await env.auth.signOut() }
                }
            }
            Section("Покупки") {
                Link("Пополнить через Telegram", destination: URL(string: "https://t.me/PandaSolveBot?start=topup")!)
            }
            Section("Поддержка") {
                Link("Telegram поддержки", destination: URL(string: "https://t.me/pandasolve_support")!)
            }
            if let error { Text(error).foregroundStyle(.red) }
        }
        .navigationTitle("Настройки")
        .task {
            do {
                let me = try await env.userRepo.me()
                telegramLinked = me.telegramLinked
            } catch { self.error = error.localizedDescription }
        }
    }

    private func issueLink() {
        Task {
            do { linkCode = try await env.userRepo.startLink() }
            catch { self.error = error.localizedDescription }
        }
    }
}
