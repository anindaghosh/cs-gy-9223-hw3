import os
import re
import requests
import mimetypes
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_GATEWAY_KEY")


def extract_label(filename):
    """Extract the label from a filename that follows the pattern '{label}{number}.jpg'"""
    # Use regex to extract the label (all characters before any digits)
    match = re.match(r"([a-zA-Z]+)\d+\.", filename)
    if match:
        return match.group(1)
    return None


def upload_image_to_api(image_path, label, api_base_url):
    """Upload an image to the API using PUT request"""

    filename = os.path.basename(image_path)

    # Determine content type based on file extension
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type:
        content_type = "application/octet-stream"

    print(f"Uploading {filename} (label: {label})...")

    # Read the image file as binary
    with open(image_path, "rb") as file:
        image_data = file.read()

    # Set up headers
    headers = {
        "Content-Type": content_type,
        "x-api-key": API_KEY,
        # Add any authentication headers if needed
        # 'Authorization': 'Bearer YOUR_TOKEN_HERE',
    }

    # Make the PUT request
    try:
        response = requests.put(api_base_url, data=image_data, headers=headers)

        # Check if the request was successful
        if response.status_code in [200, 201, 204]:
            print(f"✅ Successfully uploaded {filename}")
            return True
        else:
            print(
                f"❌ Failed to upload {filename}. Status code: {response.status_code}"
            )
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error uploading {filename}: {str(e)}")
        return False


def main():
    # Configure these variables according to your setup
    api_base_url = "https://0jbxi308pf.execute-api.us-east-1.amazonaws.com/prod/photos"  # Replace with your actual API base URL

    # Path to images directory (relative to the script)
    parent_dir = os.path.dirname(os.getcwd())
    images_dir = os.path.join(parent_dir, "images")

    # Check if images directory exists
    if not os.path.exists(images_dir):
        print(f"Error: Images directory not found at {images_dir}")
        return

    print(f"Scanning for images in: {images_dir}")

    # Keep track of statistics
    total_images = 0
    successful_uploads = 0

    # Iterate through all files in the images directory
    for filename in os.listdir(images_dir):
        file_path = os.path.join(images_dir, filename)

        # Skip directories and non-image files
        if os.path.isdir(file_path):
            continue

        # Check if it's an image file (you can expand this list)
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            continue

        total_images += 1

        # Extract label from filename
        label = extract_label(filename)
        if not label:
            print(f"❌ Could not extract label from filename: {filename}")
            continue

        # Upload the image
        if upload_image_to_api(file_path, label, api_base_url):
            successful_uploads += 1

    # Print summary
    print("\n==== Upload Summary ====")
    print(f"Total images processed: {total_images}")
    print(f"Successfully uploaded: {successful_uploads}")
    print(f"Failed uploads: {total_images - successful_uploads}")


if __name__ == "__main__":
    main()
