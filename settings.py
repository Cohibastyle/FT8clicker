import json
import os

class Settings:
    def __init__(self):
        self.config_file = 'config.json'
        self.defaults = {
            'click_interval': 500,  # ms
            'visible_bands': ['40m', '20m', '17m', '15m', '12m', '10m'],
            'cq_time_remaining': 90,
            'cqs_remaining': 10,
            'app_time_remaining': 0,  # 0 for unlimited
            'keyboard_shortcuts': True,
            'log_export_path': '~/Desktop',
            'auto_learn': False,
            'learned_buttons': {}
        }
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = self.defaults.copy()
            self.save()

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()