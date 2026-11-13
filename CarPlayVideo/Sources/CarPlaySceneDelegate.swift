import CarPlay

/// Browsing UI on the car display. Selecting a video starts playback on the
/// shared player and shows the Now Playing screen.
final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    private var interfaceController: CPInterfaceController?

    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene,
                                  didConnect interfaceController: CPInterfaceController) {
        self.interfaceController = interfaceController

        let items = VideoCatalog.all.map { video -> CPListItem in
            let item = CPListItem(text: video.title, detailText: video.subtitle)
            item.accessoryType = .disclosureIndicator
            item.handler = { [weak self] _, completion in
                PlayerManager.shared.play(video)
                self?.showNowPlaying()
                completion()
            }
            return item
        }

        let list = CPListTemplate(title: "Videolar", sections: [CPListSection(items: items)])
        interfaceController.setRootTemplate(list, animated: true, completion: nil)
    }

    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene,
                                  didDisconnectInterfaceController interfaceController: CPInterfaceController) {
        self.interfaceController = nil
    }

    private func showNowPlaying() {
        guard let controller = interfaceController,
              !(controller.topTemplate is CPNowPlayingTemplate) else { return }
        controller.pushTemplate(CPNowPlayingTemplate.shared, animated: true, completion: nil)
    }
}
