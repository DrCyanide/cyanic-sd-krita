import urllib.request
import urllib.error
import html
import json
import base64
import time
import os
import re
# Allow self-signed certs to be used. Self-signed certs allow some WebUI features (like ControlNet's camera) to work over local network.
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

class SDAPI():
    DEFAULT_HOST = 'http://127.0.0.1:7860'
    def __init__(self, host=DEFAULT_HOST, on_connection_change=None):
        self.host = host
        self.host_version = 'A1111' # SD.Next and Forge also supported
        self.supports_refiners = True # SD.Next with sd_backend == "original" does not support refiners
        self.models = []
        self.vaes = []
        self.samplers = []
        self.schedulers = []
        self.upscalers = []
        self.facerestorers = []
        self.styles = []
        self.scripts = {} # Dictionary, because it's split into txt2img scripts and img2img scripts
        self.loras = []
        self.embeddings = {}
        self.hypernetworks = []
        self.default_settings = {}
        self.defaults = {
            'sampler': '',
            'scheduler': '',
            'model': '',
            'vae': '',
            'upscaler': '',
            'refiner': '',
            'face_restorer': '',
            'color_correction': True,
        }
        self.known_thumbnail_paths = {}
        self.connected = False
        self.on_connection_change = on_connection_change # A function that can be called if self.connected changes - DO NOT CALL IN A THREAD EVALUATION!!! It will crash Krita with no error message.
        self.last_url = ''
        self.test_connection(self.host, switch_if_success=True) # If there's a connection, it'll change host and init_api(). If not, it won't wait for a bunch of startup calls, allowing Krita to boot faster.

    def change_host(self, host=DEFAULT_HOST):
        self.host = host
        self.init_api()

    def init_api(self):
        old_connected = self.connected
        try:
            response = self.get_status()
            
            if response is not None:
                self.connected = True
            else:
                self.connected = False
                return
        except Exception as e:
            self.connected = False
            if old_connected:
                self.on_connection_change()
            return # There was an issue, but the server might not be online yet.
        
        self.known_thumbnail_paths = {} # Each server can have a different file extension for the same base path

        init_processes = [
            self.get_options,
            self.set_host_version, # Some get_ functions depend on backend version
            self.get_models,
            self.get_vaes,
            self.get_samplers,
            self.get_schedulers,
            self.get_upscalers,
            self.get_facerestorers,
            self.get_styles,
            self.get_scripts,
            self.get_loras,
            self.get_embeddings,
            self.get_hypernetworks,
        ]
        for process in init_processes:
            process()

    def post(self, url, data):
        self.last_url = "{}{}".format(self.host, url)
        request = urllib.request.Request(self.last_url, data=json.dumps(data).encode('utf-8'), headers={"Content-Type": "application/json"})       
        try:
            response = urllib.request.urlopen(request)
            text = response.read()
            try:
                return json.loads(text)
            except:
                return text
        except:
            return None


    def get(self, url):
        if not self.connected:
            # Drastically improves Krita boot times when the Stable Diffusion server isn't running.
            return None 

        self.last_url = "{}{}".format(self.host, url)
        try:
            response = urllib.request.urlopen(self.last_url)
            text = response.read()
            try:
                return json.loads(text)
            except:
                return text
        except:
            return None

    def get_status(self):
        return self.get("/queue/status")
    
    def get_system_status(self):
        return self.get("/sdapi/v1/system-info/status")

    def get_progress(self):
        return self.get("/sdapi/v1/progress")

    def test_connection(self, host=None, switch_if_success=False):
        # Return True if the server is up and running.
        # Don't use the self.get() function, so it can be tested with other servers
        if host is None:
            host = self.host

        # Python seems to struggle with localhost, switch to 127.0.0.1
        if 'localhost' in host:
            host.replace('localhost', '127.0.0.1')

        try:
            last_url = "{}/queue/status".format(host)
        
            response = urllib.request.urlopen(last_url, timeout=5) # Without a timeout a stalled server can cause issues on startup
            text = response.read()
            try:
                queue_status = json.loads(text)
                success = len(queue_status.keys()) > 0
                if success and switch_if_success:
                    self.connected = True
                    self.change_host(host)
                return success
            except Exception as e:
                return False
        except Exception as e:
            original_host = host
            if 'http' not in host:
                # It's probably locally hosted on their network, and not https
                host = 'http://%s' % original_host
                result = self.test_connection(host, switch_if_success)
                if result:
                    return result
                else:
                    # Maybe they're connecting to an outside service and forgot an HTTPS
                    host = 'https://%s' % original_host
                    return self.test_connection(host, switch_if_success)
            return False

    # ===========================
    # API calls that cache values
    # ===========================

    def set_host_version(self):
        # Look at differences in the settings to figure out which backend is being run
        # If a backend has more than half of these settings, it's likely SD.Next
        # I don't want to use ALL of the settings, because if a setting is removed it'll guess incorrectly
        sdnext_unique = [
            'cross_attention_sep',
            'cuda_compile_sep',
            'models_paths_sep_options',
            'outdir_sep_dirs',
            'outdir_sep_grids',
            'postprocessing_sep_img2img',
            'postprocessing_sep_upscalers',
            'sd_lyco',
        ]
        forge_unique = [
            'forge_try_reproduce',
            'forge_unet_storage_dtype',
            'forge_inference_memory',
            'forge_async_loading',
            'forge_pin_shared_memory',
            'forge_preset',
            'forge_additional_modules',
        ]
        sdnext_points = 0
        for key in sdnext_unique:
            if key in self.default_settings.keys():
                sdnext_points = sdnext_points + 1

        forge_points = 0
        for key in forge_unique:
            if key in self.default_settings.keys():
                forge_points = forge_points + 1

        # If none of the unique values are there, it's good old A1111
        if forge_points == 0 and sdnext_points == 0:
            self.host_version = 'A1111'
        
        sdnext_percent = sdnext_points / len(sdnext_unique)
        forge_percent = forge_points / len(forge_unique)

        if sdnext_percent > forge_percent:
            self.host_version = 'SD.Next'
        elif forge_percent > sdnext_percent:
            self.host_version = 'Forge'
        else:
            self.host_version = 'A1111'


    def get_options(self):
        self.default_settings = self.get("/sdapi/v1/options")
        if self.default_settings is None: # Some sort of server error while getting the configs?
            self.default_settings = {}

        self.set_host_version()
        if self.host_version == 'SD.Next':
            if self.default_settings['sd_backend'].lower() == 'original':
                self.supports_refiners = False

        # self.defaults['sampler'] = There isn't one in settings
        # self.defaults['scheduler'] = There isn't one in the settings
        self.defaults['model'] = self.default_settings.get('sd_model_checkpoint', '')
        self.defaults['vae'] = self.default_settings.get('sd_vae', '')
        # self.defaults['upscaler'] = There isn't one in settings
        self.defaults['refiner'] = self.default_settings.get('sd_model_refiner', '')
        self.defaults['face_restorer'] = self.default_settings.get('face_restoration_model', '')
        self.defaults['color_correction'] = self.default_settings.get('img2img_color_correction', True)
        
        return self.default_settings

    def get_samplers(self):
        self.samplers = self.get("/sdapi/v1/samplers")
        if self.samplers is None:
            self.samplers = []
        return self.samplers
    
    def get_schedulers(self):
        self.schedulers = self.get("/sdapi/v1/schedulers")
        if self.schedulers is None:
            self.schedulers = []
        return self.schedulers

    def get_upscalers(self):
        self.upscalers = self.get("/sdapi/v1/upscalers")
        if self.upscalers is None:
            self.upscalers = []
        return self.upscalers
    
    def get_models(self):
        self.models = self.get("/sdapi/v1/sd-models")
        if self.models is None:
            self.models = []
        return self.models
    
    def get_model_names(self):
        if self.connected:
            return [*map(lambda x: x['model_name'], self.models)]
        else:
            return []
    
    def get_model_name(self, title):
        if len(title) == 0:
            return 'None'
        model_names = self.get_model_names()
        model_titles = [*map(lambda x: x['title'], self.models)]
        if title in model_titles and model_titles.index(title) > -1:
            return model_names[model_titles.index(title)]
        else:
            # raise Exception('Cyanic SD - No model found with title "%s"' % title)
            return 'None'
    
    def get_vae_names(self):
        if self.connected:
            return [*map(lambda x: x['model_name'], self.vaes)]
        else:
            return []
    
    def get_face_restorer_names(self):
        if self.connected:
            return [*map(lambda x: x['name'], self.facerestorers)]
        else:
            return []
    
    def get_upscaler_names(self):
        if self.connected:
            return [*map(lambda x: x['name'], self.upscalers)]
        else:
            return []

    def get_facerestorers(self):
        self.facerestorers = self.get("/sdapi/v1/face-restorers")
        if self.facerestorers:
            return self.facerestorers
        else:
            return []

    def get_styles(self):
        self.styles = self.get("/sdapi/v1/prompt-styles")
        if self.styles:
            return self.styles
        else:
            return []
    
    def get_vaes(self):
        if self.host_version == 'Forge':
            self.vaes = self.get("/sdapi/v1/sd-modules")
        else:
            self.vaes = self.get("/sdapi/v1/sd-vae")
        if self.vaes:
            return self.vaes
        else:
            return []
    
    def get_scripts(self):
        self.scripts = self.get("/sdapi/v1/scripts")
        if self.scripts:
            return self.scripts
        else:
            return {'txt2img': [], 'img2img': []}
    
    def get_loras(self):
        # Doesn't return user notes, but returns all sort of other junk
        self.loras = self.get("/sdapi/v1/loras")
        if self.loras:
            return self.loras
        else:
            return []
    
    def get_embeddings(self):
        response = self.get("/sdapi/v1/embeddings")
        if response:
            self.embeddings = response
            return self.embeddings
        else:
            return {}
    
    def get_hypernetworks(self):
        response = self.get("/sdapi/v1/hypernetworks")
        if response:
            self.hypernetworks = response
            return self.hypernetworks
        else:
            return []
    
    # TODO: /sdapi/v1/lycos exists in SD.Next, but this might be better to append to loras for consistency with other backends
        
    def get_thumbnail(self, path):
        if path in self.known_thumbnail_paths.keys():
            # Already know what the path should be
            image = self.get("/sd_extra_networks/thumb?filename=%s" % self.known_thumbnail_paths[path])
            if image is not None:
                return image
            else:
                # The saved path is wrong, remove it from the cache
                self.known_thumbnail_paths.pop(path)

        image_path = path
        ext = os.path.splitext(path)[1].lower()
        if ext != 'png' or ext != 'jpg':
            image_path = "%s.png" % os.path.splitext(path)[0]
        image = self.get("/sd_extra_networks/thumb?filename=%s" % image_path)
        if image is not None:
            self.known_thumbnail_paths[path] = image_path
            return image
    
        # Try the other extension
        if ext == 'png':
            image_path = "%s.jpg" % os.path.splitext(path)[0]
        else:
            image_path = "%s.png" % os.path.splitext(path)[0]
        image = self.get("/sd_extra_networks/thumb?filename=%s" % image_path)
        if image is not None:
            self.known_thumbnail_paths[path] = image_path
            return image

        # Try .preview.png
        image_path = "%s.preview.png" % os.path.splitext(path)[0]
        image = self.get("/sd_extra_networks/thumb?filename=%s" % image_path)
        if image is not None:
            self.known_thumbnail_paths[path] = image_path
            return image

        return None # Image was not found
    
    def get_server_extra_network_config(self, network_type='', network_name=''):
        # NOTE: network_name is case sensitive
        # SD.Next has /sd_extra_networks/info that returns data in the expected format (the same way it's saved in the server files, the .json inside the models dirs)
        # Forge and A1111 require parsing the /sd_extra_networks/get-single-card endpoint, and are incomplete with the data returned there

        generic_format = {
            "description": "",
            "sd version": "Unknown",
            "activation text": "",
            "negative text": "",
            "preferred weight": 0,
            "notes": "", # Notes don't seem to be available... idk why or where to get them from
        }

        if self.host_version == 'SD.Next':
            response = self.get("/sd_extra_networks/info?page=%s&item=%s" % (network_type.lower(), network_name))
            return response['info']
        
        response = self.get("/sd_extra_networks/get-single-card?page=%s&name=%s" % (network_type.lower(), network_name))
        if response is None:
            return generic_format
        
        # Developed on Forge backend
        raw_html = response['html']

        generic_format['description'] = re.search('<span class="description">(.*?)<\/span>', raw_html, flags=re.DOTALL)[1]
        try:
            generic_format['sd version'] = re.search('SDversion="SdVersion.(.*?)"', raw_html, flags=re.DOTALL)[1]
        except:
            generic_format['sd version'] = 'Unknown' # A1111 doesn't have SD Version in card api
            if '127.0.0.1' in self.host or 'localhost' in self.host:
                # Try to access the file system to get the sd version.
                # Yes, this could be used to get everything if server is local, but I want to use the API as much as possible.
                local_model_path = re.search('data-clipboard-text="(.*?)"', raw_html, flags=re.DOTALL)[1]
                local_model_settings_path = os.path.splitext(local_model_path)[0] + '.json'
                if os.path.exists(local_model_settings_path):
                    with open(local_model_settings_path, 'r') as file:
                        local_settings_json = json.load(file)
                        if 'sd version' in local_settings_json:
                            generic_format['sd version'] = local_settings_json['sd version']

        on_click_string = re.search('onclick=\"cardClicked\((.*?)\);', raw_html, flags=re.DOTALL)[1] # Get the parameters of the call
        on_click_params = html.unescape(on_click_string)
        # Unknown String (empty)
        # String including network_type, network_name, preferred weight, and activation text
        preferred_weight_str = re.search(':" \+ (.*) \+ ">"', on_click_params, flags=re.DOTALL)[1]
        try:
            generic_format['preferred weight'] = float(preferred_weight_str)
        except:
            # Using extra_networks_default_multiplier setting
            generic_format['preferred weight'] = self.default_settings['extra_networks_default_multiplier']
        
        try:
            generic_format['activation text'] = re.search('\+ ">" \+ " (.*?)",', on_click_params, flags=re.DOTALL)[1]
        except:
            # There is no activation text
            generic_format['activation text'] = ''

        # String for negative text
        try:
            generic_format['negative text'] = re.search('", "(.*?)",', on_click_params, flags=re.DOTALL)[1]
        except:
            generic_format['negative text'] = ''
        # Unknown boolean

        return generic_format

    # ===========================
    # Calls to make UI dev easier
    # ===========================

    def get_samplers_and_default(self):
        if self.connected and self.samplers:
            return list(map(lambda x: x['name'], self.samplers)), self.defaults['sampler']
        else:
            return [], 'None'
    
    def get_schedulers_and_default(self):
        if self.connected and self.schedulers:
            return list(map(lambda x: x['name'], self.schedulers)), self.defaults['scheduler']
        else:
            return [], 'Automatic'
    
    def get_models_and_default(self):
        if self.connected and self.models:
            return list(map(lambda x: x['title'], self.models)), self.defaults['model']
        else:
            return [], 'None'
    
    def get_vaes_and_default(self):
        if self.connected and self.vaes:
            vaes = list(map(lambda x: x['model_name'], self.vaes))
            if not 'None' in vaes:
                vaes.insert(0, 'None')
            return vaes, self.defaults['vae']
        else:
            return [], 'None'
    
    def get_upscaler_and_default(self):
        if self.connected and self.upscalers:
            return list(map(lambda x: x['name'], self.upscalers)), self.defaults['upscaler']
        else:
            return [], 'None'
    
    def get_refiners_and_default(self):
        # No difference in options yet between refiners and models
        if self.connected and self.models:
            refiner_titles = list(map(lambda x: x['title'], self.models))
            if 'None' not in refiner_titles:
                temp = ['None']
                temp.extend(refiner_titles)
                refiner_titles = temp
            return refiner_titles, self.defaults['refiner']
        else:
            return [], 'None'
        
    
    def get_face_restorers_and_default(self):
        if self.connected and self.facerestorers:
            return list(map(lambda x: x['name'], self.facerestorers)), self.defaults['face_restorer']
        else:
            return [], 'None'

    def script_installed(self, script_name):
        if self.connected and self.scripts:
            for key in self.scripts.keys():
                # Ignore case when checking if the name appears. Could potentially have issues in the future with partial matches
                if script_name.lower() in [k.lower() for k in self.scripts[key]]:
                    return True
        return False
    
    def get_style_names(self):
        if self.connected and self.styles:
            return list(map(lambda x: x['name'], self.styles))
        else:
            return []
    
    def get_style_prompts(self, names:list):
        if self.connected and self.styles:
            prompts_raw = list(map(lambda x: x['prompt'] if x['name'] in names else '', self.styles))
            prompts = ', '.join(list(filter(lambda x: len(x) > 0, prompts_raw)))
            negative_prompts_raw = list(map(lambda x: x['negative_prompt'] if x['name'] in names else '', self.styles))
            negative_prompts = ', '.join(list(filter(lambda x: len(x) > 0, negative_prompts_raw)))
            return prompts, negative_prompts
        else:
            return '', ''

    def get_lora_names(self):
        if self.connected and self.loras:
            return list(map(lambda x: x['name'], self.loras))
        else:
            return []

    def get_embedding_names(self):
        if self.connected and self.embeddings:
            if 'loaded' in self.embeddings:
                return list(self.embeddings['loaded'].keys())
        return []

    def get_hypernetwork_names(self):
        if self.connected and self.hypernetworks:
            return list(map(lambda x: x['name'], self.hypernetworks))
        else:
            return []

    # TODO: SD.Next supports lycos

    # ===========================
    # API calls to make images
    # ===========================

    def interrupt(self):
        self.post('/sdapi/v1/interrupt', {})

    # txt2img defaults to using server settings, so you can call it with as little as {"prompt":"", "negative_prompt":""}
    # This method was more robust than was needed for this project, but may make a good example in the future.
    # def txt2img(self, prompt="", negative_prompt="", width=512, height=512, seed=-1, sampler="", steps=20, cfg_scale=7, clip_skip=1, batch_size=1, batch_count=1, hr_fix=False, hr_scale=2, hr_upscaler="", styles=["None"], restore_faces=False, tiling=False, **kwargs):
    #     data = {
    #         "enable_hr": hr_fix,
    #         "denoising_strength": 0,
    #         "firstphase_width": 0,
    #         "firstphase_height": 0,
    #         "hr_scale": hr_scale,
    #         "hr_force": False,
    #         "hr_upscaler": hr_upscaler,
    #         "hr_second_pass_steps": 0,
    #         "hr_resize_x": 0,
    #         "hr_resize_y": 0,
    #         "refiner_steps": 5,
    #         "refiner_start": 0,
    #         "refiner_prompt": "",
    #         "refiner_negative": "",
    #         "prompt": prompt,
    #         "styles": styles,
    #         "seed": seed,
    #         "subseed": -1,
    #         "subseed_strength": 0,
    #         "seed_resize_from_h": -1,
    #         "seed_resize_from_w": -1,
    #         "sampler_name": sampler,
    #         "latent_sampler": sampler,
    #         "batch_size": batch_size,
    #         "n_iter": batch_count,
    #         "steps": steps,
    #         "cfg_scale": cfg_scale,
    #         "image_cfg_scale": 0, # Used by Instruct Pix2Pix models
    #         "clip_skip": clip_skip,
    #         "width": width,
    #         "height": height,
    #         "full_quality": True,
    #         "restore_faces": restore_faces,
    #         "tiling": tiling,
    #         "do_not_save_samples": False,
    #         "do_not_save_grid": False,
    #         "negative_prompt": negative_prompt,
    #         "eta": 0,
    #         "diffusers_guidance_rescale": 0.7,
    #         "s_min_uncond": 0,
    #         "s_churn": 0,
    #         "s_tmax": 0,
    #         "s_tmin": 0,
    #         "s_noise": 1,
    #         "override_settings": {}, # Override settings use the same keys as /sdapi/v1/options
    #         # "override_settings": {"sd_model_checkpoint": "modelname"}
    #         "override_settings_restore_afterwards": True,
    #         "script_args": [],
    #         "sampler_index": "Euler",
    #         "script_name": "",
    #         "send_images": True,
    #         "save_images": False,
    #         "alwayson_scripts": {}
    #     }
    #     results = self.post("/sdapi/v1/txt2img", data)
    #     if type(results['info']) is str:
    #         results['info'] = json.loads(results['info'])
    #     return results

    def cleanup_data(self, data):
        # Modify places where the format is different between internal and API
        if not 'override_settings' in data.keys():
            data['override_settings'] = {}
        if 'model' in data.keys():
            data['override_settings']['sd_model_checkpoint'] = data.pop('model')
        if 'vae' in data.keys():
            data['override_settings']['sd_vae'] = data.pop('vae')
        if 'color_correction' in data.keys():
            data['override_settings']['img2img_color_correction'] = data.pop('color_correction')

        if 'sampler' in data.keys():
            data['sampler_name'] = data.pop('sampler')
        if 'sampling_steps' in data.keys():
            data['steps'] = data.pop('sampling_steps')

        if 'hr_steps' in data.keys():
            data['hr_second_pass_steps'] = data.pop('hr_steps')

        data['override_settings_restore_afterwards'] = False # It just takes WAY too long to load different models to leave this off

        # A1111 unique settings
        if self.host_version == 'A1111':
            if 'refiner' in data.keys() and len(data['refiner']) > 0 and data['refiner'].lower() != 'none':
                data['refiner_checkpoint'] = data.pop('refiner')
            if 'refiner_start' in data.keys():
                data['refiner_switch_at'] = data.pop('refiner_start')
        
        # SD.Next unique settings
        if self.host_version == 'SD.Next':
            if 'refiner' in data.keys() and len(data['refiner']) > 0 and data['refiner'].lower() != 'none':
                data['override_settings']['sd_model_refiner'] = data.pop('refiner')
            if 'refiner_start' in data.keys():
                data['enable_hr'] = True
                data['hr_force'] = True
                # 'refiner_start' is percentage based
                start = int(data['steps'] * data['refiner_start'])
                steps = int(data['steps'] - start)
                # data['refiner_start'] = start
                data['refiner_steps'] = steps
                data['refiner_prompt'] = data['prompt']
                data['refiner_negative_prompt'] = data['negative_prompt']
        

        if 'img2img_img' in data.keys():
            data['init_images'] = [data.pop('img2img_img')]

        if 'inpaint_img' in data.keys():
            data['init_images'] = [data.pop('inpaint_img')]

        if 'mask_img' in data.keys():
            data['mask'] = data.pop('mask_img')

        if 'batch_count' in data.keys():
            data['n_iter'] = data.pop('batch_count')

        return data

    def txt2img(self, data):
        data = self.cleanup_data(data)
        self.log_request_and_response(data)
        results = self.post("/sdapi/v1/txt2img", data)
        if type(results['info']) is str:
            results['info'] = json.loads(results['info'])
        self.log_request_and_response(data, results)
        return results

    def img2img(self, data):
        data = self.cleanup_data(data)
        self.log_request_and_response(data)
        results = self.post("/sdapi/v1/img2img", data)
        if type(results['info']) is str:
            results['info'] = json.loads(results['info'])
        self.log_request_and_response(data, results)
        return results
    
    def extra(self, data):
        data = self.cleanup_data(data)
        self.log_request_and_response(data)
        results = self.post("/sdapi/v1/extra-single-image", data)
        # No 'info' section to parse
        self.log_request_and_response(data, results)
        return results
        
    def interrogate(self, data):
        self.log_request_and_response(data)
        results = self.post("/sdapi/v1/interrogate", data)
        self.log_request_and_response(data, results)
        return results

    # ===========================
    # Debugging fun!
    # ===========================

    def log_request_and_response(self, data, response=None, filename='log.json'):
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(plugin_dir, filename), 'w') as output_file:
            log = {
                'request': data,
                'response': response
            }
            output_file.write(json.dumps(log))

    def read_log(self, filename='log.json', in_plugin_dir=True):
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(plugin_dir, filename)
        if not in_plugin_dir:
            path = filename
        
        return self.read_json_file(path)

    def write_img_to_file(self, base64_str, filename='saved.png'):
        with open(filename, 'wb') as output_file:
            output_file.write(base64.b64decode(base64_str))
    
    def read_img_from_file(self, filename='saved.png'):
        my_string = ''
        with open(filename, 'rb') as input_file:
            my_string = base64.b64encode(input_file.read() )
        return my_string.decode('utf-8')
    
    def read_json_file(self, filename='log.json'):
        data = {}
        with open(filename, 'r') as input_file:
            string_format = input_file.read()
            data = json.loads(string_format)
        return data