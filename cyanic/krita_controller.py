from krita import *
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QByteArray, QThread, QPointF, pyqtSignal, Qt
import base64
# https://scripting.krita.org/lessons/layers
# https://api.kde.org/krita/html/classNode.html

class GenericWorker(QObject):
    finished = pyqtSignal()
    def __init__(self, task):
        super().__init__()
        self.task = task

    def run(self):
        self.task()
        self.finished.emit()

class KritaController():
    def __init__(self):
        self.doc = Krita.instance().activeDocument()
        self.preview_layer_uid = None

    def version_gte(self, target_version):
        # Check if the current version is greater than or equal to the target version
        # target_version can be '5', '5.1', '5.1.3'
        version = Krita.instance().version().split('.')
        target_version = target_version.split('.')
        for i in range(len(target_version)):
            # TODO: check if either version has any letters in it, for a beta or release candidate
            if int(target_version[i]) < int(version[i]):
                return False
        return True

    def run_as_thread(self, function, after_function):
        try:
            # NOTE: Krita crashes if self.thread/self.worker are local variables (just thread/worker)
            self.thread = QThread()
            self.worker = GenericWorker(function)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(after_function)
            self.worker.finished.connect(self.thread.quit)
            self.thread.start()
        except Exception as e:
            raise Exception('Cyanic SD - Exception starting thread: %s' % e )

    def create_new_doc(self):
        # create new document createDocument(width, height, name, colorSpace, bitDepth, colorProfile, DPI)
        new_doc = Krita.instance().createDocument(512, 512, "Stable Diffusion", "RGBA", "U8", "", 300.0)
        Krita.instance().activeWindow().addView(new_doc)
        self.doc = new_doc

    def get_selection_bounds(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        # return x, y, width, height
        if self.doc.selection():
            x = self.doc.selection().x()
            y = self.doc.selection().y()
            width = self.doc.selection().width()
            height = self.doc.selection().height()
            return x, y, width, height
        else:
            return 0, 0, 0, 0

    def get_canvas_bounds(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        
        bounds = self.doc.bounds()
        x = bounds.x()
        y = bounds.y()
        width = bounds.width()
        height = bounds.height()
        return x, y, width, height
    
    def resize_canvas(self, width, height):
        # Use the existing x, y
        x, y, w_old, h_old = self.get_canvas_bounds()
        w_real = width - x
        h_real = height - y
        self.doc.resizeImage(x, y, w_real, h_real)

    def get_layer_bounds(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()

        bounds = self.doc.activeNode().bounds()
        x = bounds.x()
        y = bounds.y()
        width = bounds.width()
        height = bounds.height()
        return x, y, width, height

    def get_active_layer_name(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        layer = self.doc.activeNode()
        return layer.name()

    def get_canvas_size(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        # return width, height
        return self.doc.width(), self.doc.height()
    
    def base64_to_pixeldata(self, base64str:str, width=-1, height=-1):
        b64img_data = base64.b64decode(base64str)
        image = QImage.fromData(b64img_data, 'PNG') # This formats the bytes in a way Krita can understand them
        # scale the image, used for previews to prevent flickering when scaling
        if width > -1:
            image = image.scaledToWidth(width)
        if height > -1:
            image = image.scaledToHeight(height)
        image_bits = image.bits()
        image_bits.setsize(image.byteCount())
        byte_array = QByteArray(image_bits.asstring())
        return byte_array, image.width(), image.height()

    def results_to_layers(self, results, x=0, y=0, w=-1, h=-1, layer_name=''):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()

        if w < 0:
            w = results['info']['width']
        if h < 0:
            h = results['info']['height']

        img_layer_parent = self.doc.rootNode()
        if 'images' in results: # txt2img or img2img results
            if len(results['images']) > 1:
                group = self.doc.createGroupLayer("Results")
                img_layer_parent = group
            
            for i in range(0, len(results['images'])):
                name = 'Image'
                if 'info' in results and len(results['info']['all_seeds']) > i:
                    name = layer_name if len(layer_name) > 0 else 'Seed: %s' % results['info']['all_seeds'][i]
                layer = self.doc.createNode(name, 'paintLayer')
                byte_array, img_w, img_h = self.base64_to_pixeldata(results['images'][i])
                layer.setPixelData(byte_array, x, y, img_w, img_h)
                img_layer_parent.addChildNode(layer, None)
                self.doc.refreshProjection()

            if len(results['images']) > 1:
                self.doc.rootNode().addChildNode(group, None)

        if 'image' in results: # extras results
            name = 'Image'
            if len(layer_name) > 0:
                name = layer_name
            layer = self.doc.createNode(name, 'paintLayer')
            byte_array, img_w, img_h = self.base64_to_pixeldata(results['image'], w, h)
            layer.setPixelData(byte_array, x, y, img_w, img_h)
            img_layer_parent.addChildNode(layer, None)
            self.doc.refreshProjection()

        self.doc.refreshProjection()


    def get_selected_layer_img(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()

        x, y, width, height = self.get_layer_bounds()
        # projectionPixelData works for groups, and applies filters, masks, layers in the group, etc.
        # ba = self.doc.activeNode().projectionPixelData(x, y, width, height) # QByteArray
        # # return self.doc.activeNode().thumbnail(width, height) # Gives an image, but it doesn't have the layers below it
        # bytes_per_pixel = 4
        # format = QImage.Format.Format_ARGB32
        # image = QImage(ba, width, height, (width * bytes_per_pixel), format)
        image = self.doc.projection(x, y, width, height) # Use the doc projection to include the layers below, we're just shaping it to the 
        return image
    
    def get_canvas_img(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        
        x, y, width, height = self.get_canvas_bounds()
        image = self.doc.projection(x, y, width, height)
        return image
    
    def get_selection_img(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        
        x, y, width, height = self.get_selection_bounds()
        image = self.doc.projection(x, y, width, height)
        return image
    
    def get_transparent_selection(self):
        x, y, width, height = self.get_selection_bounds()
        ba = self.doc.activeNode().projectionPixelData(x, y, width, height) # QByteArray
        return self.projection_to_qimage(ba, x, y, width, height)

    def get_transparent_layer(self):
        x, y, width, height = self.get_layer_bounds()
        ba = self.doc.activeNode().projectionPixelData(x, y, width, height) # QByteArray
        return self.projection_to_qimage(ba, x, y, width, height)

    def get_transparent_canvas(self):
        x, y, width, height = self.get_canvas_bounds()
        ba = self.doc.activeNode().projectionPixelData(x, y, width, height) # QByteArray
        return self.projection_to_qimage(ba, x, y, width, height)

    def get_mask_and_image(self, mode='canvas'):
        # mode: 'canvas', 'layer', 'selection'
        # I'm trying to find the best way to write these repetitive functions.
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            return None, None
        
        mask_layer = self.doc.activeNode()
        if not mask_layer.visible():
            # TODO: Find the next visible layer, use that as the mask.
            pass
        
        x, y, width, height = 0, 0, 0, 0
        if mode.lower() == 'canvas':
            x, y, width, height = self.get_canvas_bounds()
        if mode.lower() == 'layer':
            x, y, width, height = self.get_layer_bounds()
        if mode.lower() == 'selection':
            x, y, width, height = self.get_selection_bounds()
        

        mask_ba = mask_layer.projectionPixelData(x, y, width, height) # QByteArray
        mask_img = self.projection_to_qimage(mask_ba, x, y, width, height) # QImage
        mask_img_bw = mask_img.createAlphaMask(Qt.ImageConversionFlag.MonoOnly) # White is what the transparent was
        mask_img_bw.invertPixels() # Black is now what the transparent was
        
        mask_layer.setVisible(False)
        self.doc.refreshProjection() # Without this, the canvas doesn't refresh, and the mask is still on top
        image = self.doc.projection(x, y, width, height)
        mask_layer.setVisible(True)
        self.doc.refreshProjection() # Restore the mask
        return mask_img_bw, image


    def projection_to_qimage(self, ba:QByteArray, x, y, width, height):
        bytes_per_pixel = 4
        format = QImage.Format.Format_ARGB32
        image = QImage(ba, width, height, (width * bytes_per_pixel), format)
        return image

    def _get_layer_with_uid(self, uid, node=None):
        # nodeByName() doesn't return every node with that name, just the first one.
        # So I need to check uniqueIds
        if node is None:
            node = self.doc.rootNode()
        if node.uniqueId() == uid:
            return node
        for child in node.childNodes():
            child_results = self._get_layer_with_uid(uid, child)
            if child_results:
                return child_results

    def transform_to_width_height(self, layer, x, y, width, height):
        # If Krita 5.2+, use a transform mask.
        # Before that transform masks couldn't be controlled with the API, so raw transform
        try:
            if self.version_gte('5.2'):
                self.use_transform_mask(layer, x, y, width, height)
            else:
                self.scale_layer(layer, x, y, width, height) 
        except:
            self.scale_layer(layer, x, y, width, height) 

    def scale_layer(self, layer, x, y, width, height, strategy='Bilinear'):
        # strategy = ["Hermite", "Bicubic", "Box", "Bilinear", "Bell", "BSpline", "Lanczos3", "Mitchell"]
        origin = QPointF(x, y)
        layer.scaleNode(origin, width, height, strategy)

    def use_transform_mask(self, layer, x, y, width, height):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        # Krita 5.2+ only
        # If there's no transform mask, make one.
        # Else, reuse the existing transform mask
        mask = self.doc.createNode('Transform', 'transformmask')
        layer.addChildNode(mask, None)
        # mask.fromXML()
        

    def delete_preview_layer(self):
        if self.preview_layer_uid is None:
            return
        layer = self._get_layer_with_uid(self.preview_layer_uid)
        if layer:
            layer.setLocked(False)
            layer.remove()
        self.preview_layer_uid = None

    def update_preview_layer(self, base64str:str, x, y, w, h):
        self.doc = Krita.instance().activeDocument()
        # byte_array, img_w, img_h = self.base64_to_pixeldata(base64str)
        byte_array, img_w, img_h = self.base64_to_pixeldata(base64str, w, h) # Using a transform over and over on the layer creates flickering. 
        layer = None
        if self.preview_layer_uid is None:
            layer = self.doc.createNode('Preview', 'paintLayer')
            self.doc.rootNode().addChildNode(layer, None)
            self.preview_layer_uid = layer.uniqueId()
            # self.transform_to_width_height(layer, x, y, img_w, img_h)
        else:
            layer = self._get_layer_with_uid(self.preview_layer_uid)
        layer.setLocked(False)
        layer.setPixelData(byte_array, x, y, img_w, img_h)
        # self.transform_to_width_height(layer, x, y, w, h)
        layer.setLocked(True) # Prevent users accidentally drawing on layer       
        self.doc.refreshProjection() # Without this, the preview image doesn't draw on the canvas

        