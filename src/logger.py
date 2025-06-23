import logging

# Crear el logger y configurarlo
logger = logging.getLogger("SAIP Logger")
logger.setLevel(logging.DEBUG)

# Formato
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler de consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Evitar duplicar handlers si ya existen
if not logger.handlers:
    logger.addHandler(console_handler)