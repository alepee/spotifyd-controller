#!/usr/bin/env python3
__all__ = (
    'Player',
    'PLAYER',
)
from gi import require_version
require_version('Playerctl', '2.0')
from gi.repository import Playerctl, GLib


manager = Playerctl.PlayerManager()
print(dir(Playerctl.Player))

class Player:
    def __init__(self, player_name):
        self.player = Playerctl.Player.new_from_name(player_name)
        manager.manage_player(self.player)

    def play(self):
        self.player.play()
        
    def pause(self):
        self.player.pause()
        
    def play_pause(self):
        self.player.play_pause()
        
    def stop(self):
        self.player.stop()

    def next(self):
        self.player.next()

    def previous(self):
        self.player.previous()

    def get_artist(self):
        return self.player.get_artist()
        
    def open(self, uri):
        self.player.open(uri)

for player_name in manager.props.player_names:
    if player_name.name == 'spotifyd': PLAYER = Player(player_name)

PLAYER.open('spotify:playlist:37i9dQZF1EQqedj0y9Uwvu')

main = GLib.MainLoop()
main.run()
