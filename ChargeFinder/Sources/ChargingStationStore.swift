import Combine
import CoreLocation
import MapKit

struct ChargingStation: Identifiable {
    let id: String
    let name: String
    let address: String
    let mapItem: MKMapItem
}

@MainActor
final class ChargingStationStore: NSObject, ObservableObject, CLLocationManagerDelegate {
    static let shared = ChargingStationStore()

    @Published private(set) var stations: [ChargingStation] = []
    @Published private(set) var message = "Yakındaki istasyonları bulmak için konum izni verin."

    private let locationManager = CLLocationManager()
    private var lastSearchLocation: CLLocation?

    override private init() {
        super.init()
        locationManager.delegate = self
    }

    func findNearbyStations() {
        switch locationManager.authorizationStatus {
        case .notDetermined:
            locationManager.requestWhenInUseAuthorization()
        case .authorizedAlways, .authorizedWhenInUse:
            message = "Konum alınıyor…"
            locationManager.requestLocation()
        case .denied, .restricted:
            message = "Konum izni kapalı. Ayarlar'dan bu uygulama için konum iznini açın."
        @unknown default:
            message = "Konum izni kontrol edilemedi."
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        if manager.authorizationStatus == .authorizedAlways || manager.authorizationStatus == .authorizedWhenInUse {
            findNearbyStations()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        lastSearchLocation = location
        Task { await search(near: location) }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        message = "Konum alınamadı. Tekrar deneyin."
    }

    private func search(near location: CLLocation) async {
        var request = MKLocalSearch.Request()
        request.naturalLanguageQuery = "Electric vehicle charging station"
        request.region = MKCoordinateRegion(
            center: location.coordinate,
            latitudinalMeters: 25_000,
            longitudinalMeters: 25_000
        )
        request.pointOfInterestFilter = MKPointOfInterestFilter(including: [.evCharger])

        do {
            let response = try await MKLocalSearch(request: request).start()
            stations = response.mapItems.prefix(20).map { item in
                ChargingStation(
                    id: "\(item.placemark.coordinate.latitude),\(item.placemark.coordinate.longitude)-\(item.name ?? "")",
                    name: item.name ?? "Şarj istasyonu",
                    address: [item.placemark.thoroughfare, item.placemark.locality]
                        .compactMap { $0 }
                        .joined(separator: ", "),
                    mapItem: item
                )
            }
            message = stations.isEmpty ? "Yakında istasyon bulunamadı." : "Yakındaki istasyonlar"
        } catch {
            message = "İstasyonlar aranamadı. İnternet bağlantınızı kontrol edin."
        }
    }
}
