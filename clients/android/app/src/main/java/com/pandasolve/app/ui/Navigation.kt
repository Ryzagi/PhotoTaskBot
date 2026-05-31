package com.pandasolve.app.ui

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.navigation.navDeepLink
import com.pandasolve.app.ui.feature.albums.AlbumsScreen
import com.pandasolve.app.ui.feature.auth.SignInScreen
import com.pandasolve.app.ui.feature.history.ArchiveScreen
import com.pandasolve.app.ui.feature.home.HomeScreen
import com.pandasolve.app.ui.feature.settings.ProfileScreen
import com.pandasolve.app.ui.feature.solve.CameraScreen
import com.pandasolve.app.ui.feature.task.TaskDetailScreen

object Routes {
    const val SIGN_IN = "sign_in"
    const val HOME = "home"
    const val CAMERA = "camera"
    const val ARCHIVE = "archive"
    const val ALBUMS = "albums"
    const val PROFILE = "profile"
    const val TASK = "task/{id}"
    fun task(id: String) = "task/$id"
}

@Composable
fun AppNavigation() {
    val nav = rememberNavController()

    // Bottom-tab destinations should not stack; pop up to home and stay single-top.
    fun goTab(route: String) = nav.navigate(route) {
        popUpTo(Routes.HOME)
        launchSingleTop = true
    }

    NavHost(nav, startDestination = Routes.SIGN_IN) {
        composable(Routes.SIGN_IN) {
            SignInScreen(onSignedIn = {
                nav.navigate(Routes.HOME) { popUpTo(Routes.SIGN_IN) { inclusive = true } }
            })
        }
        composable(Routes.HOME) {
            HomeScreen(
                onCamera = { nav.navigate(Routes.CAMERA) },
                onArchive = { goTab(Routes.ARCHIVE) },
                onProfile = { goTab(Routes.PROFILE) },
                onTask = { id -> nav.navigate(Routes.task(id)) },
                onAlbums = { goTab(Routes.ALBUMS) },
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
        composable(Routes.ARCHIVE) {
            ArchiveScreen(
                onTask = { id -> nav.navigate(Routes.task(id)) },
                onCamera = { nav.navigate(Routes.CAMERA) },
                onProfile = { goTab(Routes.PROFILE) },
                onAlbums = { goTab(Routes.ALBUMS) },
            )
        }
        composable(Routes.ALBUMS) {
            AlbumsScreen(
                onArchive = { goTab(Routes.ARCHIVE) },
                onCamera = { nav.navigate(Routes.CAMERA) },
                onProfile = { goTab(Routes.PROFILE) },
            )
        }
        composable(Routes.PROFILE) {
            ProfileScreen(
                onArchive = { goTab(Routes.ARCHIVE) },
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
