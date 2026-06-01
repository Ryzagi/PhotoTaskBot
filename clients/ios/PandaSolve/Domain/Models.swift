import Foundation

// Codable models for the /v1 contract (bot/openapi.json). The APIClient uses
// .convertFromSnakeCase / .convertToSnakeCase, so Swift stays camelCase.

struct Balance: Codable, Hashable {
    let daily: Int
    let subscription: Int
}

struct Me: Codable, Hashable {
    let id: String
    let telegramLinked: Bool
    let languageCode: String
    let displayName: String?
    let balance: Balance
    let createdAt: String
    let solvedCount: Int
    let streak: Int
}

struct UpdateMeRequest: Codable {
    var languageCode: String? = nil
    var displayName: String? = nil
}

// MARK: - Solutions

struct SolutionBlock: Codable, Hashable {
    let type: String   // "text" | "math"
    let content: String
}

struct Problem: Codable, Hashable {
    let problem: String
    let steps: [SolutionBlock]
    let solution: [SolutionBlock]
}

struct Solution: Codable, Hashable {
    let title: String?
    let solutions: [Problem]
}

// MARK: - Tasks

struct TaskRef: Codable, Hashable {
    let taskId: String
    let status: String
}

struct TaskCreateText: Codable {
    let text: String
}

struct TaskUpdateRequest: Codable {
    let title: String
}

struct TaskDetail: Codable, Hashable {
    let id: String
    let status: String          // "pending" | "done" | "failed"
    let inputKind: String       // "image" | "text" | "latex"
    let inputText: String?
    let solution: Solution?
    let albumId: String?
    let modelUsed: String?
    let errorCode: String?
    let thumbnailUrl: String?
    let imageUrl: String?
    let createdAt: String
    let completedAt: String?
}

struct TaskListItem: Codable, Hashable, Identifiable {
    let id: String
    let status: String
    let inputKind: String
    let preview: String
    let thumbnailUrl: String?
    let createdAt: String
}

struct TaskList: Codable {
    let items: [TaskListItem]
    let nextBefore: String?
}

// MARK: - Folders (a.k.a. albums in the API)

struct Album: Codable, Hashable, Identifiable {
    let id: String
    let name: String
    let emoji: String?
    let color: String?
    let taskCount: Int
    let updatedAt: String
}

struct AlbumList: Codable {
    let items: [Album]
}

struct AlbumCreateRequest: Codable {
    let name: String
    var emoji: String? = nil
    var color: String? = nil
}

struct AlbumUpdateRequest: Codable {
    var name: String? = nil
    var emoji: String? = nil
    var color: String? = nil
}

struct AssignAlbumRequest: Codable {
    var albumId: String? = nil
}

// MARK: - Chat (follow-up Q&A)

struct ChatMessage: Codable, Hashable, Identifiable {
    let role: String            // "user" | "assistant"
    let content: String
    let createdAt: String
    var id: String { "\(role)-\(createdAt)-\(content.hashValue)" }
}

struct ChatThread: Codable {
    let messages: [ChatMessage]
    let remaining: Int
}

struct ChatSendRequest: Codable {
    let message: String
}

// MARK: - Misc

struct LinkStartResponse: Codable {
    let code: String
    let expiresAt: String
}

struct RegisterDeviceRequest: Codable {
    let platform: String
    let token: String
    var appVersion: String? = nil
    var locale: String? = nil
}

struct TopupUrl: Codable {
    let url: String
}
