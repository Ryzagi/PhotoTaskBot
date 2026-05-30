package com.pandasolve.app.ui.feature.solve

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.pandasolve.app.ui.component.Candy
import com.pandasolve.app.ui.component.CandyButton
import com.pandasolve.app.ui.theme.Baloo
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

    // gallery fallback
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) viewModel.submitImage(uri, null)
    }

    val previewView = remember {
        PreviewView(context).apply { scaleType = PreviewView.ScaleType.FILL_CENTER }
    }
    val imageCapture = remember {
        ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY).build()
    }
    val mainExecutor = remember { ContextCompat.getMainExecutor(context) }

    LaunchedEffect(hasPermission) {
        if (hasPermission) {
            val provider = context.getCameraProvider()
            val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
            provider.unbindAll()
            runCatching {
                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, imageCapture)
            }
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
                viewModel.submitImageBytes(bytes, null)
            }
        })
    }

    Column(Modifier.fillMaxSize().background(Color.Black)) {
        Box(
            Modifier.weight(1f).fillMaxWidth()
                .background(Brush.radialGradient(listOf(Color(0xFF3A352D), VfDeep))),
        ) {
            if (hasPermission) {
                AndroidView(factory = { previewView }, modifier = Modifier.fillMaxSize())
            } else {
                Column(
                    Modifier.fillMaxSize().padding(32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text("Дай доступ к камере 🐼", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 24.sp,
                        color = Color.White, textAlign = TextAlign.Center)
                    Spacer(Modifier.height(8.dp))
                    Text("чтобы сфотографировать задачу", fontFamily = Nunito, fontWeight = FontWeight.W600,
                        fontSize = 13.sp, color = Color.White.copy(alpha = 0.7f), textAlign = TextAlign.Center)
                    Spacer(Modifier.height(20.dp))
                    CandyButton("Разрешить", { permLauncher.launch(Manifest.permission.CAMERA) }, Modifier.fillMaxWidth(0.7f), Candy.Mint)
                    Spacer(Modifier.height(10.dp))
                    Text(
                        "или выбери из галереи →", fontFamily = Caveat, fontWeight = FontWeight.W600, fontSize = 17.sp, color = c.lav,
                        modifier = Modifier.clickable { picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                    )
                }
            }

            // framing brackets
            Box(Modifier.fillMaxSize().padding(top = 104.dp, start = 24.dp, end = 24.dp, bottom = 96.dp)) {
                CornerBracket(Alignment.TopStart, c.mint)
                CornerBracket(Alignment.TopEnd, c.mint)
                CornerBracket(Alignment.BottomStart, c.mint)
                CornerBracket(Alignment.BottomEnd, c.mint)
            }

            if (hasPermission) {
                Box(
                    Modifier.align(Alignment.BottomCenter).padding(bottom = 30.dp)
                        .clip(RoundedCornerShape(999.dp)).background(Color.Black.copy(alpha = 0.32f))
                        .padding(horizontal = 16.dp, vertical = 6.dp),
                ) { Text("наведи на задачу ✏️", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 20.sp, color = Color.White) }
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
                    Text("панда готова", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 12.sp, color = Color.White)
                }
                RoundBtn(onClick = {}) { Text("⚡", fontSize = 16.sp) }
            }
        }

        // controls
        Column(Modifier.background(Color.Black).padding(start = 30.dp, end = 30.dp, top = 18.dp, bottom = 34.dp)) {
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(Color.White.copy(alpha = 0.12f))
                    .border(1.5.dp, Color.White.copy(alpha = 0.22f), RoundedCornerShape(18.dp)).padding(horizontal = 14.dp, vertical = 11.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(Modifier.size(24.dp).clip(CircleShape).background(c.coral), contentAlignment = Alignment.Center) {
                    Text("+", fontFamily = Baloo, fontWeight = FontWeight.W700, fontSize = 16.sp, color = Color.White)
                }
                Spacer(Modifier.width(11.dp))
                Text("подсказка панде — необязательно", fontFamily = Nunito, fontWeight = FontWeight.W600, fontSize = 13.sp, color = Color(0xFFF3EAD9))
            }
            Spacer(Modifier.height(20.dp))
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("ТЕКСТ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = Color.White.copy(alpha = 0.5f))
                    Text("ФОТО", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = c.mint)
                    Text("ФАЙЛ", fontFamily = Nunito, fontWeight = FontWeight.W800, fontSize = 11.sp, color = Color.White.copy(alpha = 0.5f))
                }
                // capture (CameraX)
                Box(
                    Modifier.size(80.dp).clip(CircleShape).background(Color.White)
                        .clickable(enabled = hasPermission && !state.busy) { capture() },
                    contentAlignment = Alignment.Center,
                ) {
                    Box(Modifier.size(64.dp).clip(CircleShape).background(Brush.linearGradient(listOf(c.mint, c.sky))), contentAlignment = Alignment.Center) {
                        Icon(Icons.Filled.PhotoCamera, null, tint = Color.White, modifier = Modifier.size(26.dp))
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

    if (state.busy) {
        Box(
            Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.6f)).clickable(enabled = false) {},
            contentAlignment = Alignment.Center,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator(color = cute.mint)
                Spacer(Modifier.height(14.dp))
                Text("Панда решает… 🐼", fontFamily = Caveat, fontWeight = FontWeight.W700, fontSize = 22.sp, color = Color.White)
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
private fun BoxScope.CornerBracket(align: Alignment, color: Color) {
    val tl = align == Alignment.TopStart
    val tr = align == Alignment.TopEnd
    val bl = align == Alignment.BottomStart
    Box(
        Modifier.align(align).size(36.dp)
            .border(
                width = 4.dp, color = color,
                shape = RoundedCornerShape(
                    topStart = if (tl) 18.dp else 0.dp,
                    topEnd = if (tr) 18.dp else 0.dp,
                    bottomStart = if (bl) 18.dp else 0.dp,
                    bottomEnd = if (!tl && !tr && !bl) 18.dp else 0.dp,
                ),
            ),
    )
}

@Composable
private fun RoundBtn(onClick: () -> Unit, content: @Composable () -> Unit) {
    Box(
        Modifier.size(40.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.16f))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { content() }
}
