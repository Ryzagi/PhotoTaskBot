package com.pandasolve.app.push

import android.app.NotificationManager
import android.content.Intent
import android.net.Uri
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.pandasolve.app.MainActivity
import com.pandasolve.app.R
import com.pandasolve.app.data.repository.DeviceRepository
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import timber.log.Timber

@AndroidEntryPoint
class FcmService : FirebaseMessagingService() {

    @Inject lateinit var devices: DeviceRepository
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        Timber.i("FCM token refreshed")
        scope.launch {
            runCatching { devices.register(token) }
                .onFailure { Timber.w(it, "device register failed") }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val topic = message.data["topic"] ?: "task.completed"
        val taskId = message.data["task_id"]
        val title = message.notification?.title ?: "PandaSolve"
        val body = message.notification?.body.orEmpty()

        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("pandasolve://task/$taskId"), this, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val pi = android.app.PendingIntent.getActivity(this, 0, intent,
            android.app.PendingIntent.FLAG_IMMUTABLE or android.app.PendingIntent.FLAG_UPDATE_CURRENT)

        val channel = when (topic) {
            "task.completed", "task.failed" -> "task_updates"
            "app.broadcast" -> "promo"
            else -> "account"
        }
        val notif = NotificationCompat.Builder(this, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setContentIntent(pi)
            .setAutoCancel(true)
            .build()
        val mgr = ContextCompat.getSystemService(this, NotificationManager::class.java) ?: return
        mgr.notify(taskId?.hashCode() ?: 0, notif)
    }
}
