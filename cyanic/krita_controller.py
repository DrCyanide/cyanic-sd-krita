from krita import *
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QBuffer, QIODevice, QByteArray, QThread, QPointF, pyqtSignal, Qt, QTimer
import base64
import random
import json
# https://scripting.krita.org/lessons/layers
# https://api.kde.org/krita/html/classNode.html

class GenericWorker(QObject):
    finished = pyqtSignal()
    def __init__(self, task):
        super().__init__()
        self.task = task

    def run(self):
        try:
            self.task()
        except Exception as e:
            pass
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
            if int(target_version[i]) > int(version[i]):
                return False
        return True

    def run_as_thread(self, function, after_function):
        try:
            # NOTE: Krita crashes if self.thread/self.worker are local variables (just thread/worker)
            self.thread = QThread()
            self.worker = GenericWorker(function)
            self.worker.moveToThread(self.thread)
            self.worker.finished.connect(after_function)
            self.worker.finished.connect(self.thread.quit)
            self.thread.started.connect(self.worker.run)
            self.thread.start()
        except Exception as e:
            raise Exception('Cyanic SD - Exception starting thread: %s' % e )

    def create_new_doc(self):
        # create new document createDocument(width, height, name, colorSpace, bitDepth, colorProfile, DPI)
        new_doc = Krita.instance().createDocument(512, 512, "Stable Diffusion", "RGBA", "U8", "", 300.0)
        Krita.instance().activeWindow().addView(new_doc)
        self.doc = new_doc

    def refresh_doc(self):
        self.doc = Krita.instance().activeDocument()

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
    
    def set_selection(self, x, y, w, h):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        selection = Selection()
        selection.select(x, y, w, h, 255) # 255 = totally selected
        self.doc.setSelection(selection)

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

    def set_layer_visible(self, layer, visible=True):
        layer.setVisible(visible)

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
        png_start = 'iVBORw0KGgo' # this byte sequence is always at the start of PNG images
        image = None
        if base64str.find(png_start) == 0:
            image = QImage.fromData(b64img_data, 'PNG') # This formats the bytes in a way Krita can understand them
        else:
            image = QImage.fromData(b64img_data, 'JPEG')

        # If the image is grayscale (like ControlNet previews often are), convert it to full color
        # if image.format() == QImage.Format_Grayscale8 or image.format() == QImage.Format_Grayscale16:
        if image.isGrayscale():
            image = image.convertToFormat(QImage.Format_RGBA8888) 
        
        # scale the image, used for previews to prevent flickering when scaling
        if width > -1:
            image = image.scaledToWidth(width)
        if height > -1:
            image = image.scaledToHeight(height)
        image_bits = image.bits()
        if image_bits is not None:
            image_bits.setsize(image.byteCount())
            byte_array = QByteArray(image_bits.asstring())
            return byte_array, image.width(), image.height()
        else:
            return QByteArray(), 0, 0

    def qimage_to_b64_str(self, image:QImage):
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, 'PNG')
        b64_data = ba.toBase64().data()
        return b64_data.decode()

    def find_below(self, below_layer=None):
        dest = None
        target_node = self.doc.activeNode()
        if below_layer is not None:
            target_node = below_layer
        target_node_index = target_node.index()
        target_parent = target_node.parentNode()
        target_parent_children = target_parent.childNodes()
        max_index = len(target_parent_children)

        dest = None
        if target_node_index == max_index - 1:
            dest = target_node
        else:
            dest = target_parent_children[target_node_index - 1]
        return dest

    def find_parent_node(self, layer=None):
        child_node = layer
        if child_node is None:
            child_node = self.doc.activeNode()
        return child_node.parentNode()

    def results_to_layers(self, results, x=0, y=0, w=-1, h=-1, layer_name='', below_active=False, below_layer=None):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()

        if w < 0 or h < 0:
            # This is for img2img/txt2img results
            if 'info' in results and 'width' in results['info'] and 'height' in results['info']:
                w = results['info']['width']
                h = results['info']['height']
            else:
                if 'poses' in results: # ControlNet OpenPose Preview results
                    w = results['poses'][0]['canvas_width']
                    h = results['poses'][0]['canvas_height']
                else:
                    s_x, s_y, s_w, s_h = self.get_selection_bounds()
                    if s_w > 0 and s_h > 0:
                        w = s_w
                        h = s_h
                    else:
                        c_x, c_y, c_w, c_h = self.get_canvas_bounds()
                        w = c_w
                        h = c_h

        img_layer_parent = self.doc.rootNode()
        if below_active or below_layer is not None:
            img_layer_parent = self.find_parent_node(below_layer)

        if 'images' in results: # txt2img or img2img results
            if len(results['images']) > 1:
                group = self.doc.createGroupLayer("Results")
                img_layer_parent = group
            
            for i in range(0, len(results['images'])):
                name = 'Image'
                if len(layer_name) > 0:
                    name = layer_name
                elif 'info' in results and 'all_seeds' in results['info'] and len(results['info']['all_seeds']) > i:
                    name = 'Seed: %s' % results['info']['all_seeds'][i]
                if results['images'][i] is None or len(results['images'][i]) == 0:
                    # This can happen if there's no ControlNet Preview available
                    continue
                layer = self.doc.createNode(name, 'paintLayer')
                byte_array, img_w, img_h = self.base64_to_pixeldata(results['images'][i])
                layer.setPixelData(byte_array, x, y, img_w, img_h)
                dest = None
                if len(results['images']) == 1 and (below_active or below_layer is not None):
                    dest = self.find_below(below_layer)
                img_layer_parent.addChildNode(layer, dest)
                if img_w != w or img_h != h:
                    self.transform_to_width_height(layer, x, y, w, h)
                self.doc.refreshProjection()

            if len(results['images']) > 1:
                if below_active or below_layer is not None:
                    parent = self.find_parent_node(below_layer)
                    dest = self.find_below(below_layer)
                    parent.addChildNode(group, dest)
                else:
                    self.doc.rootNode().addChildNode(group, None)

        if 'image' in results: # extras results
            name = 'Image'
            if len(layer_name) > 0:
                name = layer_name
            if len(results['image']) == 0:
                return 
            layer = self.doc.createNode(name, 'paintLayer')
            byte_array, img_w, img_h = self.base64_to_pixeldata(results['image'], w, h)
            layer.setPixelData(byte_array, x, y, img_w, img_h)
            dest = None
            if below_active or below_layer is not None:
                dest = self.find_below(below_layer)
            # if below_active or below_layer is not None: # Needed to get the Transparency Mask in the right position
            #     target_node = self.doc.activeNode()
            #     if below_layer is not None:
            #         target_node = below_layer
            #     target_node_index = target_node.index()
            #     target_parent = target_node.parentNode()
            #     target_parent_children = target_parent.childNodes()
            #     max_index = len(target_parent_children)

            #     dest = None
            #     if target_node_index == max_index - 1:
            #         dest = target_node
            #     else:
            #         dest = target_parent_children[target_node_index - 1]

            img_layer_parent.addChildNode(layer, dest)

            if img_w != w or img_h != h:
                self.transform_to_width_height(layer, x, y, w, h)
            self.doc.refreshProjection()

        self.doc.refreshProjection()


    def result_to_transparency_mask(self, results, x=0, y=0, w=-1, h=-1):
        delay = 500 #ms
        old_active = self.doc.activeNode()
        is_group = old_active.type() == 'grouplayer'
        parent_node = old_active.parentNode()

        # Pass to results_to_layers() with a unique name
        uniqueName = 'cyanic_sd_transparent-%s' % random.randint(10000, 99999)
        self.results_to_layers(results, x, y, w, h, uniqueName, below_active=True)
        # Find the node with that unique name
        transparency_layer = self.doc.nodeByName(uniqueName)
        
        # self.doc.setActiveNode(transparency_layer)
        QTimer.singleShot(delay, lambda: self.doc.setActiveNode(transparency_layer)) # Was activating too fast in group layers
        self.doc.refreshProjection()
        self.doc.waitForDone()
        QTimer.singleShot(delay, lambda: Krita.instance().action('convert_to_transparency_mask').trigger()) # Was activating before the new layer was active
        if parent_node.type() == 'grouplayer' and not is_group:
            # TODO: revisit this... it's still applying to the group
            # If the user selected a group, the transparency mask should apply to the whole group - which is default behavior
            # If selection was a layer inside a group, parent the transparency_layer to the old_active
            # transparency_layer.remove() # Should remove it from it's parent node
            # old_active.addChildNode(transparency_layer, None)
            # The transparency mask is the new active
            QTimer.singleShot(delay, lambda:old_active.addChildNode(self.doc.activeNode(), None))
        
    def get_active_layer_uuid(self):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        if len(self.doc.activeNode().channels()) == 0: # Masks don't have channels
            self.doc.setActiveNode(self.doc.activeNode().parentNode())
        return self.doc.activeNode().uniqueId()
    
    def get_layer_from_uuid(self, uuid):
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            self.create_new_doc()
        if type(uuid) is str:
            uuid = QUuid(uuid)
        if self.version_gte('5.2'):
            return self.doc.nodeByUniqueID(uuid) # This is a 5.2 call, didn't exist in 5.1
        else:
            # iterate over all nodes
            result = self.iterate_node_by_uuid(self.doc.rootNode(), uuid)
            return result
                
    def iterate_node_by_uuid(self, start_node, uuid):
        if start_node.uniqueId() == uuid:
            return start_node
        for child in start_node.childNodes():
            result = self.iterate_node_by_uuid(child, uuid)
            if result is not None:
                return result

    
    def set_layer_uuid_as_active(self, uuid):
        node = self.get_layer_from_uuid(uuid)
        try:
            self.doc.setActiveNode(node)
        except:
            # 5.1.5 was having issues, because node was type QObject and not Node
            pass

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

    def convert_qimage_to_grayscale_mask(self, image, width, height):
        for pixel_x in range(0, width):
            for pixel_y in range(0, height):
                pixel = image.pixel(pixel_x, pixel_y)
                alpha = qAlpha(pixel)
                newPixel = qRgb(alpha, alpha, alpha)
                image.setPixel(pixel_x, pixel_y, newPixel)
        return image

    def get_mask_and_image(self, mode='canvas'):
        # mode: 'canvas', 'layer', 'selection'
        # I'm trying to find the best way to write these repetitive functions.
        self.doc = Krita.instance().activeDocument()
        if self.doc is None:
            return None, None
        
        mask_layer = self.doc.activeNode()
        if len(mask_layer.channels()) == 0:
            # This is a mask on a layer, not the layer we want to use as a mask
            mask_layer = mask_layer.parentNode()
            self.doc.setActiveNode(mask_layer)
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
        # mask_img_bw = mask_img.createAlphaMask(Qt.ImageConversionFlag.MonoOnly) # White is what the transparent was
        # mask_img_bw.invertPixels() # Black is now what the transparent was
        # # if mask_img_bw.isGrayscale():
        # mask_img_bw = mask_img_bw.convertToFormat(QImage.Format_RGBA8888) # ControlNet masks didn't like the monochrome

        mask_img_bw = self.convert_qimage_to_grayscale_mask(mask_img, width, height)


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
        except Exception as e:
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
        mask = self.doc.createTransformMask('Transform')
        layer.addChildNode(mask, None)
        bounds = layer.bounds()
        if bounds.width() == 0 or bounds.height() == 0:
            # Uh... panic? Adding this to avoid a divide by zero error
            bounds = self.doc.bounds()
        scale_x = width / bounds.width() * 1.0 # 0.4
        scale_y = height / bounds.height() * 1.0 # 0.4
        xml_data = """\
        <!DOCTYPE transform_params>
        <transform_params>
            <main id="tooltransformparams"/>
            <data mode="0">
                <free_transform>
                    <transformedCenter type="pointf" x="{x}" y="{y}"/>
                    <originalCenter type="pointf" x="{x}" y="{y}"/>
                    <rotationCenterOffset type="pointf" x="{x}" y="{y}"/>
                    <transformAroundRotationCenter type="value" value="1"/>
                    <aX type="value" value="0"/>
                    <aY type="value" value="0"/>
                    <aZ type="value" value="0"/>
                    <cameraPos type="vector3d" x="0" z="1024" y="0"/>
                    <scaleX type="value" value="{scale_x}"/>
                    <scaleY type="value" value="{scale_y}"/>
                    <shearX type="value" value="0"/>
                    <shearY type="value" value="0"/>
                    <keepAspectRatio type="value" value="0"/>
                    <flattenedPerspectiveTransform m21="0" type="transform" m13="0" m23="0" m11="1" m22="1" m33="1" m12="0" m31="0" m32="0"/>
                    <filterId type="value" value="Bicubic"/>
                </free_transform>
            </data>
        </transform_params>
        """.format(x=x, y=y, scale_x=scale_x, scale_y=scale_y)
        mask.fromXML(xml_data)

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

    def get_foreground_color_hex(self):
        view = Application.activeWindow.activeView()
        canvas = view.canvas()
        return view.foregroundColor().colorForCanvas(canvas).name() # "name" is the hex value, with lowercase letters
    
    def get_background_color_hex(self):
        view = Application.activeWindow.activeView()
        canvas = view.canvas()
        return view.backgroundColor().colorForCanvas(canvas).name() # "name" is the hex value, with lowercase letters