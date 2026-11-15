import AVKit
import UIKit

/// Phone UI styled like the Apple TV app: a large hero banner on top and
/// horizontally scrolling shelves of 16:9 cards per category. The AirPlay
/// button sends the selected video to the car display.
final class VideoListViewController: UICollectionViewController {
    private enum Section: Hashable {
        case hero
        case shelf(String)
    }

    private enum Item: Hashable {
        case hero(Video)
        case card(Video, shelf: String)

        var video: Video {
            switch self {
            case .hero(let video), .card(let video, _): return video
            }
        }
    }

    private static let headerKind = "shelf-header"
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!

    init() {
        super.init(collectionViewLayout: Self.makeLayout())
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Videolar"
        navigationController?.navigationBar.prefersLargeTitles = true
        collectionView.backgroundColor = .black

        let routePicker = AVRoutePickerView(frame: CGRect(x: 0, y: 0, width: 44, height: 44))
        routePicker.prioritizesVideoDevices = true
        routePicker.tintColor = .white
        routePicker.activeTintColor = .systemBlue
        navigationItem.rightBarButtonItem = UIBarButtonItem(customView: routePicker)

        configureDataSource()
        applySnapshot()
    }

    // MARK: - Layout

    private static func makeLayout() -> UICollectionViewCompositionalLayout {
        UICollectionViewCompositionalLayout { sectionIndex, environment in
            let width = environment.container.effectiveContentSize.width
            let isWide = environment.traitCollection.horizontalSizeClass == .regular || width > 600

            if sectionIndex == 0 {
                let item = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(1),
                                                                    heightDimension: .fractionalHeight(1)))
                let heroHeight = min(width * 9 / 16, isWide ? 420 : 260)
                let group = NSCollectionLayoutGroup.horizontal(layoutSize: .init(widthDimension: .fractionalWidth(1),
                                                                                 heightDimension: .absolute(heroHeight)),
                                                               subitems: [item])
                let section = NSCollectionLayoutSection(group: group)
                section.contentInsets = .init(top: 8, leading: 16, bottom: 24, trailing: 16)
                return section
            }

            // Cards show the next card peeking in, like tvOS shelves.
            let cardWidth: CGFloat = isWide ? 300 : width * 0.72
            let item = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(1),
                                                                heightDimension: .fractionalHeight(1)))
            let group = NSCollectionLayoutGroup.horizontal(layoutSize: .init(widthDimension: .absolute(cardWidth),
                                                                             heightDimension: .absolute(cardWidth * 9 / 16 + 48)),
                                                           subitems: [item])
            let section = NSCollectionLayoutSection(group: group)
            section.orthogonalScrollingBehavior = .groupPaging
            section.interGroupSpacing = 16
            section.contentInsets = .init(top: 8, leading: 16, bottom: 28, trailing: 16)
            let header = NSCollectionLayoutBoundarySupplementaryItem(
                layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: .estimated(32)),
                elementKind: headerKind, alignment: .top)
            section.boundarySupplementaryItems = [header]
            return section
        }
    }

    // MARK: - Data

    private func configureDataSource() {
        let heroRegistration = UICollectionView.CellRegistration<HeroCell, Video> { cell, _, video in
            cell.configure(with: video)
        }
        let cardRegistration = UICollectionView.CellRegistration<CardCell, Video> { cell, _, video in
            cell.configure(with: video)
        }
        let headerRegistration = UICollectionView.SupplementaryRegistration<UICollectionViewListCell>(
            elementKind: Self.headerKind) { [weak self] header, _, indexPath in
            guard let self, case .shelf(let title) = self.dataSource.sectionIdentifier(for: indexPath.section) else { return }
            var content = UIListContentConfiguration.plainHeader()
            content.text = title
            content.textProperties.font = .preferredFont(forTextStyle: .title3).bold()
            content.textProperties.color = .white
            content.directionalLayoutMargins = .zero
            header.contentConfiguration = content
            header.backgroundConfiguration = .clear()
        }

        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) { collectionView, indexPath, item in
            switch item {
            case .hero(let video):
                return collectionView.dequeueConfiguredReusableCell(using: heroRegistration, for: indexPath, item: video)
            case .card(let video, _):
                return collectionView.dequeueConfiguredReusableCell(using: cardRegistration, for: indexPath, item: video)
            }
        }
        dataSource.supplementaryViewProvider = { collectionView, _, indexPath in
            collectionView.dequeueConfiguredReusableSupplementary(using: headerRegistration, for: indexPath)
        }
    }

    private func applySnapshot() {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        if let featured = VideoCatalog.all.first {
            snapshot.appendSections([.hero])
            snapshot.appendItems([.hero(featured)], toSection: .hero)
        }
        for shelf in VideoCatalog.shelves {
            snapshot.appendSections([.shelf(shelf.title)])
            snapshot.appendItems(shelf.videos.map { .card($0, shelf: shelf.title) }, toSection: .shelf(shelf.title))
        }
        dataSource.apply(snapshot, animatingDifferences: false)
    }

    override func collectionView(_ collectionView: UICollectionView, didSelectItemAt indexPath: IndexPath) {
        guard let item = dataSource.itemIdentifier(for: indexPath) else { return }
        PlayerManager.shared.play(item.video)
        let playerVC = AVPlayerViewController()
        playerVC.player = PlayerManager.shared.player
        present(playerVC, animated: true)
    }
}

