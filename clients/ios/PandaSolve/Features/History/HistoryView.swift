import SwiftUI

struct HistoryView: View {
    let onSelect: (String) -> Void

    @Environment(AppEnvironment.self) private var env
    @State private var items: [TaskListItem] = []
    @State private var error: String?

    var body: some View {
        List {
            ForEach(items) { item in
                Button { onSelect(item.id) } label: {
                    VStack(alignment: .leading) {
                        HStack {
                            Text(item.inputKind == "image" ? "🖼" : "📝")
                            Text(item.preview).lineLimit(2)
                        }
                        Text(item.createdAt).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
            if let error { Text(error).foregroundStyle(.red) }
        }
        .navigationTitle("История")
        .task { await load() }
    }

    private func load() async {
        do {
            let result = try await env.taskRepo.list(limit: 30, before: nil)
            items = result.items
        } catch { self.error = error.localizedDescription }
    }
}
