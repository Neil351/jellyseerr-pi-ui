# Launch Scripts

This directory contains scripts for launching the Jellyseerr Pi UI in different modes.

## Scripts

### `emulationstation-launch.sh`
**Use this for EmulationStation integration**

Launches the app from EmulationStation by:
1. Killing EmulationStation to free the framebuffer
2. Running Jellyseerr UI in fullscreen mode
3. Restarting EmulationStation when you exit the app

**To add to EmulationStation:**
```bash
# Make executable
chmod +x ~/jellyseerr-ui/scripts/emulationstation-launch.sh

# Add to your EmulationStation systems config
# Edit: ~/.emulationstation/es_systems.cfg
# Add a new system entry pointing to this script
```

**Example EmulationStation entry:**
```xml
<system>
  <name>jellyseerr</name>
  <fullname>Jellyseerr</fullname>
  <path>~/jellyseerr-ui/scripts</path>
  <extension>.sh</extension>
  <command>%ROM%</command>
  <platform>pc</platform>
  <theme>custom</theme>
</system>
```

### `run.sh`
**Direct launch from console (F4 from EmulationStation)**

Use when you've already exited EmulationStation and want to run the app:
```bash
cd ~/jellyseerr-ui
./scripts/run.sh
```

Runs in fullscreen framebuffer mode with mouse disabled.

### `test.sh`
**Testing mode for SSH or desktop**

Use for testing over SSH (requires X11 forwarding) or on desktop Linux:
```bash
cd ~/jellyseerr-ui
./scripts/test.sh
```

Runs in windowed mode without framebuffer requirements.

## Quick Start

**First time setup:**
```bash
cd ~/jellyseerr-ui

# Make all scripts executable
chmod +x scripts/*.sh

# Test that it works (exit EmulationStation first with F4)
./scripts/run.sh
```

**From EmulationStation:**
1. Set up the launcher: `chmod +x scripts/emulationstation-launch.sh`
2. Configure EmulationStation to launch it (see example above)
3. Select Jellyseerr from EmulationStation menu
4. Use controller to navigate and request media
5. Press START button to exit and return to EmulationStation
