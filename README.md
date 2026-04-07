# uiautomator2-cli

CLI wrapper for [uiautomator2](https://github.com/openatx/uiautomator2), enabling AI agents and humans to operate Android devices from the command line.

Every command prints the equivalent uiautomator2 Python code alongside its result, making it easy to build or replay automation scripts.

## Installation

```bash
pip install uiautomator2-cli
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install uiautomator2-cli
```

## Requirements

- Python >= 3.8
- An Android device connected via ADB (USB or network)

## Quick Start

```bash
# Take a screenshot
u2cli screenshot screen.png

# Click a button by text
u2cli click --text "Settings"

# Type into the focused field
u2cli send-keys "hello world"

# Press the back key
u2cli press back

# Start an app
u2cli app-start com.android.settings

# Dump the UI hierarchy
u2cli dump-hierarchy
```

## Global Options

All commands accept the following options at the top level (before the subcommand):

| Option | Description |
|---|---|
| `-s, --serial` | Target device serial (also reads `ANDROID_SERIAL` env var) |
| `--json` | Output result as JSON |
| `--version` | Show the version and exit |

```bash
# Target a specific device
u2cli -s emulator-5554 screenshot

# Output as JSON for scripting
u2cli --json get-text --text "Battery"

# Combine both
u2cli -s emulator-5554 --json device-info

# Use environment variable
ANDROID_SERIAL=emulator-5554 u2cli screenshot
```

## Element Selectors

Commands that operate on UI elements accept one or more selector options:

| Option | Description |
|---|---|
| `--text TEXT` | Exact text match |
| `--text-contains TEXT` | Text contains substring |
| `--text-matches REGEX` | Text matches regex |
| `--text-starts-with TEXT` | Text starts with prefix |
| `--resource-id ID` | Resource ID (e.g. `com.pkg:id/btn`) |
| `--class-name CLASS` | UI class name |
| `--description DESC` | Content description (exact) |
| `--description-contains DESC` | Content description contains substring |
| `--package PKG` | Package name |
| `--index N` | Sibling index |
| `--instance N` | Global instance index (0-based) |
| `--clickable` | Element is clickable |
| `--scrollable` | Element is scrollable |
| `--checkable` | Element is checkable |
| `--checked` | Element is checked |
| `--enabled` | Element is enabled |
| `--focused` | Element is focused |
| `--selected` | Element is selected |

## Commands

### Element Commands

| Command | Description |
|---|---|
| `click` | Click a UI element |
| `long-click` | Long-click a UI element |
| `get-text` | Get the text of a UI element |
| `set-text TEXT` | Set text on a UI element (clears first) |
| `clear-text` | Clear text from a UI element |
| `exists` | Check whether a UI element exists |
| `wait` | Wait for an element to appear (or disappear with `--gone`) |
| `element-info` | Get detailed info about a UI element |
| `swipe-element` | Swipe on a UI element (`--direction left\|right\|up\|down`) |
| `scroll` | Scroll a scrollable element |

### XPath Commands

| Command | Description |
|---|---|
| `xpath-click XPATH` | Click an element by XPath |
| `xpath-get-text XPATH` | Get text of an element by XPath |
| `xpath-exists XPATH` | Check if an element exists by XPath |
| `xpath-set-text XPATH TEXT` | Set text on an element by XPath |

### Device / Screen Commands

| Command | Description |
|---|---|
| `screenshot [FILENAME]` | Take a screenshot (default: `screenshot.png`) |
| `dump-hierarchy` | Dump the UI hierarchy as a compact text tree |
| `device-info` | Show device information (model, SDK, screen size, …) |
| `ui-info` | Show UiAutomator device info |
| `window-size` | Get screen width and height |
| `screen-on` | Wake the device |
| `screen-off` | Put the device to sleep |
| `orientation` | Get or set screen orientation |
| `press KEY` | Press a hardware/soft key (`home`, `back`, `menu`, `enter`, …) |
| `swipe FX FY TX TY` | Swipe between two coordinates |
| `swipe-ext DIRECTION` | High-level directional swipe (`left\|right\|up\|down`) |
| `click-coord X Y` | Click at coordinates |
| `double-click X Y` | Double-click at coordinates |
| `long-click-coord X Y` | Long-click at coordinates |
| `send-keys TEXT` | Type text into the focused input field |
| `open-notification` | Pull down the notification shade |
| `open-quick-settings` | Pull down the quick settings panel |
| `open-url URL` | Open a URL in the default browser |
| `shell CMD...` | Run an ADB shell command on the device |
| `current-app` | Show the foreground app (package + activity) |

### App Management Commands

| Command | Description |
|---|---|
| `app-start PACKAGE` | Launch an app by package name |
| `app-stop PACKAGE` | Force-stop an app |
| `app-clear PACKAGE` | Clear app data (`pm clear`) |
| `app-install APK` | Install an APK from a local path or URL |
| `app-uninstall PACKAGE` | Uninstall an app |
| `app-info PACKAGE` | Get app version info |
| `app-list` | List installed packages |
| `app-list-running` | List currently running packages |
| `app-wait PACKAGE` | Wait until an app is running |

## Examples

```bash
# Click a button by resource ID
u2cli click --resource-id com.android.settings:id/action_bar

# Get the text of an element
u2cli get-text --text-contains "Battery"

# Set text in a search field
u2cli set-text "hello" --resource-id com.example:id/search_input

# Wait for an element to appear (10s timeout)
u2cli wait --text "Done" --timeout 10

# Wait for an element to disappear
u2cli wait --text "Loading" --gone

# Check if an element exists (no wait)
u2cli exists --text "Sign In"

# Click via XPath
u2cli xpath-click "//android.widget.Button[@text='OK']"

# Swipe up to scroll
u2cli swipe-ext up

# Swipe from coordinates (relative 0-1)
u2cli swipe 0.5 0.8 0.5 0.2

# Press volume up
u2cli press volume_up

# Run a shell command
u2cli shell pm list packages -3

# Dump UI hierarchy to file
u2cli dump-hierarchy -o hierarchy.txt

# Output as JSON for scripting
u2cli --json get-text --text "Battery"

# Target a specific device
u2cli -s emulator-5554 screenshot
```

## JSON Output

Add `--json` before the subcommand to get structured output:

```bash
$ u2cli --json exists --text "Settings"
{"u2_code": "d(text='Settings').exists", "result": true}

$ u2cli --json get-text --resource-id com.android.settings:id/title
{"u2_code": "d(resourceId='com.android.settings:id/title').get_text(timeout=10.0)", "result": "Settings"}
```

The `u2_code` field contains the equivalent uiautomator2 Python code.

## License

MIT
