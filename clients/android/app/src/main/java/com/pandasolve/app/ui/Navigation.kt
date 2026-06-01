package com.pandasolve.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.navigation.navDeepLink
import com.pandasolve.app.auth.AuthState
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.i18n.stringsFor
import com.pandasolve.app.ui.feature.auth.SignInScreen
import com.pandasolve.app.ui.feature.home.HomeScreen
import com.pandasolve.app.ui.feature.settings.ProfileScreen
import com.pandasolve.app.ui.feature.solve.CameraScreen
import com.pandasolve.app.ui.feature.task.TaskDetailScreen

object Routes {
    const val SPLASH = "splash"
    const val SIGN_IN = "sign_in"
    const val HOME = "home"
    const val CAMERA = "camera"
    const val PROFILE = "profile"
    const val TASK = "task/{id}"
    fun task(id: String) = "task/$id"
}

@Composable
fun AppNavigation(root: RootViewModel = hiltViewModel()) {
    val nav = rememberNavController()
    val authState by root.authState.collectAsStateWithLifecycle()
    val language by root.language.collectAsStateWithLifecycle()
    val currentRoute = nav.currentBackStackEntryAsState().value?.destination?.route

    // Auth gate: while the persisted session is restored we sit on SPLASH, then
    // route once. Guarded by `currentRoute == SPLASH` so a notification deep link
    // (which lands directly on a task) isn't clobbered.
    LaunchedEffect(authState, currentRoute) {
        if (currentRoute != Routes.SPLASH) return@LaunchedEffect
        when (authState) {
            AuthState.SIGNED_IN -> nav.navigate(Routes.HOME) {
                popUpTo(Routes.SPLASH) { inclusive = true }
            }
            AuthState.SIGNED_OUT -> nav.navigate(Routes.SIGN_IN) {
                popUpTo(Routes.SPLASH) { inclusive = true }
            }
            AuthState.LOADING -> Unit
        }
    }

    // Bottom-tab destinations should not stack; pop up to home and stay single-top.
    fun goTab(route: String) = nav.navigate(route) {
        popUpTo(Routes.HOME)
        launchSingleTop = true
    }

    CompositionLocalProvider(LocalStrings provides stringsFor(language)) {
    NavHost(nav, startDestination = Routes.SPLASH) {
        composable(Routes.SPLASH) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        }
        composable(Routes.SIGN_IN) {
            SignInScreen(onSignedIn = {
                nav.navigate(Routes.HOME) { popUpTo(Routes.SIGN_IN) { inclusive = true } }
            })
        }
        composable(Routes.HOME) {
            HomeScreen(
                onCamera = { nav.navigate(Routes.CAMERA) },
                onProfile = { goTab(Routes.PROFILE) },
                onTask = { id -> nav.navigate(Routes.task(id)) },
            )
        }
        composable(Routes.CAMERA) {
            CameraScreen(
                onClose = { nav.popBackStack() },
                onCaptured = { id ->
                    nav.navigate(Routes.task(id)) { popUpTo(Routes.HOME) }
                },
            )
        }
        composable(Routes.PROFILE) {
            ProfileScreen(
                onHome = { goTab(Routes.HOME) },
                onCamera = { nav.navigate(Routes.CAMERA) },
                onSignOut = { nav.navigate(Routes.SIGN_IN) { popUpTo(Routes.HOME) { inclusive = true } } },
            )
        }
        composable(
            Routes.TASK,
            arguments = listOf(navArgument("id") { type = NavType.StringType }),
            // Notification tap opens pandasolve://task/<id> (see FcmService + manifest intent-filter).
            deepLinks = listOf(navDeepLink { uriPattern = "pandasolve://task/{id}" }),
        ) { entry ->
            TaskDetailScreen(
                taskId = entry.arguments?.getString("id").orEmpty(),
                onBack = { nav.popBackStack() },
            )
        }
    }
    }
}
