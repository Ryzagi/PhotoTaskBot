import SwiftUI

struct HomeView: View {
    let onOpenTask: (String) -> Void
    let onOpenHistory: () -> Void
    let onOpenSolve: () -> Void
    let onOpenSettings: () -> Void

    @Environment(AppEnvironment.self) private var env
    @State private var daily = 0
    @State private var subscription = 0
    @State private var error: String?

    var body: some View {
        VStack(spacing: 20) {
            HStack {
                Text("🐼 PandaSolve").font(.title.bold())
                Spacer()
                Button(action: onOpenHistory) { Image(systemName: "clock.arrow.circlepath") }
                Button(action: onOpenSettings) { Image(systemName: "gearshape") }
            }
            .padding(.bottom, 8)

            VStack(alignment: .leading) {
                Text("Сегодня осталось")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)
                Text("\(daily)")
                    .font(.system(size: 56, weight: .heavy))
                if subscription > 0 {
                    Label("\(subscription) донат", systemImage: "star.fill")
                        .padding(.top, 4)
                        .foregroundStyle(.orange)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))

            Spacer()

            Button(action: onOpenSolve) {
                Text("Решить задачу")
                    .font(.title3.bold())
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .buttonStyle(.borderedProminent)

            if let error { Text(error).foregroundStyle(.red) }
        }
        .padding()
        .task { await refresh() }
        .navigationBarBackButtonHidden(true)
    }

    private func refresh() async {
        do {
            let me = try await env.userRepo.me()
            daily = me.balance.daily
            subscription = me.balance.subscription
        } catch { self.error = error.localizedDescription }
    }
}
