import SwiftUI

struct RootView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.colorScheme) private var systemScheme
    @State private var prefs = AppPrefs.shared
    @State private var path = NavigationPath()
    @State private var tab: CuteTab = .home
    @State private var showCamera = false
    @State private var isSignedIn = SupabaseAuth.shared.isSignedIn

    var body: some View {
        let dark = prefs.theme == "dark" || (prefs.theme == "system" && systemScheme == .dark)
        NavigationStack(path: $path) {
            Group {
                if !isSignedIn {
                    SignInView(onSignedIn: { isSignedIn = true })
                } else if tab == .profile {
                    SettingsView(onHome: { tab = .home },
                                 onCamera: { showCamera = true },
                                 onSignOut: { isSignedIn = false; tab = .home })
                } else {
                    HomeView(onOpenTask: { id in path.append(Route.task(id)) },
                             onOpenSolve: { showCamera = true },
                             onOpenSettings: { tab = .profile })
                }
            }
            .navigationDestination(for: Route.self) { route in
                if case .task(let id) = route { TaskDetailView(taskId: id) }
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            SolveView(onCreated: { id in
                showCamera = false
                path.append(Route.task(id))
            })
            .environment(\.cute, dark ? .dark : .light)
            .environment(\.strings, Strings.forCode(prefs.language))
        }
        .environment(\.cute, dark ? .dark : .light)
        .environment(\.strings, Strings.forCode(prefs.language))
        .preferredColorScheme(prefs.theme == "system" ? nil : (dark ? .dark : .light))
        .tint(dark ? CutePalette.dark.mintDeep : CutePalette.light.mintDeep)
    }
}

enum Route: Hashable {
    case task(String)
}
