import UIKit

/// Placeholder artwork shared by the phone and CarPlay UIs, since the catalog has no images.
enum Artwork {
    static func colors(for video: Video) -> [UIColor] {
        // String.hashValue is randomized per launch; use a stable sum so colors don't change.
        let sum = video.id.unicodeScalars.reduce(0) { $0 &+ Int($1.value) &* 31 }
        let hue = CGFloat(sum % 360) / 360
        return [UIColor(hue: hue, saturation: 0.75, brightness: 0.75, alpha: 1),
                UIColor(hue: fmod(hue + 0.12, 1), saturation: 0.85, brightness: 0.3, alpha: 1)]
    }

    /// A 16:9 Apple TV style poster with the title drawn in, for CarPlay image rows
    /// (they show images only, no text).
    static func poster(for video: Video, width: CGFloat = 320, scale: CGFloat = 2) -> UIImage {
        let size = CGSize(width: width, height: width * 9 / 16)
        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        return UIGraphicsImageRenderer(size: size, format: format).image { context in
            let rect = CGRect(origin: .zero, size: size)
            UIBezierPath(roundedRect: rect, cornerRadius: width * 0.05).addClip()

            let cg = context.cgContext
            let space = CGColorSpaceCreateDeviceRGB()
            let fill = colors(for: video).map(\.cgColor) as CFArray
            if let gradient = CGGradient(colorsSpace: space, colors: fill, locations: nil) {
                cg.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: size.width, y: size.height), options: [])
            }
            let shade = [UIColor.clear.cgColor, UIColor.black.withAlphaComponent(0.75).cgColor] as CFArray
            if let gradient = CGGradient(colorsSpace: space, colors: shade, locations: [0.4, 1]) {
                cg.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: 0, y: size.height), options: [])
            }

            let iconSize = size.height * 0.3
            let icon = UIImage(systemName: "play.circle.fill")?
                .withTintColor(UIColor.white.withAlphaComponent(0.9), renderingMode: .alwaysOriginal)
            icon?.draw(in: CGRect(x: (size.width - iconSize) / 2, y: size.height * 0.22,
                                  width: iconSize, height: iconSize))

            let paragraph = NSMutableParagraphStyle()
            paragraph.lineBreakMode = .byTruncatingTail
            let attributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: size.height * 0.11, weight: .bold),
                .foregroundColor: UIColor.white,
                .paragraphStyle: paragraph,
            ]
            let inset = width * 0.05
            (video.title as NSString).draw(
                in: CGRect(x: inset, y: size.height * 0.74, width: size.width - inset * 2, height: size.height * 0.2),
                withAttributes: attributes)
        }
    }
}
