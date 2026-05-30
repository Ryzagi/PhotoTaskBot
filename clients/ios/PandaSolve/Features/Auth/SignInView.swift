import SwiftUI

struct SignInView: View {
    let onSignedIn: () -> Void

    @Environment(AppEnvironment.self) private var env
    @State private var email = ""
    @State private var password = ""
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        VStack(spacing: 16) {
            Text("🐼 PandaSolve")
                .font(.system(size: 40, weight: .heavy))
                .padding(.bottom, 16)

            TextField("Email", text: $email)
                .textContentType(.emailAddress)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .textFieldStyle(.roundedBorder)

            SecureField("Пароль", text: $password)
                .textFieldStyle(.roundedBorder)

            Button("Войти", action: signInEmail)
                .buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity)
                .disabled(busy)

            Button("Continue with Apple", action: signInApple)
                .frame(maxWidth: .infinity)
                .disabled(busy)

            Button("Continue with Google", action: signInGoogle)
                .frame(maxWidth: .infinity)
                .disabled(busy)

            if let error { Text(error).foregroundStyle(.red) }
        }
        .padding(24)
    }

    private func signInEmail() {
        Task {
            busy = true; error = nil
            do {
                try await env.auth.signIn(email: email, password: password)
                onSignedIn()
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func signInApple() {
        Task {
            busy = true; error = nil
            do {
                try await env.auth.signInWithApple()
                onSignedIn()
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }

    private func signInGoogle() {
        Task {
            busy = true; error = nil
            do {
                try await env.auth.signInWithGoogle()
                onSignedIn()
            } catch { self.error = error.localizedDescription }
            busy = false
        }
    }
}
