# PC LED - Android App Controller (ADB)

A small desktop app for Windows/macOS/Linux that uses **ADB** to manage apps on a connected Android phone.

## Features
- Detect connected devices
- List installed packages
- Launch/stop apps
- Uninstall apps
- Install your own APKs

## Prerequisites
- **ADB** installed and available on your `PATH`
  - Android Platform Tools: https://developer.android.com/studio/releases/platform-tools
- USB debugging enabled on your phone
- Put the [downloaded file](https://github.com/ctrbyszz/pcled/releases/latest) to the platform-tools folder

## Run
```bash
python app.py
```

## Notes
- This UI is built with Tkinter (bundled with most Python installations).
- If multiple devices are connected, select the target device in the dropdown.

## Safety
Uninstalling system apps can break your device. Use with caution.
