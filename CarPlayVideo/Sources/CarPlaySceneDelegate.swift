import CarPlay

/// Car display styled as closely to the Apple TV app as CarPlay templates allow:
/// one horizontal shelf of 16:9 posters per category. Tapping a poster starts
/// playback on the shared player and shows the Now Playing screen; tapping a
/// shelf title opens the full list for that category.
final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    private var interfaceController: CPInterfaceController?

    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene,
                                  didConnect interfaceController: CPInterfaceController) {
        self.interfaceController = interfaceController
        let scale = interfaceController.carTraitCollection.displayScale

        let sections = VideoCatalog.shelves.map { shelf -> CPListSection in
            let videos = Array(shelf.videos.prefix(CPMaximumNumberOfGridImages))
            let row = CPListImageRowItem(text: shelf.title,
                                         images: videos.map { Artwork.poster(for: $0, scale: max(scale, 1)) })
            row.listImageRowHandler = { [weak self] _, index, completion in
                self?.play(videos[index])
                completion()
            }
            row.handler = { [weak self] _, completion in
                self?.showShelf(title: shelf.title, videos: shelf.videos, scale: scale)
                completion()
            }
            return CPListSection(items: [row])
        }

        let home = CPListTemplate(title: "Videolar", sections: sections)
        interfaceController.setRootTemplate(home, animated: true, completion: nil)
    }

    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene,
                                  didDisconnectInterfaceController interfaceController: CPInterfaceController) {
        self.interfaceController = nil
    }

    private func showShelf(title: String, videos: [Video], scale: CGFloat) {
        let items = videos.map { video -> CPListItem in
            let item = CPListItem(text: video.title, detailText: video.subtitle,
                                  image: Artwork.poster(for: video, width: 160, scale: max(scale, 1)))
            item.accessoryType = .disclosureIndicator
            item.handler = { [weak self] _, completion in
                self?.play(video)
                completion()
            }
            return item
        }
        interfaceController?.pushTemplate(CPListTemplate(title: title, sections: [CPListSection(items: items)]),
                                          animated: true, completion: nil)
    }

    private func play(_ video: Video) {
        PlayerManager.shared.play(video)
        guard let controller = interfaceController,
              !(controller.topTemplate is CPNowPlayingTemplate) else { return }
        controller.pushTemplate(CPNowPlayingTemplate.shared, animated: true, completion: nil)
    }
}
