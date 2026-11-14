import Foundation

struct RadioStation: Decodable, Identifiable, Hashable {
    let stationuuid: String
    let name: String
    let url_resolved: String
    let codec: String
    let bitrate: Int

    var id: String { stationuuid }

    var streamURL: URL? {
        guard let url = URL(string: url_resolved),
              ["http", "https"].contains(url.scheme?.lowercased() ?? "") else { return nil }
        return url
    }

    var details: String {
        [codec.isEmpty ? nil : codec.uppercased(), bitrate > 0 ? "\(bitrate) kbps" : nil]
            .compactMap { $0 }
            .joined(separator: " · ")
    }
}
