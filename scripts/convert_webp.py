import os
import re
from PIL import Image

def main():
    root = '/Users/robertsugarman-warner/Downloads/The-One-Club-clone'
    img_dir = os.path.join(root, 'images')
    
    converted_files = set()
    
    print("Converting images...")
    for dirpath, dirnames, filenames in os.walk(img_dir):
        if 'uk-sold' in dirpath:
            continue
        for file in filenames:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(dirpath, file)
                name, ext = os.path.splitext(file)
                webp_name = name + '.webp'
                webp_path = os.path.join(dirpath, webp_name)
                
                try:
                    with Image.open(filepath) as img:
                        img.save(webp_path, 'webp', quality=95)
                    rel_orig = os.path.relpath(filepath, root)
                    rel_webp = os.path.relpath(webp_path, root)
                    # We store the base filename without extension to do regex replace later
                    converted_files.add(name)
                    print(f"Converted {rel_orig} to {rel_webp}")
                except Exception as e:
                    print(f"Error converting {filepath}: {e}")
    
    print("Updating HTML, CSS, and JS files...")
    # Now update references in the codebase
    extensions = ('.html', '.css', '.js', '.py')
    for dirpath, dirnames, filenames in os.walk(root):
        if '.git' in dirpath or 'agents' in dirpath or 'images' in dirpath:
            continue
        for file in filenames:
            if file.endswith(extensions):
                filepath = os.path.join(dirpath, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    orig_content = content
                    # Simple regex replace for paths in /images/...
                    # It's safer to just replace .jpg and .png with .webp for the files we converted
                    for name in converted_files:
                        content = re.sub(rf'({name})\.jpg\b', r'\1.webp', content, flags=re.IGNORECASE)
                        content = re.sub(rf'({name})\.png\b', r'\1.webp', content, flags=re.IGNORECASE)
                        content = re.sub(rf'({name})\.jpeg\b', r'\1.webp', content, flags=re.IGNORECASE)
                        
                    if content != orig_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Updated references in {os.path.relpath(filepath, root)}")
                except Exception as e:
                    # Some files might not be text
                    pass

if __name__ == "__main__":
    main()
