import CarPlay
import Combine
import MapKit

final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    private var interfaceController: CPInterfaceController?
    private var stationsSubscription: AnyCancellable?

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        self.interfaceController = interfaceController
        let template = CPListTemplate(title: "Şarj İstasyonları", sections: [CPListSection(items: [])])
        interfaceController.setRootTemplate(template, animated: true)

        stationsSubscription = ChargingStationStore.shared.$stations.sink { [weak self] stations in
            let items = stations.map { station in
                CPListItem(text: station.name, detailText: station.address) { _, completion in
                    station.mapItem.openInMaps(launchOptions: [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving])
                    completion()
                }
            }
            template.updateSections([CPListSection(items: items)])
            if stations.isEmpty {
                ChargingStationStore.shared.findNearbyStations()
            }
            _ = self
        }
    }

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didDisconnectInterfaceController interfaceController: CPInterfaceController
    ) {
        stationsSubscription = nil
        self.interfaceController = nil
    }
}
