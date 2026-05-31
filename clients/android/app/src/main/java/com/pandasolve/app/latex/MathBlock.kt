package com.pandasolve.app.latex

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/**
 * Math block renderer.
 *
 * TODO: Switch this back to JLatexMath / Math-View once the JitPack coordinate
 * is sorted (see clients/android/gradle/libs.versions.toml). For the initial
 * build-and-install pass we render LaTeX as monospace text so the rest of the
 * UI flow can be smoke-tested without depending on a third-party renderer.
 */
@Composable
fun MathBlock(latex: String, modifier: Modifier = Modifier) {
    Text(
        text = latexToUnicode(latex),
        modifier = modifier.fillMaxWidth(),
        style = MaterialTheme.typography.bodyMedium,
    )
}

/**
 * Inline-mixed text. Same Unicode-prettified fallback as [MathBlock].
 */
@Composable
fun MixedText(content: String, modifier: Modifier = Modifier) {
    Text(
        text = latexToUnicode(content),
        modifier = modifier.fillMaxWidth(),
        style = MaterialTheme.typography.bodyMedium,
    )
}
