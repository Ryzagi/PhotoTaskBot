import Foundation

struct Balance: Codable, Hashable {
    let daily: Int
    let subscription: Int
}

struct Me: Codable, Hashable {
    let id: String
    let telegramLinked: Bool
    let languageCode: String
    let balance: Balance
}

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
    let solutions: [Problem]
}

struct TaskDetail: Codable, Hashable {
    let id: String
    let status: String  // "pending" | "done" | "failed"
    let inputKind: String
    let solution: Solution?
    let thumbnailUrl: String?
    let createdAt: String
}

struct TaskListItem: Codable, Hashable, Identifiable {
    let id: String
    let preview: String
    let inputKind: String
    let createdAt: String
}

struct TaskList: Codable {
    let items: [TaskListItem]
    let nextBefore: String?
}
