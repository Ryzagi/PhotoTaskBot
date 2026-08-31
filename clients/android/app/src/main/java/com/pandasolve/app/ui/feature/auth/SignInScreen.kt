package com.pandasolve.app.ui.feature.auth

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.clickable
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import com.pandasolve.app.BuildConfig
import com.pandasolve.app.auth.AuthError
import com.pandasolve.app.i18n.EnStrings
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.i18n.supportedLanguages
import com.pandasolve.app.ui.component.Candy
import com.pandasolve.app.ui.component.CandyButton
import com.pandasolve.app.ui.component.Panda
import com.pandasolve.app.ui.component.dotPaper
import com.pandasolve.app.ui.theme.Baloo
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute

@Composable
fun SignInScreen(onSignedIn: () -> Unit, viewModel: SignInViewModel = hiltViewModel()) {
    val c = cute
    val t = LocalStrings.current
    val state by viewModel.state.collectAsState()
    LaunchedEffect(state.signedIn) { if (state.signedIn) onSignedIn() }
    val currentLang = if (t == EnStrings) "en" else "ru"

    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var authMode by rememberSaveable { mutableStateOf("signin") }   // "signin" | "signup"
    val isSignup = authMode == "signup"

    val bob = rememberInfiniteTransition(label = "bob")
    val dy by bob.animateFloat(0f, -10f, infiniteRepeatable(tween(1800, easing = FastOutSlowInEasing), RepeatMode.Reverse), label = "dy")

    Column(
        Modifier
            .fillMaxSize()
            .dotPaper(c.paper, c.ink.copy(alpha = 0.07f))
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 26.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(16.dp))
        // language selector
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            supportedLanguages.forEach { opt ->
                val sel = opt.code == currentLang
                Text(
                    opt.code.uppercase(),
                    fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp,
                    color = if (sel) c.mintDeep else c.inkFaint,
                    modifier = Modifier.clip(RoundedCornerShape(999.dp))
                        .background(if (sel) c.mintSoft else c.card)
                        .clickable { viewModel.setLanguage(opt.code) }
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                )
                Spacer(Modifier.width(6.dp))
            }
        }
        Spacer(Modifier.height(16.dp))
        Panda(Modifier.size(118.dp).offset(y = dy.dp))
        Text(t.signinGreeting, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 30.sp, color = c.coralDeep)
        Text(t.signinTitle, fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 30.sp,
            lineHeight = 33.sp, color = c.ink, textAlign = TextAlign.Center)
        Spacer(Modifier.height(10.dp))
        Text(t.signinSubtitle,
            fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkSoft,
            textAlign = TextAlign.Center, modifier = Modifier.widthIn(max = 260.dp))

        Spacer(Modifier.height(22.dp))
        // sign in / sign up toggle
        Row(
            Modifier.clip(RoundedCornerShape(999.dp)).background(c.card)
                .border(2.dp, c.line, RoundedCornerShape(999.dp)).padding(3.dp),
        ) {
            listOf("signin" to t.tabSignIn, "signup" to t.tabSignUp).forEach { (m, lbl) ->
                val sel = authMode == m
                Text(
                    lbl,
                    fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 13.sp,
                    color = if (sel) Color.White else c.inkSoft,
                    modifier = Modifier.clip(RoundedCornerShape(999.dp))
                        .background(if (sel) c.mintDeep else Color.Transparent)
                        .clickable { authMode = m }
                        .padding(horizontal = 20.dp, vertical = 8.dp),
                )
            }
        }

        Spacer(Modifier.height(18.dp))
        CuteField(t.fieldEmail, email, { email = it }, focus = true)
        Spacer(Modifier.height(12.dp))
        CuteField(t.fieldPassword, password, { password = it }, password = true)

        Spacer(Modifier.height(16.dp))
        CandyButton(
            if (isSignup) t.signupButton else t.signinButton,
            { if (isSignup) viewModel.signUpWithEmail(email, password) else viewModel.signInWithEmail(email, password) },
            Modifier.fillMaxWidth(), Candy.Mint, enabled = !state.busy,
        )

        // Only in sign-in mode — there is no password to recover while signing up.
        if (!isSignup) {
            Spacer(Modifier.height(10.dp))
            Text(
                t.forgotPassword,
                fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 12.sp,
                color = c.inkFaint, textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(enabled = !state.busy) { viewModel.sendPasswordReset(email) },
            )
        }

        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.weight(1f).height(2.dp).clip(RoundedCornerShape(2.dp)).background(c.line))
            Text("  ${t.orDivider}  ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.inkFaint)
            Box(Modifier.weight(1f).height(2.dp).clip(RoundedCornerShape(2.dp)).background(c.line))
        }
        Spacer(Modifier.height(14.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            CandyButton("Google", viewModel::signInWithGoogle, Modifier.weight(1f), Candy.Ghost, enabled = !state.busy)
            // Apple sign-in isn't available on Android yet — show it as coming soon.
            Box(Modifier.weight(1f)) {
                CandyButton("Apple", {}, Modifier.fillMaxWidth().alpha(0.55f), Candy.Ghost, enabled = false)
                Box(
                    Modifier.align(Alignment.TopEnd).offset(x = (-6).dp, y = (-5).dp)
                        .clip(RoundedCornerShape(999.dp)).background(c.lav)
                        .padding(horizontal = 8.dp, vertical = 2.dp),
                ) {
                    Text(t.soon.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 9.sp, color = Color.White)
                }
            }
        }

        val errText = when (state.error) {
            AuthError.EMPTY_FIELDS -> t.errEmptyFields
            AuthError.INVALID_CREDENTIALS -> t.errInvalidCredentials
            AuthError.USER_EXISTS -> t.errUserExists
            AuthError.WEAK_PASSWORD -> t.errWeakPassword
            AuthError.INVALID_EMAIL -> t.errInvalidEmail
            AuthError.EMAIL_NOT_CONFIRMED -> t.errEmailNotConfirmed
            AuthError.RATE_LIMITED -> t.errRateLimited
            AuthError.NETWORK -> t.errNetwork
            AuthError.UNKNOWN -> t.errUnknown
            AuthError.CANCELLED, null -> null
        }
        errText?.let { err ->
            Spacer(Modifier.height(14.dp))
            Text(err, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.coralDeep, textAlign = TextAlign.Center)
            if (state.error == AuthError.UNKNOWN) {
                state.errorDetail?.let { d ->
                    Spacer(Modifier.height(4.dp))
                    Text(d, fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 10.sp, color = c.inkFaint, textAlign = TextAlign.Center)
                }
            }
        }
        if (state.pendingConfirmation) {
            Spacer(Modifier.height(14.dp))
            Text(t.checkInbox, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.mintDeep, textAlign = TextAlign.Center)
        }
        if (state.resetEmailSent) {
            Spacer(Modifier.height(14.dp))
            Text(t.resetEmailSent, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.mintDeep, textAlign = TextAlign.Center)
        }

        Spacer(Modifier.height(20.dp))
        Text(t.signinTerms,
            fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 11.sp, color = c.inkFaint,
            textAlign = TextAlign.Center, lineHeight = 15.sp)
        Spacer(Modifier.height(6.dp))
        val ctx = LocalContext.current
        Text(
            t.privacyPolicy,
            fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.mintDeep,
            textAlign = TextAlign.Center,
            modifier = Modifier.clickable {
                runCatching {
                    ctx.startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse("${BuildConfig.API_BASE_URL}/privacy")))
                }
            },
        )
        Spacer(Modifier.height(28.dp))
    }
}

@Composable
private fun CuteField(
    label: String,
    value: String,
    onChange: (String) -> Unit,
    focus: Boolean = false,
    password: Boolean = false,
) {
    val c = cute
    var reveal by remember { mutableStateOf(false) }
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(c.card)
            .border(2.dp, if (focus) c.mint else c.line, RoundedCornerShape(20.dp))
            .padding(horizontal = 16.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(label.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
            Spacer(Modifier.height(3.dp))
            BasicTextField(
                value = value,
                onValueChange = onChange,
                singleLine = true,
                visualTransformation = if (password && !reveal) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
                cursorBrush = SolidColor(c.mintDeep),
                textStyle = androidx.compose.ui.text.TextStyle(
                    fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.ink,
                ),
                decorationBox = { inner ->
                    if (value.isEmpty()) {
                        Text(if (password) "••••••••" else "you@example.com",
                            fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 15.sp, color = c.inkFaint)
                    }
                    inner()
                },
            )
        }
        if (password) {
            Text(
                if (reveal) "🙈" else "👁️",
                fontSize = 18.sp,
                modifier = Modifier.clip(RoundedCornerShape(999.dp)).clickable { reveal = !reveal }.padding(6.dp),
            )
        }
    }
}
