# SCPI_COMMANDS

Script Python pour contrôler un oscilloscope et un générateur de fonctions via TCP/IP (SCPI).

## Fonctionnalités
- Connexion à des instruments via TCP/IP (type PuTTY/telnet)
- Envoi et lecture de commandes SCPI
- Structure extensible pour ajouter la configuration des canaux

## Utilisation
1. Modifiez les adresses IP dans `main.py` selon vos instruments.
2. Lancez le script :
   ```powershell
   python main.py
   ```

## À faire
- Ajouter la configuration facile des canaux oscilloscope et générateur
- Interface CLI plus conviviale
