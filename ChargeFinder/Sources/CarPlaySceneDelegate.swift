import CarPlay
import Combine
import MapKit

final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    private var stationsSubscription: AnyCancellable?

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        let template = CPListTemplate(title: "Şarj İstasyonları", sections: [CPListSection(items: [])])
        interfaceController.setRootTemplate(template, animated: true)

        stationsSubscription = ChargingStationStore.shared.$stations.sink { stations in
            let items = stations.map { station -> CPListItem in
                let item = CPListItem(text: station.name, detailText: station.address)
                item.handler = { _, completion in
                    station.mapItem.openInMaps(launchOptions: [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving])
                    completion()
                }
                return item
            }
            template.updateSections([CPListSection(items: items)])
            if stations.isEmpty {
                ChargingStationStore.shared.findNearbyStations()
            }
        }
    }

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didDisconnectInterfaceController interfaceController: CPInterfaceController
    ) {
        stationsSubscription = nil
    }
}
