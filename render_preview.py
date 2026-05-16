import jinja2
import os

def render_preview():
    # Setup Jinja2
    template_dir = os.path.abspath("app/templates")
    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader)
    
    # Load template
    template = env.get_template("campana.html")
    
    # Render with dummy data
    html_content = template.render(
        nombre="Smartphone X Pro",
        descripcion="El futuro en tus manos. Diseño minimalista, potencia sin precedentes y una cámara que redefine la fotografía móvil. Oferta limitada por lanzamiento.",
        id_click=999
    )
    
    # Fix static paths for local preview (relative to where we save the file)
    # The image is in app/static/premium_product_mockup.png
    # If we save preview.html in the root, /static/ becomes app/static/
    html_content = html_content.replace('src="/static/', 'src="app/static/')
    
    # Save to file
    preview_path = os.path.abspath("preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Preview saved to: {preview_path}")

if __name__ == "__main__":
    render_preview()
