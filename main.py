"""
Script principal pour contrôler un oscilloscope et un générateur de fonctions via TCP/IP (SCPI).
Connexion type PuTTY (telnet/SSH).
"""

import socket
import sys

# Classe de base pour les instruments SCPI
class SCPIInstrument:
    def __init__(self, ip, port=5025):
        self.ip = ip
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.ip, self.port), timeout=5)

    def send(self, command):
        if self.sock:
            self.sock.sendall((command + '\n').encode())

    def query(self, command):
        self.send(command)
        return self.sock.recv(4096).decode().strip()

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

def menu():
    print("\n--- Contrôle SCPI Instruments ---")
    print("1. Identifier les instruments")
    print("2. Configurer un canal oscilloscope")
    print("3. Configurer un canal générateur de fonctions")
    print("4. Envoyer une commande SCPI personnalisée")
    print("5. Modifier l'adresse IP d'un instrument")
    print("0. Quitter")
    return input("Choix : ")

def config_oscilloscope(oscillo):
    ch = input("Numéro de canal à configurer (ex: 1) : ")
    vdiv = input("Volts/div (ex: 0.5) : ")
    tdiv = input("Temps/div (ex: 0.001) : ")
    oscillo.send(f":CHAN{ch}:SCAL {vdiv}")
    oscillo.send(f":TIM:SCAL {tdiv}")
    print(f"Canal {ch} configuré : {vdiv} V/div, {tdiv} s/div")

def config_generateur(gen):
    ch = input("Numéro de canal à configurer (ex: 1) : ")
    freq = input("Fréquence (Hz) : ")
    ampl = input("Amplitude (Vpp) : ")
    forme = input("Forme d’onde (SIN, SQU, RAMP, etc.) : ")
    gen.send(f":SOUR{ch}:FUNC {forme}")
    gen.send(f":SOUR{ch}:FREQ {freq}")
    gen.send(f":SOUR{ch}:VOLT {ampl}")
    print(f"Générateur canal {ch} configuré : {forme}, {freq} Hz, {ampl} Vpp")

def scpi_custom(instr):
    cmd = input("Commande SCPI à envoyer : ")
    print("Réponse :", instr.query(cmd))

# Exemple d’utilisation
if __name__ == "__main__":
    oscillo_ip = input("Entrer l'adresse IP de l'oscilloscope : ") or "192.168.0.10"
    gen_ip = input("Entrer l'adresse IP du générateur de fonctions : ") or "192.168.0.11"
    oscillo = SCPIInstrument(oscillo_ip)
    gen = SCPIInstrument(gen_ip)
    try:
        oscillo.connect()
        gen.connect()
        while True:
            choix = menu()
            if choix == "1":
                print("Oscilloscope ID:", oscillo.query("*IDN?"))
                print("Générateur ID:", gen.query("*IDN?"))
            elif choix == "2":
                config_oscilloscope(oscillo)
            elif choix == "3":
                config_generateur(gen)
            elif choix == "4":
                cible = input("Sur quel instrument ? (oscillo/gen) : ")
                instr = oscillo if cible.lower().startswith("o") else gen
                scpi_custom(instr)
            elif choix == "5":
                cible = input("Quel instrument ? (oscillo/gen) : ")
                new_ip = input("Nouvelle adresse IP : ")
                if cible.lower().startswith("o"):
                    oscillo.close()
                    oscillo = SCPIInstrument(new_ip)
                    oscillo.connect()
                    print("IP oscilloscope modifiée.")
                else:
                    gen.close()
                    gen = SCPIInstrument(new_ip)
                    gen.connect()
                    print("IP générateur modifiée.")
            elif choix == "0":
                print("Fermeture...")
                break
            else:
                print("Choix invalide.")
    except Exception as e:
        print("Erreur :", e)
    finally:
        oscillo.close()
        gen.close()
