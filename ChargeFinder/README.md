# ChargeFinder

Swift iOS starter for finding nearby EV charging points and opening directions in Apple Maps. It includes an iPhone list and a CarPlay list template.

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
