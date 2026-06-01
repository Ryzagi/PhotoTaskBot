import Foundation

/// Folders (called "albums" in the API). Includes a session count cache so
/// Profile can show the folder count without waiting.
final class AlbumRepository {
    private let api: APIClient
    private(set) var lastCount: Int?
    init(api: APIClient) { self.api = api }

    func list() async throws -> [Album] {
        let resp: AlbumList = try await api.get("/v1/albums")
        lastCount = resp.items.count
        return resp.items
    }

    func create(name: String, emoji: String?, color: String?) async throws -> Album {
        try await api.post("/v1/albums", body: AlbumCreateRequest(name: name, emoji: emoji, color: color))
    }

    func update(id: String, name: String?, emoji: String?, color: String?) async throws -> Album {
        try await api.patch("/v1/albums/\(id)", body: AlbumUpdateRequest(name: name, emoji: emoji, color: color))
    }

    func delete(id: String) async throws {
        try await api.delete("/v1/albums/\(id)")
    }

    /// Assign (or clear with nil) a task's folder. The endpoint echoes back ids; ignored.
    func assign(taskId: String, albumId: String?) async throws {
        struct AssignResp: Codable {}
        let _: AssignResp = try await api.post("/v1/tasks/\(taskId)/album", body: AssignAlbumRequest(albumId: albumId))
    }
}
