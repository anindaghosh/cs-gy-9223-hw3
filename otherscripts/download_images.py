import requests
import os
import time
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("PEXELS_API_KEY")


def download_images(label, num_images, output_dir, api_key):
    """
    Downloads images of a specified label at high resolution using Pexels API
    and saves them to a directory.

    Args:
        label (str): The label of the images to download (e.g., "cats", "dogs").
        num_images (int): The number of images to download.
        output_dir (str): The directory to save the images to.
        api_key (str): Pexels API key.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Using Pexels API for high-quality images
    search_url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}

    # Set parameters for the API request
    params = {
        "query": label,
        "per_page": min(
            80, max(num_images, 15)
        ),  # Fetch more than needed to handle duplicates
        "size": "large",  # Get high resolution images
    }

    try:
        # Get image search results
        print(f"Searching for {label} images on Pexels...")
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()

        search_results = response.json()

        if "photos" not in search_results or len(search_results["photos"]) == 0:
            print(f"No images found for {label}")
            return

        photos = search_results["photos"]

        # Download up to num_images
        for i in range(min(num_images, len(photos))):
            # Get the high-resolution image URL
            image_url = photos[i]["src"]["large2x"]  # 1880px wide typically

            try:
                print(f"Downloading image {label}{i+1} from Pexels URL: {image_url}...")
                img_response = requests.get(image_url, stream=True)
                img_response.raise_for_status()

                image_name = f"{label}{i+1}.jpg"
                image_path = os.path.join(output_dir, image_name)

                with open(image_path, "wb") as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"Downloaded: {image_name}")

                # Small delay to avoid rate limiting
                time.sleep(0.8)

            except requests.exceptions.RequestException as e:
                print(f"Error downloading image {label}{i+1}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Error searching for {label} images: {e}")


def main():
    # You need to register for a free Pexels API key at: https://www.pexels.com/api/

    # Check if API key is provided
    if api_key == "YOUR_PEXELS_API_KEY":
        print("Please register for a Pexels API key at https://www.pexels.com/api/")
        print("Then replace 'YOUR_PEXELS_API_KEY' in the script with your actual key")
        return

    labels = [
        "cats",
        "dogs",
        "teachers",
        "cars",
        "helicopters",
        "trains",
        "planes",
        "bikes",
        "boats",
        "birds",
        "executives",
        "students",
        "mice",
        "elephants",
        "lions",
        "tigers",
        "bears",
        "monkeys",
        "pandas",
        "giraffes",
    ]
    num_images_per_label = 20
    parent_dir = os.path.dirname(os.getcwd())
    output_dir = os.path.join(parent_dir, "images")

    print(f"Images will be saved to: {output_dir}")

    for label in labels:
        print(f"\nDownloading {num_images_per_label} {label} images...")
        download_images(label, num_images_per_label, output_dir, api_key)

    print("\nDownload complete! All images have been saved.")


if __name__ == "__main__":
    main()
