import Foundation

final class UserRepository {
    private let api: APIClient
    init(api: APIClient) { self.api = api }

    func me() async throws -> Me {
        try await api.get("/v1/me")
    }

    func startLink() async throws -> String {
        struct Resp: Codable { let code: String; let expiresAt: String }
        let resp: Resp = try await api.post("/v1/auth/link/start", body: EmptyBody())
        return resp.code
    }

    func updateLanguage(_ code: String) async throws -> Me {
        struct Req: Codable { let languageCode: String }
        return try await api.post("/v1/me", body: Req(languageCode: code))
    }
}

struct EmptyBody: Codable {}
