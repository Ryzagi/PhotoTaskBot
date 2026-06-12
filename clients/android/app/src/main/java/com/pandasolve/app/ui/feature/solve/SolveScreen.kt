package com.pandasolve.app.ui.feature.solve

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Image
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.LocalLifecycleOwner
import coil.compose.AsyncImage
import com.pandasolve.app.i18n.LocalStrings
import com.pandasolve.app.ui.component.Candy
import com.pandasolve.app.ui.component.CandyButton
import com.pandasolve.app.ui.theme.Caveat
import com.pandasolve.app.ui.theme.Nunito
import com.pandasolve.app.ui.theme.cute
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

private val VfDeep = Color(0xFF211E19)

@Composable
fun CameraScreen(
    onClose: () -> Unit,
    onCaptured: (String) -> Unit,
    viewModel: SolveViewModel = hiltViewModel(),
) {
    val c = cute
    val t = LocalStrings.current
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val state by viewModel.state.collectAsState()
    LaunchedEffect(state.createdTaskId) { state.createdTaskId?.let { onCaptured(it) } }

    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
        )
    }
    val permLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasPermission = granted
    }
    LaunchedEffect(Unit) { if (!hasPermission) permLauncher.launch(Manifest.permission.CAMERA) }

    // Telegram-style review step: a captured photo / picked image waits here with an
    // optional caption before it's submitted.
    var pendingBytes by remember { mutableStateOf<ByteArray?>(null) }
    var pendingUri by remember { mutableStateOf<android.net.Uri?>(null) }
    var caption by remember { mutableStateOf("") }

    // gallery fallback — preview + caption before submitting (same as a capture)
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) { pendingUri = uri; pendingBytes = null }
    }

    val previewView = remember {
        PreviewView(context).apply { scaleType = PreviewView.ScaleType.FILL_CENTER }
    }
    val imageCapture = remember {
        ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY).build()
    }
    val mainExecutor = remember { ContextCompat.getMainExecutor(context) }

    var mode by remember { mutableStateOf("photo") }   // "photo" | "text"
    var problemText by remember { mutableStateOf("") }
    var camera by remember { mutableStateOf<Camera?>(null) }
    var torchOn by remember { mutableStateOf(false) }

    LaunchedEffect(hasPermission) {
        if (hasPermission) {
            val provider = context.getCameraProvider()
            val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
            provider.unbindAll()
            camera = runCatching {
                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, imageCapture)
            }.getOrNull()
            torchOn = false
        }
    }

    fun capture() {
        if (state.busy) return
        imageCapture.takePicture(mainExecutor, object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                val buffer = image.planes[0].buffer
                val bytes = ByteArray(buffer.remaining())
                buffer.get(bytes)
                image.close()
                // Show the shot for review + caption instead of submitting straight away.
                pendingBytes = bytes
                pendingUri = null
            }
        })
    }

    Column(Modifier.fillMaxSize().background(Color.Black)) {
        Box(
            Modifier.weight(1f).fillMaxWidth()
                .background(Brush.radialGradient(listOf(Color(0xFF3A352D), VfDeep))),
        ) {
            when {
                mode == "text" -> {
                    // type-a-problem card
                    Column(
                        Modifier.fillMaxSize().padding(start = 24.dp, end = 24.dp, top = 104.dp, bottom = 24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Column(
                            Modifier.fillMaxWidth().weight(1f).clip(RoundedCornerShape(20.dp))
                                .background(c.card).padding(18.dp),
                        ) {
                            Text(t.solveProblemLabel, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 10.sp, color = c.inkFaint)
                            Spacer(Modifier.height(8.dp))
                            BasicTextField(
                                value = problemText,
                                onValueChange = { problemText = it },
                                modifier = Modifier.fillMaxSize(),
                                cursorBrush = SolidColor(c.mintDeep),
                                textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 16.sp, color = c.ink, lineHeight = 23.sp),
                                decorationBox = { inner ->
                                    if (problemText.isEmpty()) {
                                        Text(t.solveTextPlaceholder,
                                            fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 16.sp, color = c.inkFaint, lineHeight = 23.sp)
                                    }
                                    inner()
                                },
                            )
                        }
                    }
                }
                hasPermission -> AndroidView(
                    factory = { previewView },
                    modifier = Modifier.fillMaxSize().pointerInput(camera) {
                        // pinch-to-zoom, like the stock camera
                        detectTransformGestures { _, _, zoom, _ ->
                            val cam = camera ?: return@detectTransformGestures
                            val zs = cam.cameraInfo.zoomState.value
                            val current = zs?.zoomRatio ?: 1f
                            val min = zs?.minZoomRatio ?: 1f
                            val max = zs?.maxZoomRatio ?: 1f
                            cam.cameraControl.setZoomRatio((current * zoom).coerceIn(min, max))
                        }
                    },
                )
                else -> Column(
                    Modifier.fillMaxSize().padding(32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text(t.cameraPermTitle, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 24.sp,
                        color = Color.White, textAlign = TextAlign.Center)
                    Spacer(Modifier.height(8.dp))
                    Text(t.cameraPermSubtitle, fontFamily = Nunito, fontWeight = FontWeight.W600,
                        fontSize = 13.sp, color = Color.White.copy(alpha = 0.7f), textAlign = TextAlign.Center)
                    Spacer(Modifier.height(20.dp))
                    CandyButton(t.cameraPermAllow, { permLauncher.launch(Manifest.permission.CAMERA) }, Modifier.fillMaxWidth(0.7f), Candy.Mint)
                    Spacer(Modifier.height(10.dp))
                    Text(
                        t.cameraOrType, fontFamily = Caveat, fontWeight = FontWeight.W600, fontSize = 17.sp, color = c.lav,
                        modifier = Modifier.clickable { mode = "text" },
                    )
                }
            }

            if (mode == "photo") {
                if (hasPermission) {
                    Box(
                        Modifier.align(Alignment.BottomCenter).padding(bottom = 30.dp)
                            .clip(RoundedCornerShape(999.dp)).background(Color.Black.copy(alpha = 0.32f))
                            .padding(horizontal = 16.dp, vertical = 6.dp),
                    ) { Text(t.cameraAim, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 20.sp, color = Color.White) }
                }
            }

            // top bar
            Row(
                Modifier.fillMaxWidth().align(Alignment.TopCenter).padding(top = 52.dp, start = 22.dp, end = 22.dp),
                horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically,
            ) {
                RoundBtn(onClick = onClose) {
                    Icon(Icons.Filled.Close, null, tint = Color.White, modifier = Modifier.size(18.dp))
                }
                Row(
                    Modifier.clip(RoundedCornerShape(999.dp)).background(c.mint.copy(alpha = 0.22f))
                        .border(1.5.dp, c.mint, RoundedCornerShape(999.dp)).padding(horizontal = 14.dp, vertical = 7.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(Modifier.size(7.dp).clip(CircleShape).background(c.mint))
                    Spacer(Modifier.width(8.dp))
                    Text(t.cameraReady, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = Color.White)
                }
                RoundBtn(
                    onClick = {
                        camera?.let { cam ->
                            torchOn = !torchOn
                            cam.cameraControl.enableTorch(torchOn)
                        }
                    },
                    active = torchOn,
                ) { Text("⚡", fontSize = 16.sp) }
            }
        }

        // controls
        Column(Modifier.background(Color.Black).padding(start = 30.dp, end = 30.dp, top = 22.dp, bottom = 34.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    fun modeColor(m: String) = if (mode == m) c.mint else Color.White.copy(alpha = 0.5f)
                    Text(t.modeText, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = modeColor("text"),
                        modifier = Modifier.clickable { mode = "text" })
                    Text(t.modePhoto, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = modeColor("photo"),
                        modifier = Modifier.clickable { mode = "photo" })
                    Text(t.modeFile, fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = Color.White.copy(alpha = 0.5f),
                        modifier = Modifier.clickable { picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) })
                }
                // shutter — captures a photo or submits the typed problem
                val canSubmit = if (mode == "text") problemText.isNotBlank() && !state.busy else hasPermission && !state.busy
                Box(
                    Modifier.size(80.dp).clip(CircleShape).background(Color.White)
                        .clickable(enabled = canSubmit) {
                            if (mode == "text") viewModel.submitText(problemText) else capture()
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Box(Modifier.size(64.dp).clip(CircleShape).background(Brush.linearGradient(listOf(c.mint, c.sky))), contentAlignment = Alignment.Center) {
                        Icon(
                            if (mode == "text") Icons.Filled.Check else Icons.Filled.PhotoCamera,
                            null, tint = Color.White, modifier = Modifier.size(26.dp),
                        )
                    }
                }
                // gallery fallback (picker)
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterEnd) {
                    Box(
                        Modifier.size(50.dp).clip(RoundedCornerShape(14.dp))
                            .background(Brush.linearGradient(listOf(c.lav, c.pink)))
                            .clickable(enabled = !state.busy) {
                                picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Filled.Image, null, tint = Color.White, modifier = Modifier.size(22.dp))
                    }
                }
            }
            state.error?.let { err ->
                Spacer(Modifier.height(10.dp))
                Text(err, fontFamily = Nunito, fontWeight = FontWeight.W700, fontSize = 12.sp, color = c.coral)
            }
        }
    }

    // Full-screen review of the captured/picked photo with an optional caption (Telegram-style).
    val previewModel: Any? = pendingBytes ?: pendingUri
    if (previewModel != null) {
        Column(Modifier.fillMaxSize().background(Color.Black)) {
            Box(Modifier.weight(1f).fillMaxWidth()) {
                AsyncImage(
                    model = previewModel,
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier.fillMaxSize(),
                )
                Box(Modifier.align(Alignment.TopStart).padding(top = 50.dp, start = 20.dp)) {
                    RoundBtn(onClick = { pendingBytes = null; pendingUri = null; caption = "" }) {
                        Icon(Icons.Filled.Close, null, tint = Color.White, modifier = Modifier.size(18.dp))
                    }
                }
            }
            // caption + send bar
            Row(
                Modifier.fillMaxWidth().background(Color.Black)
                    .padding(horizontal = 16.dp, vertical = 14.dp)
                    .imePadding().navigationBarsPadding(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    Modifier.weight(1f).clip(RoundedCornerShape(22.dp))
                        .background(Color.White.copy(alpha = 0.14f))
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                ) {
                    BasicTextField(
                        value = caption,
                        onValueChange = { caption = it },
                        cursorBrush = SolidColor(c.mint),
                        textStyle = TextStyle(fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 15.sp, color = Color.White),
                        decorationBox = { inner ->
                            if (caption.isEmpty()) {
                                Text(t.captionPlaceholder, fontFamily = Nunito, fontWeight = FontWeight.W600,
                                    fontSize = 15.sp, color = Color.White.copy(alpha = 0.5f))
                            }
                            inner()
                        },
                    )
                }
                Spacer(Modifier.width(12.dp))
                Box(
                    Modifier.size(52.dp).clip(CircleShape)
                        .background(Brush.linearGradient(listOf(c.mint, c.sky)))
                        .clickable(enabled = !state.busy) {
                            val cap = caption.trim().ifBlank { null }
                            val bytes = pendingBytes
                            val uri = pendingUri
                            pendingBytes = null; pendingUri = null; caption = ""
                            if (bytes != null) viewModel.submitImageBytes(bytes, cap)
                            else if (uri != null) viewModel.submitImage(uri, cap)
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.AutoMirrored.Filled.Send, null, tint = Color.White, modifier = Modifier.size(22.dp))
                }
            }
        }
    }

    if (state.busy) {
        Box(
            Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.6f)).clickable(enabled = false) {},
            contentAlignment = Alignment.Center,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator(color = cute.mint)
                Spacer(Modifier.height(14.dp))
                Text(t.solvingPanda, fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 22.sp, color = Color.White)
            }
        }
    }
}

private suspend fun Context.getCameraProvider(): ProcessCameraProvider =
    suspendCoroutine { cont ->
        val future = ProcessCameraProvider.getInstance(this)
        future.addListener({ cont.resume(future.get()) }, ContextCompat.getMainExecutor(this))
    }

@Composable
private fun RoundBtn(onClick: () -> Unit, active: Boolean = false, content: @Composable () -> Unit) {
    Box(
        Modifier.size(40.dp).clip(CircleShape)
            .background(if (active) cute.butter else Color.White.copy(alpha = 0.16f))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { content() }
}
