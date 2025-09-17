import asyncio
import sys
import os

def check_dependencies():
    missing_deps = []
    
    try:
        import playwright
        print("✅ Playwright: Instalado")
    except ImportError:
        print("❌ Playwright no está instalado")
        missing_deps.append("playwright")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv: Instalado") 
    except ImportError:
        print("❌ python-dotenv no está instalado")
        missing_deps.append("python-dotenv")
    
    try:
        import requests
        print("✅ requests: Instalado")
    except ImportError:
        print("❌ requests no está instalado") 
        missing_deps.append("requests")
    
    if missing_deps:
        print(f"\n💡 Para instalar: pip install {' '.join(missing_deps)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando Roulette Scraper con Playwright...")
    print("=" * 50)
    
    if not check_dependencies():
        print("\n❌ Faltan dependencias.")
        sys.exit(1)
    
    if not os.path.exists("roulette_scraper_playwright.py"):
        print("❌ Error: No se encuentra roulette_scraper_playwright.py")
        sys.exit(1)
    
    try:
        from roulette_scraper_playwright import main
        print("✅ Archivo principal: Cargado")
        print("🎯 Iniciando...")
        asyncio.run(main())
    except ImportError as e:
        print(f"❌ Error importando: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario")
    except Exception as e:
        print(f"\n💥 Error: {e}")