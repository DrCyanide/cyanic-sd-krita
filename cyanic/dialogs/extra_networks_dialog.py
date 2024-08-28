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
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None, prompt_txt=''):
        super().__init__()
        self.setWindowTitle('Extra Networks')
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close
        self.prompt_txt = prompt_txt

        self.label_key = 'name' # 'alias' isn't part of hypernetwork
        self.show_icons = False

        self.thumbnails = {}

        self.model_filter = 'all'
        self.search_text = ''

        self.loras = []
        self.hypernetworks = []
        self.embeddings = []
        self.tabs = QTabWidget()
        self.lora_list = QListWidget()
        self.hypernetwork_list = QListWidget()
        self.embedding_list = QListWidget()

        self.list_width = int(ExtraNetworksDialog.MAX_WIDTH * 4.5)
        self.list_height = int(ExtraNetworksDialog.MAX_WIDTH * 2.5)

        # self.importer_tab = QWidget()
        self.setLayout(QVBoxLayout())
        self.load_settings()
        self.init_ui()

    def open_menu(self, position, network_list:QListWidget):
        menu = QMenu()
        index = network_list.indexAt(position)
        item = network_list.itemFromIndex(index)

        if item is None:
            # The user didn't click on an item
            return

        customizeAction = menu.addAction("Customize")
        action = menu.exec_(network_list.mapToGlobal(position))

        if action == customizeAction:
            # Open customize options for this item
            # raise Exception('Clicked on %s' % item.text())
            network_type = ''
            if self.tabs.currentWidget() == self.lora_list:
                network_type = 'lora'
            elif self.tabs.currentWidget() == self.hypernetwork_list:
                network_type = 'hypernetwork'
            else:
                # Not a valid network type?
                return
            network_name = item.text()
            self.customizer = ExtraNetworksEditDialog(self.settings_controller, self.api, network_type, network_name, show_thumbnail=self.show_icons)
            self.customizer.show()

    def init_ui(self):
        header = QWidget()
        header.setLayout(QHBoxLayout())
        header.layout().setContentsMargins(0,0,0,0)

        self.toggle_images_checkbox = QCheckBox('Show thumbnails')
        self.toggle_images_checkbox.setChecked(self.show_icons)
        self.toggle_images_checkbox.toggled.connect(lambda: self.update_show_icons())
        header.layout().addWidget(self.toggle_images_checkbox)

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
        self.lora_list.customContextMenuRequested.connect(lambda x: self.open_menu(x, self.lora_list))
        self.tabs.addTab(self.lora_list, 'Loras')

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
        self.lora_list.customContextMenuRequested.connect(lambda x: self.open_menu(x, self.lora_list))
        self.tabs.addTab(self.hypernetwork_list, 'Hypernetworks')

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
        self.search_text = self.search_bar.text().lower()
        self.set_widget_values()

    def get_thumbnail(self, network_type, network_name):
        cached_thumbnail = self.settings_controller.get_cached_thumbnail(network_type, network_name)
        if cached_thumbnail is not None:
            return cached_thumbnail
        # Get thumbnail from server
        path = ''
        if network_type == 'embedding':
            # Embeddings is split into loaded and skipped, and needs to be handled differently
            network_source = self.embeddings
            if network_name in self.embeddings['loaded']:
                path = self.embeddings['loaded'][network_name]['path']
            elif network_name in self.embeddings['skipped']:
                path = self.embeddings['skipped'][network_name]['path']
            
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
        return raw_img
        
    
    def update_prompt_txt(self, prompt_txt=''):
        self.prompt_txt = prompt_txt

    def update_show_icons(self):
        self.show_icons = self.toggle_images_checkbox.isChecked()
        self.settings_controller.set('show_extra_network_thumbnails', self.show_icons)
        self.settings_controller.save() # This setting should be applied to future opens
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
        new_embeddings = {'loaded':[], 'skipped': []}

        if raw_embeddings is None:
            # server isn't started, or has no embeddings
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

    def set_widget_values(self):
        self.lora_list.clear()
        self.hypernetwork_list.clear()
        self.embedding_list.clear()
        self.loras = self.api.get_loras()
        self.hypernetworks = self.api.get_hypernetworks()
        # self.embeddings = self.api.get_embeddings()
        self.embeddings = self.map_embeddings(self.api.get_embeddings()) # NOT A LIST! A dict with loaded/skipped keys

        # Filter by search
        if len(self.search_text) > 0:
            # TODO: Offer option to search by notes and description
            self.loras = list(filter(lambda lora: self.search_text in lora['name'].lower() or self.search_text in lora['alias'].lower(), self.loras))

            self.hypernetworks = list(filter(lambda hypernetwork: self.search_text in hypernetwork['name'].lower(), self.hypernetworks))

            # Need to pop the embeddings that don't match.
            for loaded in self.embeddings['loaded'].keys():
                if self.search_text in loaded.lower():
                    self.embeddings['loaded'].pop(loaded)
            for skipped in self.embeddings['skipped'].keys():
                if self.search_text in skipped.lower():
                    self.embeddings['skipped'].pop(skipped)

        # Filter down the list of models returned
        if self.model_filter != 'all':
            # Edit self.lora and self.hypernetwork to remove the models that don't fit the filter
            # embeddings don't have the same info, and are filtered on server side as 'loaded' or 'skipped' based on current SD model
            extra_network_settings = self.settings_controller.get_extra_network_settings()
            new_loras = []
            for lora in self.loras:
                sd_version = 'unknown'
                if lora['name'].lower() in extra_network_settings['lora']:
                    sd_version = extra_network_settings['lora'][lora['name'].lower()]['sd version'].lower()
                if sd_version == self.model_filter:
                    new_loras.append(lora)
            self.loras = new_loras

            new_hypernetworks = []
            for hn in self.hypernetworks:
                sd_version = 'unknown'
                if hn['name'].lower() in extra_network_settings['hypernetwork']:
                    sd_version = extra_network_settings['hypernetwork'][hn['name'].lower()]['sd version'].lower()
                if sd_version == self.model_filter:
                    new_hypernetworks.append(hn)

            self.hypernetworks = new_hypernetworks

        self.toggle_images_checkbox.setChecked(self.show_icons)

        unknown_thumbnail = self.raw_img_to_qicon(self.settings_controller.get_unknown_thumbnail())

        for lora in self.loras:
            list_item = QListWidgetItem()
            label = lora[self.label_key]
            icon = unknown_thumbnail
            if self.show_icons:
                raw_img = self.get_thumbnail('lora', lora['name'])
                if raw_img:
                    icon = self.raw_img_to_qicon(raw_img)
            list_item = QListWidgetItem(icon, label, self.lora_list)
            list_item.setToolTip(label)
            
            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('lora', lora)
            list_item.setSelected(re_found is not None)
            # list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))
    
        for hypernetwork in self.hypernetworks:
            list_item = QListWidgetItem()
            label = hypernetwork[self.label_key]
            icon = unknown_thumbnail
            if self.show_icons:
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
            sep = QListWidgetItem("--- %s ---" % embedding_status, self.embedding_list)
            sep.setFlags(Qt.NoItemFlags)
            sep.setSizeHint(QSize(self.list_width, 30))

            for embedding in self.embeddings[embedding_status]:
                list_item = QListWidgetItem()
                label = embedding[self.label_key]
                icon = unknown_thumbnail
                if self.show_icons:
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
        label = data[self.label_key]
        if network_type is not 'embedding':
            return '<%s:%s:1.0>' % (network_type, label)
        else:
            return label
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
                self.prompt_txt = "%s %s" % (self.prompt_txt, self.create_default_value('lora', lora_data))

        for hypernetwork_item in self.hypernetwork_list.selectedItems():
            # Get the data
            hypernetwork_data = list(filter(lambda x: x[self.label_key] == hypernetwork_item.text(), self.hypernetworks))[0]
            re_found = self.find_in_text('hypernetwork', hypernetwork_data)
            if re_found is None:
                # The lora isn't in the string, add it
                self.prompt_txt = "%s %s" % (self.prompt_txt, self.create_default_value('hypernetwork', hypernetwork_data))

        for embedding_item in self.embedding_list.selectedItems():
            # Get the data
            embedding_data = list(filter(lambda x: x[self.label_key] == embedding_item.text(), self.embeddings))[0]
            re_found = self.find_in_text('embedding', embedding_data)
            if re_found is None:
                # The lora isn't in the string, add it
                self.prompt_txt = "%s %s" % (self.prompt_txt, self.create_default_value('embedding', embedding_data))

    def closeEvent(self, event):
        return # Close should act as a cancel, not a confirm.
        # if self.on_close is not None:
            # self.write_new_prompt_txt()
            # self.on_close(self.prompt_txt)

    def write_changes_and_close(self):
        self.write_new_prompt_txt()
        self.on_close(self.prompt_txt)
        self.close()

    def show(self):
        super().show()
        self.set_widget_values()