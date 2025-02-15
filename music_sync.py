#!/usr/bin/env python3
import rumps
import subprocess
import os
import json
from datetime import datetime

class MusicSyncApp(rumps.App):
    def __init__(self):
        super(MusicSyncApp, self).__init__("🎵")
        
        # Load config
        self.config = self.load_config()
        
        # Menu items
        self.sync_button = rumps.MenuItem("Sync Now")
        self.last_sync = rumps.MenuItem("Last Sync: Never")
        self.settings = rumps.MenuItem("Settings...")
        
        # Add menu items
        self.menu = [
            self.sync_button,
            self.last_sync,
            None,  # Separator
            self.settings
        ]

    @rumps.clicked("Sync Now")
    def sync(self, _):
        try:
            # Start sync
            self.sync_button.title = "Syncing..."
            self.sync_button.set_callback(None)  # Disable during sync
            
            # Run rsync command
            rsync_cmd = [
                "rsync",
                "-av",
                "--delete",
                self.config["source_path"] + "/",
                f"{self.config['server_user']}@{self.config['server_address']}:{self.config['server_path']}"
            ]
            
            result = subprocess.run(rsync_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"rsync failed: {result.stderr}")
            
            # Trigger Plex scan via API
            if self.config.get("plex_token"):
                self.trigger_plex_scan()
            
            # Update last sync time
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.last_sync.title = f"Last Sync: {now}"
            
            # Show success notification
            rumps.notification(
                title="Music Sync Complete",
                subtitle="Library successfully synchronized",
                message=f"Synced at {now}"
            )
            
        except Exception as e:
            rumps.notification(
                title="Music Sync Failed",
                subtitle="Error during synchronization",
                message=str(e)
            )
        
        finally:
            # Re-enable sync button
            self.sync_button.title = "Sync Now"
            self.sync_button.set_callback(self.sync)

    @rumps.clicked("Settings...")
    def settings_dialog(self, _):
        # Note: In a full implementation, this would open a proper settings window
        # For now, we'll just show where to edit the config file
        config_path = os.path.expanduser("~/.music-sync-config.json")
        rumps.notification(
            title="Music Sync Settings",
            subtitle="Edit configuration file:",
            message=config_path
        )

    def load_config(self):
        """Load configuration from JSON file"""
        config_path = os.path.expanduser("~/.music-sync-config.json")
        
        if not os.path.exists(config_path):
            # Create default config
            default_config = {
                "source_path": os.path.expanduser("~/Music"),
                "server_address": "mini.local",
                "server_user": "your_username",
                "server_path": "/volume1/music",
                "plex_token": "",  # Optional: Your Plex token for API access
                "plex_server": "http://mini.local:32400"  # Your Plex server address
            }
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def trigger_plex_scan(self):
        """Trigger a Plex library scan via API"""
        if not self.config.get("plex_token"):
            return
            
        import requests
        
        headers = {
            'X-Plex-Token': self.config['plex_token']
        }
        
        # Get music library section ID
        sections_url = f"{self.config['plex_server']}/library/sections"
        response = requests.get(sections_url, headers=headers)
        response.raise_for_status()
        
        # Find music library section
        for section in response.json()['MediaContainer']['Directory']:
            if section['type'] == 'artist':
                section_id = section['key']
                break
        else:
            raise Exception("No music library found in Plex")
        
        # Trigger scan
        scan_url = f"{self.config['plex_server']}/library/sections/{section_id}/refresh"
        response = requests.get(scan_url, headers=headers)
        response.raise_for_status()

if __name__ == "__main__":
    MusicSyncApp().run()