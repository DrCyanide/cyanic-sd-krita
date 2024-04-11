import urllib.request
import urllib.error
import json
import base64
import time
import os
# Allow self-signed certs to be used. Self-signed certs allow some WebUI features (like ControlNet's camera) to work over local network.
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

class SDAPI():
    DEFAULT_HOST = 'http://127.0.0.1:7860'
    def __init__(self, host=DEFAULT_HOST):
        self.host = host
        self.host_version = 'A1111' # SD.Next also supported
        self.supports_refiners = True # SD.Next with sd_backend == "original" does not support refiners
        self.models = []
        self.vaes = []
        self.samplers = []
        self.upscalers = []
        self.facerestorers = []
        self.styles = []
        self.scripts = {} # Dictionary, because it's split into txt2img scripts and img2img scripts
        self.loras = []
        self.embeddings = []
        self.hypernetworks = []
        self.default_settings = {}
        self.defaults = {
            'sampler': '',
            'model': '',
            'vae': '',
            'upscaler': '',
            'refiner': '',
            'face_restorer': '',
            'color_correction': True,
        }
        self.connected = False
        self.last_url = ''
        self.init_api()

    def change_host(self, host=DEFAULT_HOST):
        self.host = host
        self.init_api()

    def init_api(self):
        try:
            response = self.get_status()
            if response is not None:
                self.connected = True
            else:
                self.connected = False
                return
        except Exception as e:
            self.connected = False
            return # There was an issue, but the server might not be online yet.
        init_processes = [
            self.get_models,
            self.get_vaes,
            self.get_samplers,
            self.get_upscalers,
            self.get_facerestorers,
            self.get_styles,
            self.get_scripts,
            self.get_loras,
            self.get_embeddings,
            self.get_hypernetworks,
            self.get_options,
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
        sdnext_points = 0
        for key in sdnext_unique:
            if key in self.default_settings.keys():
                sdnext_points = sdnext_points + 1
        if sdnext_points > len(sdnext_unique) / 2:
            self.host_version = 'SD.Next'
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
        return self.facerestorers

    def get_styles(self):
        self.styles = self.get("/sdapi/v1/prompt-styles")
        return self.styles
    
    def get_vaes(self):
        self.vaes = self.get("/sdapi/v1/sd-vae")
        return self.vaes
    
    def get_scripts(self):
        self.scripts = self.get("/sdapi/v1/scripts")
        return self.scripts
    
    def get_loras(self):
        # Doesn't return user notes, but returns all sort of other junk
        self.loras = self.get("/sdapi/v1/loras")
        return self.loras
    
    def get_embeddings(self):
        self.embeddings = self.get("/sdapi/v1/embeddings")
        return self.embeddings
    
    def get_hypernetworks(self):
        self.hypernetworks = self.get("/sdapi/v1/hypernetworks")
        return self.hypernetworks
    
    # TODO: /sdapi/v1/lycos exists in SD.Next
    
    # ===========================
    # Calls to make UI dev easier
    # ===========================

    def get_samplers_and_default(self):
        if self.connected and self.samplers:
            return list(map(lambda x: x['name'], self.samplers)), self.defaults['sampler']
        else:
            return [], 'None'
    
    def get_models_and_default(self):
        if self.connected and self.models:
            return list(map(lambda x: x['title'], self.models)), self.defaults['model']
        else:
            return [], 'None'
    
    def get_vaes_and_default(self):
        if self.connected and self.vaes:
            return list(map(lambda x: x['model_name'], self.vaes)), self.defaults['vae']
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

        results = self.post("/sdapi/v1/txt2img", data)
        if type(results['info']) is str:
            results['info'] = json.loads(results['info'])
        self.log_request_and_response(data, results)
        return results

    def img2img(self, data):
        data = self.cleanup_data(data)

        results = self.post("/sdapi/v1/img2img", data)
        if type(results['info']) is str:
            results['info'] = json.loads(results['info'])
        self.log_request_and_response(data, results)
        return results
    
    def extra(self, data):
        data = self.cleanup_data(data)
        results = self.post("/sdapi/v1/extra-single-image", data)
        # No 'info' section to parse
        self.log_request_and_response(data, results)
        return results
        
    def interrogate(self, data):
        results = self.post("/sdapi/v1/interrogate", data)
        self.log_request_and_response(data, results)
        return results

    # ===========================
    # Debugging fun!
    # ===========================

    def log_request_and_response(self, data, response, filename='log.json'):
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(plugin_dir, filename), 'w') as output_file:
            log = {
                'request': data,
                'response': response
            }
            output_file.write(json.dumps(log))

    def write_img_to_file(self, base64_str, filename='saved.png'):
        with open(filename, 'wb') as output_file:
            output_file.write(base64.b64decode(base64_str))
    
    def read_img_from_file(self, filename='saved.png'):
        my_string = ''
        with open(filename, 'rb') as input_file:
            my_string = base64.b64encode(input_file.read() )
        return my_string.decode('utf-8')
    
    def read_json_file(self, filename='test.json'):
        data = {}
        with open(filename, 'r') as input_file:
            string_format = input_file.read()
            data = json.loads(string_format)
        return data