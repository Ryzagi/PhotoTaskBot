import SwiftUI
import Observation

@Observable @MainActor final class HomeModel {
    var me: Me?
    var albums: [Album] = []
    var items: [TaskListItem] = []
    var selectedAlbumId: String?
    var query = ""
    var loading = true

    func refresh(_ env: AppEnvironment) async {
        loading = items.isEmpty
        async let meR = try? env.userRepo.me()
        async let albumsR = try? env.albumRepo.list()
        async let tasksR = try? env.taskRepo.list(limit: 100, before: nil, albumId: selectedAlbumId,
                                                  q: query.isEmpty ? nil : query)
        me = await meR ?? me
        albums = await albumsR ?? albums
        items = await tasksR?.items ?? items
        loading = false
    }
}

struct HomeView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    let onOpenTask: (String) -> Void
    let onOpenSolve: () -> Void
    let onOpenSettings: () -> Void

    @State private var model = HomeModel()
    @State private var openDays: [String: Bool] = [:]
    @State private var showCreateFolder = false

    private let albumColors: [Color] = []

    var body: some View {
        ZStack(alignment: .bottom) {
            DotPaper(paper: c.paper, dot: c.ink.opacity(0.07))
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    header
                    bambooCard.padding(.top, 12)
                    folderChips.padding(.top, 14)
                    searchField.padding(.top, 12)
                    threads.padding(.top, 16)
                    Spacer(minLength: 110)
                }
                .padding(.horizontal, 20).padding(.top, 8)
            }
            CuteBottomBar(tab: .home, onHome: {}, onCamera: onOpenSolve, onProfile: onOpenSettings)
        }
        .task { await model.refresh(env) }
        .onChange(of: model.selectedAlbumId) { Task { await model.refresh(env) } }
        .onChange(of: model.query) { Task { await model.refresh(env) } }
        .sheet(isPresented: $showCreateFolder) {
            FolderEditorSheet { name, emoji, color in
                Task { _ = try? await env.albumRepo.create(name: name, emoji: emoji, color: color); await model.refresh(env) }
            }
        }
    }

    private var header: some View {
        HStack(spacing: 10) {
            PandaFace().frame(width: 40, height: 40)
            VStack(alignment: .leading, spacing: 0) {
                Text(t.welcomeBack).font(caveat(17, .semibold)).foregroundStyle(c.inkSoft)
                Text(model.me?.displayName ?? "🐼").font(baloo(19, .bold)).foregroundStyle(c.ink)
            }
            Spacer()
            if let streak = model.me?.streak, streak > 0 {
                Pill(text: "🔥 \(streak) \(t.daysShort)", bg: c.butterSoft, fg: c.butterDeep, shadow: c.butterShadow.opacity(0.4))
            }
        }
    }

    private var bambooCard: some View {
        let daily = model.me?.balance.daily ?? 0
        let sub = model.me?.balance.subscription ?? 0
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(t.bambooToday).font(nunito(10, .heavy)).foregroundStyle(c.mintDeep)
                Spacer()
            }
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("\(daily + sub)").font(baloo(40, .heavy)).foregroundStyle(c.mintDeep)
                Text(t.statSolved == "solved" ? "solutions" : "решения").font(nunito(14, .bold)).foregroundStyle(c.inkSoft)
                Spacer()
            }
            HStack(spacing: 5) {
                ForEach(0..<5, id: \.self) { i in
                    Leaf(face: i < min(daily, 5) ? c.mint : c.paper2, shadow: i < min(daily, 5) ? c.mintShadow : c.line)
                }
                if daily > 5 { Text("+\(daily - 5)").font(nunito(11, .heavy)).foregroundStyle(c.mintDeep) }
                if sub > 0 {
                    Text("🎋 \(sub)").font(nunito(11, .heavy)).foregroundStyle(c.mintDeep)
                        .padding(.horizontal, 8).padding(.vertical, 3)
                        .background(Capsule().fill(c.mintSoft))
                }
                Spacer()
            }
            Text(t.dailyFreeHint).font(nunito(11, .bold)).foregroundStyle(c.inkSoft)
        }
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 24).fill(c.card))
        .overlay(RoundedRectangle(cornerRadius: 24).stroke(c.mint, lineWidth: 2))
    }

    private var folderChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                chip("📚 " + t.filterAll, count: model.items.count, selected: model.selectedAlbumId == nil) {
                    model.selectedAlbumId = nil
                }
                ForEach(model.albums) { a in
                    chip("\(a.emoji ?? "📁") \(a.name)", count: a.taskCount, selected: model.selectedAlbumId == a.id) {
                        model.selectedAlbumId = model.selectedAlbumId == a.id ? nil : a.id
                    }
                }
                Button { showCreateFolder = true } label: {
                    Text("＋").font(baloo(16, .bold)).foregroundStyle(c.lavDeep)
                        .frame(width: 34, height: 34)
                        .background(Circle().fill(c.lavSoft))
                }
            }
        }
    }

    private func chip(_ label: String, count: Int, selected: Bool, action: @escaping () -> Void) -> some View {
        HStack(spacing: 6) {
            Text(label).font(nunito(12, .heavy))
            Text("\(count)").font(nunito(11, .heavy)).opacity(0.7)
        }
        .foregroundStyle(selected ? .white : c.lavDeep)
        .padding(.horizontal, 13).padding(.vertical, 8)
        .background(Capsule().fill(selected ? c.lav : c.lavSoft))
        .onTapGesture(perform: action)
    }

    private var searchField: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass").font(.system(size: 13, weight: .bold)).foregroundStyle(c.inkFaint)
            TextField(t.searchHint, text: Bindable(model).query)
                .font(nunito(13, .bold)).foregroundStyle(c.ink)
                .autocorrectionDisabled()
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .background(Capsule().fill(c.card))
        .overlay(Capsule().stroke(c.line, lineWidth: 2))
    }

    @ViewBuilder private var threads: some View {
        let (today, yesterday) = Dates.todayYesterday()
        let groups = Dictionary(grouping: model.items) { Dates.localDay($0.createdAt) }
            .sorted { $0.key > $1.key }
        if model.items.isEmpty && !model.loading {
            Text(model.query.isEmpty ? t.noTasks : t.searchEmpty)
                .font(nunito(14, .semibold)).foregroundStyle(c.inkFaint)
                .frame(maxWidth: .infinity).padding(.top, 30)
        }
        VStack(alignment: .leading, spacing: 10) {
            ForEach(Array(groups.enumerated()), id: \.element.key) { idx, group in
                let named = group.key == today || group.key == yesterday
                let label = group.key == today ? t.dayToday : group.key == yesterday ? t.dayYesterday
                    : Dates.pretty(group.key, en: AppPrefs.shared.language == "en")
                let isOpen = openDays[group.key] ?? (idx == 0)
                HStack(alignment: .bottom) {
                    Text(label.prefix(1).uppercased() + label.dropFirst()).font(baloo(17, .heavy)).foregroundStyle(c.ink)
                    if named {
                        Text(Dates.pretty(group.key, en: AppPrefs.shared.language == "en"))
                            .font(caveat(15, .bold)).foregroundStyle(c.inkFaint)
                    }
                    Spacer()
                    DayChevron(open: isOpen, color: c.mintDeep, bg: c.mintSoft)
                }
                .contentShape(Rectangle())
                .onTapGesture { openDays[group.key] = !isOpen }
                if isOpen {
                    ForEach(group.value) { item in
                        ThreadCard(item: item) { onOpenTask(item.id) }
                    }
                }
            }
        }
    }
}

