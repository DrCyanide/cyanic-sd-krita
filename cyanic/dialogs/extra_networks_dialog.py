from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import re
import os
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from . import ExtraNetworksManageDialog, ExtraNetworksEditDialog
from krita import Krita


class ExtraNetworksDialog(QDialog):
    MAX_HEIGHT = 150
    MAX_WIDTH = 150
    # MAX_HEIGHT = 100
    # MAX_WIDTH = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None, prompt_txt='', negative_txt=''):
        super().__init__()
        self.setWindowTitle('Extra Networks')
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close
        self.prompt_txt = prompt_txt
        self.negative_txt = negative_txt
        self.is_shown = False

        self.label_key = 'name' # 'alias' isn't part of hypernetwork
        self.show_icons = False

        self.unknown_thumbnails = {'lora': {}, 'hypernetwork': {}, 'embedding': {}}  # Used to 'cache' which thumbnails don't exist on server

        self.model_filter = 'all'
        self.search_text = ''

        self.loras = []
        self.hypernetworks = []
        self.embeddings = {'loaded':[], 'skipped': []}
        self.tabs = QTabWidget()
        self.lora_list = QListWidget()
        self.hypernetwork_list = QListWidget()
        self.embedding_list = QListWidget()
        self.extra_network_settings = {'lora':{}, 'hypernetwork': {}}

        self.list_width = int(ExtraNetworksDialog.MAX_WIDTH * 4.5)
        self.list_height = int(ExtraNetworksDialog.MAX_WIDTH * 2.5)

        # self.importer_tab = QWidget()
        self.setLayout(QVBoxLayout())
        self.reload_button = QPushButton('Refresh')
        self.load_settings()
        self.init_ui()

    def open_menu(self, position, network_list:QListWidget):
        menu = QMenu()
        index = network_list.indexAt(position)
        item = network_list.itemFromIndex(index)

        if item is None:
            # The user didn't click on an item
            return
        
        network_name = item.text()
        network_type = ''
        if self.tabs.currentWidget() == self.lora_list:
            network_type = 'lora'
        elif self.tabs.currentWidget() == self.hypernetwork_list:
            network_type = 'hypernetwork'
        else:
            # Not a valid network type?
            network_type = ''

        text = 'Customize' # Don't use menu.addAction('Customize'). For some reason it makes the menu stay open after you click Customize
        customizeAction = menu.addAction(text)
        customizeAction.triggered.connect(lambda x: self.open_customizer(network_type, network_name))
        menu.exec_(network_list.mapToGlobal(position)) # This .exec_ call puts the right click menu on the item being clicked
    
    def open_customizer(self, network_type, network_name):
            # Open customize options for this item
            self.customizer = ExtraNetworksEditDialog(self.settings_controller, self.api, network_type, network_name, show_thumbnail=self.show_icons)
            self.customizer.show()
            

    def init_ui(self):
        self.warning = QWidget()
        self.warning.setLayout(QHBoxLayout())
        self.warning.layout().setContentsMargins(0,0,0,0)

        warning_text = QLabel("Can't grab model settings from remote SD Backends, only thumbnails.\nPlease open Krita on computer running SD, then use the Manage button to export/import settings.")
        self.warning.layout().addWidget(warning_text)

        self.layout().addWidget(self.warning)

        header = QWidget()
        header.setLayout(QHBoxLayout())
        header.layout().setContentsMargins(0,0,0,0)

        # Show Thumbnails
        self.toggle_images_checkbox = QCheckBox('Thumbnails')
        self.toggle_images_checkbox.setToolTip('Show or Hide thumbnails')
        self.toggle_images_checkbox.setChecked(self.show_icons)
        self.toggle_images_checkbox.toggled.connect(lambda: self.update_show_icons())
        header.layout().addWidget(self.toggle_images_checkbox)

        # Reload from server
        self.reload_button = QPushButton('Refresh')
        self.reload_button.setIcon(Krita.instance().icon('view-refresh'))
        self.setToolTip('Refresh the lora/hypernetwork custom data from server, skips thumbnails')
        self.reload_button.clicked.connect(lambda: self.load_extra_networks(skip_cached=False))
        header.layout().addWidget(self.reload_button)

        # Model Filter
        self.model_filter_box = QComboBox()
        self.model_filter_box.wheelEvent = lambda event : None
        self.model_filter_box.setToolTip('SD Model version')
        self.model_filter_box.addItems(SettingsController.SD_MODEL_VERSIONS)
        self.model_filter_box.setCurrentIndex(0)
        self.model_filter_box.currentIndexChanged.connect(lambda: self.update_filtered_models())
        header.layout().addWidget(self.model_filter_box)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Search')
        self.search_bar.textChanged.connect(lambda: self.update_search_text())
        header.layout().addWidget(self.search_bar)

        # Manage
        self.customizer = None # Done for closing children purposes
        self.manage_dialog = ExtraNetworksManageDialog(self.settings_controller, self.api, self.manage_extra_networks_dialog_closed)
        self.manage_button = QPushButton('Manage')
        self.manage_button.setIcon(Krita.instance().icon('properties'))
        self.manage_button.setToolTip('Import/Export extra network settings')
        self.manage_button.clicked.connect(lambda: self.open_manage_extra_networks_dialog())
        header.layout().addWidget(self.manage_button)

        self.layout().addWidget(header)

        icon_size = QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT)

        self.layout().addWidget(self.tabs)
        # Tabs for Lora (and LyCORIS), Hypernetwork, Textual Inversion
        self.lora_list = QListWidget()
        self.lora_list.setMinimumWidth(self.list_width) # Sets width of the overall popup dialog.
        self.lora_list.setMinimumHeight(self.list_height) # Sets height of the overall popup dialog.
        self.lora_list.setFlow(QListView.Flow.LeftToRight)
        # self.lora_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lora_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lora_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lora_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.lora_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lora_list.setViewMode(QListWidget.IconMode)
        self.lora_list.setIconSize(icon_size) # Adjusts the height/width of preview icons, but hid the label for the items
        # Add right-click menu
        self.lora_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lora_list.customContextMenuRequested.connect(lambda position: self.open_menu(position, self.lora_list))
        self.tabs.addTab(self.lora_list, 'Loras')

        # Hypernetworks
        self.hypernetwork_list = QListWidget()
        self.hypernetwork_list.setFlow(QListView.Flow.LeftToRight)
        self.hypernetwork_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.hypernetwork_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.hypernetwork_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.hypernetwork_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hypernetwork_list.setViewMode(QListWidget.IconMode)
        self.hypernetwork_list.setIconSize(icon_size)
        # Add right-click menu
        self.lora_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lora_list.customContextMenuRequested.connect(lambda position: self.open_menu(position, self.hypernetwork_list))
        self.tabs.addTab(self.hypernetwork_list, 'Hypernetworks')

        # Embeddings
        self.embedding_list = QListWidget()
        self.embedding_list.setFlow(QListView.Flow.LeftToRight)
        self.embedding_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.embedding_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.embedding_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.embedding_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.embedding_list.setViewMode(QListWidget.IconMode)
        self.embedding_list.setIconSize(icon_size)
        self.tabs.addTab(self.embedding_list, 'Embeddings')
        
        self.layout().addWidget(self.tabs)

        footer = QWidget()
        footer.setLayout(QHBoxLayout())
        footer.layout().setContentsMargins(0,0,0,0)

        write_button = QPushButton('Update prompt')
        write_button.clicked.connect(lambda: self.write_changes_and_close())
        footer.layout().addWidget(write_button)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(lambda: self.close())
        footer.layout().addWidget(cancel_button)

        self.layout().addWidget(footer)
        self.set_widget_values()


    def open_manage_extra_networks_dialog(self):
        self.manage_dialog.show()

    def manage_extra_networks_dialog_closed(self):
        # Only called if there's an update.
        self.set_widget_values()

    def update_filtered_models(self):
        self.model_filter = self.model_filter_box.currentText().lower()
        self.set_widget_values()

    def update_search_text(self):
        self.search_text = self.search_bar.text().strip().lower()
        self.set_widget_values()

    def get_thumbnail(self, network_type, network_name):
        if not self.is_shown:
            return None

        cached_thumbnail = self.settings_controller.get_cached_thumbnail(network_type, network_name)
        if cached_thumbnail is not None:
            return cached_thumbnail
        
        if network_name in self.unknown_thumbnails[network_type] and self.unknown_thumbnails[network_type][network_name]:
            # Already checked this, it doesn't exist on server
            return None
        
        # Get thumbnail from server
        path = ''
        if network_type == 'embedding':
            # Embeddings is split into loaded and skipped, and needs to be handled differently
            matching_loaded_embeddings = list(filter(lambda embedding: embedding['name'] == network_name, self.embeddings['loaded']))
            matching_skipped_embeddings = list(filter(lambda embedding: embedding['name'] == network_name, self.embeddings['skipped']))

            if len(matching_loaded_embeddings) > 0:
                path = matching_loaded_embeddings[0]['path']
            elif len(matching_skipped_embeddings) > 0:
                path = matching_skipped_embeddings[0]['path']
            
        else:
            network_source = None
            if network_type == 'lora':
                network_source = self.loras
            if network_type == 'hypernetwork':
                network_source = self.hypernetworks
            path = list(filter(lambda network: network['name'] == network_name, network_source))[0]['path']
        raw_img = self.api.get_thumbnail(path)
        # Save thumbnail to cache
        if raw_img is not None:
            self.settings_controller.cache_thumbnail(network_type, network_name, raw_img)
        else:
            self.unknown_thumbnails[network_type][network_name] = True
        return raw_img
        
    
    def update_prompt_txt(self, prompt_txt='', negative_txt=''):
        self.prompt_txt = prompt_txt
        self.negative_txt = negative_txt

    def update_show_icons(self):
        self.show_icons = self.toggle_images_checkbox.isChecked()
        self.settings_controller.set('show_extra_network_thumbnails', self.show_icons)
        # self.settings_controller.save() # This setting should be applied to future opens
        self.set_widget_values()

    def raw_img_to_qicon(self, raw_img):
        ba = QByteArray(raw_img)
        qimage = QImage()
        qimage.loadFromData(ba)
        icon = QIcon(QPixmap.fromImage(qimage))
        return icon

    def map_embeddings(self, raw_embeddings):
        # Try to make embeddings return similar to the other network types
        # Need to guess the path based on other methods
        # {
        #   'loaded': [
        #       {'name': 'myEmbedding', 'alias': 'myEmbedding', 'path': 'guess/at/thumbnail.preview.png'}
        #   ],
        #   'skipped': [
        #       {'name': 'myEmbedding2', 'alias': 'myEmbedding2', 'path': 'guess/at/thumbnail.preview.png'}
        #   ],
        # }
        new_embeddings = {'loaded':[], 'skipped': []}

        if raw_embeddings is None:
            # server isn't started, or has no embeddings
            return new_embeddings

        if len(raw_embeddings.keys()) == 0:
            # The server doesn't have (or can't return) a list of embeddings
            # https://github.com/lllyasviel/stable-diffusion-webui-forge/issues/1600
            return new_embeddings

        # TODO: Try to find the directory in the Settings, like a sane person!
        embeddings_dir = ''
        if len(self.loras) > 0:
            lora_path = os.path.split(self.loras[0]['path'])[0] # Root dir for loras
            models_root = os.path.split(lora_path)[0] # Root dir for models
            common_root = os.path.split(models_root)[0] # same directory as web-ui.bat
            embeddings_dir = os.path.join(common_root, 'embeddings') # This is where it is on my local system anyway

        for embedding_status in ['loaded', 'skipped']:
            for embedding_name in raw_embeddings[embedding_status].keys():
                path = os.path.join(embeddings_dir, '%s.preview.png' % embedding_name)
                # raise Exception('Path: %s' % path)
                data = {
                    'name': embedding_name,
                    'alias': embedding_name,
                    'path': path,
                }
                new_embeddings[embedding_status].append(data)
        return new_embeddings

    def load_settings(self):
        self.show_icons = self.settings_controller.get('show_extra_network_thumbnails', False) # Default to False for faster loading times
        self.load_extra_networks()

    def load_extra_networks(self, skip_cached=True):
        self.reload_button.setDisabled(True)
        # Pull extra network settings
        self.extra_network_settings = self.settings_controller.get_extra_network_settings()
        # Check if the settings are missing any network that the server has
        if not self.api.connected or not self.is_shown:
            self.reload_button.setDisabled(False)
            return
        self.settings_controller.update_api_host(self.api.host) # Set the correct server address to save these settings with.

        lora_names = self.api.get_lora_names()
        hypernetwork_names = self.api.get_hypernetwork_names()
        for lora_name in lora_names:
            if lora_name not in self.extra_network_settings['lora'].keys() or (not skip_cached):
                # Pull that lora info from the server
                lora_data = self.api.get_server_extra_network_config(network_type='lora', network_name=lora_name)
                self.extra_network_settings = self.settings_controller.write_network_to_network_settings(self.extra_network_settings, network_type='lora', network_name=lora_name, setting_values=lora_data)

        self.settings_controller.save_extra_network_settings(self.extra_network_settings)

        for hn_name in hypernetwork_names:
            if hn_name not in self.extra_network_settings['hypernetwork'].keys() or (not skip_cached):
                # Pull that lora info from the server
                hn_data = self.api.get_server_extra_network_config(network_type='hypernetwork', network_name=hn_name)
                self.extra_network_settings = self.settings_controller.write_network_to_network_settings(self.extra_network_settings, network_type='hypernetwork', network_name=hn_name, setting_values=hn_data)

        self.settings_controller.save_extra_network_settings(self.extra_network_settings)
        self.reload_button.setDisabled(False)

    def set_widget_values(self):
        self.lora_list.clear()
        self.hypernetwork_list.clear()
        self.embedding_list.clear()

        visible_loras = self.loras
        visible_hypernetworks = self.hypernetworks
        visible_embeddings = self.embeddings

        # Filter by search
        if len(self.search_text) > 0:
            # TODO: Offer option to search by notes and description
            visible_loras = list(filter(lambda lora: self.search_text in lora['name'].lower() or self.search_text in lora['alias'].lower(), visible_loras))

            visible_hypernetworks = list(filter(lambda hypernetwork: self.search_text in hypernetwork['name'].lower(), visible_hypernetworks))

            # Need to pop the embeddings that don't match.
            visible_embeddings['loaded'] = list(filter(lambda embedding: self.search_text in embedding['name'].lower(), visible_embeddings['loaded']))
            visible_embeddings['skipped'] = list(filter(lambda embedding: self.search_text in embedding['name'].lower(), visible_embeddings['skipped']))

        # Filter down the list of models returned
        if self.model_filter != 'all':
            # Edit self.lora and self.hypernetwork to remove the models that don't fit the filter
            # embeddings don't have the same info, and are filtered on server side as 'loaded' or 'skipped' based on current SD model
            new_loras = []
            for lora in visible_loras:
                sd_version = 'unknown'
                lora_name = lora['name']
                if lora_name in self.extra_network_settings['lora']:
                    lora_settings = self.extra_network_settings['lora'][lora_name]
                    if 'kra_override' in lora_settings and 'sd version' in lora_settings['kra_override']:
                        sd_version = lora_settings['kra_override']['sd version'].lower()
                    else:
                        sd_version = lora_settings[self.api.host]['sd version'].lower()
                if sd_version == self.model_filter:
                    new_loras.append(lora)
            visible_loras = new_loras

            new_hypernetworks = []
            for hn in visible_hypernetworks:
                sd_version = 'unknown'
                hn_name = hn['name']
                if hn_name in self.extra_network_settings['hypernetwork']:
                    hn_settings = self.extra_network_settings['hypernetwork'][hn_name]
                    if 'kra_override' in hn_settings and 'sd version' in hn_settings['kra_override']:
                        sd_version = hn_settings['kra_override']['sd version'].lower()
                    else:
                        sd_version = hn_settings[self.api.host]['sd version'].lower()
                if sd_version == self.model_filter:
                    new_hypernetworks.append(hn)

            visible_hypernetworks = new_hypernetworks

        self.toggle_images_checkbox.setChecked(self.show_icons)

        unknown_thumbnail = self.raw_img_to_qicon(self.settings_controller.get_unknown_thumbnail())

        if len(visible_loras) == 0:
            sep = QListWidgetItem("--- No Loras Found ---", self.lora_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))
        else:
            sep = QListWidgetItem("--- %s Loras Found ---" % len(visible_loras), self.lora_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))

        for lora in visible_loras:
            list_item = QListWidgetItem()
            label = lora[self.label_key]
            icon = unknown_thumbnail
            if self.show_icons and self.is_shown:
                raw_img = self.get_thumbnail('lora', lora['name'])
                if raw_img:
                    icon = self.raw_img_to_qicon(raw_img)
            list_item = QListWidgetItem(icon, label, self.lora_list)
            list_item.setToolTip(label)
            
            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('lora', lora)
            list_item.setSelected(re_found is not None)
            # list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))
    
        if len(visible_hypernetworks) == 0:
            sep = QListWidgetItem("--- No Hypernetworks Found ---", self.hypernetwork_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))
        else:
            sep = QListWidgetItem("--- %s Hypernetworks Found ---" % len(visible_loras), self.hypernetwork_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))

        for hypernetwork in visible_hypernetworks:
            list_item = QListWidgetItem()
            label = hypernetwork[self.label_key]
            icon = unknown_thumbnail
            if self.show_icons and self.is_shown:
                # Don't even try to get the thumbnails from the server if icons are turned off.
                raw_img = self.get_thumbnail('hypernetwork', hypernetwork['name'])
                if raw_img:
                    icon = self.raw_img_to_qicon(raw_img)
            list_item = QListWidgetItem(icon, label, self.hypernetwork_list)
            list_item.setToolTip(label)

            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('hypernetwork', hypernetwork)
            list_item.setSelected(re_found is not None)
            # list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))

        for embedding_status in ['loaded', 'skipped']:
            # Add a separator
            sep = QListWidgetItem("--- %s Embeddings ---" % embedding_status.title(), self.embedding_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))

            for embedding in visible_embeddings[embedding_status]:
                list_item = QListWidgetItem()
                label = embedding[self.label_key]
                icon = unknown_thumbnail
                if self.show_icons and self.is_shown:
                    raw_img = self.get_thumbnail('embedding', embedding['name'])
                    if raw_img:
                        icon = self.raw_img_to_qicon(raw_img)
                list_item = QListWidgetItem(icon, label, self.embedding_list)
                list_item.setToolTip(label)
                
                # Regex to see if this was already in the prompt
                re_found = self.find_in_text('embedding', embedding)
                list_item.setSelected(re_found is not None)
                # list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))


    def create_default_value(self, network_type, data):
        # TODO: add weight and activation text to default value
        network_name = data[self.label_key]
        if network_type is not 'embedding':
            text = '<%s:%s' % (network_type, network_name)
            custom_settings = self.settings_controller.get_extra_network_data(network_type, network_name)

            # Need to factor in kra_override + api.host settings
            if 'preferred weight' in custom_settings['kra_override']:
                if custom_settings['kra_override']['preferred weight'] == 0.0:
                    text = '%s:1.0>' % text
                else:
                    text = '%s:%s>' % (text, custom_settings['kra_override']['preferred weight'])
            else:
                if custom_settings[self.api.host]['preferred weight'] == 0.0:
                    text = '%s:1.0>' % text
                else:
                    text = '%s:%s>' % (text, custom_settings[self.api.host]['preferred weight'])

            if 'activation text' in custom_settings['kra_override'] and len(custom_settings['kra_override']['activation text']) > 0:
                text = '%s %s' % (text, custom_settings['kra_override']['activation text'])
            else:
                if len(custom_settings[self.api.host]['activation text']) > 0:
                    text = '%s %s' % (text, custom_settings[self.api.host]['activation text'])
            
            negative_text = ''
            if 'negative text' in custom_settings['kra_override'] and len(custom_settings['kra_override']['negative text']) > 0:
                negative_text = custom_settings['kra_override']['negative text']
            else:
                if len(custom_settings[self.api.host]['negative text']) > 0:
                    negative_text = custom_settings[self.api.host]['negative text']

            return text, negative_text
            # return '<%s:%s:1.0>' % (network_type, network_name)
        else:
            return network_name, ''
        # self.network_default_values['%s:%s' % (network_type, label)] = '<%s:%s:1.0>' % (network_type, label)

    def find_in_text(self, network_type, data):
        if network_type is not 'embedding':
            possible_names = data['name']
            if 'alias' in data.keys():
                possible_names = '%s|%s' % (possible_names, data['alias'])
            re_found = re.search("<%s:(%s):.*?>" % (network_type, possible_names), self.prompt_txt, re.IGNORECASE)
            return re_found
        else:
            # This regex might be poor...
            re_found = re.search("(%s)" % data['name'], self.prompt_txt)

    # ExtraNetworkCardWidget - extends QListWidgetItem() and has QBrush() to show if active
        # thumbnail
        # name
        # description.txt
        # SD Version (SD1, SDXL)
        # Activation text
        # prefered weight

    # If on localhost, I can import settings from the filesystem.
    # settings_controller will need to save the extra_network_settings in a separate file.
    # That separate json can be imported on another computer.

    def write_new_prompt_txt(self):
        for lora_item in self.lora_list.selectedItems():
            # Get the data
            lora_data = list(filter(lambda x: x[self.label_key] == lora_item.text(), self.loras))[0]
            re_found = self.find_in_text('lora', lora_data)
            if re_found is None:
                # The lora isn't in the string, add it
                prompt, negative_prompt = self.create_default_value('lora', lora_data)
                self.prompt_txt = "%s %s" % (self.prompt_txt, prompt)
                if len(negative_prompt) > 0:
                    self.negative_txt = "%s %s" % (self.negative_txt, negative_prompt)

        for hypernetwork_item in self.hypernetwork_list.selectedItems():
            # Get the data
            hypernetwork_data = list(filter(lambda x: x[self.label_key] == hypernetwork_item.text(), self.hypernetworks))[0]
            re_found = self.find_in_text('hypernetwork', hypernetwork_data)
            if re_found is None:
                # The hypernetwork isn't in the string, add it
                prompt, negative_prompt = self.create_default_value('hypernetwork', hypernetwork_data)
                self.prompt_txt = "%s %s" % (self.prompt_txt, prompt)
                if len(negative_prompt) > 0:
                    self.negative_txt = "%s %s" % (self.negative_txt, negative_prompt)

        for embedding_item in self.embedding_list.selectedItems():
            # Get the data
            embedding_data = list(filter(lambda x: x[self.label_key] == embedding_item.text(), self.embeddings))[0]
            re_found = self.find_in_text('embedding', embedding_data)
            if re_found is None:
                # The embedding isn't in the string, add it
                prompt, negative_prompt = self.create_default_value('embedding', embedding_data)
                self.prompt_txt = "%s %s" % (self.prompt_txt, prompt)
                if len(negative_prompt) > 0:
                    self.negative_txt = "%s %s" % (self.negative_txt, negative_prompt)

    def load_all_settings(self):
        # Pull in all the settings
        self.load_server_data()
        self.load_settings()

    def load_server_data(self):
        self.loras = self.api.get_loras()
        self.hypernetworks = self.api.get_hypernetworks()
        self.embeddings = self.map_embeddings(self.api.get_embeddings()) # NOT A LIST! A dict with loaded/skipped keys

        if 'localhost' in self.api.host or '127.0.0.1' in self.api.host:
            self.warning.setHidden(True)
        else:
            self.warning.setHidden(False)

    def closeEvent(self, event):
        self.close_children()
        return # Close should act as a cancel, not a confirm.
        # if self.on_close is not None:
            # self.write_new_prompt_txt()
            # self.on_close(self.prompt_txt)

    def write_changes_and_close(self):
        self.write_new_prompt_txt()
        self.on_close(self.prompt_txt, self.negative_txt)
        self.close()

    def show(self):
        super().show()
        self.is_shown = True
        self.load_all_settings()
        self.set_widget_values()

    def close(self):
        self.close_children()
        self.is_shown = False
        super().close()

    def close_children(self):
        # Close the child dialogs
        if self.customizer is not None:
            self.customizer.close()
        if self.manage_dialog is not None:
            self.manage_dialog.close()