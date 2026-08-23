import Foundation
import UIKit

final class DeviceRepository {
    private let api: APIClient
    init(api: APIClient) { self.api = api }

    func register(token: String) async throws {
        struct Req: Codable {
            let platform: String
            let token: String
            let appVersion: String?
            let locale: String?
        }
        struct Resp: Codable { let id: String }
        let req = Req(
            platform: "ios",
            token: token,
            appVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String,
            locale: Locale.preferredLanguages.first
        )
        let _: Resp = try await api.post("/v1/devices", body: req)
    }

    func unregister(token: String) async throws {
        struct Empty: Codable {}
        let _: Empty = try await api.post("/v1/devices/\(token)", body: Empty())
        // Note: backend uses DELETE; APIClient currently exposes only post/get.
        // Add a delete helper when this becomes a real flow.
    }
}