// MARK: - Artwork

/// Placeholder artwork: a per-video gradient, since the catalog has no images.
private final class ArtworkView: UIView {
    override class var layerClass: AnyClass { CAGradientLayer.self }

    func configure(with video: Video) {
        let gradient = layer as! CAGradientLayer
        gradient.colors = Artwork.colors(for: video).map(\.cgColor)
        gradient.startPoint = CGPoint(x: 0, y: 0)
        gradient.endPoint = CGPoint(x: 1, y: 1)
    }
}

/// Shared tvOS-like press/highlight feedback.
private class ScalingCell: UICollectionViewCell {
    override var isHighlighted: Bool {
        didSet {
            UIView.animate(withDuration: 0.2, delay: 0, usingSpringWithDamping: 0.7, initialSpringVelocity: 0) {
                self.transform = self.isHighlighted ? CGAffineTransform(scaleX: 1.05, y: 1.05) : .identity
            }
        }
    }
}

private final class CardCell: ScalingCell {
    private let artwork = ArtworkView()
    private let playIcon = UIImageView(image: UIImage(systemName: "play.circle.fill"))
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()

    override init(frame: CGRect) {
        super.init(frame: frame)
        artwork.layer.cornerRadius = 12
        artwork.layer.cornerCurve = .continuous
        artwork.clipsToBounds = true

        playIcon.tintColor = UIColor.white.withAlphaComponent(0.9)
        playIcon.preferredSymbolConfiguration = .init(pointSize: 36)

        titleLabel.font = .preferredFont(forTextStyle: .subheadline).bold()
        titleLabel.textColor = .white
        subtitleLabel.font = .preferredFont(forTextStyle: .caption1)
        subtitleLabel.textColor = .lightGray

        let labels = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel])
        labels.axis = .vertical
        labels.spacing = 2

        [artwork, playIcon, labels].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            contentView.addSubview($0)
        }
        NSLayoutConstraint.activate([
            artwork.topAnchor.constraint(equalTo: contentView.topAnchor),
            artwork.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            artwork.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            artwork.heightAnchor.constraint(equalTo: artwork.widthAnchor, multiplier: 9.0 / 16.0),
            playIcon.centerXAnchor.constraint(equalTo: artwork.centerXAnchor),
            playIcon.centerYAnchor.constraint(equalTo: artwork.centerYAnchor),
            labels.topAnchor.constraint(equalTo: artwork.bottomAnchor, constant: 8),
            labels.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 2),
            labels.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -2),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    func configure(with video: Video) {
        artwork.configure(with: video)
        titleLabel.text = video.title
        subtitleLabel.text = video.subtitle
    }
}

private final class HeroCell: ScalingCell {
    private let artwork = ArtworkView()
    private let shade = CAGradientLayer()
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()
    private let playButton = UILabel()

    override init(frame: CGRect) {
        super.init(frame: frame)
        contentView.layer.cornerRadius = 16
        contentView.layer.cornerCurve = .continuous
        contentView.clipsToBounds = true

        shade.colors = [UIColor.clear.cgColor, UIColor.black.withAlphaComponent(0.8).cgColor]
        shade.locations = [0.35, 1]
        artwork.layer.addSublayer(shade)

        titleLabel.font = .preferredFont(forTextStyle: .title1).bold()
        titleLabel.textColor = .white
        titleLabel.numberOfLines = 2
        subtitleLabel.font = .preferredFont(forTextStyle: .subheadline)
        subtitleLabel.textColor = UIColor.white.withAlphaComponent(0.8)

        // Non-interactive pill; the whole cell is the tap target.
        playButton.text = "  ▶︎  Oynat  "
        playButton.font = .preferredFont(forTextStyle: .headline)
        playButton.textColor = .black
        playButton.backgroundColor = .white
        playButton.layer.cornerRadius = 8
        playButton.clipsToBounds = true

        let stack = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel, playButton])
        stack.axis = .vertical
        stack.alignment = .leading
        stack.spacing = 6
        stack.setCustomSpacing(12, after: subtitleLabel)

        [artwork, stack].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            contentView.addSubview($0)
        }
        NSLayoutConstraint.activate([
            artwork.topAnchor.constraint(equalTo: contentView.topAnchor),
            artwork.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
            artwork.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            artwork.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            stack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(lessThanOrEqualTo: contentView.trailingAnchor, constant: -20),
            stack.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),
            playButton.heightAnchor.constraint(equalToConstant: 40),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    override func layoutSubviews() {
        super.layoutSubviews()
        shade.frame = artwork.bounds
    }

    func configure(with video: Video) {
        artwork.configure(with: video)
        titleLabel.text = video.title
        subtitleLabel.text = video.subtitle
    }
}

private extension UIFont {
    func bold() -> UIFont {
        guard let descriptor = fontDescriptor.withSymbolicTraits(.traitBold) else { return self }
        return UIFont(descriptor: descriptor, size: 0)
    }
}
