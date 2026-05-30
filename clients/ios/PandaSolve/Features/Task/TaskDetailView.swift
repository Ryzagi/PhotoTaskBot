import SwiftUI

struct TaskDetailView: View {
    let taskId: String

    @Environment(AppEnvironment.self) private var env
    @State private var status: String = "pending"
    @State private var problems: [Problem] = []
    @State private var pollTask: Task<Void, Never>?
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if status == "pending" {
                    HStack { ProgressView(); Text("Решаю задачу 🐼") }
                } else if status == "failed" {
                    Text("Не удалось решить. Попробуйте позже.")
                        .foregroundStyle(.red)
                } else {
                    ForEach(Array(problems.enumerated()), id: \.offset) { _, problem in
                        ProblemCard(problem: problem)
                    }
                }
                if let error { Text(error).foregroundStyle(.red) }
            }
            .padding()
        }
        .navigationTitle("Решение")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { startPolling() }
        .onDisappear { pollTask?.cancel() }
    }

    private func startPolling() {
        pollTask = Task {
            while !Task.isCancelled {
                do {
                    let detail = try await env.taskRepo.get(id: taskId)
                    status = detail.status
                    if let solution = detail.solution { problems = solution.solutions }
                    if status != "pending" { return }
                } catch { self.error = error.localizedDescription; return }
                try? await Task.sleep(nanoseconds: 2_000_000_000)
            }
        }
    }
}

private struct ProblemCard: View {
    let problem: Problem
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Задание").font(.headline)
            MixedText(problem.problem)
            Text("Решение").font(.headline)
            ForEach(Array(problem.steps.enumerated()), id: \.offset) { i, b in
                HStack(alignment: .top) {
                    Text("\(i + 1).").bold()
                    BlockView(block: b)
                }
            }
            Text("Ответ").font(.headline)
            ForEach(Array(problem.solution.enumerated()), id: \.offset) { _, b in
                BlockView(block: b)
            }
        }
        .padding()
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
}

private struct BlockView: View {
    let block: SolutionBlock
    var body: some View {
        if block.type == "math" {
            MathLatexView(latex: block.content.trimmingCharacters(in: CharacterSet(charactersIn: "$")))
        } else {
            MixedText(block.content)
        }
    }
}
