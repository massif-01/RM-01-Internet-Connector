#!/usr/bin/env python3
"""
Generate DMG background image with arrow
"""
from PIL import Image, ImageDraw, ImageFont
import sys

def create_dmg_background(width=800, height=400, output_path='dmg-background.png'):
    # Create white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw arrow from left to right (center)
    arrow_color = (200, 200, 200)  # Light gray
    arrow_y = height // 2
    arrow_start_x = width // 2 - 150
    arrow_end_x = width // 2 + 150
    
    # Draw arrow line
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)], 
              fill=arrow_color, width=3)
    
    # Draw arrow head
    arrow_head_size = 20
    arrow_head = [
        (arrow_end_x, arrow_y),
        (arrow_end_x - arrow_head_size, arrow_y - arrow_head_size//2),
        (arrow_end_x - arrow_head_size, arrow_y + arrow_head_size//2)
    ]
    draw.polygon(arrow_head, fill=arrow_color)
    
    # Try to add text at the bottom
    try:
        font_size = 24
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Add text
    text = "RM-01 Internet Connector"
    subtext = "Your Mac, One-Hand Remote."
    
    # Calculate text position (centered, near bottom)
    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = height - 100
        
        # Draw main text
        draw.text((text_x, text_y), text, fill=(150, 150, 150), font=font)
        
        # Draw subtext
        small_font_size = 16
        try:
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", small_font_size)
        except:
            small_font = font
        
        subtext_bbox = draw.textbbox((0, 0), subtext, font=small_font)
        subtext_width = subtext_bbox[2] - subtext_bbox[0]
        subtext_x = (width - subtext_width) // 2
        subtext_y = text_y + 35
        
        draw.text((subtext_x, subtext_y), subtext, fill=(180, 180, 180), font=small_font)
    except:
        pass  # Skip text if there's any error
    
    # Save image
    img.save(output_path, 'PNG')
    print(f"DMG background created: {output_path}")

if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'dmg-background.png'
    create_dmg_background(output_path=output)







