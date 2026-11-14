import SwiftUI
import MapKit

struct StationListView: View {
    @ObservedObject private var store = ChargingStationStore.shared
    @State private var netflixMessage: String?

    var body: some View {
        NavigationStack {
            List {
                Section("Hikâyeler · demo") {
                    StoryStripView()
                        .listRowInsets(EdgeInsets(top: 8, leading: 0, bottom: 8, trailing: 0))
                }

                Section("Netflix · iPhone") {
                    Button {
                        openNetflix()
                    } label: {
                        Label("Netflix’i aç", systemImage: "play.rectangle.fill")
                    }
                    Text("Netflix’in resmî uygulamasına veya web sitesine geçiş yapar. CarPlay’de video göstermez.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Radyo · popüler Türkiye kanalları") {
                    RadioSectionView()
                }

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
            .alert("Netflix", isPresented: Binding(
                get: { netflixMessage != nil },
                set: { if !$0 { netflixMessage = nil } }
            )) {
                Button("Tamam", role: .cancel) { netflixMessage = nil }
            } message: {
                Text(netflixMessage ?? "")
            }
        }
    }

    private func openNetflix() {
        guard let url = URL(string: "https://www.netflix.com/") else {
            netflixMessage = "Netflix bağlantısı oluşturulamadı."
            return
        }

        UIApplication.shared.open(url, options: [:]) { opened in
            DispatchQueue.main.async {
                netflixMessage = opened
                    ? "Netflix açıldı. Video oynatımını Netflix uygulamasında veya web sitesinde başlatıp kontrol edin."
                    : "Netflix açılamadı. İnternet bağlantınızı kontrol edin."
            }
        }
    }

    private func openInMaps(_ station: ChargingStation) {
        station.mapItem.openInMaps(launchOptions: [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving])
    }
}
