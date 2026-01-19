# FT8Clicker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

FT8Clicker is an automation tool designed to simplify FT8 digital mode communication by automating repetitive button clicks in FT8 software like WSJT-X. It intelligently manages transmission enabling, CQ calls, and band changes while incorporating safety features to prevent unsupervised operation.  It is best for responding to a pileup, but may not be optimal for DX hunting, as it doesnt have knowledge on Callsigns decoded.

![FT8Clicker Interface](screenshots/ft8clicker-interface1%20screenshot.png.png)

## Why FT8Clicker?

I created FT8Clicker because I was tired of manually pressing the "Enable Tx" button every minute during FT8 sessions. Traditional FT8 operation requires frequent intervention, but I wanted longer automation intervals for more efficient operation. However, I also wanted the automation to be intelligent and safe—not completely unsupervised. FT8Clicker achieves this by:

- Automatically enabling transmission when needed
- Forcing CQ calls at configurable intervals
- Cycling through bands when a set number of CQs are reached
- Including safeguards like runaway detection and cooldown periods

This is my first coding project in almost 30 years, so feedback and contributions are very welcome!

## Features

- **Automated FT8 Operation**: Intelligently clicks buttons based on learned positions and timers
- **Color-Based State Detection**: Uses pixel color sampling to detect button states accurately
- **Real-Time Visual Feedback**: Circular progress indicators and auto-scaling timeline graph
- **Safe Automation**: Runaway detection, cooldown periods, and configurable limits
- **Cross-Platform**: Works on macOS, Windows, and Linux with native screen capture
- **User-Friendly Interface**: Inspired by Yaesu FTDX Series Radio design
- **Delayed Tooltips**: Contextual help on 3-second hover
- **Comprehensive Logging**: Timestamped events with export capability

## How It Works

FT8Clicker automates the FT8 workflow by:

1. **Learning Button Positions**: You teach the app where buttons are in your FT8 software by clicking "Learn", selecting a button, and pressing 'L' over the target button.

2. **State Detection**: The app continuously monitors button colors to detect active/inactive states using majority color sampling from a 9x9 pixel area.

3. **Intelligent Automation**:
   - Automatically enables transmission when the "Enable Tx" button appears inactive
   - Sends CQ calls after a configurable time interval (default: 200 seconds)
   - Cycles through learned bands after a set number of consecutive CQs (default: 3). This counter tracks consecutive forced CQ calls, i.e., when your FT8 application repeatedly calls a station and the station doesn't reply, so when the CQ time runs out, it will force a CQ. The counter resets when a QSO is established (transmission enabled).
   - Stops automatically after a maximum runtime (default: 60 minutes)

4. **Safety Features**:
   - Runaway detection stops automation after 3 consecutive short QSOs (<5 seconds)
   - Cooldown periods prevent rapid button clicking
   - Only cycles through properly learned bands
   - Manual clicks are tracked and affect counters

5. **Visual Monitoring**: Real-time graph shows click history with color-coded bars, and circular progress arcs display remaining times/counters.

## Installation

### Prerequisites
- Python 3.x
- Compatible FT8 software (WSJT-X recommended)

### Downloads
Pre-built executables are available for download from the [Releases](https://github.com/yourusername/FT8Clicker/releases) page:
- **Windows**: Download `FT8Clicker.exe`
- **macOS**: Download `FT8Clicker.dmg`

### From Source
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### macOS Specific
Enable Screen Recording permission in System Settings → Privacy & Security → Screen Recording for your Python environment.

## Usage

1. **Setup FT8 Software**: Open WSJT-X or compatible FT8 software
2. **Launch FT8Clicker**: Run `python main.py`
3. **Learn Buttons**: Click "Learn", select each button (Enable Tx, CQ, bands), move mouse to FT8 button, press 'L'
4. **Configure Settings**: Adjust timers, visible bands, and intervals as needed
5. **Start Automation**: Click "Start" (turns green) to begin
6. **Monitor**: Watch the progress arcs and graph for real-time feedback
7. **Stop**: Click "Stop" or let it auto-stop after configured time

### Keyboard Shortcuts
- **S**: Start/Stop
- **P**: Pause/Resume

### Troubleshooting
- Ensure FT8 software is running and buttons are visible
- Check screen recording permissions on macOS
- Verify button positions are learned correctly
- In WSJT-X, set TX Watchdog > CQ Time

## Safety Tips

- ensure that you have an auto tuner, so that when the program changes bands, that your antenna is properly tuned.  Or use with only a single band.
- make sure that your power level is set appropriately for FT8 operation on the bands you are using.
- make sure that your computer does not go to sleep while the program is running.
- In order to avoid being flagged as a bot by other hams, please monitor the program while it is running, and make sure to occasionally intervene manually.  The program has been known to malfunciton in certain situations, so please keep an eye on it.
- Since the program takes control of your mouse, please do not use your computer for other tasks while it is running.
- Always comply with your local regulations regarding automated transmissions.

## Requirements

- **Python 3.x**
- **PyQt6** for GUI
- **PyAutoGUI** for cross-platform automation
- **MSS** for screen capture
- **Matplotlib** for graphing
- Compatible FT8 software (WSJT-X, etc.)

See `requirements.txt` for exact versions.

## Contributing

This is my first coding project in nearly 30 years, so I'm eager for feedback and improvements! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Areas for improvement:
- Additional platform support
- More FT8 software compatibility
- Enhanced UI themes
- Better error handling

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is provided "as is", without warranty of any kind. The user assumes all responsibility for its use. The author is not liable for any damages arising from its use.
Please use responsibly and in accordance with amateur radio regulations.

## Support

For issues, questions, or feedback, please open an issue on this GitHub repository.

---

Built with ❤️ by 5N0YEN