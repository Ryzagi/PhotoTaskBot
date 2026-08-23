package com.pandasolve.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.pandasolve.app.ui.AppNavigation
import com.pandasolve.app.ui.theme.PandaSolveTheme
import com.pandasolve.app.ui.theme.ThemeManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var themeManager: ThemeManager

    // Android 13+ requires runtime opt-in for notifications; without it FCM task
    // pushes are silently dropped. Ask once on launch (result handled by the OS UI).
    private val notifPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            notifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
        setContent {
            val mode by themeManager.mode.collectAsState()
            val dark = when (mode) {
                ThemeManager.LIGHT -> false
                ThemeManager.DARK -> true
                else -> isSystemInDarkTheme()
            }
            PandaSolveTheme(dark = dark) {
                Surface(color = MaterialTheme.colorScheme.background) {
                    // Edge-to-edge: keep content below the status bar / notch.
                    Box(Modifier.fillMaxSize().statusBarsPadding()) {
                        AppNavigation()
                    }
                }
            }
        }
    }
}
