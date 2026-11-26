import subprocess
import re
import undetected_chromedriver as uc


def get_chrome_version_windows():
    try:
        # Commande pour interroger le registre Windows
        cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
        output = subprocess.check_output(cmd, shell=True).decode()
        version = re.search(r'REG_SZ\s+([\d.]+)', output)
        return version.group(1) if version else "Version non trouvée"
    except Exception as e:
        return f"Erreur : {e}"



def init_driver(chrome_version=None):
    """
    Initialise et retourne un navigateur undetected_chromedriver configuré
    avec les en-têtes HTTP personnalisés (ex: langue française).
    """

    options = uc.ChromeOptions()

    # Lancement du driver
    driver = uc.Chrome(options=options, version_main=int(chrome_version.split(".")[0]), use_subprocess=True)
    # Activation du protocole CDP (Chrome DevTools Protocol)
    driver.execute_cdp_cmd("Network.enable", {})

    # Configuration des headers personnalisés
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Accept-Language": "en-US,en;q=0.9"
        }
    })

    return driver


