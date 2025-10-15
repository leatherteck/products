from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 image with transparent background
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Colors - Red and white (matching LeatherTek branding)
red = (220, 38, 38)  # Red from logo
white = (255, 255, 255)
dark_bg = (26, 26, 26)  # Dark background

# Draw dark circular background
circle_margin = 10
draw.ellipse([circle_margin, circle_margin, size-circle_margin, size-circle_margin],
             fill=dark_bg)

# Draw stylized "LT" letters in the center
try:
    # Try to use a nice font
    font_size = 120
    font = ImageFont.truetype("arial.ttf", font_size)
except:
    # Fallback to default font
    font = ImageFont.load_default()

# Draw "L" in white
text = "L"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x1 = (size // 2) - text_width - 10
y1 = (size - text_height) // 2
draw.text((x1, y1), text, fill=white, font=font)

# Draw "T" in red
text = "T"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
x2 = (size // 2) + 10
draw.text((x2, y1), text, fill=red, font=font)

# Save as PNG first
img.save('leathertek_icon.png')

# Convert to ICO with multiple sizes
img.save('leathertek.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])

print("Simple icon created successfully!")
print("- leathertek_icon.png (preview)")
print("- leathertek.ico (for application)")
