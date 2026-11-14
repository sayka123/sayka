# ChargeFinder

Swift iOS starter for finding nearby EV charging points and opening directions in Apple Maps. It includes an iPhone list and a CarPlay list template.

The iPhone screen also contains a swipeable, local sample-stories demo. It is not connected to Instagram and is intentionally excluded from CarPlay.

The iPhone screen has a link to Netflix's official website; iOS may hand it off to the Netflix app. This does not embed Netflix or guarantee playback. Netflix video is not exposed in CarPlay by this app.

The radio section fetches popular Turkish stations, sorted by Radio Browser click counts, and streams the selected station with AVPlayer. Station stream availability and rights are managed by each station and can change. This radio list is currently iPhone-only; exposing it in CarPlay requires Apple's separate CarPlay audio entitlement and an audio-category CarPlay implementation.

## Generate and open the Xcode project

On a Mac with Xcode installed, install XcodeGen (`brew install xcodegen`), then from this directory run:

```sh
xcodegen generate
open ChargeFinder.xcodeproj
```

Select your iPhone or the CarPlay simulator in Xcode and build. Set a unique bundle identifier and configure your Apple developer team before signing.

## CarPlay access

Apple requires approval for the EV charging CarPlay entitlement before the app can run as a CarPlay app in a vehicle or simulator. Request the EV charging category through Apple's CarPlay entitlement process and configure the approved capability and provisioning profile in Xcode. This starter intentionally does not include an unapproved entitlement.

## Scope and limitations

- Search uses MapKit's EV-charger points of interest and requires location permission and internet access.
- Search results may not include connector type, live availability, or pricing; verify these details with a charging-network provider before relying on them.
- Build and CarPlay simulator testing require macOS and Xcode. The current Hoplite workspace is Linux-based, so those checks cannot run here.
