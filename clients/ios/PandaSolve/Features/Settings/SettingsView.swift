import SwiftUI
import Observation

struct SettingsView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    let onHome: () -> Void
    let onCamera: () -> Void
    let onSignOut: () -> Void

    @State private var me: Me?
    @State private var albumCount = 0
    @State private var selAch: Ach?
    @State private var showTopUpNote = false

    var body: some View {
        ZStack(alignment: .bottom) {
            DotPaper(paper: c.paper, dot: c.ink.opacity(0.07))
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text(t.profileTitle).font(baloo(24, .heavy)).foregroundStyle(c.ink)
                    hero
                    stats
                    achievementsRow
                    rows
                    Spacer(minLength: 100)
                }
                .padding(.horizontal, 20).padding(.top, 8)
            }
            CuteBottomBar(tab: .profile, onHome: onHome, onCamera: onCamera, onProfile: {})
        }
        .task {
            me = try? await env.userRepo.me()
            albumCount = (try? await env.albumRepo.list().count) ?? 0
        }
        .alert(t.rowTopUp, isPresented: $showTopUpNote) {
            Button("OK", role: .cancel) {}
        } message: { Text(t.topUpUnavailable) }
        .sheet(item: $selAch) { a in achievementDetail(a) }
    }

    private var hero: some View {
        HStack(spacing: 14) {
            PandaFace().frame(width: 60, height: 60)
                .background(Circle().fill(.white))
            VStack(alignment: .leading, spacing: 2) {
                Text(me?.displayName ?? "🐼").font(baloo(21, .heavy)).foregroundStyle(c.ink)
                Text(me?.id.prefix(18).description ?? "").font(nunito(11, .bold)).foregroundStyle(c.inkSoft)
            }
            Spacer()
        }
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 28)
            .fill(LinearGradient(colors: [c.lavSoft, c.card], startPoint: .leading, endPoint: .trailing)))
        .overlay(RoundedRectangle(cornerRadius: 28).stroke(c.lav, lineWidth: 2))
    }

    private var stats: some View {
        HStack(spacing: 10) {
            stat("\(me?.streak ?? 0)", t.statStreak, c.butterDeep)
            stat("\(me?.solvedCount ?? 0)", t.statSolved, c.mintDeep)
            stat("\(albumCount)", t.statAlbums, c.lavDeep)
        }
    }

    private func stat(_ v: String, _ k: String, _ color: Color) -> some View {
        VStack(spacing: 5) {
            Text(v).font(baloo(26, .heavy)).foregroundStyle(color)
            Text(k.uppercased()).font(nunito(10, .heavy)).foregroundStyle(c.inkSoft)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 12)
        .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.line, lineWidth: 2))
    }

    private var achievementsRow: some View {
        let achs = Ach.catalog(solved: me?.solvedCount ?? 0, streak: me?.streak ?? 0, albums: albumCount, en: AppPrefs.shared.language == "en")
        return VStack(alignment: .leading, spacing: 9) {
            Text(t.achievements).font(baloo(14, .bold)).foregroundStyle(c.ink)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 9) {
                    ForEach(achs) { a in
                        let done = a.cur >= a.target
                        Text(a.emoji).font(.system(size: 24))
                            .opacity(done ? 1 : 0.35)
                            .frame(width: 52, height: 52)
                            .background(RoundedRectangle(cornerRadius: 16).fill(done ? c.mintSoft : c.paper2))
                            .onTapGesture { selAch = a }
                    }
                }
            }
        }
    }

    private func achievementDetail(_ a: Ach) -> some View {
        VStack(spacing: 8) {
            Text(a.emoji).font(.system(size: 44))
            Text(a.title).font(baloo(18, .heavy)).foregroundStyle(c.ink)
            Text(a.desc).font(nunito(13, .semibold)).foregroundStyle(c.inkSoft)
            Text("\(min(a.cur, a.target)) / \(a.target)").font(baloo(16, .heavy)).foregroundStyle(c.mintDeep)
        }
        .padding(30)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(c.paper)
        .presentationDetents([.height(240)])
    }

    private var rows: some View {
        VStack(spacing: 8) {
            row("🎋", c.mintSoft, t.rowTopUp, trail: t.rowTopUpHint.uppercased()) { showTopUpNote = true }
            row("🌍", c.lavSoft, t.rowLanguage, trail: AppPrefs.shared.language == "en" ? "English" : "Русский") {
                AppPrefs.shared.language = AppPrefs.shared.language == "en" ? "ru" : "en"
                Task { _ = try? await env.userRepo.updateLanguage(AppPrefs.shared.language) }
            }
            row("🌗", c.skySoft, t.rowTheme, trail: themeLabel) {
                AppPrefs.shared.theme = ["system": "light", "light": "dark", "dark": "system"][AppPrefs.shared.theme] ?? "system"
            }
            row("🧠", c.mintSoft, t.rowSolveMode, trail: AppPrefs.shared.solveMode == "explain" ? t.solveModeExplain : t.solveModeSolve) {
                AppPrefs.shared.solveMode = AppPrefs.shared.solveMode == "explain" ? "solve" : "explain"
            }
            HStack(spacing: 13) {
                iconBox("🔔", c.butterSoft)
                VStack(alignment: .leading, spacing: 1) {
                    Text(t.rowNotifications).font(baloo(14, .heavy)).foregroundStyle(c.ink)
                    Text(t.notificationsHint.uppercased()).font(nunito(10, .bold)).foregroundStyle(c.inkFaint)
                }
                Spacer()
                Toggle("", isOn: Binding(get: { AppPrefs.shared.notifEnabled }, set: { AppPrefs.shared.notifEnabled = $0 }))
                    .labelsHidden().tint(c.mint)
            }
            .padding(.horizontal, 14).padding(.vertical, 8)
            .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
            .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.line, lineWidth: 2))
            row("👋", c.coralSoft, t.rowSignOut, trail: "→", danger: true) {
                Task { try? await env.auth.signOut(); onSignOut() }
            }
        }
    }

    private var themeLabel: String {
        switch AppPrefs.shared.theme { case "light": return t.themeLight; case "dark": return t.themeDark; default: return t.themeSystem }
    }

    private func row(_ emoji: String, _ iconBg: Color, _ label: String, trail: String, danger: Bool = false, action: @escaping () -> Void) -> some View {
        HStack(spacing: 13) {
            iconBox(emoji, iconBg)
            Text(label).font(baloo(14, .heavy)).foregroundStyle(danger ? c.coralDeep : c.ink)
            Spacer()
            Text(trail).font(nunito(11, .heavy)).foregroundStyle(danger ? c.coralDeep : c.inkSoft)
        }
        .padding(.horizontal, 14).padding(.vertical, 11)
        .background(RoundedRectangle(cornerRadius: 20).fill(c.card))
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.line, lineWidth: 2))
        .contentShape(Rectangle())
        .onTapGesture(perform: action)
    }

    private func iconBox(_ emoji: String, _ bg: Color) -> some View {
        Text(emoji).font(.system(size: 16))
            .frame(width: 34, height: 34)
            .background(RoundedRectangle(cornerRadius: 12).fill(bg))
    }
}

