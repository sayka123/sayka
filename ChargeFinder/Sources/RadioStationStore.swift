import Foundation
import Combine

@MainActor
final class RadioStationStore: ObservableObject {
    @Published private(set) var stations: [RadioStation] = []
    @Published private(set) var message = "Popüler istasyonlar yükleniyor…"
    @Published private(set) var isLoading = false

    func loadStations() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        guard let url = URL(string: "https://de1.api.radio-browser.info/json/stations/search?countrycode=TR&hidebroken=true&order=clickcount&reverse=true&limit=30") else {
            message = "Radyo listesi adresi geçersiz."
            return
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 15
        request.setValue("ChargeFinder/1.0", forHTTPHeaderField: "User-Agent")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard (response as? HTTPURLResponse)?.statusCode == 200 else {
                message = "Radyo listesi şu anda alınamıyor."
                return
            }
            stations = try JSONDecoder().decode([RadioStation].self, from: data)
                .filter { $0.streamURL != nil && !$0.name.isEmpty }
            message = stations.isEmpty ? "Şu anda istasyon bulunamadı." : "En çok dinlenenlerden seçin"
        } catch {
            message = "Radyo listesi yüklenemedi. İnternet bağlantınızı kontrol edip yenileyin."
        }
    }
}
