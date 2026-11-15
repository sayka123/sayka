import Foundation

struct Video: Hashable {
    let id: String
    let title: String
    let subtitle: String
    let category: String
    let url: URL
}

enum VideoCatalog {
    // Apple's public HLS test streams; replace with your own content.
    static let all: [Video] = [
        Video(id: "bipbop-adv",
              title: "Apple HLS Örnek (fMP4)",
              subtitle: "Gelişmiş HLS test akışı",
              category: "Öne Çıkanlar",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8")!),
        Video(id: "bipbop-ts",
              title: "Apple HLS Örnek (TS)",
              subtitle: "Klasik HLS test akışı",
              category: "Öne Çıkanlar",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8")!),
        Video(id: "bipbop-4x3",
              title: "Apple BipBop 4:3",
              subtitle: "Basit HLS test akışı",
              category: "Klasikler",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8")!),
    ]

    /// Categories in first-appearance order, each becoming one horizontal shelf.
    static var shelves: [(title: String, videos: [Video])] {
        var order: [String] = []
        var grouped: [String: [Video]] = [:]
        for video in all {
            if grouped[video.category] == nil { order.append(video.category) }
            grouped[video.category, default: []].append(video)
        }
        return order.map { ($0, grouped[$0]!) }
    }
}
