from .cyanic_widget import CyanicWidget

# Widgets that don't implement CyanicWidget (manage layout or Cyanic SD settings)
from .collapsible import CollapsibleWidget
from .sd_connection import SDConnectionWidget
from .labeled_slider import LabeledSlider

# Widgets that SHOULD implement CyanicWidget (provide image generation settings)
from .prompts import PromptWidget
from .seed import SeedWidget
from .models import ModelsWidget
from .generate import GenerateWidget
from .image_in import ImageInWidget
from .soft_inpaint import SoftInpaintWidget
from .denoise import DenoiseWidget
from .extensions import ExtensionWidget
from .mask import MaskWidget
from .color_correction import ColorCorrectionWidget
from .batch import BatchWidget
from .hires_fix import HiResFixWidget
from .cfg import CFGWidget
from .interrogate_model import InterrogateModelWidget
from .interrogate import InterrogateWidget