import Foundation

final class TaskRepository {
    private let api: APIClient
    init(api: APIClient) { self.api = api }

    func submitImage(data: Data, caption: String?) async throws -> String {
        struct Resp: Codable { let taskId: String; let status: String }
        var fields: [String: String] = [:]
        if let caption { fields["caption"] = caption }
        let resp: Resp = try await api.postMultipart(
            "/v1/tasks",
            fields: fields,
            file: (name: "file", filename: "task.jpg", data: data, mime: "image/jpeg")
        )
        return resp.taskId
    }

    func submitText(text: String) async throws -> String {
        struct Req: Codable { let text: String }
        struct Resp: Codable { let taskId: String; let status: String }
        let resp: Resp = try await api.post("/v1/tasks/text", body: Req(text: text))
        return resp.taskId
    }

    func get(id: String) async throws -> TaskDetail {
        try await api.get("/v1/tasks/\(id)")
    }

    func list(limit: Int, before: String?) async throws -> TaskList {
        var q: [URLQueryItem] = [URLQueryItem(name: "limit", value: "\(limit)")]
        if let before { q.append(URLQueryItem(name: "before", value: before)) }
        return try await api.get("/v1/tasks", query: q)
    }
}
