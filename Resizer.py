import sys
import subprocess

def install_and_upgrade():
    print("Starting pip upgrade and Pillow installation...")

    # Upgrade pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("Successfully upgraded pip")
    except subprocess.CalledProcessError:
        print("Failed to upgrade pip")
        return False

    # Install Pillow
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("Successfully installed Pillow")
    except subprocess.CalledProcessError:
        print("Failed to install Pillow")
        return False

    return True

def resize_image():
    try:
        from PIL import Image

        # Open the image
        img = Image.open('grass.png')

        # Resize to 64x64 with antialiasing
        resized_img = img.resize((64, 64), Image.Resampling.LANCZOS)

        # Save the resized image
        resized_img.save('grass.png')
        print("Successfully resized image to 64x64")
        return True
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        return False

def main():
    if install_and_upgrade():
        # After successful installation, try to resize the image
        if resize_image():
            print("All operations completed successfully")
        else:
            print("Image resize failed")
    else:
        print("Installation/upgrade failed")

if __name__ == "__main__":
    main()