// MARK: - Thread card (ported from Android ThreadCard.kt)

struct ThreadCard: View {
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    let item: TaskListItem
    let onTap: () -> Void

    var body: some View {
        HStack(spacing: 13) {
            Text(item.inputKind == "image" ? "🖼" : "📝").font(.system(size: 22))
                .frame(width: 48, height: 48)
                .background(RoundedRectangle(cornerRadius: 14).fill(c.mintSoft))
            VStack(alignment: .leading, spacing: 4) {
                Text(item.preview.isEmpty ? t.untitled : item.preview)
                    .font(nunito(13.5, .bold)).foregroundStyle(c.ink)
                    .lineLimit(2).multilineTextAlignment(.leading)
                HStack(spacing: 0) {
                    Text(item.status == "done" ? "● " + t.statusSolved : "◐ " + t.statusTalking)
                        .font(nunito(10, .heavy))
                        .foregroundStyle(item.status == "done" ? c.mintDeep : c.lavDeep)
                    Text("  ·  ").font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
                    Text(item.inputKind).font(nunito(10, .heavy)).foregroundStyle(c.inkSoft)
                }
            }
            Spacer()
            Text(Dates.localDay(item.createdAt)).font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
        }
        .padding(11)
        .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.line, lineWidth: 2))
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
    }
}

// MARK: - Folder create sheet (name + emoji + color, like Android's dialog)

struct FolderEditorSheet: View {
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    @Environment(\.dismiss) private var dismiss
    let onCreate: (String, String?, String?) -> Void

    @State private var name = ""
    @State private var emoji = "📚"
    private let emojis = ["📚", "➗", "🔤", "📐", "✏️", "⚗️", "🌍", "🎨"]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t.albumNewTitle).font(baloo(18, .heavy)).foregroundStyle(c.ink)
            Text(t.albumNameLabel).font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
            TextField(t.albumNameHint, text: $name)
                .font(nunito(15, .bold)).foregroundStyle(c.ink)
                .padding(.horizontal, 14).padding(.vertical, 12)
                .background(RoundedRectangle(cornerRadius: 16).fill(c.card))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(c.mint, lineWidth: 2))
            Text(t.albumIconLabel).font(nunito(10, .heavy)).foregroundStyle(c.inkFaint)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(emojis, id: \.self) { e in
                        Text(e).font(.system(size: 20))
                            .frame(width: 42, height: 42)
                            .background(RoundedCornerCard(selected: emoji == e, c: c))
                            .onTapGesture { emoji = e }
                    }
                }
            }
            HStack(spacing: 10) {
                CandyButton(text: t.cancel, variant: .ghost) { dismiss() }
                CandyButton(text: t.albumCreate, enabled: !name.isEmpty) {
                    onCreate(name, emoji, nil); dismiss()
                }
            }
            .padding(.top, 6)
        }
        .padding(22)
        .presentationDetents([.height(320)])
        .presentationBackground(c.paper)
    }

    private struct RoundedCornerCard: View {
        let selected: Bool; let c: CutePalette
        var body: some View {
            RoundedRectangle(cornerRadius: 14).fill(selected ? c.mintSoft : c.card)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(selected ? c.mint : c.line, lineWidth: 2))
        }
    }
}
