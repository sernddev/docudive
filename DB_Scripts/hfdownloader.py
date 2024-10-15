import os
import configparser
import sys
from huggingface_hub import snapshot_download
from tqdm import tqdm

def load_config(config_file):
    """
    Load parameters from the configuration file. If the file does not exist,
    prompt the user for input and save to the configuration file.

    Returns:
    - model_name: The name of the Hugging Face model to download.
    - download_path: The local path to download the model (defaults to current working directory if not provided).
    - token: Hugging Face access token (optional, if downloading private models).
    """
    config = configparser.ConfigParser()

    # Check if the config file exists
    if os.path.exists(config_file):
        config.read(config_file)
        model_name = config.get('Settings', 'model_name', fallback=None)
        download_path = config.get('Settings', 'download_path', fallback=os.getcwd())  # Use current directory as fallback
        token = config.get('Settings', 'token', fallback=None)
    else:
        model_name = None
        download_path = None
        token = None

    # If any required config values are missing, ask the user for input
    if not model_name:
        model_name = input("Enter the model name (e.g., 'meta-llama/Llama-2'): ")

    if not download_path:
        download_path = input(f"Enter the output directory to save the model (default: {os.getcwd()}): ") or os.getcwd()

    # Ensure the download path is properly set and creates directories if necessary
    if not download_path or download_path == ".":
        # Extract the model folder name from the model_name, replacing slashes with directory structure
        model_dir = model_name.replace("/", os.sep)
        # Set the download path to current directory + model directory
        download_path = os.path.join(os.getcwd(), model_dir)
        print(f"Using current directory as download path: {download_path}")
    else:
        # If a custom path is provided, ensure all directories are created
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)
        print(f"Using specified download path: {download_path}")

    if not token:
        token = input("Enter your Hugging Face token (or press Enter to skip): ") or None

    # Save the new/updated settings to the config file
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            config.add_section('Settings')
            config.set('Settings', 'model_name', model_name)
            config.set('Settings', 'download_path', download_path)
            config.set('Settings', 'token', token if token else '')
            config.write(f)

    return model_name, download_path, token


def download_hf_model(model_name: str, download_path: str, token: str = None):
    """
    Downloads a Hugging Face model, resumes if the download was interrupted.

    Parameters:
    - model_name: The model name or repo_id on Hugging Face (e.g., "meta-llama/Llama-2").
    - download_path: The path to save the downloaded model.
    - token: Optional. Hugging Face token for private models.
    """

    # Ensure the directory exists
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    print(f"Starting/resuming download for model: {model_name}")
    confirm = input("Enter yes to continue downloading...")
    if 'yes' not in confirm:
        print(f"download is stopped: {model_name}")
        sys.exit(0)
    # Use tqdm to show a progress bar
    with tqdm(total=100, desc="Downloading model", unit="files", ncols=100) as pbar:
        try:
            # Download or resume download for the model
            snapshot_download(
                repo_id=model_name,
                local_dir=download_path,
                local_dir_use_symlinks=False,
                resume_download=True,  # Resumes download if interrupted
                token=token  # Use the token if required
            )
            pbar.update(100)  # Update progress bar to 100% once completed
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            return False

    print(f"Model download completed and saved to: {download_path}")
    return True


if __name__ == "__main__":
    # Get the config file path from the command line argument
    if len(sys.argv) < 2:
        print("Usage: python script.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Load configuration or ask for input
    model_name, download_path, token = load_config(config_file)

    # Download the model with resume option
    download_hf_model(model_name, download_path, token)

