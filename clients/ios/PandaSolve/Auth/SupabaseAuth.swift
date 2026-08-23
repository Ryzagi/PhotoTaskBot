import AuthenticationServices
import CryptoKit
import Foundation
import KeychainAccess
import Supabase
import UIKit

/// Supabase Auth bridge for iOS.
///
/// - Email/password: direct Supabase call.
/// - Apple: native `ASAuthorizationAppleIDProvider` (required by App Store
///   guideline 4.8 when offering any third-party sign-in). The identity
///   token is then passed to Supabase via `signInWithIdToken`.
/// - Google: Supabase's OAuth flow (`signInWithOAuth(provider: .google)`),
///   which opens `ASWebAuthenticationSession` under the hood. The redirect
///   URL `app.pandasolve.client://login-callback` must be registered both in
///   Supabase Auth settings and in Info.plist (CFBundleURLTypes).
final class SupabaseAuth: NSObject {
    static let shared = SupabaseAuth()

    let client: SupabaseClient
    private let keychain = Keychain(service: "app.pandasolve.client.auth")
    private var appleHandler: AppleSignInHandler?

    private override init() {
        let url = URL(string: Bundle.main.object(forInfoDictionaryKey: "SUPABASE_URL") as? String ?? "")!
        let key = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_ANON_KEY") as? String ?? ""
        self.client = SupabaseClient(supabaseURL: url, supabaseKey: key)
        super.init()
    }

    var isSignedIn: Bool { client.auth.currentSession != nil }

    func signIn(email: String, password: String) async throws {
        try await client.auth.signIn(email: email, password: password)
    }

    /// Create an email/password account. Returns true when a session is active
    /// immediately (Supabase "Confirm email" OFF); false when a confirmation
    /// email was sent and the user must verify first. Mirrors Android.
    func signUp(email: String, password: String) async throws -> Bool {
        try await client.auth.signUp(email: email, password: password)
        return client.auth.currentSession != nil
    }

    // MARK: - Apple

    func signInWithApple() async throws {
        let nonce = Self.randomNonce()
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]
        request.nonce = Self.sha256(nonce)

        let handler = AppleSignInHandler()
        appleHandler = handler                 // strong ref while modal lives
        defer { appleHandler = nil }
        let result = try await handler.perform(request: request)

        guard
            let credential = result.credential as? ASAuthorizationAppleIDCredential,
            let tokenData = credential.identityToken,
            let idToken = String(data: tokenData, encoding: .utf8)
        else {
            throw SupabaseAuthError.invalidAppleCredential
        }

        try await client.auth.signInWithIdToken(
            credentials: .init(provider: .apple, idToken: idToken, nonce: nonce)
        )
    }

    // MARK: - Google

    func signInWithGoogle() async throws {
        let redirect = URL(string: "app.pandasolve.client://login-callback")!
        try await client.auth.signInWithOAuth(provider: .google, redirectTo: redirect) { session in
            session.prefersEphemeralWebBrowserSession = false
        }
    }

    // MARK: - Misc

    func signOut() async throws { try await client.auth.signOut() }

    func currentAccessToken() async throws -> String? {
        client.auth.currentSession?.accessToken
    }

    // MARK: - Helpers

    private static func randomNonce(length: Int = 32) -> String {
        let alphabet: [Character] = Array("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-._")
        var bytes = [UInt8](repeating: 0, count: length)
        _ = SecRandomCopyBytes(kSecRandomDefault, length, &bytes)
        return String(bytes.map { alphabet[Int($0) % alphabet.count] })
    }

    private static func sha256(_ input: String) -> String {
        let digest = SHA256.hash(data: Data(input.utf8))
        return digest.map { String(format: "%02x", $0) }.joined()
    }
}

enum SupabaseAuthError: Error {
    case invalidAppleCredential
    case userCancelled
}

/// Wraps `ASAuthorizationController` with async/await.
private final class AppleSignInHandler: NSObject,
    ASAuthorizationControllerDelegate,
    ASAuthorizationControllerPresentationContextProviding {

    private var continuation: CheckedContinuation<ASAuthorization, Error>?

    func perform(request: ASAuthorizationAppleIDRequest) async throws -> ASAuthorization {
        try await withCheckedThrowingContinuation { cont in
            continuation = cont
            let controller = ASAuthorizationController(authorizationRequests: [request])
            controller.delegate = self
            controller.presentationContextProvider = self
            controller.performRequests()
        }
    }

    func authorizationController(controller: ASAuthorizationController,
                                 didCompleteWithAuthorization authorization: ASAuthorization) {
        continuation?.resume(returning: authorization); continuation = nil
    }

    func authorizationController(controller: ASAuthorizationController,
                                 didCompleteWithError error: Error) {
        if let asError = error as? ASAuthorizationError, asError.code == .canceled {
            continuation?.resume(throwing: SupabaseAuthError.userCancelled)
        } else {
            continuation?.resume(throwing: error)
        }
        continuation = nil
    }

    @MainActor
    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow } ?? ASPresentationAnchor()
    }
}
