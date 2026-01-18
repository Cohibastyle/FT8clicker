FT8Clicker v0.6 Functional Specification Document

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [User Guide](#user-guide)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Troubleshooting](#troubleshooting)
- [Design](#design)
  - [User Interface Layout](#user-interface-layout)
  - [Components](#components)
- [Technical Specifications](#technical-specifications)
- [Settings and Configuration](#settings-and-configuration)
- [Testing and Validation](#testing-and-validation)
- [Support](#support)
- [License](#license)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [Disclaimer](#disclaimer)

## Introduction
This app is designed to facilitate FT8 communication by automating the clicking process for FT8 signals. It is compatible with various FT8 software and can be customized to suit user preferences.  Built by 5N0YEN

## Features
- Automated clicking for FT8 signals by moving mouse and simulating clicks
- Customizable timers for forcing a CQ and to change bands.
- User-friendly interface inspired by Yaesu FTDX Series Radio
- Compatibility with popular FT8 software (WSJTX, etc.)
- Support for Mac, Windows, and Linux with native screen capture backends
- Compatible with multi-monitor setups
- Accurate color-based button state detection using majority color sampling
- Real-time learned button background updates based on pixel color
- ON/OFF state detection based on grayscale vs. color
- Circular progress indicators for timers and counters
- Real-time event timeline graph with auto-scaling axes
- Delayed hover tooltips for all interactive elements
- Runaway detection and safeguards

## Requirements
### Functional Requirements
- The app must automate mouse clicks on FT8 software buttons based on learned positions and timers.
- Users must be able to learn button positions by moving the mouse and pressing a key.
- The app must support timers for CQ presses, band changes, and overall runtime.
- Band buttons must allow single selection, with automatic cycling when CQsRemaining reaches zero.
- The graphical display must show a real-time timeline of clicks with color-coded indicators.
- Circular progress indicators must display remaining time/count for CQ Time, CQs Remaining, and App Time.
- The graph must auto-scale X-axis from 10 to 100 bars and Y-axis from 30 seconds upward.
- CQ counter must decrement on both manual and automatic clicks.- Band cycling must only occur through learned bands, with appropriate logging if none available.
- Interactive elements must display delayed tooltips (3 seconds) with contextual help.- Runaway detection must stop automation after 3 short QSOs (<5 seconds).

### Non-Functional Requirements
- Compatibility: Work with WSJTX and similar FT8 software on macOS 10.15+ (using Quartz), Windows 10+ (using PyAutoGUI), Linux (Ubuntu 18.04+) (using PyAutoGUI).
- Reliability: Include safeguards like error handling for invalid configurations.

### Constraints
- Built using Python 3.x with PyQt6 and PyAutoGUI.
- Must comply with amateur radio regulations; users are responsible for legal use.

## User Guide
### Installation
1. Ensure Python 3.x is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`
### Usage
1. Open your preferred FT8 software, tested with WSJT-x.
2. Launch FT8Clicker.
3. Learn the positions of the FT8 buttons by clicking the "Learn" button and following the prompts. The app will capture the button's position and color for accurate state detection.
4. Configure the click interval and other settings as needed.
5. Start the clicking process by pressing the "Start" button.
6. Monitor the FT8 software for automated clicks based on button states.
7. Observe the circular progress indicators and real-time graph for visual feedback.
8. Hover over buttons and arcs for 3 seconds to see contextual help tooltips.
9. Use the Help button for an in-app guide.

### Troubleshooting
- If the application does not start, ensure that your system meets the minimum requirements.
- If clicks are not being registered, check the compatibility settings with your FT8 software.
- In WSJT-x, set TX Watchdog > CQ Time to prevent unpredictable behavior.
- Band changes only occur for learned bands; ensure bands are properly learned before expecting cycling.
- macOS: Screen Recording permission is required for pixel detection. Enable it in System Settings → Privacy & Security → Screen Recording for Visual Studio Code (or your Python app), then restart FT8Clicker.
- For further assistance, refer to the FAQ section on the official website.

## Design
### User Interface Layout
The look and feel will be inspired by a Yaesu FTDX Series Radio.  Black Background with white, blue and orange text and accents and organized into clear sections for ease of use. 

The app consists of the following main sections:
1. **Header**: Displays the app name and version and author.
2. **Button List**: Contains buttons for various FT8 functions.
3. **Learn and Locate Icons**: Buttons to learn the position and color of the FT8 buttons on the screen and to move the mouse to a learned coordinate.
4. **Main Function Buttons**: Buttons to start, stop, and configure the clicking process.
5. **Status Display Area**: Shows real-time status and countdowns based on settings.
6. **Graphical Display Area**: Visual representation of the clicking process history and status.
7. **Footer**: Contains copyright and version information.

### Components
#### Button List
- Tx Enable
- Tx 6 (aka 'CQ')
- Band Buttons (40m, 20m, 17m, 15m, 12m, 10m) - It is possible to select which buttons are shown via the settings. These are the initial buttons. Other buttons include 160m, 30m, 6m, 2m, 70cm.
  - The band name, Tx Enable, and Tx 6 will be shown on the button in big bold italic text.
- learn and find buttons
  - to learn a button, press the learn button, then select a button (the selected button will change color to indicate it is chosen for learning), and move the mouse cursor to the FT8 app button and press L. When the LEARN button is pressed, its label changes to "LEARNING" and the color changes to show that it is in learning mode. The log window will display "Select a button, then move the mouse cursor to the FT8 app button and press L". After L is pressed, it will say "`buttonname` has been learned at location `x,y` with color `r,g,b'". The app uses majority color detection from a 9x9 pixel area around the cursor to accurately capture the button's inactive state color.
  - to locate a button, press the locate button, then select a button, and the mouse will move to that position on the screen.
- Buttons once learned:
  - Can be clicked to move the mouse to that position on the screen.  After the mouse will return to the previous position.
  - Can be re-learned going through the learn process again.
  - All button locations will be regularly checked for the color, and this color will be used for the background of the button in the app.  
  - When only a single color state is known for a button, it is treated as OFF.
  - When multiple color states are detected, grayscale (white/gray/silver/black) is OFF and any other color is ON.
- All buttons display delayed tooltips (3 seconds hover) with contextual help descriptions.

#### Main Function Buttons
- **Start/Stop Button**: STOPPED (red) pauses all counters; RUNNING (green) resets counters to settings and starts automation.
- **Pause Button**: Only visible when running. PAUSE ON (yellow) pauses all automation and timers; PAUSE OFF (white) resumes.
- **Settings Button**: Opens the settings menu where users can customize click intervals, button visibility, values for *CQTimeRemaining*, *CQsRemaining*, *AppTimeRemaining*, and other preferences. Unlearn all or some of the learned buttons.
- **Help Button**: Opens a resizable popup guide covering controls, learn/locate, and permissions.
- All buttons will be labeled with their keyboard shortcut for easy reference, e.g., (S)tart, (P)ause.
- All buttons display delayed tooltips (3 seconds hover) with usage instructions.

#### Status Display Area
- Displays real-time information about the clicking process, including:
  - Current status (Running, Paused, Stopped).
  - Circular progress indicators for:
    - CQ Time Remaining: Arc showing countdown until auto-CQ, resets on Tx Enable. Green=plenty, Yellow=warning, Red=critical.
    - CQs Remaining: Arc showing count until band change. Decrements on each CQ (manual or auto).
    - App Time Remaining: Arc showing overall runtime countdown. Counts down total runtime.
  - Countdown timer until CQ is auto-pressed (*CQTimeRemaining*).
    - Is reset whenever the Enable TX is pressed automatically.
    - When reached, the app will automatically click the CQ button.
    - Default value 90 Seconds, adjustable from 60 -3000 seconds.
  - Countdown counter of number of CQs until band change (*CQsRemaining*).
    - Decrements on both manual and automatic CQ clicks.
    - When reached, the app will automatically click the next learned band to the right of the current band, or back to the first band if at the end.
    - Default Value 10, Adjustable from 0 - 100.
  - Countdown timer of overall app runtime (*AppTimeRemaining*).
    - When reached, the app will automatically stop clicking.
    - Default value of 30 minutes, adjustable from 5 minute to 240 minutes.
- All arc indicators display delayed tooltips (3 seconds hover) with detailed explanations.

#### Log
- A log window showing timestamps of app functions, detections, and presses. The window should be scalable and have a button to clear the log.
- every log entry will be timestamped, and include:
  - When the app is started, paused, resumed, and stopped.
  - When the Enable TX button is auto-clicked.
  - When the CQ button is auto-clicked.
  - When the band is changed, including the new band selected.
  - When a learned button changes state to ON or OFF.
  - Sampled pixel colors with closest color names when learning new states.
  - Screen capture method logged once per session.
  - Any errors or issues encountered during operation.
- The log can be exported to a file.

#### Graphical Display Area
- Visual representation of the clicking process history and status, including:
  - A timeline of clicks made.
    - Y-axis shows the duration between clicks (in seconds), auto-scaling from 30 seconds upward.
    - X-axis shows the sequence number of clicks made over time, auto-scaling from 10 to 100 bars.
    - Light grey horizontal lines to show 30-second intervals on the vertical axis.
    - Shows the most recent 100 clicks, or at least 10 initially.
    - Graph is reactive and will scale as needed when the app window is resized.
  - Indicators for each vertical bar:
    - Green: Auto-clicked Enable TX.
    - Yellow: CQ pressed (manual or auto).
    - Orange: Band changed as *CQsRemaining* reaches zero.
    - Red: App stopped as *AppTimeRemaining* reaches zero.
    - Grey: Current growing bar showing real-time duration.
- Can be Minimized to reduce clutter

## Support
For support and updates, visit the official FT8Clicker website or contact the support team via email at the github repository
## License
This software is licensed under the MIT License. See the LICENSE file for more information.
## Changelog
### v0.6
- Implemented accurate color-based button state detection using majority color sampling
- Added native Quartz screen capture for macOS to avoid cursor interference
- Added macOS Screen Recording permission checks and guidance
- Enhanced cross-platform compatibility with platform-specific backends
- Improved button learning process with real-time color capture and ON/OFF state detection
- Added multi-monitor support
- Enhanced logging with RGB color names, sampled data, and ON/OFF state changes
- Real-time learned button background updates from pixel color
- Added circular progress indicators for CQ Time, CQs Remaining, and App Time
- Implemented real-time event timeline graph with auto-scaling axes (X: 10-100 bars, Y: 30s+)
- Added runaway detection for short QSOs (<5 seconds)
- CQ counter now decrements on both manual and automatic clicks
- Added cooldown mechanism after Tx Enable clicks
- Implemented delayed hover tooltips (3 seconds) for all buttons and arc indicators
- Band cycling now only occurs through learned bands with appropriate error handling
## Disclaimer
Use this software at your own risk. The developers are not responsible for any damages or issues arising from the use of this application.  
Please ensure compliance with all relevant regulations and guidelines when using automated tools for FT8 communication.

## Technical Specifications
### Frameworks and Libraries
- Built using Python 3.x
- Utilizes PyQt6 for GUI development
- Uses PyAutoGUI for automating mouse clicks and keyboard inputs on Windows and Linux
- Uses Quartz/CoreGraphics for native screen capture and color detection on macOS
- Other dependencies as listed in requirements.txt

### Data Models
- **Learned Buttons**: Stored in settings.json with `pos` and `states` (color-to-state mapping).
- **Click History**: In-memory list of recent click events used for charting.
- **Settings**: JSON-backed preferences (click interval, visible bands, timers, learned buttons).

### Safeguards
- The app includes safeguards to prevent unintended behavior, such as:
  - Error handling for invalid configurations
  - Limits on maximum click intervals to prevent excessive clicking
  - Runaway detection: stops automation after 3 consecutive short QSOs (<5 seconds)
  - Cooldown period after Tx Enable clicks to prevent rapid cycling
  - CQ counter decrementing on manual clicks to maintain accuracy
  - Band cycling only through learned bands, with logging if none available

## Settings and Configuration
- **Click Interval**: Adjustable from 100ms to 3000ms (default: 500ms) for time between automated clicks.
- **Visible Bands**: Checkbox list to show/hide band buttons (default: 40m, 20m, 17m, 15m, 12m, 10m). This affects which band buttons are displayed in the Button List and next band selection during cycling.
- **Timers**:
  - *CQTimeRemaining*: Customizable (default: 90 seconds); resets on auto-Tx Enable.
  - *CQsRemaining*: Customizable (default: 10); triggers band change.
  - *AppTimeRemaining*: Customizable (default: Unlimited); stops app when reached.
- **Unlearn Buttons**: Option to unlearn all or specific learned positions.
- **Additional**: Keyboard shortcuts enabled by default; log export writes to log.txt in the working directory.

## Testing and Validation
### Unit Tests
- Verify timer resets on Tx Enable click.
- Test position learning stores (x, y, color) correctly.
- Validate band cycling logic.

### Integration Tests
- Simulate FT8 software interaction; check auto-clicks and band switches.
- Test multi-monitor setup compatibility.

### User Acceptance Criteria
- As a user, I can learn a button position so that automation works without manual input.
- As a user, the app stops automatically after *AppTimeRemaining* to prevent runaway operation.
- As a user, I can hover over buttons and indicators for 3 seconds to receive contextual help.
- As a user, band cycling only occurs through properly learned bands with clear error messaging.

## Support
For support and updates, visit the official FT8Clicker website or contact the support team via email at the GitHub repository.

## License
This software is licensed under the MIT License. See the LICENSE file for more information.

## Changelog
### v0.6
- Accurate color-based state detection with majority sampling
- macOS Quartz capture with Screen Recording permission guidance
- Real-time button color updates and ON/OFF state logging
- Circular progress arcs for timers and counters
- Auto-scaling real-time graph with color-coded event bars
- Runaway detection and automation safeguards
- Delayed tooltips for enhanced usability
- Learned band cycling with error handling
### v0.5
- Fixed bugs related to click intervals
- Enhanced user interface
### v0.4
- Initial release with basic features

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure to follow the coding standards and include appropriate tests.

## Acknowledgments
- Thanks to the open-source community for their valuable libraries and tools.
- Special thanks to FT8 enthusiasts for their feedback and support during development.

## Disclaimer
Use this software at your own risk. The developers are not responsible for any damages or issues arising from the use of this application.
Please ensure compliance with all relevant regulations and guidelines when using automated tools for FT8 communication.

