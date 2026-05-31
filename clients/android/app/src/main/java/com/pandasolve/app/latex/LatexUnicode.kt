package com.pandasolve.app.latex

/**
 * Lightweight LaTeX → readable-Unicode converter.
 *
 * The solver returns LaTeX-flavoured content (`\cdot`, `\frac{a}{b}`, `$...$`,
 * `x^{2}`, Greek macros, …). We don't ship a full math typesetter, so this turns
 * the common subset into plain Unicode that reads cleanly in a Compose `Text`.
 * It is deliberately forgiving: anything it doesn't recognise has its leading
 * backslash stripped (so `\sin` → `sin`) rather than shown raw.
 */

private val SUPERSCRIPT = mapOf(
    '0' to '⁰', '1' to '¹', '2' to '²', '3' to '³', '4' to '⁴', '5' to '⁵',
    '6' to '⁶', '7' to '⁷', '8' to '⁸', '9' to '⁹', '+' to '⁺', '-' to '⁻',
    '=' to '⁼', '(' to '⁽', ')' to '⁾', 'n' to 'ⁿ', 'i' to 'ⁱ', 'x' to 'ˣ',
)

private val SUBSCRIPT = mapOf(
    '0' to '₀', '1' to '₁', '2' to '₂', '3' to '₃', '4' to '₄', '5' to '₅',
    '6' to '₆', '7' to '₇', '8' to '₈', '9' to '₉', '+' to '₊', '-' to '₋',
    '=' to '₌', '(' to '₍', ')' to '₎', 'a' to 'ₐ', 'e' to 'ₑ', 'o' to 'ₒ',
    'x' to 'ₓ', 'n' to 'ₙ', 'i' to 'ᵢ', 'j' to 'ⱼ', 'k' to 'ₖ',
)

// Applied longest-key-first so e.g. \leftarrow is handled before \le.
private val SYMBOLS = mapOf(
    "\\cdot" to "·", "\\times" to "×", "\\div" to "÷", "\\pm" to "±", "\\mp" to "∓",
    "\\ast" to "∗", "\\star" to "⋆", "\\bullet" to "•",
    "\\leq" to "≤", "\\le" to "≤", "\\leqslant" to "≤", "\\geq" to "≥", "\\ge" to "≥",
    "\\geqslant" to "≥", "\\neq" to "≠", "\\ne" to "≠", "\\approx" to "≈",
    "\\equiv" to "≡", "\\propto" to "∝", "\\sim" to "∼", "\\cong" to "≅",
    "\\infty" to "∞", "\\partial" to "∂", "\\nabla" to "∇", "\\sum" to "∑",
    "\\prod" to "∏", "\\int" to "∫", "\\oint" to "∮", "\\sqrt" to "√",
    "\\Rightarrow" to "⇒", "\\Leftarrow" to "⇐", "\\Leftrightarrow" to "⇔",
    "\\rightarrow" to "→", "\\leftarrow" to "←", "\\leftrightarrow" to "↔",
    "\\to" to "→", "\\mapsto" to "↦", "\\implies" to "⇒",
    "\\alpha" to "α", "\\beta" to "β", "\\gamma" to "γ", "\\delta" to "δ",
    "\\varepsilon" to "ε", "\\epsilon" to "ε", "\\zeta" to "ζ", "\\eta" to "η",
    "\\theta" to "θ", "\\vartheta" to "ϑ", "\\iota" to "ι", "\\kappa" to "κ",
    "\\lambda" to "λ", "\\mu" to "μ", "\\nu" to "ν", "\\xi" to "ξ", "\\pi" to "π",
    "\\rho" to "ρ", "\\sigma" to "σ", "\\tau" to "τ", "\\upsilon" to "υ",
    "\\varphi" to "φ", "\\phi" to "φ", "\\chi" to "χ", "\\psi" to "ψ", "\\omega" to "ω",
    "\\Gamma" to "Γ", "\\Delta" to "Δ", "\\Theta" to "Θ", "\\Lambda" to "Λ",
    "\\Xi" to "Ξ", "\\Pi" to "Π", "\\Sigma" to "Σ", "\\Phi" to "Φ", "\\Psi" to "Ψ",
    "\\Omega" to "Ω",
    "\\angle" to "∠", "\\circ" to "∘", "\\degree" to "°", "\\perp" to "⊥",
    "\\parallel" to "∥", "\\cap" to "∩", "\\cup" to "∪", "\\subset" to "⊂",
    "\\supset" to "⊃", "\\subseteq" to "⊆", "\\supseteq" to "⊇", "\\in" to "∈",
    "\\notin" to "∉", "\\forall" to "∀", "\\exists" to "∃", "\\emptyset" to "∅",
    "\\cdots" to "⋯", "\\ldots" to "…", "\\dots" to "…", "\\vdots" to "⋮",
).entries.sortedByDescending { it.key.length }

