import AVFoundation
import Combine
import Foundation

@MainActor
final class RadioPlayer: ObservableObject {
    static let shared = RadioPlayer()

    @Published private(set) var currentStation: RadioStation?
    @Published private(set) var message = "Bir istasyon seçin."

    private var player: AVPlayer?
    private var itemObservation: AnyCancellable?

    func toggle(_ station: RadioStation) {
        if currentStation?.id == station.id, player?.timeControlStatus == .playing {
            player?.pause()
            message = "Duraklatıldı"
            return
        }

        guard let url = station.streamURL else {
            message = "Bu istasyonun yayın adresi geçersiz."
            return
        }

        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            message = "Ses oynatımı başlatılamadı."
            return
        }

        currentStation = station
        message = "\(station.name) yayınına bağlanıyor…"
        Task {
            guard let clickURL = URL(string: "https://de1.api.radio-browser.info/json/url/\(station.stationuuid)") else { return }
            var request = URLRequest(url: clickURL)
            request.setValue("ChargeFinder/1.0", forHTTPHeaderField: "User-Agent")
            _ = try? await URLSession.shared.data(for: request)
        }
        let item = AVPlayerItem(url: url)
        itemObservation = item.publisher(for: \.status).sink { [weak self] status in
            Task { @MainActor in
                guard let self, self.currentStation?.id == station.id else { return }
                switch status {
                case .readyToPlay:
                    self.message = "\(station.name) yayını hazır"
                case .failed:
                    self.message = "Bu istasyon şu anda yayın yapmıyor. Başka bir istasyon deneyin."
                default:
                    break
                }
            }
        }
        player = AVPlayer(playerItem: item)
        player?.play()
    }

    func isPlaying(_ station: RadioStation) -> Bool {
        currentStation?.id == station.id && player?.timeControlStatus == .playing
    }
}
