# Settings Controller 2
import json
import os.path
from PyQt5.QtCore import QByteArray
from krita import *

class SettingsController():
    # Loads and saves settings for the entire plug-in
    def __init__(self):
        self.settings = {} # Settings loaded from .json files
        self.tmp_settings = {} # What's staged to be saved, the WIP settings
        self.key_mapping = {} # Convert keys the widgets use (controller notation) into paths in the JSON uses (model notation)
        self.loaded_key_mappings = False

        self.active_doc = Krita.instance().activeDocument()

        self.kra_unique_key = 'cyanic_sd_settings'
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))
        self.user_settings_file = os.path.join(self.plugin_dir, 'user_settings.json')
        self.default_settings_file = os.path.join(self.plugin_dir, 'default_settings.json')
        try:
            self.load()
        except Exception as e:
            raise Exception('Cyanic SD - Exception with Settings Controller - %s' % e)


    def update_active_doc(self):
        self.active_doc = Krita.instance().activeDocument()

    def merge_dicts(self, original_dict, updated_dict):
        for key in original_dict.keys():
            if key in updated_dict:
                if type(original_dict[key]) == dict:
                    original_dict[key] = self.merge_dicts(original_dict[key], updated_dict[key])
                else:
                    original_dict[key] = updated_dict[key]
        return original_dict

    def load(self):
        # Load default first, then merge in user settings. It's safer for updates that add new settings.
        if os.path.isfile(self.default_settings_file):
            with open(self.default_settings_file, 'r') as f:
                self.tmp_settings = json.load(f)
        else:
            raise Exception('Cyanic SD - No default settings file found in %s' % self.plugin_dir)
        
        self.key_mapping = self.load_settings_map(self.tmp_settings['cyanic_sd_settings_version']) # Shouldn't be None in any version of the plugin distributed with this SettingsController.
        self.loaded_key_mappings = True

        # User settings
        if os.path.isfile(self.user_settings_file):
            user_settings = {}
            with open(self.user_settings_file, 'r') as f:
                user_settings = json.load(f)

            old_version = None
            # Check if user_settings are on the same version as default_settings
            if 'cyanic_sd_settings_version' not in user_settings or user_settings['cyanic_sd_settings_version'] != self.tmp_settings['cyanic_sd_settings_version']:
                old_key_mapping = None
                if 'cyanic_sd_settings_version' not in user_settings:
                    # Going from Alpha (1) to Beta (2). The mapping and versions were added retroactively in Beta
                    old_version = 1
                else:
                    old_version = user_settings['cyanic_sd_settings_version']
                
                old_key_mapping = self.load_settings_map(old_version)
                for key in old_key_mapping.keys():
                    if key in self.key_mapping.keys():
                        # The setting still exists in the new version, so it's OK to port over that setting.
                        self.tmp_settings[key] = self._get(old_key_mapping[key], user_settings)

                # Rename the old settings as a backup.
                backup_file = os.path.join(self.plugin_dir, 'user_settings_backup_%s.json' % old_version)
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(self.user_settings_file, backup_file)
                self.save_user_settings() # Effectively overwrites the user_settings
            else:
                # Proceed to merge the user_settings with the default
                self.tmp_settings = self.merge_dicts(self.tmp_settings, user_settings)

        self.load_kra_settings()

        # Sync settings with the tmp_settings (done last so that self.saveUserSettings() can work as a way to clear bad user_settings)
        self.settings = self.tmp_settings

    def load_settings_map(self, version):
        # Trying a Model-View-Controller system. The mappings allow for the widgets in the plugin to use a common name, and have that data be saved in different places as needs require.
        mapping_file = os.path.join(self.plugin_dir, 'settings_mappings', '%s.json' % version)
        if not os.path.isfile(mapping_file):
            return {}
        
        key_mapping = {}
        with open(mapping_file, 'r') as f:
            key_mapping = json.load(f)
        return key_mapping


    def load_kra_settings(self):
        # Write to tmp_settings, because this will change as the user switches back and forth between documents.
        if self.active_doc is None:
            # Krita can load without an open doc
            return

        data = self.active_doc.annotation(self.kra_unique_key)
        str_settings = bytes(data).decode()
        if len(str_settings) > 0:
            self.tmp_settings['kra_file_overridden_settings'] = json.loads(str_settings) # No need to merge_dicts(), because that would introduce artifacts from other .kra files
        else:
            # Set the default prompts for this file
            prompt_keys = ['prompts_txt_shared', 'prompts_txt_txt2img', 'prompts_txt_img2img', 'prompts_txt_inpaint']
            prompt_negative_keys = ['prompts_txt_shared_negative', 'prompts_txt_txt2img_negative', 'prompts_txt_img2img_negative', 'prompts_txt_inpaint_negative']
            
            mode = self.get('new_doc_prompt_mode')
            if mode == 'last':
                pass # No need to change anything - whatever was in tmp_settings stays 
            elif mode == 'initial':
                # Overwrite the prompts with the initial
                prompt = self.get('prompt_initial')
                prompt_negative = self.get('prompt_negative_initial')

                for key in prompt_keys:
                    self.set(key, [prompt])
                for key in prompt_negative_keys:
                    self.set(key, [prompt_negative])
            else: # elif mode == 'empty':
                for key in prompt_keys:
                    self.set(key, [''])
                for key in prompt_negative_keys:
                    self.set(key, [''])

    def save_user_settings(self):
        # write tmp_settings to user_setting
        try:
            with open(self.user_settings_file, 'w') as f:
                f.write(json.dumps(self.tmp_settings, indent=4))
        except Exception as e:
            raise Exception('Cyanic SD - Error saving user settings: %s' % e)
        
    def save_kra_settings(self):
        # Write tmp_settings to KRA
        # doc.setAnnotation('my_unique_key', 'description', QByteArray('my data'.encode())
        if self.active_doc is None:
            return
        str_settings = json.dumps(self.tmp_settings['kra_file_overridden_settings'])
        self.active_doc.setAnnotation(self.kra_unique_key, 'Cyanic SD plugin settings', QByteArray(str_settings.encode()))

    def clear_file_prompt_history(self):
        # tmp_settings should have the most recent file's history.
        if self.active_doc is None:
            return
        
        history_arrays = [
            'prompts_txt_shared',
            'prompts_txt_shared_negative',
            'prompts_txt_txt2img',
            'prompts_txt_txt2img_negative',
            'prompts_txt_img2img',
            'prompts_txt_img2img_negative',
            'prompts_txt_inpaint',
            'prompts_txt_inpaint_negative',
        ]
        for key in history_arrays:
            self.set(key, [])
            
        self.save_kra_settings()

    def save(self):
        self.settings = self.tmp_settings
        self.save_user_settings()
        self.save_kra_settings()

    # The key system should be slightly abstracted, so that widgets don't need to have a perfect map of the settings files.
    # The exception to this is extensions, which should have all of their internal data self contained

    def _navigate_dict(self, key, my_dict):
        split_key = key.split('.', 1)
        if not split_key[0] in my_dict.keys():
            my_dict[split_key[0]] = {} # This could be used to add a setting that was missing in earlier saves
        return split_key[1], my_dict[split_key[0]]


    def get(self, key, default=None):
        try:
            return self._get(self.key_mapping[key])
        except:
            return default

    def _get(self, key, my_dict=None):
        # Recursive way to iterate through the key
        if my_dict == None:
            my_dict = self.tmp_settings

        if key.count('.') > 0:
            # split_key = key.split('.', 1)
            # return self._get(split_key[1], my_dict[split_key[0]])
            new_key, my_dict = self._navigate_dict(key, my_dict)
            return self._get(new_key, my_dict)
        else:
            return my_dict[key]
            
            
    def set(self, key, value):
        if key in self.key_mapping:
            self._set(self.key_mapping[key], value)
        # Else, trying to set a key that doesn't exist.
        # Some widgets can trigger this behavior on accident due to reuse in new settings, so it's ignored rather than raising an error

    def _set(self, key, value, my_dict=None):
        # Recursive way to iterate through the key and set the value
        if my_dict == None:
            my_dict = self.tmp_settings

        if key.count('.') > 0:
            # split_key = key.split('.', 1)
            # self._set(split_key[1], value, my_dict[split_key[0]])
            new_key, my_dict = self._navigate_dict(key, my_dict)
            return self._set(new_key, value, my_dict)
        else:
            my_dict[key] = value


    def append(self, key, value):
        # Append the value to the list if it's not in the list.
        self._append(self.key_mapping[key], value)

    def _append(self, key, value, my_dict=None):
        if my_dict == None:
            my_dict = self.tmp_settings

        if key.count('.') > 0:
            # split_key = key.split('.', 1)
            # self._append(split_key[1], value, my_dict[split_key[0]])
            new_key, my_dict = self._navigate_dict(key, my_dict)
            self._append(new_key, value, my_dict)
        else:
            # self.settings[key] = [*self.settings[key], value] # Not sure why I did it this way in the last version, but it worked.
            my_dict[key] = [*my_dict[key], value]


    def remove(self, key, value):
        # Remove the value from a list if it's in the list
        self._remove(self.key_mapping[key], value)

    def _remove(self, key, value, my_dict=None):
        if my_dict == None:
            my_dict = self.tmp_settings
        
        if key.count('.') > 0:
            # split_key = key.split('.', 1)
            # self._remove(split_key[1], value, my_dict[split_key[0]])
            new_key, my_dict = self._navigate_dict(key, my_dict)
            self._remove(new_key, value, my_dict)
        else:
            index = my_dict[key].index(value)
            if index > -1:
                my_dict[key].pop(index)


    def toggle(self, key, value=None):
        # Can toggle booleans, or toggle an value being in or out of a list.
        self._toggle(self.key_mapping[key], value)

    def _toggle(self, key, value=None, my_dict=None):
        if my_dict == None:
            my_dict = self.tmp_settings
        
        if key.count('.') > 0:
            # split_key = key.split('.', 1)
            # self._toggle(split_key[1], value, my_dict[split_key[0]])
            new_key, my_dict = self._navigate_dict(key, my_dict)
            self._remove(new_key, value, my_dict)
        else:
            if type(my_dict[key]) is bool:
                my_dict[key] = not my_dict[key]

            elif type(my_dict[key]) is list:
                if value in my_dict[key]:
                    self._remove(key, value, my_dict)
                else:
                    self._append(key, value, my_dict)


    def has_key(self, key):
        return self._has_key(self.key_mapping[key])

    def _has_key(self, key, my_dict=None):
        if my_dict == None:
            my_dict = self.tmp_settings
        
        if key.count('.') > 0:
            new_key, my_dict = self._navigate_dict(key, my_dict)
            return self._has_key(new_key, my_dict)
        else:
            return key in my_dict.keys()