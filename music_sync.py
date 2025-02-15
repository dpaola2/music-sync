#!/usr/bin/env python3

import rumps
import subprocess
import os
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.expanduser('~/.music-sync/debug.log'),
    filemode='w'  # Clear log file each time
)

class MusicSyncApp(rumps.App):
    def __init__(self):
        super(MusicSyncApp, self).__init__(
            "🎵",
            title="🎵",
            quit_button=None,  # Hide the quit button since we'll add our own
            icon=None  # Don't use an icon to prevent dock icon
        )
        rumps.debug_mode(False) 
        logging.debug("App initialized")
        
        # Load config
        self.config = self.load_config()
        logging.debug(f"Loaded config: {self.config}")
        
        # Menu items
        self.sync_button = rumps.MenuItem("Sync Now", callback=self.sync)
        self.last_sync = rumps.MenuItem("Last Sync: Never", callback=None)
        self.settings = rumps.MenuItem("Settings...", callback=self.settings_dialog)
        
        # Add menu items
        self.menu = [
            self.sync_button,
            self.last_sync,
            None,  # Separator
            self.settings
        ]

    def load_config(self):
        """Load configuration from JSON file"""
        config_path = os.path.expanduser("~/.music-sync/config.json")
        
        if not os.path.exists(config_path):
            # Create default config
            default_config = {
                "source_path": os.path.expanduser("~/Music/Swinsian"),
                "server_address": "Daves-Mac-mini.local",
                "server_user": os.getenv("USER"),
                "server_path": "/Volumes/DATA/music-library",
                "plex_token": "",
                "plex_server": "http://Daves-Mac-mini.local:32400"
            }
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
        
        with open(config_path, 'r') as f:
            return json.load(f)

    @rumps.clicked("Sync Now")
    def sync(self, _):
        """Handle sync button click"""
        try:
            logging.debug("Starting sync")
            
            # Disable sync button and update text
            self.sync_button.title = "Syncing..."
            self.sync_button.set_callback(None)
            
            # Build rsync command
            rsync_cmd = [
                "rsync",
                "-avvvP",  # Triple v for maximum verbosity, P for progress
                "--stats",  # Show file transfer stats
                "--human-readable",  # Show sizes in human-readable format
                "--itemize-changes",  # Show detailed information about each change
                "--delete",
                "--progress",
                f"{self.config['source_path']}/",
                f"{self.config['server_user']}@{self.config['server_address']}:{self.config['server_path']}"
            ]
            
            logging.debug(f"Running rsync command: {' '.join(rsync_cmd)}")
            
            # Run rsync
            process = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'  # Replace invalid characters instead of failing
            )
            
            logging.debug("rsync process completed with return code: %d", process.returncode)
            if process.stdout:
                logging.debug("rsync stdout:\n%s", process.stdout)
            if process.stderr:
                logging.debug("rsync stderr:\n%s", process.stderr)
            
            if process.returncode != 0:
                raise Exception(f"rsync failed with code {process.returncode}")
            
            # Update last sync time
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.last_sync.title = f"Last Sync: {now}"
            
            rumps.notification(
                title="Music Sync Complete",
                subtitle="Library successfully synchronized",
                message=f"Synced at {now}"
            )
            
            logging.debug("Sync completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Sync failed: {error_msg}")
            rumps.notification(
                title="Music Sync Failed",
                subtitle="Error during synchronization",
                message=error_msg
            )
        
        finally:
            # Re-enable sync button
            self.sync_button.title = "Sync Now"
            self.sync_button.set_callback(self.sync)

    @rumps.clicked("Settings...")
    def settings_dialog(self, _):
        """Open settings dialog"""
        config_path = os.path.expanduser("~/.music-sync/config.json")
        os.system(f"open {config_path}")

if __name__ == "__main__":
    try:
        app = MusicSyncApp()
        logging.debug("Starting app.run()")
        app.run()
    except Exception as e:
        logging.exception("Error running app:")