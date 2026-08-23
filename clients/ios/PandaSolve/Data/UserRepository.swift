import Foundation

final class UserRepository {
    private let api: APIClient
    /// Last loaded profile, kept so screens can show counts instantly on re-open.
    private(set) var lastMe: Me?

    init(api: APIClient) { self.api = api }

    func me() async throws -> Me {
        let m: Me = try await api.get("/v1/me")
        lastMe = m
        return m
    }

    func startLink() async throws -> String {
        let resp: LinkStartResponse = try await api.post("/v1/auth/link/start", body: EmptyBody())
        return resp.code
    }

    func updateLanguage(_ code: String) async throws -> Me {
        try await api.post("/v1/me", body: UpdateMeRequest(languageCode: code))
    }

    func updateDisplayName(_ name: String) async throws -> Me {
        try await api.post("/v1/me", body: UpdateMeRequest(displayName: name))
    }
}

struct EmptyBody: Codable {}
