from PIL import Image

# Load the LeatherTek logo
img = Image.open('leathertech-logo.png')

# Convert to RGB if needed (ICO doesn't support RGBA well)
if img.mode == 'RGBA':
    # Create white background
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
    img = background
elif img.mode != 'RGB':
    img = img.convert('RGB')

# Save as ICO with multiple sizes (for better quality at different resolutions)
img.save('leathertek.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])

print("Icon created successfully: leathertek.ico")
