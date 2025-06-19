"""
Script principal pour contrôler un oscilloscope et un générateur de fonctions via TCP/IP (SCPI).
Connexion type PuTTY (telnet/SSH).
"""

import socket
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

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
        self.mode = tk.StringVar(value="both")  # both, oscillo, gen
        self.load_ips()
        self.build_mode_selector()
        self.build_gui()

    def build_mode_selector(self):
        top = tk.Toplevel(self.root)
        top.title("Choix du mode de pilotage")
        tk.Label(top, text="Que voulez-vous piloter ?").pack(padx=10, pady=5)
        tk.Radiobutton(top, text="Oscilloscope et Générateur", variable=self.mode, value="both").pack(anchor="w", padx=10)
        tk.Radiobutton(top, text="Oscilloscope seulement", variable=self.mode, value="oscillo").pack(anchor="w", padx=10)
        tk.Radiobutton(top, text="Générateur seulement", variable=self.mode, value="gen").pack(anchor="w", padx=10)
        tk.Button(top, text="Valider", command=top.destroy).pack(pady=10)
        self.root.wait_window(top)

    def build_gui(self):
        frm = tk.Frame(self.root)
        frm.pack(padx=10, pady=10)
        row = 0
        if self.mode.get() in ("both", "oscillo"):
            tk.Label(frm, text="IP Oscilloscope:").grid(row=row, column=0)
            tk.Entry(frm, textvariable=self.oscillo_ip).grid(row=row, column=1)
            row += 1
        if self.mode.get() in ("both", "gen"):
            tk.Label(frm, text="IP Générateur:").grid(row=row, column=0)
            tk.Entry(frm, textvariable=self.gen_ip).grid(row=row, column=1)
            row += 1
        tk.Button(frm, text="Connecter", command=self.connect).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        tk.Button(frm, text="Sauvegarder les adresses", command=self.save_ips).grid(row=row, column=0, columnspan=2, pady=2)
        row += 1
        if self.mode.get() in ("both", "oscillo"):
            tk.Button(frm, text="Identifier Oscillo", command=lambda:self.identify(instr="oscillo")).grid(row=row, column=0, columnspan=2, sticky="ew")
            row += 1
            tk.Button(frm, text="Configurer canal oscillo", command=self.config_oscillo).grid(row=row, column=0, columnspan=2, sticky="ew")
            row += 1
            tk.Button(frm, text="Acquérir et afficher la courbe", command=self.acquire_and_plot).grid(row=row, column=0, columnspan=2, sticky="ew")
            row += 1
        if self.mode.get() in ("both", "gen"):
            tk.Button(frm, text="Identifier Générateur", command=lambda:self.identify(instr="gen")).grid(row=row, column=0, columnspan=2, sticky="ew")
            row += 1
            tk.Button(frm, text="Configurer canal générateur", command=self.config_gen).grid(row=row, column=0, columnspan=2, sticky="ew")
            row += 1
        tk.Button(frm, text="Commande SCPI personnalisée", command=self.scpi_custom).grid(row=row, column=0, columnspan=2, sticky="ew")

    def acquire_and_plot(self):
        if not self.oscillo:
            messagebox.showwarning("Non connecté", "Connectez d'abord l'oscilloscope.")
            return
        try:
            # Demander le canal à l'utilisateur
            ch = simpledialog.askstring("Canal", "Numéro de canal à acquérir (ex: 1) :", parent=self.root) or "1"
            # Configurer le format ASCII et le canal
            self.oscillo.send(":WAV:FORM ASCii")
            self.oscillo.send(f":WAV:SOUR CHAN{ch}")
            # Demander le nombre de points (ex: 1000 pour rapidité)
            self.oscillo.send(":WAV:POIN:MODE RAW")
            self.oscillo.send(":WAV:POIN 1000")
            # Envoyer la requête et lire toute la réponse
            self.oscillo.send(":WAV:DATA?")
            data = b""
            while True:
                part = self.oscillo.sock.recv(4096)
                data += part
                if len(part) < 4096:
                    break
            data_str = data.decode(errors="ignore")
            # Nettoyer la réponse (enlever entête, etc.)
            if "\n" in data_str:
                data_str = data_str.split("\n",1)[-1]
            y = [float(val) for val in data_str.replace("\n","").split(",") if val.strip()]
            if not y:
                messagebox.showerror("Erreur acquisition", "Aucune donnée reçue.")
                return
            # Normalisation pour affichage Canvas
            width, height = 800, 300
            min_y, max_y = min(y), max(y)
            scale = (height-20) / (max_y - min_y) if max_y != min_y else 1
            points = []
            for i, v in enumerate(y):
                x = int(i * width / (len(y)-1))
                y_canvas = height - 10 - int((v - min_y) * scale)
                points.append((x, y_canvas))
            # Création fenêtre et Canvas
            win = tk.Toplevel(self.root)
            win.title(f"Courbe CH{ch} (RTB2004)")
            canvas = tk.Canvas(win, width=width, height=height, bg="white")
            canvas.pack()
            for i in range(1, len(points)):
                canvas.create_line(points[i-1][0], points[i-1][1], points[i][0], points[i][1], fill="blue")
        except Exception as e:
            messagebox.showerror("Erreur acquisition", str(e))

    def save_ips(self):
        data = {"oscillo_ip": self.oscillo_ip.get(), "gen_ip": self.gen_ip.get(), "mode": self.mode.get()}
        try:
            with open("scpi_ips.json", "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Sauvegarde", "Adresses IP sauvegardées !")
        except Exception as e:
            messagebox.showerror("Erreur sauvegarde", str(e))

    def connect(self):
        try:
            if self.oscillo: self.oscillo.close()
            if self.gen: self.gen.close()
            if self.mode.get() in ("both", "oscillo"):
                self.oscillo = SCPIInstrument(self.oscillo_ip.get())
                self.oscillo.connect()
            else:
                self.oscillo = None
            if self.mode.get() in ("both", "gen"):
                self.gen = SCPIInstrument(self.gen_ip.get())
                self.gen.connect()
            else:
                self.gen = None
            messagebox.showinfo("Connexion", "Connexion réussie !")
        except Exception as e:
            messagebox.showerror("Erreur connexion", str(e))

    def identify(self, instr=None):
        try:
            if instr == "oscillo":
                osc_id = self.oscillo.query("*IDN?") if self.oscillo else "Non connecté"
                messagebox.showinfo("Identification", f"Oscilloscope: {osc_id}")
            elif instr == "gen":
                gen_id = self.gen.query("*IDN?") if self.gen else "Non connecté"
                messagebox.showinfo("Identification", f"Générateur: {gen_id}")
            else:
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
        cible = None
        if self.mode.get() == "both":
            cible = simpledialog.askstring("Instrument", "Sur quel instrument ? (oscillo/gen) :")
        elif self.mode.get() == "oscillo":
            cible = "oscillo"
        elif self.mode.get() == "gen":
            cible = "gen"
        instr = self.oscillo if cible and cible.lower().startswith("o") else self.gen
        cmd = simpledialog.askstring("Commande SCPI", "Commande à envoyer :")
        try:
            rep = instr.query(cmd)
            messagebox.showinfo("Réponse", rep)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def load_ips(self):
        if os.path.exists("scpi_ips.json"):
            try:
                with open("scpi_ips.json", "r") as f:
                    data = json.load(f)
                self.oscillo_ip.set(data.get("oscillo_ip", "192.168.0.10"))
                self.gen_ip.set(data.get("gen_ip", "192.168.0.11"))
                self.mode.set(data.get("mode", "both"))
            except Exception:
                pass

