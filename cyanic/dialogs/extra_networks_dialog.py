from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import re
import os
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController


class ExtraNetworksDialog(QDialog):
    MAX_HEIGHT = 100
    MAX_WIDTH = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None, prompt_txt=''):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close
        self.prompt_txt = prompt_txt

        self.label_key = 'name' # 'alias' isn't part of hypernetwork
        self.show_icons = False # TODO: Make it toggle
        self.enabled_networks = []

        self.thumbnails = {}

        self.loras = []
        self.hypernetworks = []
        self.embeddings = []
        self.tabs = QTabWidget()
        self.lora_list = QListWidget()
        self.hypernetwork_list = QListWidget()
        self.embedding_list = QListWidget()

        # self.importer_tab = QWidget()
        self.setLayout(QVBoxLayout())
        self.init_ui()

    def init_ui(self):
        # Filter by Version?
        self.layout().addWidget(self.tabs)
        # Tabs for Lora (and LyCORIS), Hypernetwork, Textual Inversion
        self.lora_list = QListWidget()
        # self.lora_list.setFixedHeight(ExtraNetworksDialog.MAX_HEIGHT)
        self.lora_list.setFlow(QListView.Flow.LeftToRight)
        # self.lora_list.setFixedWidth(ExtraNetworksDialog.MAX_WIDTH)
        # self.lora_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lora_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lora_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lora_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.lora_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lora_list.setViewMode(QListWidget.IconMode)
        self.lora_list.setIconSize(QSize(ExtraNetworksDialog.MAX_HEIGHT, ExtraNetworksDialog.MAX_HEIGHT))
        # self.layout().addWidget(self.lora_list)
        self.tabs.addTab(self.lora_list, 'Loras')

        self.hypernetwork_list = QListWidget()
        # self.hypernetwork_list.setFixedHeight(ExtraNetworksDialog.MAX_HEIGHT)
        self.hypernetwork_list.setFlow(QListView.Flow.LeftToRight)
        self.hypernetwork_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.hypernetwork_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.hypernetwork_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.hypernetwork_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hypernetwork_list.setViewMode(QListWidget.IconMode)
        self.hypernetwork_list.setIconSize(QSize(ExtraNetworksDialog.MAX_HEIGHT, ExtraNetworksDialog.MAX_HEIGHT))
        # self.layout().addWidget(self.hypernetwork_list)
        self.tabs.addTab(self.hypernetwork_list, 'Hypernetworks')

        self.embedding_list = QListWidget()
        # self.embedding_list.setFixedHeight(ExtraNetworksDialog.MAX_HEIGHT)
        self.embedding_list.setFlow(QListView.Flow.LeftToRight)
        self.embedding_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.embedding_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.embedding_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.embedding_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.embedding_list.setViewMode(QListWidget.IconMode)
        self.embedding_list.setIconSize(QSize(ExtraNetworksDialog.MAX_HEIGHT, ExtraNetworksDialog.MAX_HEIGHT))
        # self.layout().addWidget(self.embedding_list)
        self.tabs.addTab(self.embedding_list, 'Embeddings')
        
        self.layout().addWidget(self.tabs)

        footer = QWidget()
        footer.setLayout(QVBoxLayout())
        footer.layout().setContentsMargins(0,0,0,0)

        write_button = QPushButton('Update prompt')
        footer.layout().addWidget(write_button)

        cancel_button = QPushButton('Cancel')
        footer.layout().addWidget(cancel_button)

        self.layout().addWidget(footer)
        self.set_widget_values()


    def get_thumbnail(self, path):
        # Assumes the server isn't going to update icons while Krita is running.
        if path in self.thumbnails.keys():
            return self.thumbnails[path]
        raw_img = self.api.get_thumbnail(path)
        self.thumbnails[path] = raw_img
        return raw_img
    
    def update_prompt_txt(self, prompt_txt=''):
        self.prompt_txt = prompt_txt

    def raw_img_to_qicon(self, raw_img):
        ba = QByteArray(raw_img)
        qimage = QImage()
        qimage.loadFromData(ba)
        icon = QIcon(QPixmap.fromImage(qimage))
        return icon

    def map_embeddings(self, raw_embeddings):
        # Try to make embeddings return similar to the other network types
        # Need to guess the path based on other methods
        if len(raw_embeddings) == 0:
            # server isn't started, or has no embeddings
            self.embeddings = []
            return

        # TODO: Try to find the directory in the Settings, like a sane person!
        embeddings_dir = ''
        if len(self.loras) > 0:
            lora_path = os.path.split(self.loras[0]['path'])[0] # Root dir for loras
            models_root = os.path.split(lora_path)[0] # Root dir for models
            common_root = os.path.split(models_root)[0] # same directory as web-ui.bat
            embeddings_dir = os.path.join(common_root, 'embeddings') # This is where it is on my local system anyway

        new_embeddings = []
        for embedding_name in raw_embeddings['loaded'].keys():
            path = ''
            if len(embeddings_dir) > 0:
                path = os.path.join(embeddings_dir, '%s.pt' % embedding_name)
            data = {
                'name': embedding_name,
                'alias': embedding_name,
                'path': path,
            }
            new_embeddings.append(data)
        self.embeddings = new_embeddings

    def set_widget_values(self):
        self.lora_list.clear()
        self.enabled_networks.clear()
        self.loras = self.api.get_loras()
        self.hypernetworks = self.api.get_hypernetworks()
        # self.embeddings = self.api.get_embeddings()
        self.map_embeddings(self.api.get_embeddings())

        for lora in self.loras:
            raw_img = self.get_thumbnail(lora['path'])
            list_item = QListWidgetItem()
            label = lora[self.label_key]
            if self.show_icons and raw_img:
                icon = self.raw_img_to_qicon(raw_img)
                list_item = QListWidgetItem(icon, label, self.lora_list)
            else:
                list_item = QListWidgetItem(label, self.lora_list)

            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('lora', lora)
            list_item.setSelected(re_found is not None)
            list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))
    
        for hypernetwork in self.hypernetworks:
            raw_img = self.get_thumbnail(hypernetwork['path'])
            list_item = QListWidgetItem()
            label = hypernetwork[self.label_key]
            if self.show_icons and raw_img:
                icon = self.raw_img_to_qicon(raw_img)
                list_item = QListWidgetItem(icon, label, self.hypernetwork_list)
            else:
                list_item = QListWidgetItem(label, self.hypernetwork_list)

            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('hypernetwork', hypernetwork)
            list_item.setSelected(re_found is not None)
            list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))

        for embedding in self.embeddings:
            raw_img = self.get_thumbnail(embedding['path'])
            list_item = QListWidgetItem()
            label = embedding[self.label_key]
            if self.show_icons and raw_img:
                icon = self.raw_img_to_qicon(raw_img)
                list_item = QListWidgetItem(icon, label, self.embedding_list)
            else:
                list_item = QListWidgetItem(label, self.embedding_list)

            # Regex to see if this was already in the prompt
            re_found = self.find_in_text('embedding', embedding)
            list_item.setSelected(re_found is not None)
            list_item.setSizeHint(QSize(ExtraNetworksDialog.MAX_WIDTH, ExtraNetworksDialog.MAX_HEIGHT))


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
        if self.on_close is not None:
            self.write_new_prompt_txt()
            self.on_close(self.prompt_txt)