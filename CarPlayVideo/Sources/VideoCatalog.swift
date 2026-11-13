import Foundation

struct Video: Equatable {
    let id: String
    let title: String
    let subtitle: String
    let url: URL
}

enum VideoCatalog {
    // Apple's public HLS test streams; replace with your own content.
    static let all: [Video] = [
        Video(id: "bipbop-adv",
              title: "Apple HLS Örnek (fMP4)",
              subtitle: "Gelişmiş HLS test akışı",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8")!),
        Video(id: "bipbop-ts",
              title: "Apple HLS Örnek (TS)",
              subtitle: "Klasik HLS test akışı",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8")!),
        Video(id: "bipbop-4x3",
              title: "Apple BipBop 4:3",
              subtitle: "Basit HLS test akışı",
              url: URL(string: "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8")!),
    ]
}
