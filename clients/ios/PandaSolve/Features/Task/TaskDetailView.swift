import SwiftUI
import PhotosUI
import Observation

@Observable @MainActor final class TaskModel {
    var task: TaskDetail?
    var albums: [Album] = []
    var chat: [ChatMessage] = []
    var chatRemaining = 3
    var sending = false
    var needTopUp = false
    var failed = false

    func load(_ env: AppEnvironment, id: String) async {
        task = env.taskRepo.cachedTask(id) ?? task
        async let albumsR = try? env.albumRepo.list()
        async let chatR = try? env.taskRepo.chatHistory(id: id)
        albums = await albumsR ?? []
        if let thread = await chatR { chat = thread.messages; chatRemaining = thread.remaining }
        for _ in 0..<30 {
            guard let t = try? await env.taskRepo.get(id: id) else { failed = task == nil; return }
            task = t
            if t.status != "pending" { return }
            try? await Task.sleep(for: .seconds(2))
        }
    }

    func send(_ env: AppEnvironment, id: String, text: String, image: Data?) async {
        sending = true
        defer { sending = false }
        do {
            let thread: ChatThread
            if let image { thread = try await env.taskRepo.sendChatImage(id: id, data: image, caption: text) }
            else { thread = try await env.taskRepo.sendChat(id: id, message: text) }
            chat = thread.messages; chatRemaining = thread.remaining; needTopUp = false
        } catch {
            if case APIError.http(let status, _) = error, status == 402 { needTopUp = true }
        }
    }
}

