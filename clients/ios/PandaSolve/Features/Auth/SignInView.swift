import SwiftUI

struct SignInView: View {
    @Environment(AppEnvironment.self) private var env
    @Environment(\.cute) private var c
    @Environment(\.strings) private var t
    let onSignedIn: () -> Void

    @State private var email = ""
    @State private var password = ""
    @State private var mode = "signin"        // signin | signup
    @State private var busy = false
    @State private var error: AuthUIError?
    @State private var pendingConfirmation = false
    @State private var bob = false

    var body: some View {
        ZStack {
            DotPaper(paper: c.paper, dot: c.ink.opacity(0.07))
            ScrollView {
                VStack(spacing: 0) {
                    HStack(spacing: 6) {
                        Spacer()
                        ForEach(["ru", "en"], id: \.self) { code in
                            let sel = AppPrefs.shared.language == code
                            Text(code.uppercased()).font(nunito(12, .heavy))
                                .foregroundStyle(sel ? c.mintDeep : c.inkFaint)
                                .padding(.horizontal, 12).padding(.vertical, 6)
                                .background(Capsule().fill(sel ? c.mintSoft : c.card))
                                .onTapGesture { AppPrefs.shared.language = code }
                        }
                    }
                    .padding(.top, 8)

                    PandaFace().frame(width: 118, height: 118)
                        .offset(y: bob ? -10 : 0)
                        .animation(.easeInOut(duration: 1.8).repeatForever(autoreverses: true), value: bob)
                        .onAppear { bob = true }
                        .padding(.top, 8)

                    Text(t.signinGreeting).font(caveat(30, .bold)).foregroundStyle(c.coralDeep)
                    Text(t.signinTitle).font(baloo(30, .heavy)).foregroundStyle(c.ink)
                        .multilineTextAlignment(.center)
                    Text(t.signinSubtitle).font(nunito(14, .semibold)).foregroundStyle(c.inkSoft)
                        .multilineTextAlignment(.center).frame(maxWidth: 260).padding(.top, 10)

                    HStack(spacing: 0) {
                        ForEach([("signin", t.tabSignIn), ("signup", t.tabSignUp)], id: \.0) { m, lbl in
                            let sel = mode == m
                            Text(lbl).font(nunito(13, .heavy))
                                .foregroundStyle(sel ? .white : c.inkSoft)
                                .padding(.horizontal, 20).padding(.vertical, 8)
                                .background(Capsule().fill(sel ? c.mintDeep : .clear))
                                .onTapGesture { mode = m }
                        }
                    }
                    .padding(3)
                    .background(Capsule().fill(c.card))
                    .overlay(Capsule().stroke(c.line, lineWidth: 2))
                    .padding(.top, 22)

                    VStack(spacing: 12) {
                        CuteField(label: t.fieldEmail, value: $email, focusTint: true, placeholder: "you@example.com")
                        CuteField(label: t.fieldPassword, value: $password, secure: true, placeholder: "••••••••")
                    }
                    .padding(.top, 18)

                    CandyButton(text: mode == "signup" ? t.signupButton : t.signinButton, enabled: !busy) { submit() }
                        .padding(.top, 16)

                    HStack {
                        Capsule().fill(c.line).frame(height: 2)
                        Text("  \(t.orDivider)  ").font(nunito(11, .heavy)).foregroundStyle(c.inkFaint)
                        Capsule().fill(c.line).frame(height: 2)
                    }
                    .padding(.vertical, 14)

                    HStack(spacing: 10) {
                        CandyButton(text: "Google", variant: .ghost, enabled: !busy) { signInGoogle() }
                        ZStack(alignment: .topTrailing) {
                            CandyButton(text: "Apple", variant: .ghost, enabled: false) {}
                                .opacity(0.55)
                            Text(t.soon.uppercased()).font(nunito(9, .heavy)).foregroundStyle(.white)
                                .padding(.horizontal, 8).padding(.vertical, 2)
                                .background(Capsule().fill(c.lav))
                                .offset(x: -6, y: -5)
                        }
                    }

                    if let msg = error?.text(t) {
                        Text(msg).font(nunito(13, .bold)).foregroundStyle(c.coralDeep)
                            .multilineTextAlignment(.center).padding(.top, 14)
                    }
                    if pendingConfirmation {
                        Text(t.checkInbox).font(nunito(13, .bold)).foregroundStyle(c.mintDeep)
                            .multilineTextAlignment(.center).padding(.top, 14)
                    }

                    Text(t.signinTerms).font(nunito(11, .semibold)).foregroundStyle(c.inkFaint)
                        .multilineTextAlignment(.center).padding(.top, 20)
                    Link(t.privacyPolicy,
                         destination: URL(string: (Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String ?? "https://panda-api.upword.live") + "/privacy")!)
                        .font(nunito(11, .heavy)).foregroundStyle(c.mintDeep)
                        .padding(.top, 6).padding(.bottom, 28)
                }
                .padding(.horizontal, 26)
            }
        }
    }

    private func submit() {
        guard !email.isEmpty, !password.isEmpty else { error = .emptyFields; return }
        run { [email, password, mode] in
            if mode == "signup" {
                let signedIn = try await env.auth.signUp(email: email, password: password)
                if signedIn { onSignedIn() } else { pendingConfirmation = true }
            } else {
                try await env.auth.signIn(email: email, password: password)
                onSignedIn()
            }
        }
    }

    private func signInGoogle() {
        run { try await env.auth.signInWithGoogle(); onSignedIn() }
    }

    private func run(_ op: @escaping () async throws -> Void) {
        busy = true; error = nil; pendingConfirmation = false
        Task {
            do { try await op() } catch { print("AUTH_DEBUG error: \(error)"); self.error = AuthUIError.from(error) }
            busy = false
        }
    }
}
