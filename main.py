"""
Script principal pour contrôler un oscilloscope et un générateur de fonctions via TCP/IP (SCPI).
Connexion type PuTTY (telnet/SSH).
"""

import socket
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox

# Classe de base pour les instruments SCPI
class SCPIInstrument:
    def __init__(self, ip, port  =5025):
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

class SCPIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCPI Instruments GUI")
        self.oscillo_ip = tk.StringVar(value="192.168.0.10")
        self.gen_ip = tk.StringVar(value="192.168.0.11")
        self.oscillo = None
        self.gen = None
        self.build_gui()

    def build_gui(self):
        frm = tk.Frame(self.root)
        frm.pack(padx=10, pady=10)
        tk.Label(frm, text="IP Oscilloscope:").grid(row=0, column=0)
        tk.Entry(frm, textvariable=self.oscillo_ip).grid(row=0, column=1)
        tk.Label(frm, text="IP Générateur:").grid(row=1, column=0)
        tk.Entry(frm, textvariable=self.gen_ip).grid(row=1, column=1)
        tk.Button(frm, text="Connecter", command=self.connect).grid(row=2, column=0, columnspan=2, pady=5)
        tk.Button(frm, text="Identifier", command=self.identify).grid(row=3, column=0, columnspan=2, sticky="ew")
        tk.Button(frm, text="Configurer canal oscillo", command=self.config_oscillo).grid(row=4, column=0, columnspan=2, sticky="ew")
        tk.Button(frm, text="Configurer canal générateur", command=self.config_gen).grid(row=5, column=0, columnspan=2, sticky="ew")
        tk.Button(frm, text="Commande SCPI personnalisée", command=self.scpi_custom).grid(row=6, column=0, columnspan=2, sticky="ew")

    def connect(self):
        try:
            if self.oscillo: self.oscillo.close()
            if self.gen: self.gen.close()
            self.oscillo = SCPIInstrument(self.oscillo_ip.get())
            self.gen = SCPIInstrument(self.gen_ip.get())
            self.oscillo.connect()
            self.gen.connect()
            messagebox.showinfo("Connexion", "Connexion réussie !")
        except Exception as e:
            messagebox.showerror("Erreur connexion", str(e))

    def identify(self):
        try:
            osc_id = self.oscillo.query("*IDN?") if self.oscillo else "Non connecté"
            gen_id = self.gen.query("*IDN?") if self.gen else "Non connecté"
            messagebox.showinfo("Identification", f"Oscilloscope: {osc_id}\nGénérateur: {gen_id}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def config_oscillo(self):
        if not self.oscillo:
            messagebox.showwarning("Non connecté", "Connectez d'abord l'oscilloscope.")
            return
        ch = simpledialog.askstring("Canal", "Numéro de canal :")
        vdiv = simpledialog.askstring("Volts/div", "Volts/div :")
        tdiv = simpledialog.askstring("Temps/div", "Temps/div :")
        try:
            self.oscillo.send(f":CHAN{ch}:SCAL {vdiv}")
            self.oscillo.send(f":TIM:SCAL {tdiv}")
            messagebox.showinfo("Succès", f"Canal {ch} configuré : {vdiv} V/div, {tdiv} s/div")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def config_gen(self):
        if not self.gen:
            messagebox.showwarning("Non connecté", "Connectez d'abord le générateur.")
            return
        ch = simpledialog.askstring("Canal", "Numéro de canal :")
        freq = simpledialog.askstring("Fréquence", "Fréquence (Hz) :")
        ampl = simpledialog.askstring("Amplitude", "Amplitude (Vpp) :")
        forme = simpledialog.askstring("Forme", "Forme d’onde (SIN, SQU, RAMP, etc.) :")
        try:
            self.gen.send(f":SOUR{ch}:FUNC {forme}")
            self.gen.send(f":SOUR{ch}:FREQ {freq}")
            self.gen.send(f":SOUR{ch}:VOLT {ampl}")
            messagebox.showinfo("Succès", f"Générateur canal {ch} configuré : {forme}, {freq} Hz, {ampl} Vpp")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def scpi_custom(self):
        cible = simpledialog.askstring("Instrument", "Sur quel instrument ? (oscillo/gen) :")
        instr = self.oscillo if cible and cible.lower().startswith("o") else self.gen
        cmd = simpledialog.askstring("Commande SCPI", "Commande à envoyer :")
        try:
            rep = instr.query(cmd)
            messagebox.showinfo("Réponse", rep)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

# Exemple d’utilisation
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
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
    else:
        root = tk.Tk()
        app = SCPIApp(root)
        root.mainloop()
