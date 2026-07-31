import SwiftUI
import iosMath

/// SwiftUI wrapper over `MTMathUILabel` from iosMath. Renders pure LaTeX
/// (without `$` delimiters).
struct MathLatexView: UIViewRepresentable {
    let latex: String

    func makeUIView(context: Context) -> MTMathUILabel {
        let label = MTMathUILabel()
        label.fontSize = 18            // default font is Latin Modern Math
        label.textAlignment = .left
        label.mode = .text
        label.latex = latex
        return label
    }

    func updateUIView(_ uiView: MTMathUILabel, context: Context) {
        if uiView.latex != latex { uiView.latex = latex }
    }
}

/// Renders a string that may contain inline math (`$...$`) interleaved with prose.
/// Splits on `$...$` and lays out as a vertical stack — refine to a wrapped flow
/// layout when we have time. For block-only math, use `MathLatexView` directly.
struct MixedText: View {
    let content: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(Array(Self.parse(content).enumerated()), id: \.offset) { _, segment in
                switch segment {
                case .text(let s): Text(s)
                case .math(let s): MathLatexView(latex: s)
                }
            }
        }
    }

    // Internal (not private) so unit tests can exercise the `$…$` splitting.
    enum Segment: Equatable { case text(String), math(String) }

    static func parse(_ s: String) -> [Segment] {
        var out: [Segment] = []
        var buffer = ""
        var inMath = false
        var i = s.startIndex
        while i < s.endIndex {
            let c = s[i]
            if c == "$" {
                if !buffer.isEmpty {
                    out.append(inMath ? .math(buffer) : .text(buffer))
                    buffer = ""
                }
                inMath.toggle()
            } else {
                buffer.append(c)
            }
            i = s.index(after: i)
        }
        if !buffer.isEmpty { out.append(inMath ? .math(buffer) : .text(buffer)) }
        return out
    }
}

#Preview("Solution rendering") {
    ScrollView {
        VStack(alignment: .leading, spacing: 14) {
            Text("Steps with inline math:").font(baloo(16, .bold))
            MixedText(content: "Используем дискриминант $D = b^2 - 4ac$ для уравнения $x^2 - 5x + 6 = 0$")
            MixedText(content: "Подставляем: $D = (-5)^2 - 4 \\cdot 1 \\cdot 6 = 25 - 24 = 1$")
            MixedText(content: "Корни: $x_{1,2} = \\frac{-b \\pm \\sqrt{D}}{2a} = \\frac{5 \\pm 1}{2}$")
            Text("Block math:").font(baloo(16, .bold))
            MathLatexView(latex: "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}")
            MathLatexView(latex: "x_1 = 3, \\quad x_2 = 2")
        }
        .padding(20)
    }
    .background(Color(red: 0.99, green: 0.96, blue: 0.93))
}
