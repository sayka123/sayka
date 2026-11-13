import AVKit
import UIKit

/// Phone UI: pick a video, then use the AirPlay button to send it to the car display.
final class VideoListViewController: UITableViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        title = "CarPlay Video"
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "cell")

        let routePicker = AVRoutePickerView(frame: CGRect(x: 0, y: 0, width: 44, height: 44))
        routePicker.prioritizesVideoDevices = true
        navigationItem.rightBarButtonItem = UIBarButtonItem(customView: routePicker)
    }

    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        VideoCatalog.all.count
    }

    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell", for: indexPath)
        let video = VideoCatalog.all[indexPath.row]
        var content = cell.defaultContentConfiguration()
        content.text = video.title
        content.secondaryText = video.subtitle
        cell.contentConfiguration = content
        cell.accessoryType = .disclosureIndicator
        return cell
    }

    override func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        PlayerManager.shared.play(VideoCatalog.all[indexPath.row])
        let playerVC = AVPlayerViewController()
        playerVC.player = PlayerManager.shared.player
        present(playerVC, animated: true)
    }
}