struct TaskDetailView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    @Environment(\.dismiss) private var dismiss
    let taskId: String

    @State private var model = TaskModel()
    @State private var draft = ""
    @State private var attach: Data?
    @State private var pickerItem: PhotosPickerItem?
    @State private var answerRevealed = false
    @State private var showAlbumPicker = false

    var body: some View {
        ZStack(alignment: .bottom) {
            DotPaper(paper: c.paper, dot: c.ink.opacity(0.07))
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        header
                        albumChip.padding(.top, 14)
                        conditionCard.padding(.top, 16)
                        solutionSection.padding(.top, 20)
                        answerCard.padding(.top, 18)
                        chatSection.padding(.top, 22)
                        Color.clear.frame(height: 120).id("bottom")
                    }
                    .padding(.horizontal, 20).padding(.top, 8)
                }
                .onChange(of: model.chat.count) { withAnimation { proxy.scrollTo("bottom") } }
            }
            chatBar
        }
        .navigationBarBackButtonHidden(true)
        .task { await model.load(env, id: taskId) }
        .sheet(isPresented: $showAlbumPicker) { albumPicker }
        .onChange(of: pickerItem) {
            guard let item = pickerItem else { return }
            Task { attach = try? await item.loadTransferable(type: Data.self); pickerItem = nil }
        }
    }

    private var header: some View {
        HStack {
            Button { dismiss() } label: {
                Text("‹").font(baloo(20, .bold)).foregroundStyle(c.ink)
                    .frame(width: 38, height: 38)
                    .background(RoundedRectangle(cornerRadius: 14).fill(c.card))
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.line, lineWidth: 2))
            }
            Spacer()
            VStack(spacing: 0) {
                Text(model.task?.solution?.title ?? t.taskTitleFallback)
                    .font(baloo(16, .bold)).foregroundStyle(c.ink).lineLimit(1)
                if let created = model.task?.createdAt {
                    let secs = model.task?.completedAt.flatMap { Dates.solveSeconds(created, $0) }
                    Text(Dates.localTime(created) + (secs.map { " · \($0) \(t.secondsShort)" } ?? ""))
                        .font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
                }
            }
            Spacer()
            Text("💚").font(.system(size: 17))
                .frame(width: 38, height: 38)
                .background(RoundedRectangle(cornerRadius: 14).fill(c.coralSoft))
        }
    }

    private var albumChip: some View {
        let name = model.albums.first { $0.id == model.task?.albumId }?.name
        return HStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 3).fill(c.mint).frame(width: 9, height: 9)
            Text("\(name ?? t.chooseFolder)  ⌄").font(nunito(11, .heavy)).foregroundStyle(c.lavDeep)
        }
        .padding(.horizontal, 13).padding(.vertical, 7)
        .background(Capsule().fill(c.lavSoft))
        .onTapGesture { showAlbumPicker = true }
    }

    private var conditionCard: some View {
        let condition = model.task?.inputText
            ?? model.task?.solution?.solutions.first?.problem
            ?? (model.failed ? t.taskLoadFailed : "…")
        return ZStack(alignment: .topLeading) {
            Text(condition).font(nunito(14, .semibold)).foregroundStyle(c.ink)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(17).padding(.top, 6)
                .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.mint, lineWidth: 2))
            Text(t.solveProblemLabel).font(nunito(10, .heavy)).foregroundStyle(c.butterDeep)
                .padding(.horizontal, 12).padding(.vertical, 4)
                .background(RoundedRectangle(cornerRadius: 6).fill(c.butter))
                .rotationEffect(.degrees(-3))
                .offset(x: 18, y: -9)
        }
    }

    @ViewBuilder private var solutionSection: some View {
        let pending = model.task?.status == "pending" || model.task == nil
        VStack(alignment: .leading, spacing: 12) {
            SectionLabel(text: pending ? t.solvingLabel : t.solutionLabel, fg: c.mintDeep, bg: c.mintSoft)
            if pending {
                stepRow(1, t.solvingStep)
            } else if let steps = model.task?.solution?.solutions.first?.steps {
                ForEach(Array(steps.enumerated()), id: \.offset) { i, block in
                    stepRow(i + 1, block.content)
                }
            }
        }
    }

    private func stepRow(_ n: Int, _ text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text("\(n)").font(baloo(12, .heavy)).foregroundStyle(c.mintDeep)
                .frame(width: 24, height: 24)
                .background(Circle().fill(c.mintSoft))
            MixedText(content: text)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 16).fill(c.card))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(c.line, lineWidth: 2))
    }

    @ViewBuilder private var answerCard: some View {
        let answer = model.task?.solution?.solutions.first?.solution.map(\.content).joined(separator: "  ")
        let explain = AppPrefs.shared.solveMode == "explain"
        let hide = explain && answer != nil && !answerRevealed
        VStack(alignment: .leading, spacing: 6) {
            Text(t.answerLabel).font(nunito(11, .heavy)).foregroundStyle(c.mintDeep)
            if hide {
                Text(t.revealAnswer).font(baloo(15, .bold)).foregroundStyle(Color(red: 0.12, green: 0.37, blue: 0.26))
                    .frame(maxWidth: .infinity).padding(.vertical, 16)
                    .background(RoundedRectangle(cornerRadius: 14).fill(Color(red: 0.12, green: 0.37, blue: 0.26).opacity(0.13)))
                    .onTapGesture { answerRevealed = true }
            } else {
                MixedText(content: answer ?? "…")
                    .font(baloo(22, .bold)).foregroundStyle(Color(red: 0.12, green: 0.37, blue: 0.26))
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 20)
            .fill(LinearGradient(colors: [c.mint, C2(0x9FE0BF)], startPoint: .leading, endPoint: .trailing)))
    }

    @ViewBuilder private var chatSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionLabel(text: t.askPandaLabel, fg: c.lavDeep, bg: c.lavSoft)
            if model.chat.isEmpty {
                Text(t.chatEmptyHint).font(nunito(14, .semibold)).foregroundStyle(c.inkFaint)
            }
            ForEach(model.chat) { msg in
                bubble(msg)
            }
            if model.sending {
                Text(t.pandaTyping).font(nunito(12, .bold)).foregroundStyle(c.lavDeep)
            }
            if model.needTopUp {
                Text(t.chatLimitReached).font(nunito(13, .bold)).foregroundStyle(c.coralDeep)
                Text(t.topUpUnavailable).font(nunito(11, .bold)).foregroundStyle(c.inkFaint)
            } else if model.chatRemaining <= 0 && !model.chat.isEmpty {
                Text(t.chatPaidHint).font(nunito(11, .bold)).foregroundStyle(c.inkFaint)
            } else if !model.chat.isEmpty {
                Text(String(format: t.chatRemainingFmt, model.chatRemaining))
                    .font(nunito(11, .bold)).foregroundStyle(c.inkFaint)
            }
        }
    }

    private func bubble(_ msg: ChatMessage) -> some View {
        let me = msg.role == "user"
        return HStack {
            if me { Spacer(minLength: 40) }
            VStack(alignment: .leading, spacing: 6) {
                if let url = msg.imageUrl.flatMap(URL.init) {
                    AsyncImage(url: url) { img in img.resizable().scaledToFill() } placeholder: { c.paper2 }
                        .frame(maxWidth: 180, maxHeight: 140).clipShape(RoundedRectangle(cornerRadius: 12))
                }
                if !msg.content.isEmpty {
                    Text(msg.content).font(nunito(13.5, .semibold))
                        .foregroundStyle(me ? .white : c.ink)
                }
            }
            .padding(.horizontal, 14).padding(.vertical, 10)
            .background(RoundedRectangle(cornerRadius: 18).fill(me ? c.coral : c.card))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(me ? c.coralShadow : c.line, lineWidth: 2))
            if !me { Spacer(minLength: 40) }
        }
    }

    private var chatBar: some View {
        VStack(spacing: 8) {
            if attach != nil {
                HStack(spacing: 10) {
                    if let data = attach, let ui = UIImage(data: data) {
                        Image(uiImage: ui).resizable().scaledToFill()
                            .frame(width: 44, height: 44).clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                    Text("📎").font(.system(size: 14))
                    Spacer()
                    Text("✕").font(.system(size: 15)).foregroundStyle(c.coralDeep)
                        .onTapGesture { attach = nil }
                }
                .padding(8)
                .background(RoundedRectangle(cornerRadius: 16).fill(c.card))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(c.line, lineWidth: 2))
            }
            HStack(spacing: 4) {
                PhotosPicker(selection: $pickerItem, matching: .images) {
                    Text("📎").font(.system(size: 18)).frame(width: 38, height: 38)
                }
                TextField(t.askMore, text: $draft)
                    .font(nunito(14, .semibold)).foregroundStyle(c.ink)
                Button {
                    let text = draft.trimmingCharacters(in: .whitespaces)
                    let image = attach
                    draft = ""; attach = nil
                    Task { await model.send(env, id: taskId, text: text, image: image) }
                } label: {
                    Image(systemName: "paperplane.fill").font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 40, height: 40)
                        .background(Circle().fill(LinearGradient(colors: [c.coral, c.pink], startPoint: .topLeading, endPoint: .bottomTrailing)))
                }
                .disabled((draft.isEmpty && attach == nil) || model.sending)
            }
            .padding(.leading, 6).padding(.trailing, 8).padding(.vertical, 8)
            .background(Capsule().fill(c.card))
            .overlay(Capsule().stroke(c.line, lineWidth: 2))
        }
        .padding(20)
    }

    private var albumPicker: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(t.albumPickerTitle).font(baloo(18, .heavy)).foregroundStyle(c.ink)
            if model.albums.isEmpty {
                Text(t.albumPickerEmpty).font(nunito(13, .semibold)).foregroundStyle(c.inkSoft)
            }
            ForEach(model.albums) { a in
                HStack {
                    Text("\(a.emoji ?? "📁") \(a.name)").font(nunito(14, .bold)).foregroundStyle(c.ink)
                    Spacer()
                    if a.id == model.task?.albumId { Text("✓").foregroundStyle(c.mintDeep) }
                }
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 14).fill(c.card))
                .onTapGesture { assign(a.id) }
            }
            HStack {
                Text(t.albumNone).font(nunito(14, .bold)).foregroundStyle(c.inkSoft)
                Spacer()
            }
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 14).fill(c.card))
            .onTapGesture { assign(nil) }
        }
        .padding(22)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(c.paper)
        .presentationDetents([.medium])
    }

    private func assign(_ albumId: String?) {
        showAlbumPicker = false
        Task {
            try? await env.albumRepo.assign(taskId: taskId, albumId: albumId)
            await model.load(env, id: taskId)
        }
    }
}

private func C2(_ hex: UInt32) -> Color {
    Color(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
}
