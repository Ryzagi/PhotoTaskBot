import Foundation
import Observation

/// Lightweight DI container. Built once at app start; passed via .environment(_:).
@Observable
final class AppEnvironment {
    let auth: SupabaseAuth
    let api: APIClient
    let userRepo: UserRepository
    let taskRepo: TaskRepository
    let deviceRepo: DeviceRepository

    private init(
        auth: SupabaseAuth,
        api: APIClient,
        userRepo: UserRepository,
        taskRepo: TaskRepository,
        deviceRepo: DeviceRepository
    ) {
        self.auth = auth
        self.api = api
        self.userRepo = userRepo
        self.taskRepo = taskRepo
        self.deviceRepo = deviceRepo
    }

    static let live: AppEnvironment = {
        let auth = SupabaseAuth.shared
        let api = APIClient(auth: auth)
        return AppEnvironment(
            auth: auth,
            api: api,
            userRepo: UserRepository(api: api),
            taskRepo: TaskRepository(api: api),
            deviceRepo: DeviceRepository(api: api)
        )
    }()
}
