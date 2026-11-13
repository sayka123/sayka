import AVFoundation
import MediaPlayer

/// Single AVPlayer shared by the phone UI and the CarPlay scene.
/// Video reaches the car display via AirPlay ("video in the car", parked only);
/// if the car reports video unavailable, the system falls back to audio.
final class PlayerManager {
    static let shared = PlayerManager()

    let player = AVPlayer()
    private(set) var current: Video?

    private init() {
        player.allowsExternalPlayback = true
        player.usesExternalPlaybackWhileExternalScreenIsActive = true
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback, policy: .longFormVideo)
        configureRemoteCommands()
    }

    func play(_ video: Video) {
        try? AVAudioSession.sharedInstance().setActive(true)
        if current != video {
            current = video
            player.replaceCurrentItem(with: AVPlayerItem(url: video.url))
        }
        player.play()
        updateNowPlaying()
    }

    func togglePlayPause() {
        if player.timeControlStatus == .paused { player.play() } else { player.pause() }
        updateNowPlaying()
    }

    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.addTarget { [weak self] _ in
            guard let self, self.player.currentItem != nil else { return .noActionableNowPlayingItem }
            self.player.play()
            self.updateNowPlaying()
            return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            self?.player.pause()
            self?.updateNowPlaying()
            return .success
        }
        center.togglePlayPauseCommand.addTarget { [weak self] _ in
            self?.togglePlayPause()
            return .success
        }
        center.skipForwardCommand.preferredIntervals = [15]
        center.skipForwardCommand.addTarget { [weak self] _ in self?.seek(by: 15) ?? .commandFailed }
        center.skipBackwardCommand.preferredIntervals = [15]
        center.skipBackwardCommand.addTarget { [weak self] _ in self?.seek(by: -15) ?? .commandFailed }
    }

    private func seek(by seconds: Double) -> MPRemoteCommandHandlerStatus {
        guard player.currentItem != nil else { return .noActionableNowPlayingItem }
        let target = CMTimeAdd(player.currentTime(), CMTime(seconds: seconds, preferredTimescale: 600))
        player.seek(to: target) { [weak self] _ in self?.updateNowPlaying() }
        return .success
    }

    private func updateNowPlaying() {
        guard let video = current else {
            MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
            return
        }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: video.title,
            MPMediaItemPropertyArtist: video.subtitle,
            MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaType.video.rawValue,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: player.currentTime().seconds,
            MPNowPlayingInfoPropertyPlaybackRate: player.rate,
        ]
        if let duration = player.currentItem?.duration.seconds, duration.isFinite {
            info[MPMediaItemPropertyPlaybackDuration] = duration
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }
}
