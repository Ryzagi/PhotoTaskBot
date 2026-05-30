import Foundation
import UIKit
import UserNotifications

@MainActor
final class PushService: NSObject, UNUserNotificationCenterDelegate {
    static let shared = PushService()

    func register(application: UIApplication) async {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .badge, .sound])
            if granted { application.registerForRemoteNotifications() }
        } catch {
            print("Push authorization failed:", error.localizedDescription)
        }
    }

    /// Call from AppDelegate.didRegisterForRemoteNotificationsWithDeviceToken.
    /// Sends the APNs device token to /v1/devices via DeviceRepository.
    func handleDeviceToken(_ deviceToken: Data) async {
        let hex = deviceToken.map { String(format: "%02x", $0) }.joined()
        do {
            try await AppEnvironment.live.deviceRepo.register(token: hex)
        } catch {
            print("Device registration failed (non-fatal):", error.localizedDescription)
        }
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completion: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completion([.banner, .badge, .sound])
    }
}
