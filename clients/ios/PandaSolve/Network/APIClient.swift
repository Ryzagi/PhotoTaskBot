import Foundation

/// Thin URLSession-based client. Replace with the swift-openapi-generator output
/// once `bot/openapi.json` is published; the shape below keeps screens
/// compilable in the meantime.
final class APIClient {
    private let baseURL: URL
    private let auth: SupabaseAuth
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(auth: SupabaseAuth) {
        self.baseURL = URL(string: Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String ?? "https://api.pandasolve.app")!
        self.auth = auth
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 30
        cfg.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: cfg)
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
    }

    func get<T: Decodable>(_ path: String, query: [URLQueryItem] = []) async throws -> T {
        var url = baseURL.appendingPathComponent(path)
        if !query.isEmpty {
            var comp = URLComponents(url: url, resolvingAgainstBaseURL: true)!
            comp.queryItems = query
            url = comp.url!
        }
        var req = URLRequest(url: url)
        req.httpMethod = "GET"
        try await attachAuth(&req)
        let (data, response) = try await session.data(for: req)
        try checkStatus(response, data: data)
        return try decoder.decode(T.self, from: data)
    }

    func post<T: Decodable, B: Encodable>(_ path: String, body: B) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try encoder.encode(body)
        try await attachAuth(&req)
        let (data, response) = try await session.data(for: req)
        try checkStatus(response, data: data)
        return try decoder.decode(T.self, from: data)
    }

    func postMultipart<T: Decodable>(_ path: String, fields: [String: String], file: (name: String, filename: String, data: Data, mime: String)) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = "POST"
        let boundary = "PandaSolve-" + UUID().uuidString
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        var body = Data()
        for (k, v) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(k)\"\r\n\r\n".data(using: .utf8)!)
            body.append(v.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(file.name)\"; filename=\"\(file.filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(file.mime)\r\n\r\n".data(using: .utf8)!)
        body.append(file.data)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = body
        try await attachAuth(&req)
        let (data, response) = try await session.data(for: req)
        try checkStatus(response, data: data)
        return try decoder.decode(T.self, from: data)
    }

    private func attachAuth(_ req: inout URLRequest) async throws {
        if let token = try? await auth.currentAccessToken() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    private func checkStatus(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        if !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.http(status: http.statusCode, body: body)
        }
    }
}

enum APIError: Error {
    case invalidResponse
    case http(status: Int, body: String)
}
