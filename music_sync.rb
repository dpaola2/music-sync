#!/usr/bin/env ruby

require 'rubygems'
require 'json'
require 'net/http'
require 'uri'
require 'time'
require 'fileutils'

require 'appscript'
include Appscript

class MusicSync
  def initialize
    @config = load_config
    setup_menu_bar
  end

  def run
    # Keep the app running
    loop do
      sleep 1
    end
  end

  private

  def load_config
    config_path = File.expand_path('~/.music-sync-config.json')
    
    unless File.exist?(config_path)
      default_config = {
        'source_path' => File.expand_path('~/Music/Swinsian'),
        'server_address' => 'Daves-Mac-mini.local',
        'server_user' => 'dave',
        'server_path' => '/Volumes/DATA/Music Library',
        'plex_token' => '', # Optional: Your Plex token for API access
        'plex_server' => 'http://Daves-mac-mini.local:32400' # Your Plex server address
      }
      
      File.write(config_path, JSON.pretty_generate(default_config))
      return default_config
    end
    
    JSON.parse(File.read(config_path))
  end

  def setup_menu_bar
    app = app('System Events').processes['SystemUIServer']
    
    # Create menu bar extra
    @menu_bar = app.menu_bars[1].menu_bar_items.end.make(
      :new => :menu_bar_item,
      :with_properties => { :title => '🎵' }
    )
    
    # Create menu
    menu = @menu_bar.menus[1].make(:new => :menu)
    
    # Add menu items
    @sync_item = menu.menu_items.end.make(
      :new => :menu_item,
      :with_properties => { :title => 'Sync Now' }
    )
    
    @last_sync_item = menu.menu_items.end.make(
      :new => :menu_item,
      :with_properties => { :title => 'Last Sync: Never', :enabled => false }
    )
    
    menu.menu_items.end.make(
      :new => :menu_item,
      :with_properties => { :title => '-' } # Separator
    )
    
    @settings_item = menu.menu_items.end.make(
      :new => :menu_item,
      :with_properties => { :title => 'Settings...' }
    )
    
    # Set up click handlers
    @sync_item.clicked.connect { sync_library }
    @settings_item.clicked.connect { show_settings }
  end

  def sync_library
    begin
      @sync_item.title.set('Syncing...')
      @sync_item.enabled.set(false)
      
      # Run rsync
      rsync_cmd = [
        'rsync',
        '-av',
        '--delete',
        "#{@config['source_path']}/",
        "#{@config['server_user']}@#{@config['server_address']}:#{@config['server_path']}"
      ]
      
      result = system(*rsync_cmd)
      raise "rsync failed" unless result
      
      # Trigger Plex scan if configured
      trigger_plex_scan if @config['plex_token'].to_s.length > 0
      
      # Update last sync time
      now = Time.now.strftime('%Y-%m-%d %H:%M')
      @last_sync_item.title.set("Last Sync: #{now}")
      
      # Show notification
      app('System Events').processes['NotificationCenter'].notifications.end.make(
        :new => :notification,
        :with_properties => {
          :title => 'Music Sync Complete',
          :subtitle => 'Library successfully synchronized',
          :message => "Synced at #{now}"
        }
      )
      
    rescue => e
      app('System Events').processes['NotificationCenter'].notifications.end.make(
        :new => :notification,
        :with_properties => {
          :title => 'Music Sync Failed',
          :subtitle => 'Error during synchronization',
          :message => e.message
        }
      )
      
    ensure
      @sync_item.title.set('Sync Now')
      @sync_item.enabled.set(true)
    end
  end

  def trigger_plex_scan
    return unless @config['plex_token']
    
    # Get music library section ID
    uri = URI("#{@config['plex_server']}/library/sections")
    req = Net::HTTP::Get.new(uri)
    req['X-Plex-Token'] = @config['plex_token']
    
    res = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(req)
    end
    
    raise "Failed to get Plex sections" unless res.is_a?(Net::HTTPSuccess)
    
    # Parse JSON response and find music library
    sections = JSON.parse(res.body)
    music_section = sections['MediaContainer']['Directory'].find { |dir| dir['type'] == 'artist' }
    raise "No music library found in Plex" unless music_section
    
    # Trigger scan
    uri = URI("#{@config['plex_server']}/library/sections/#{music_section['key']}/refresh")
    req = Net::HTTP::Get.new(uri)
    req['X-Plex-Token'] = @config['plex_token']
    
    res = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(req)
    end
    
    raise "Failed to trigger Plex scan" unless res.is_a?(Net::HTTPSuccess)
  end

  def show_settings
    config_path = File.expand_path('~/.music-sync-config.json')
    app('System Events').processes['NotificationCenter'].notifications.end.make(
      :new => :notification,
      :with_properties => {
        :title => 'Music Sync Settings',
        :subtitle => 'Edit configuration file:',
        :message => config_path
      }
    )
  end
end

# Start the app
MusicSync.new.run