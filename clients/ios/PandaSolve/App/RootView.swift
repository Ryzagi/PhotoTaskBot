import SwiftUI

struct RootView: View {
    @Environment(AppEnvironment.self) private var env
    @State private var path = NavigationPath()
    @State private var isSignedIn: Bool

    init() {
        _isSignedIn = State(initialValue: SupabaseAuth.shared.isSignedIn)
    }

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if isSignedIn {
                    HomeView(onOpenTask: { id in path.append(Route.task(id)) },
                             onOpenHistory: { path.append(Route.history) },
                             onOpenSolve: { path.append(Route.solve) },
                             onOpenSettings: { path.append(Route.settings) })
                } else {
                    SignInView(onSignedIn: { isSignedIn = true })
                }
            }
            .navigationDestination(for: Route.self) { route in
                switch route {
                case .solve:
                    SolveView(onCreated: { id in path.append(Route.task(id)) })
                case .task(let id):
                    TaskDetailView(taskId: id)
                case .history:
                    HistoryView(onSelect: { id in path.append(Route.task(id)) })
                case .settings:
                    SettingsView()
                }
            }
        }
    }
}

enum Route: Hashable {
    case solve
    case task(String)
    case history
    case settings
}
