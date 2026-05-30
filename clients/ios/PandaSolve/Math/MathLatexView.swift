import SwiftUI
import iosMath

/// SwiftUI wrapper over `MTMathUILabel` from iosMath. Renders pure LaTeX
/// (without `$` delimiters).
struct MathLatexView: UIViewRepresentable {
    let latex: String

    func makeUIView(context: Context) -> MTMathUILabel {
        let label = MTMathUILabel()
        label.font = MTFontManager().latinModernFont(withSize: 18)
        label.textAlignment = .left
        label.labelMode = .text
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
            ForEach(Array(parse(content).enumerated()), id: \.offset) { _, segment in
                switch segment {
                case .text(let s): Text(s)
                case .math(let s): MathLatexView(latex: s)
                }
            }
        }
    }

    private enum Segment { case text(String), math(String) }

    private func parse(_ s: String) -> [Segment] {
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
