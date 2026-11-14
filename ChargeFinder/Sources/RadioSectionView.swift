import SwiftUI

struct RadioSectionView: View {
    @StateObject private var stations = RadioStationStore()
    @StateObject private var player = RadioPlayer.shared

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(stations.message)
                .font(.caption)
                .foregroundStyle(.secondary)

            if stations.isLoading && stations.stations.isEmpty {
                ProgressView()
            } else if stations.stations.isEmpty {
                Button("Yeniden dene") {
                    Task { await stations.loadStations() }
                }
            } else {
                ForEach(stations.stations) { station in
                    Button {
                        player.toggle(station)
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: player.isPlaying(station) ? "pause.circle.fill" : "play.circle.fill")
                                .font(.title2)
                                .foregroundStyle(.tint)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(station.name)
                                    .foregroundStyle(.primary)
                                    .lineLimit(1)
                                Text(station.details.isEmpty ? "Canlı internet yayını" : station.details)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer(minLength: 0)
                        }
                    }
                    .buttonStyle(.plain)
                }

                if !player.message.isEmpty {
                    Text(player.message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .accessibilityLiveRegion(.polite)
                }

                Button("Listeyi yenile") {
                    Task { await stations.loadStations() }
                }
                .font(.caption)
                .disabled(stations.isLoading)
            }
        }
        .task { await stations.loadStations() }
    }
}
