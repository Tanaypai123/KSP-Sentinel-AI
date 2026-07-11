import sys
import os

# Add the 'dataset/app' directory to sys.path so that imports like 'app.ai.*' resolve.
_current_dir = os.path.abspath(os.path.dirname(__file__))
_dataset_app_path = os.path.abspath(os.path.join(_current_dir, 'dataset', 'app'))
if _dataset_app_path not in sys.path:
    sys.path.insert(0, _dataset_app_path)
