import Foundation

final class TaskRepository {
    private let api: APIClient
    private var taskCache: [String: TaskDetail] = [:]
    init(api: APIClient) { self.api = api }

    func submitImage(data: Data, caption: String?) async throws -> String {
        var fields: [String: String] = [:]
        if let caption { fields["caption"] = caption }
        let resp: TaskRef = try await api.postMultipart(
            "/v1/tasks",
            fields: fields,
            file: (name: "file", filename: "task.jpg", data: data, mime: "image/jpeg")
        )
        return resp.taskId
    }

    func submitText(text: String) async throws -> String {
        let resp: TaskRef = try await api.post("/v1/tasks/text", body: TaskCreateText(text: text))
        return resp.taskId
    }

    func cachedTask(_ id: String) -> TaskDetail? { taskCache[id] }

    func get(id: String) async throws -> TaskDetail {
        let t: TaskDetail = try await api.get("/v1/tasks/\(id)")
        taskCache[id] = t
        return t
    }

    func list(limit: Int, before: String?, albumId: String? = nil, q: String? = nil) async throws -> TaskList {
        var query: [URLQueryItem] = [URLQueryItem(name: "limit", value: "\(limit)")]
        if let before { query.append(URLQueryItem(name: "before", value: before)) }
        if let albumId { query.append(URLQueryItem(name: "album_id", value: albumId)) }
        if let q, !q.isEmpty { query.append(URLQueryItem(name: "q", value: q)) }
        return try await api.get("/v1/tasks", query: query)
    }

    func rename(id: String, title: String) async throws -> TaskDetail {
        let t: TaskDetail = try await api.patch("/v1/tasks/\(id)", body: TaskUpdateRequest(title: title))
        taskCache[id] = t
        return t
    }

    func chatHistory(id: String) async throws -> ChatThread {
        try await api.get("/v1/tasks/\(id)/chat")
    }

    func sendChat(id: String, message: String) async throws -> ChatThread {
        try await api.post("/v1/tasks/\(id)/chat", body: ChatSendRequest(message: message))
    }

    /// Follow-up question with an attached photo (vision context) + caption.
    func sendChatImage(id: String, data: Data, caption: String) async throws -> ChatThread {
        try await api.postMultipart(
            "/v1/tasks/\(id)/chat/image",
            fields: ["message": caption],
            file: (name: "file", filename: "attach.jpg", data: data, mime: "image/jpeg"))
    }
}