// MARK: - Achievements catalog (ported from Android SettingsScreen.kt)

struct Ach: Identifiable {
    let id = UUID()
    let emoji: String, title: String, desc: String, cur: Int, target: Int

    static func catalog(solved: Int, streak: Int, albums: Int, en: Bool) -> [Ach] {
        [
            Ach(emoji: "🌱", title: en ? "First solve" : "Первое решение", desc: en ? "Solve your first task" : "Реши свою первую задачу", cur: solved, target: 1),
            Ach(emoji: "🔥", title: en ? "3-day streak" : "Серия 3 дня", desc: en ? "Solve 3 days in a row" : "Решай 3 дня подряд", cur: streak, target: 3),
            Ach(emoji: "✏️", title: en ? "10 solutions" : "10 решений", desc: en ? "Solve 10 tasks" : "Реши 10 задач", cur: solved, target: 10),
            Ach(emoji: "🦉", title: en ? "25 solutions" : "25 решений", desc: en ? "Solve 25 tasks" : "Реши 25 задач", cur: solved, target: 25),
            Ach(emoji: "🎓", title: en ? "3 folders" : "3 папки", desc: en ? "Create 3 folders" : "Создай 3 папки", cur: albums, target: 3),
            Ach(emoji: "📚", title: en ? "5 folders" : "5 папок", desc: en ? "Create 5 folders" : "Создай 5 папок", cur: albums, target: 5),
            Ach(emoji: "📅", title: en ? "Week streak" : "Серия 7 дней", desc: en ? "Solve 7 days in a row" : "Решай 7 дней подряд", cur: streak, target: 7),
            Ach(emoji: "💯", title: en ? "100 solutions" : "100 решений", desc: en ? "Solve 100 tasks" : "Реши 100 задач", cur: solved, target: 100),
            Ach(emoji: "🌟", title: en ? "Month streak" : "Серия 30 дней", desc: en ? "Solve 30 days in a row" : "Решай 30 дней подряд", cur: streak, target: 30),
            Ach(emoji: "🏆", title: en ? "500 solutions" : "500 решений", desc: en ? "Solve 500 tasks" : "Реши 500 задач", cur: solved, target: 500),
        ]
    }
}