fun latexToUnicode(input: String): String {
    var s = input

    // LaTeX line break + spacing macros → plain space.
    s = s.replace("\\\\", " ")
    s = Regex("""\\[,;:!> ]""").replace(s, " ")
    s = s.replace("\\quad", " ").replace("\\qquad", "  ")

    // Math-mode delimiters.
    s = s.replace("$$", "").replace("$", "")
    s = s.replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
    s = s.replace("\\left", "").replace("\\right", "")

    // Style wrappers → keep the contents.
    s = Regex("""\\(?:text|textbf|textit|mathbf|mathrm|mathit|boldsymbol|operatorname)\{([^{}]*)\}""")
        .replace(s) { it.groupValues[1] }

    // \frac{a}{b} → (a)/(b); loop a few times for limited nesting.
    repeat(4) {
        s = Regex("""\\frac\{([^{}]*)\}\{([^{}]*)\}""")
            .replace(s) { "(${it.groupValues[1]})/(${it.groupValues[2]})" }
    }
    // \sqrt{x} → √(x)
    s = Regex("""\\sqrt\{([^{}]*)\}""").replace(s) { "√(${it.groupValues[1]})" }

    // Accents: attach a combining mark to the argument (e.g. \dot{x} → ẋ, \vec{v} → v⃗).
    s = Regex("""\\dot\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "̇" }
    s = Regex("""\\ddot\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "̈" }
    s = Regex("""\\hat\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "̂" }
    s = Regex("""\\(?:bar|overline)\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "̄" }
    s = Regex("""\\vec\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "⃗" }
    s = Regex("""\\tilde\{([^{}]*)\}""").replace(s) { it.groupValues[1] + "̃" }

    // Named symbols / Greek (longest first).
    for ((k, v) in SYMBOLS) s = s.replace(k, v)

    // Superscripts and subscripts.
    s = Regex("""\^\{([^{}]*)\}""").replace(s) { superscript(it.groupValues[1]) }
    s = Regex("""\^(\S)""").replace(s) { superscript(it.groupValues[1]) }
    s = Regex("""_\{([^{}]*)\}""").replace(s) { subscript(it.groupValues[1]) }
    s = Regex("""_(\S)""").replace(s) { subscript(it.groupValues[1]) }

    // Any remaining \command → strip the backslash (keeps sin, cos, log, lim…).
    s = Regex("""\\([a-zA-Z]+)""").replace(s) { it.groupValues[1] }

    // Leftover grouping braces and tidy whitespace.
    s = s.replace("{", "").replace("}", "")
    s = Regex("""[ \t]{2,}""").replace(s, " ").trim()
    return s
}

private fun superscript(t: String): String =
    if (t.isNotEmpty() && t.all { SUPERSCRIPT.containsKey(it) }) t.map { SUPERSCRIPT[it] }.joinToString("")
    else "^($t)"

private fun subscript(t: String): String =
    if (t.isNotEmpty() && t.all { SUBSCRIPT.containsKey(it) }) t.map { SUBSCRIPT[it] }.joinToString("")
    else "_($t)"
