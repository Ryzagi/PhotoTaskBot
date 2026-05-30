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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
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
    val state by viewModel.state.collectAsState()
    LaunchedEffect(state.signedIn) { if (state.signedIn) onSignedIn() }

    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }

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
        Spacer(Modifier.height(40.dp))
        Panda(Modifier.size(118.dp).offset(y = dy.dp))
        Text("Приве-е-ет! ✿", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 30.sp, color = c.coralDeep)
        Text("Давай решать\nвместе", fontFamily = Baloo, fontWeight = FontWeight.W800, fontSize = 30.sp,
            lineHeight = 33.sp, color = c.ink, textAlign = TextAlign.Center)
        Spacer(Modifier.height(10.dp))
        Text("Сфоткай задачу — я объясню по шагам. Не просто ответ 💚",
            fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 14.sp, color = c.inkSoft,
            textAlign = TextAlign.Center, modifier = Modifier.widthIn(max = 260.dp))

        Spacer(Modifier.height(26.dp))
        CuteField("почта", email, { email = it }, focus = true)
        Spacer(Modifier.height(12.dp))
        CuteField("пароль", password, { password = it }, password = true)

        Spacer(Modifier.height(16.dp))
        CandyButton("Войти 🚀", { viewModel.signInWithEmail(email, password) }, Modifier.fillMaxWidth(), Candy.Mint, enabled = !state.busy)

        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.weight(1f).height(2.dp).clip(RoundedCornerShape(2.dp)).background(c.line))
            Text("  ИЛИ  ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.inkFaint)
            Box(Modifier.weight(1f).height(2.dp).clip(RoundedCornerShape(2.dp)).background(c.line))
        }
        Spacer(Modifier.height(14.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            CandyButton("Google", viewModel::signInWithGoogle, Modifier.weight(1f), Candy.Ghost, enabled = !state.busy)
            CandyButton("Apple", viewModel::signInWithApple, Modifier.weight(1f), Candy.Ghost, enabled = !state.busy)
        }

        state.error?.let { err ->
            Spacer(Modifier.height(14.dp))
            Text(err, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 13.sp, color = c.coralDeep, textAlign = TextAlign.Center)
        }

        Spacer(Modifier.height(20.dp))
        Text("Войдя, ты соглашаешься с правилами и конфиденциальностью.",
            fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 11.sp, color = c.inkFaint,
            textAlign = TextAlign.Center, lineHeight = 15.sp)
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
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(c.card)
            .border(2.dp, if (focus) c.mint else c.line, RoundedCornerShape(20.dp))
            .padding(horizontal = 16.dp, vertical = 11.dp),
    ) {
        Text(label.uppercase(), fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
        Spacer(Modifier.height(3.dp))
        BasicTextField(
            value = value,
            onValueChange = onChange,
            singleLine = true,
            visualTransformation = if (password) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
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
}
