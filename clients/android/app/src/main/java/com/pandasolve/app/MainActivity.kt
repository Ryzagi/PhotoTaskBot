package com.pandasolve.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.LaunchedEffect
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
            // enableEdgeToEdge()'s default detector reads the *system* night mode,
            // so picking "dark" inside the app while the phone is in light mode
            // would leave dark status-bar icons on the dark paper. Re-apply the
            // styles whenever our own `dark` flag flips.
            LaunchedEffect(dark) {
                enableEdgeToEdge(
                    statusBarStyle = SystemBarStyle.auto(TRANSPARENT, TRANSPARENT) { dark },
                    navigationBarStyle = SystemBarStyle.auto(LIGHT_SCRIM, DARK_SCRIM) { dark },
                )
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

// Scrims the platform draws behind a 3-button navigation bar when it can't be
// fully transparent (values from the androidx edge-to-edge guidance).
private const val TRANSPARENT = android.graphics.Color.TRANSPARENT
private val LIGHT_SCRIM = android.graphics.Color.argb(0xe6, 0xFF, 0xFF, 0xFF)
private val DARK_SCRIM = android.graphics.Color.argb(0x80, 0x1b, 0x1b, 0x1b)
