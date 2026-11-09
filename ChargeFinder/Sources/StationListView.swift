import SwiftUI
import MapKit

struct StationListView: View {
    @ObservedObject private var store = ChargingStationStore.shared

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text(store.message)
                    Button("Yakınımdaki istasyonları ara", action: store.findNearbyStations)
                }

                Section("İstasyonlar") {
                    ForEach(store.stations) { station in
                        Button {
                            openInMaps(station)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(station.name).foregroundStyle(.primary)
                                Text(station.address).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Şarj Bul")
        }
    }

    private func openInMaps(_ station: ChargingStation) {
        station.mapItem.openInMaps(launchOptions: [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving])
    }
}
