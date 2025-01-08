# Settings Controller 2
import json
import os.path
from PyQt5.QtCore import QByteArray
from krita import *
import datetime

# Loads and saves settings for the entire plug-in
class SettingsController():
    
    SD_MODEL_VERSIONS = [
        'All', # Not official, just allow all options. "All" should always be first.
        'SD1',
        'SD2',
        'SD3', 
        'SDXL',
        'Flux', # Supported by Forge
        'Unknown', # "Unknown" should always be last
    ]
    def __init__(self):
        self.settings = {} # Settings loaded from .json file and .kra file (gets updated on .save() and .load())
        self.tmp_settings = {} # What's staged to be saved, the WIP settings
        self.key_mapping = {} # Convert keys the widgets use (controller notation) into paths in the JSON uses (model notation)
        self.loaded_key_mappings = False
        self.api_host = '' # Used for saving lora/hypernetwork settings

        self.active_doc = Krita.instance().activeDocument()

        self.kra_unique_key = 'cyanic_sd_settings'
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))
        self.user_settings_file = os.path.join(self.plugin_dir, 'user_settings.json')
        self.default_settings_file = os.path.join(self.plugin_dir, 'default_settings.json')
        self.icon_dir = os.path.join(self.plugin_dir, 'icons')
        self.extra_networks_dir = os.path.join(self.plugin_dir, 'extra_networks')
        self.extra_networks_settings_file = os.path.join(self.extra_networks_dir, 'extra_networks.json')
        self.extra_networks_thumbnail_dir = os.path.join(self.extra_networks_dir, 'thumbnails')
        self.unknown_thumbnail = None
        self.default_extra_network_data = {
            'description': '',
            'sd version': SettingsController.SD_MODEL_VERSIONS[-1], # 'Unknown' should always be the last value
            'activation text': '',
            'negative text': '',
            'preferred weight': 0, # A1111 default is 0, which gets translated to a weight of 1.0
            'notes': '',
        }
        try:
            self.load()
        except Exception as e:
            raise Exception('Cyanic SD - Exception with Settings Controller - %s' % e)

    def update_api_host(self, new_host=''):
        self.api_host = new_host

    def update_active_doc(self):
        self.active_doc = Krita.instance().activeDocument()

    def set_active_doc(self, doc):
        # Sometimes "active" isn't what Krita thinks, it's the last document used (for saving)
        self.active_doc = doc

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
                self.save_user_settings() # Effectively overwrites the outdated user_settings with up-to-date version
            else:
                # Proceed to merge the user_settings with the default
                self.tmp_settings = self.merge_dicts(self.tmp_settings, user_settings)

        self.load_kra_settings()
        # Sync settings with the tmp_settings (done last so that self.save_user_settings() can work as a way to clear bad user_settings)
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
            str_data = json.dumps(self.tmp_settings, indent=4)
            if "&txt2img" in str_data:
                raise Exception('Cyanic SD - Corrupted user_settings: %s' % self.tmp_settings['common']['prompting']['include_sharing'])
            with open(self.user_settings_file, 'w') as f:
                f.write(str_data)
        except Exception as e:
            raise Exception('Cyanic SD - Error saving user settings: %s' % e)
        
    def save_kra_settings(self):
        # Write tmp_settings to KRA
        # doc.setAnnotation('my_unique_key', 'description', QByteArray('my data'.encode())
        if self.active_doc is None:
            return
        str_settings = json.dumps(self.tmp_settings['kra_file_overridden_settings'])
        self.active_doc.setAnnotation(self.kra_unique_key, 'Cyanic SD plugin settings', QByteArray(str_settings.encode()))

    def revert_settings(self):
        # Revert settings to whatever was used on the last save/load.
        self.tmp_settings = self.settings

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
        

    # Extra Network saved settings and thumbnail caching
    # Extra Networks have APIs that differ between A1111, Forge, SD.Next, etc, so handling this locally is the best option.

    def load_local_server_extra_network_settings(self, dirs):
        # Dirs should be obtained from the lora or hypernetwork API endpoint's "path", without the filenames
        if type(dirs) == str:
            dirs = [dirs]
        
        # Filter to only existing paths
        dirs = list(filter(lambda dir: os.path.exists(dir), dirs))
        if len(dirs) == 0:
            return
        
        # If they're files, get their parent dir instead
        folder_dirs = []
        for dir in dirs:
            if os.path.isdir(dir):
                folder_dirs.append(dir)
            else:
                folder_dirs.append(os.path.split(dir)[0])
        dirs = folder_dirs
        
        existing_settings = {'lora':{}, 'hypernetwork': {}}
        for dir in dirs:
            # Note: lycoris is counted under the lora network_type in the API
            network_type = self._folder_to_network_type(os.path.split(dir)[1])
            saved_settings = self._read_settings_from_server_folder(dir)
            existing_settings[network_type].update(saved_settings)

        self.save_extra_network_settings(existing_settings)


    def _folder_to_network_type(self, folder_name):
        # Not including a separate lycoris network type, because A1111 APIs treats them as part of lora
        if 'hypernetwork' in folder_name:
            return 'hypernetwork' # get rid of pluralizations
        else:
           return 'lora'


    def _read_settings_from_server_folder(self, folder):
        # Search this folder for any .json files
        settings = {}
        server_data_files = [x for x in os.listdir(folder) if 'json' in os.path.splitext(x)[1].lower()]
        for server_file in server_data_files:
            with open(os.path.join(folder, server_file), 'r') as file:
                data = json.load(file)
                network_name = os.path.splitext(server_file)[0].lower()
                settings[network_name] = data
        return settings


    def _thumbnail_file_path(self, network_type:str, network_name:str):
        return os.path.join(self.extra_networks_thumbnail_dir, network_type.lower(), '%s.png' % network_name.lower())


    def cache_thumbnail(self, network_type:str, network_name:str, thumbnail):
        # Writes the thumbnail data recieved from the API to the local file system
        try:
            save_target = self._thumbnail_file_path(network_type, network_name)
            os.makedirs(os.path.split(save_target)[0], exist_ok=True) # Create the folder if it doesn't already exist
            with open(save_target, 'wb') as file:
                file.write(thumbnail)
        except:
            pass

    def get_cached_thumbnail(self, network_type:str, network_name:str):
        # Returns the thumbnail from the local file system
        try:
            target_file = self._thumbnail_file_path(network_type, network_name)
            if os.path.exists(target_file):
                data = None
                with open(target_file, 'rb') as file:
                    data = file.read()
                return data
            return None
        except:
            return None
    
    def get_unknown_thumbnail(self):
        if self.unknown_thumbnail is None:
            with open(os.path.join(self.icon_dir, 'unknown_network.png'), 'rb') as file:
                self.unknown_thumbnail = file.read()
        return self.unknown_thumbnail

    def get_extra_network_settings(self):
        # From the Krita settings
        existing_settings = {'lora':{}, 'hypernetwork': {}}
        if os.path.exists(self.extra_networks_settings_file):
            with open(self.extra_networks_settings_file, 'r') as file:
                existing_settings = json.load(file)
        return existing_settings

    def write_network_to_network_settings(self, extra_network_settings, network_type, network_name, setting_values, as_override=False):
        # DOES NOT SAVE! Only used to build the bigger list of networks
        # setting_values = default_extra_network_data format, can be missing fields if as_override
        manditory_keys = ['lora', 'hypernetwork']
        for key in manditory_keys:
            if key not in extra_network_settings:
                extra_network_settings[key] = {}
        
        if not network_name in extra_network_settings[network_type]:
            extra_network_settings[network_type][network_name] = {'kra_override': {}}
        
        # if network_type == 'hypernetwork':
        #     raise Exception(extra_network_settings)
        if as_override:
            # Overrides can be missing default values. Missing values will use the settings from the server
            setting_values['kra_last_modified'] = '%s' % datetime.datetime.now()
            extra_network_settings[network_type][network_name]['kra_override'] = setting_values
        else:
            # Server settings must have all of the default values
            
            # data = self.default_extra_network_data # This was causing every lora/hypernetwork to have the exact same values
            data = {}
            for key in self.default_extra_network_data.keys():
                data[key] = self.default_extra_network_data[key]

            for key in setting_values.keys():
                data[key] = setting_values[key] # Allows for updates if the setting_values has more keys than default

            # Write date that it was updated
            data['kra_last_modified'] = '%s' % datetime.datetime.now()
            extra_network_settings[network_type][network_name][self.api_host] = data
            
        return extra_network_settings
    

    def save_extra_network_settings(self, extra_network_settings):
        # {
        #   lora: {
        #       lora_name: {
        #           kra_overrides: {},           
        #           server_address: self.default_extra_network_data
        #       }
        #   },
        #   hypernetwork: {
        #       hypernetwork_name: {
        #           kra_overrides: {},
        #           server_address: self.default_extra_network_data
        #       }
        #   }
        # }
        manditory_keys = ['lora', 'hypernetwork']
        for key in manditory_keys:
            if key not in extra_network_settings:
                extra_network_settings[key] = {}

        dump = json.dumps(extra_network_settings, indent=4)
        os.makedirs(self.extra_networks_dir, exist_ok=True) # Create the folder if it doesn't already exist
        with open(self.extra_networks_settings_file, 'w') as file:
            file.write(dump)
            file.close()
        # raise Exception('Finished writing: %s' % self.extra_networks_settings_file) 

    def delete_extra_network_data(self):
        # Just write an empty array to it
        default_settings = {'lora':{}, 'hypernetwork': {}}
        self.save_extra_network_settings(default_settings)

    def delete_thumbnails(self):
        for folder in os.listdir(self.extra_networks_thumbnail_dir):
            folder_path = os.path.join(self.extra_networks_thumbnail_dir, folder)
            for file in os.listdir(folder_path):
                os.remove(os.path.join(folder_path, file))

    def set_extra_network_data_from_dict(self, network_type:str, network_name:str, data):
        # See default_extra_network_data for example of data format
        save_data = self.default_extra_network_data

        # Make sure the new data has the minimum number of fields
        for key in save_data.keys():
            if key in data.keys():
                save_data[key] = data[key]

        existing_settings = self.get_extra_network_settings()
        if network_type.lower() not in existing_settings.keys():
            existing_settings[network_type.lower()] = {}
        
        if network_name.lower() in existing_settings[network_type.lower()].keys():
            # Need to update the existing data with the new data
            existing_settings[network_type.lower()][network_name.lower()].update(save_data)
        else:
            existing_settings[network_type.lower()][network_name.lower()] = save_data

        self.save_extra_network_settings(existing_settings)


    def get_extra_network_data(self, network_type:str, network_name:str):
        # Return one specific instance 
        existing_settings = self.get_extra_network_settings()
        if network_type.lower() not in existing_settings.keys() or network_name not in existing_settings[network_type.lower()].keys():
            # No data, use the defaults
            empty = {
                'kra_override': {},
                self.api_host: {}
            }
            for key in self.default_extra_network_data:
                empty[self.api_host][key] = self.default_extra_network_data[key]
            return empty
        
        
        found_data = existing_settings[network_type.lower()][network_name]
        # Make sure the found data has all the keys the default does, to preserve consistency
        # This may seem like overkill, but it will make sure older save files work with newer plugin versions
        returned_data = {}
        for host_name in found_data.keys():
            if host_name == 'kra_override':
                # Don't need to check it for completeness, it's likely to be missing fields
                returned_data[host_name] = found_data['kra_override']
                continue 
            else:
                returned_data[host_name] = {}
                for key in self.default_extra_network_data:
                    if key in found_data[host_name].keys():
                        returned_data[host_name][key] = found_data[host_name][key]
                    else:
                        returned_data[host_name][key] = self.default_extra_network_data[key]

        return returned_data

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