# Exemple d’utilisation
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("Que voulez-vous piloter ?")
        print("1. Oscilloscope et Générateur")
        print("2. Oscilloscope seulement")
        print("3. Générateur seulement")
        mode = input("Choix : ")
        use_oscillo = mode in ("1", "2")
        use_gen = mode in ("1", "3")
        oscillo = gen = None
        if use_oscillo:
            oscillo_ip = input("Entrer l'adresse IP de l'oscilloscope : ") or "192.168.0.10"
            oscillo = SCPIInstrument(oscillo_ip)
        if use_gen:
            gen_ip = input("Entrer l'adresse IP du générateur de fonctions : ") or "192.168.0.11"
            gen = SCPIInstrument(gen_ip)
        try:
            if use_oscillo:
                oscillo.connect()
            if use_gen:
                gen.connect()
            while True:
                print("\n--- Contrôle SCPI Instruments ---")
                if use_oscillo:
                    print("1. Identifier l'oscilloscope")
                    print("2. Configurer un canal oscilloscope")
                if use_gen:
                    print("3. Identifier le générateur")
                    print("4. Configurer un canal générateur")
                print("5. Envoyer une commande SCPI personnalisée")
                print("6. Modifier l'adresse IP d'un instrument")
                print("0. Quitter")
                choix = input("Choix : ")
                if choix == "1" and use_oscillo:
                    print("Oscilloscope ID:", oscillo.query("*IDN?"))
                elif choix == "2" and use_oscillo:
                    config_oscilloscope(oscillo)
                elif choix == "3" and use_gen:
                    print("Générateur ID:", gen.query("*IDN?"))
                elif choix == "4" and use_gen:
                    config_generateur(gen)
                elif choix == "5":
                    cible = None
                    if use_oscillo and use_gen:
                        cible = input("Sur quel instrument ? (oscillo/gen) : ")
                    elif use_oscillo:
                        cible = "oscillo"
                    elif use_gen:
                        cible = "gen"
                    instr = oscillo if cible and cible.lower().startswith("o") else gen
                    scpi_custom(instr)
                elif choix == "6":
                    cible = input("Quel instrument ? (oscillo/gen) : ")
                    new_ip = input("Nouvelle adresse IP : ")
                    if cible.lower().startswith("o") and use_oscillo:
                        oscillo.close()
                        oscillo = SCPIInstrument(new_ip)
                        oscillo.connect()
                        print("IP oscilloscope modifiée.")
                    elif use_gen:
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
            if use_oscillo and oscillo:
                oscillo.close()
            if use_gen and gen:
                gen.close()
    else:
        root = tk.Tk()
        app = SCPIApp(root)
        root.mainloop()
