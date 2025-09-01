import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import json
from datetime import datetime, timedelta
import random

class ApplicationPriseDeNotes:
    def appliquer_theme(self):
        theme = "sombre" if self.theme_sombre else "clair"
        couleurs = self.couleurs[theme]

        self.fenetre_principale.configure(bg=couleurs["fond"])

    def appliquer_couleurs(widget):
        try:
            widget.configure(bg=couleurs["fond"], fg=couleurs["texte"])
        except:
            pass
        for child in widget.winfo_children():
            self.appliquer_couleurs(child)

        appliquer_couleurs(self.fenetre_principale)

        # Appliquer les couleurs aux champs spécifiques
        self.zone_texte.configure(bg=couleurs["fond"], fg=couleurs["texte"], insertbackground=couleurs["texte"])
        self.entree_titre.configure(bg=couleurs["fond"], fg=couleurs["texte"], insertbackground=couleurs["texte"])
        self.entree_recherche.configure(bg=couleurs["fond"], fg=couleurs["texte"], insertbackground=couleurs["texte"])
        self.liste_notes.configure(bg=couleurs["fond"], fg=couleurs["texte"])
        self.liste_rappels.configure(bg=couleurs["fond"], fg=couleurs["texte"])


    def basculer_theme(self):
        self.theme_sombre = not self.theme_sombre
        self.appliquer_theme()
        
        
    def __init__(self):
        # Fenêtre principale
        self.fenetre_principale = tk.Tk()
        self.fenetre_principale.title("StudyHelper - Prise de Notes Intelligente")
        self.fenetre_principale.geometry("1200x800")
        self.fenetre_principale.configure(bg="#f0f0f0")
        self.notes_filtrees = []  # Liste temporaire pour les résultats de recherche

        
        # Variables principales
        self.notes_liste = []
        self.note_actuelle = None
        self.dossier_notes = "mes_notes"
        self.rappels_liste = []
        
        # Créer le dossier de notes si il n'existe pas
        if not os.path.exists(self.dossier_notes):
            os.makedirs(self.dossier_notes)
        
        # Charger les données sauvegardées
        self.charger_donnees()
        
        # Créer l'interface
        self.creer_interface()
        
        # Démarrer les rappels
        self.verifier_rappels()

    def creer_interface(self):
        # Barre de menu principale
        self.barre_menu = tk.Menu(self.fenetre_principale)
        self.fenetre_principale.config(menu=self.barre_menu)
        
        # Menu Thème
        menu_theme = tk.Menu(self.barre_menu, tearoff=0)
        self.barre_menu.add_cascade(label="Thème", menu=menu_theme)
        menu_theme.add_command(label="Basculer Thème", command=self.basculer_theme)

        # Thème par défaut
        self.theme_sombre = False
        self.couleurs = {
            "clair": {
                "fond": "#f5f7fa",
                "texte": "#2c3e50",
                "bouton": "#3498db",
                "bouton_fg": "white"
            },
            "sombre": {
                "fond": "#2c3e50",
                "texte": "#ecf0f1",
                "bouton": "#34495e",
                "bouton_fg": "white"
            }
        }
        self.appliquer_theme()

        # Menu Fichier
        menu_fichier = tk.Menu(self.barre_menu, tearoff=0)
        self.barre_menu.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Nouvelle note", command=self.nouvelle_note)
        menu_fichier.add_command(label="Scanner un document", command=self.scanner_document)
        menu_fichier.add_command(label="Sauvegarder", command=self.sauvegarder_donnees)
        
        # Menu Outils
        menu_outils = tk.Menu(self.barre_menu, tearoff=0)
        self.barre_menu.add_cascade(label="Outils", menu=menu_outils)
        menu_outils.add_command(label="Générer un Quiz", command=self.generer_quiz)
        menu_outils.add_command(label="Créer un Podcast", command=self.creer_podcast)
        menu_outils.add_command(label="Ajouter un Rappel", command=self.ajouter_rappel)
        
        # Cadre principal divisé en 3 parties
        cadre_principal = tk.Frame(self.fenetre_principale, bg="#f0f0f0")
        cadre_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. Panel de gauche - Liste des notes
        self.creer_panel_notes(cadre_principal)
        
        # 2. Panel central - Éditeur de texte
        self.creer_editeur_texte(cadre_principal)
        
        # 3. Panel de droite - Outils IA et fonctions
        self.creer_panel_outils(cadre_principal)

    def programmer_sauvegarde_auto(self):
        self.sauvegarder_donnees()
        self.fenetre_principale.after(self.auto_save_interval, self.programmer_sauvegarde_auto)

    def creer_panel_notes(self, parent):
        # Cadre pour la liste des notes
        cadre_notes = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=1)
        cadre_notes.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        cadre_notes.configure(width=250)
        cadre_notes.pack_propagate(False)
        
        # Champ de recherche
        self.entree_recherche = tk.Entry(cadre_notes, font=("Arial", 10))
        self.entree_recherche.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.entree_recherche.insert(0, "🔍 Rechercher...")
        self.entree_recherche.bind("<KeyRelease>", self.filtrer_notes)
        self.entree_recherche.bind("<FocusIn>", self.effacer_placeholder_recherche)
        self.entree_recherche.bind("<FocusOut>", self.restaurer_placeholder_recherche)

        # Bouton pour effacer la recherche
        btn_effacer = tk.Button(cadre_notes, text="❌ Effacer", font=("Arial", 9),
                                command=self.effacer_recherche, bg="#95a5a6", fg="white")
        btn_effacer.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Titre
        titre_notes = tk.Label(cadre_notes, text="📚 Mes Notes", font=("Arial", 14, "bold"), 
                              bg="white", fg="#2c3e50")
        titre_notes.pack(pady=10)
        
        # Boutons d'action
        cadre_boutons = tk.Frame(cadre_notes, bg="white")
        cadre_boutons.pack(fill=tk.X, padx=10, pady=5)
        
        btn_nouvelle = tk.Button(cadre_boutons, text="+ Nouvelle note", 
                               command=self.nouvelle_note, bg="#3498db", fg="white",
                               font=("Arial", 10))
        btn_nouvelle.pack(fill=tk.X, pady=2)
        
        btn_scanner = tk.Button(cadre_boutons, text="📷 Scanner un document", 
                              command=self.scanner_document, bg="#e74c3c", fg="white",
                              font=("Arial", 10))
        btn_scanner.pack(fill=tk.X, pady=2)
        
        # Liste des notes avec scrollbar
        cadre_liste = tk.Frame(cadre_notes, bg="white")
        cadre_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar_notes = tk.Scrollbar(cadre_liste)
        scrollbar_notes.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.liste_notes = tk.Listbox(cadre_liste, yscrollcommand=scrollbar_notes.set,
                                    font=("Arial", 10), selectmode=tk.SINGLE)
        self.liste_notes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.liste_notes.bind('<<ListboxSelect>>', self.selectionner_note)
        
        scrollbar_notes.config(command=self.liste_notes.yview)
        
        # Mettre à jour la liste
        self.mettre_a_jour_liste_notes()
        
        # Intervalle de sauvegarde automatique (en millisecondes)
        self.auto_save_interval = 300000  # 5 minutes
        self.programmer_sauvegarde_auto()
        
    def filtrer_notes(self, event=None):
        mot_cle = self.entree_recherche.get().lower()
        self.liste_notes.delete(0, tk.END)
        self.notes_filtrees = []  # Réinitialiser la liste filtrée

        for note in self.notes_liste:
            titre = note.get("titre", "").lower()
            contenu = note.get("contenu", "").lower()
            if mot_cle in titre or mot_cle in contenu:
                date_courte = note['date_creation'][:10]
                self.liste_notes.insert(tk.END, f"{note['titre']} ({date_courte})")
                self.notes_filtrees.append(note)

        self.surligner_resultats(mot_cle)

    def surligner_resultats(self, mot_cle):
        self.zone_texte.tag_remove("highlight", "1.0", tk.END)
        if not mot_cle or mot_cle == "🔍 Rechercher...":
            return
        mot_cle = mot_cle.lower()
        contenu = self.zone_texte.get("1.0", tk.END).lower()
        index = "1.0"
        while True:
            index = self.zone_texte.search(mot_cle, index, nocase=1, stopindex=tk.END)
            if not index:
                break
            fin = f"{index}+{len(mot_cle)}c"
            self.zone_texte.tag_add("highlight", index, fin)
            index = fin
        if self.theme_sombre:
            self.zone_texte.tag_config("highlight", background="#ffcc00", foreground="black")
        else:
            self.zone_texte.tag_config("highlight", background="yellow", foreground="black")


    def effacer_placeholder_recherche(self, event):
        if self.entree_recherche.get() == "🔍 Rechercher...":
            self.entree_recherche.delete(0, tk.END)
            self.entree_recherche.config(fg="black")

    def restaurer_placeholder_recherche(self, event):
        if not self.entree_recherche.get():
            self.entree_recherche.insert(0, "🔍 Rechercher...")
            self.entree_recherche.config(fg="gray")

    def effacer_recherche(self):
        self.entree_recherche.delete(0, tk.END)
        self.mettre_a_jour_liste_notes()

    def creer_editeur_texte(self, parent):
        # Cadre principal pour l'éditeur
        cadre_editeur = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=1)
        cadre_editeur.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Barre d'outils de l'éditeur
        barre_outils = tk.Frame(cadre_editeur, bg="#ecf0f1", height=40)
        barre_outils.pack(fill=tk.X, padx=5, pady=5)
        barre_outils.pack_propagate(False)
        
        # Titre de la note
        tk.Label(barre_outils, text="Titre:", bg="#ecf0f1", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entree_titre = tk.Entry(barre_outils, font=("Arial", 12), width=30)
        self.entree_titre.pack(side=tk.LEFT, padx=5)
        
        # Bouton sauvegarder
        btn_sauvegarder = tk.Button(barre_outils, text="💾 Sauvegarder", 
                                  command=self.sauvegarder_note_actuelle, 
                                  bg="#27ae60", fg="white", font=("Arial", 10))
        btn_sauvegarder.pack(side=tk.RIGHT, padx=5)
        
        # Zone de texte principale avec scrollbar
        cadre_texte = tk.Frame(cadre_editeur)
        cadre_texte.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar_texte = tk.Scrollbar(cadre_texte)
        scrollbar_texte.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.zone_texte = tk.Text(cadre_texte, yscrollcommand=scrollbar_texte.set,
                                font=("Arial", 11), wrap=tk.WORD, bg="white")
        self.zone_texte.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_texte.config(command=self.zone_texte.yview)

    def creer_panel_outils(self, parent):
        # Cadre pour les outils IA
        cadre_outils = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=1)
        cadre_outils.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        cadre_outils.configure(width=300)
        cadre_outils.pack_propagate(False)
        
        # Titre
        titre_outils = tk.Label(cadre_outils, text="🤖 Assistant IA", 
                              font=("Arial", 14, "bold"), bg="white", fg="#8e44ad")
        titre_outils.pack(pady=10)
        
        # Boutons d'outils IA
        cadre_boutons_ia = tk.Frame(cadre_outils, bg="white")
        cadre_boutons_ia.pack(fill=tk.X, padx=10, pady=5)
        
        btn_resumer = tk.Button(cadre_boutons_ia, text="📝 Résumer le texte", 
                              command=self.resumer_texte, bg="#9b59b6", fg="white",
                              font=("Arial", 10))
        btn_resumer.pack(fill=tk.X, pady=2)
        
        btn_corriger = tk.Button(cadre_boutons_ia, text="✏️ Corriger l'orthographe", 
                               command=self.corriger_orthographe, bg="#34495e", fg="white",
                               font=("Arial", 10))
        btn_corriger.pack(fill=tk.X, pady=2)
        
        btn_quiz = tk.Button(cadre_boutons_ia, text="❓ Générer un Quiz", 
                           command=self.generer_quiz, bg="#f39c12", fg="white",
                           font=("Arial", 10))
        btn_quiz.pack(fill=tk.X, pady=2)

        btn_podcast = tk.Button(cadre_boutons_ia, text="🎙️ Créer un Podcast", 
                              command=self.creer_podcast, bg="#e67e22", fg="white",
                              font=("Arial", 10))
        btn_podcast.pack(fill=tk.X, pady=2)
        
        # Section Collaboration
        tk.Label(cadre_outils, text="👥 Collaboration", font=("Arial", 12, "bold"), 
                bg="white", fg="#2980b9").pack(pady=(20, 10))
        
        cadre_collab = tk.Frame(cadre_outils, bg="white")
        cadre_collab.pack(fill=tk.X, padx=10)
        
        btn_partager = tk.Button(cadre_collab, text="📤 Partager une note", 
                               command=self.partager_note, bg="#3498db", fg="white",
                               font=("Arial", 10))
        btn_partager.pack(fill=tk.X, pady=2)
        
        btn_importer = tk.Button(cadre_collab, text="📥 Importer une note", 
                               command=self.importer_note, bg="#1abc9c", fg="white",
                               font=("Arial", 10))
        btn_importer.pack(fill=tk.X, pady=2)
        
        # Section Rappels
        tk.Label(cadre_outils, text="⏰ Rappels", font=("Arial", 12, "bold"), 
                bg="white", fg="#e74c3c").pack(pady=(20, 10))
        
        cadre_rappels = tk.Frame(cadre_outils, bg="white")
        cadre_rappels.pack(fill=tk.X, padx=10)
        
        btn_rappel = tk.Button(cadre_rappels, text="+ Ajouter un rappel", 
                             command=self.ajouter_rappel, bg="#e74c3c", fg="white",
                             font=("Arial", 10))
        btn_rappel.pack(fill=tk.X, pady=2)
        
        # Liste des rappels
        self.liste_rappels = tk.Listbox(cadre_rappels, height=4, font=("Arial", 9))
        self.liste_rappels.pack(fill=tk.X, pady=5)
        self.mettre_a_jour_rappels()

    # FONCTIONS PRINCIPALES
            
    def nouvelle_note(self):
        titre = simpledialog.askstring("Nouvelle Note", "Titre de la note:")
        if titre:
            nouvelle_note = {
                'id': len(self.notes_liste) + 1,
                'titre': titre,
                'contenu': '',
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': []
            }
            self.notes_liste.append(nouvelle_note)
            self.mettre_a_jour_liste_notes()
            self.charger_note(nouvelle_note)
            messagebox.showinfo("Succès", f"Note '{titre}' créée avec succès!")

    def scanner_document(self):
        fichier_image = filedialog.askopenfilename(
            title="Sélectionner une image à scanner",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if fichier_image:
            # Simulation du scan et OCR
            texte_scanne = self.simuler_ocr(fichier_image)
            
            titre = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M')}"
            note_scannee = {
                'id': len(self.notes_liste) + 1,
                'titre': titre,
                'contenu': texte_scanne,
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': ['scanné'],
                'image_source': fichier_image
            }
            self.notes_liste.append(note_scannee)
            self.mettre_a_jour_liste_notes()
            self.charger_note(note_scannee)
            messagebox.showinfo("Scanner", f"Document scanné et converti en texte!\nNote: {titre}")

    def simuler_ocr(self, fichier_image):
        # Simulation simple d'OCR (dans un vrai projet, utilisez pytesseract)
        exemples_texte = [
            "Voici le contenu extrait de votre document scanné.\n\nCours de Mathématiques\n- Théorème de Pythagore\n- Équations du second degré\n- Fonctions trigonométriques",
            "Notes de cours - Informatique\n\n1. Algorithmique\n2. Structures de données\n3. Programmation orientée objet\n\nExercices à faire pour la semaine prochaine.",
            "Résumé de lecture\n\nChapitre 1: Introduction\nLes concepts fondamentaux sont...\n\nChapitre 2: Développement\nAnalyse approfondie des éléments..."
        ]
        return random.choice(exemples_texte)

    def selectionner_note(self, event):
        selection = self.liste_notes.curselection()
        if selection:
            index = selection[0]
            if hasattr(self, "notes_filtrees") and self.notes_filtrees:
                note = self.notes_filtrees[index]
            else:
                note = self.notes_liste[index]
            self.charger_note(note)


    def charger_note(self, note):
        self.note_actuelle = note
        self.entree_titre.delete(0, tk.END)
        self.entree_titre.insert(0, note['titre'])
        
        self.zone_texte.delete(1.0, tk.END)
        self.zone_texte.insert(1.0, note['contenu'])

    def sauvegarder_note_actuelle(self):
        if self.note_actuelle:
            self.note_actuelle['titre'] = self.entree_titre.get()
            self.note_actuelle['contenu'] = self.zone_texte.get(1.0, tk.END).strip()
            self.mettre_a_jour_liste_notes()
            self.sauvegarder_donnees()
            messagebox.showinfo("Sauvegarde", "Note sauvegardée avec succès!")

    def mettre_a_jour_liste_notes(self):
        self.liste_notes.delete(0, tk.END)
        for note in self.notes_liste:
            date_courte = note['date_creation'][:10]
            self.liste_notes.insert(tk.END, f"{note['titre']} ({date_courte})")

    # FONCTIONS IA SIMULÉES
    
    def resumer_texte(self):
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée!")
            return
        
        texte = self.zone_texte.get(1.0, tk.END).strip()
        if not texte:
            messagebox.showwarning("Attention", "Aucun texte à résumer!")
            return
        
        # Simulation d'un résumé IA
        mots = texte.split()
        if len(mots) > 50:
            resume = " ".join(mots[:30]) + "...\n\n[RÉSUMÉ IA]\nPoints clés identifiés:\n- Concept principal abordé\n- Éléments importants à retenir\n- Conclusion ou synthèse"
        else:
            resume = f"[RÉSUMÉ IA]\nTexte court détecté. Points principaux:\n{texte[:100]}..."
        
        # Créer une nouvelle note avec le résumé
        titre_resume = f"Résumé - {self.note_actuelle['titre']}"
        note_resume = {
            'id': len(self.notes_liste) + 1,
            'titre': titre_resume,
            'contenu': resume,
            'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'tags': ['résumé', 'IA']
        }
        self.notes_liste.append(note_resume)
        self.mettre_a_jour_liste_notes()
        messagebox.showinfo("Résumé IA", "Résumé généré et sauvegardé!")

    def corriger_orthographe(self):
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée!")
            return
        
        messagebox.showinfo("Correction", "Correction orthographique effectuée!\n(Simulation - dans un vrai projet, intégrez un correcteur comme LanguageTool)")

    def generer_quiz(self):
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée!")
            return
        
        # Simulation de génération de quiz
        questions_quiz = [
            "1. Quel est le concept principal abordé dans cette note?",
            "2. Quels sont les points clés à retenir?",
            "3. Comment peut-on appliquer ces connaissances?",
            "4. Quelles sont les implications de ce sujet?",
            "5. Quelle est votre compréhension personnelle?"
        ]
        
        quiz_texte = f"QUIZ GÉNÉRÉ - {self.note_actuelle['titre']}\n\n"
        quiz_texte += "\n".join(questions_quiz)
        quiz_texte += "\n\n[Généré automatiquement par l'IA StudyHelper]"
        
        # Créer une note quiz
        titre_quiz = f"Quiz - {self.note_actuelle['titre']}"
        note_quiz = {
            'id': len(self.notes_liste) + 1,
            'titre': titre_quiz,
            'contenu': quiz_texte,
            'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'tags': ['quiz', 'IA']
        }
        self.notes_liste.append(note_quiz)
        self.mettre_a_jour_liste_notes()
        messagebox.showinfo("Quiz", "Quiz généré avec succès!")

    def creer_podcast(self):
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée!")
            return
        
        script_podcast = f"""SCRIPT PODCAST - {self.note_actuelle['titre']}

[INTRO MUSICALE]

Bonjour et bienvenue dans ce nouvel épisode de StudyHelper Podcast!
Aujourd'hui, nous allons explorer le sujet: {self.note_actuelle['titre']}

[DÉVELOPPEMENT]
Basé sur vos notes personnelles, voici les points clés:

{self.note_actuelle['contenu'][:200]}...

[CONCLUSION]
Pour résumer cette session d'apprentissage...

[OUTRO]
Merci de nous avoir écoutés! N'oubliez pas de réviser vos notes.

[Durée estimée: 5-10 minutes]
[Généré par StudyHelper IA]"""
        
        # Créer une note podcast
        titre_podcast = f"Podcast - {self.note_actuelle['titre']}"
        note_podcast = {
            'id': len(self.notes_liste) + 1,
            'titre': titre_podcast,
            'contenu': script_podcast,
            'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'tags': ['podcast', 'audio', 'IA']
        }
        self.notes_liste.append(note_podcast)
        self.mettre_a_jour_liste_notes()
        messagebox.showinfo("Podcast", "Script de podcast généré!\n(Dans un vrai projet, ajoutez une synthèse vocale)")

    # FONCTIONS COLLABORATION
    
    def partager_note(self):
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée!")
            return
        
        fichier_partage = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers StudyHelper", "*.json")],
            title="Partager la note"
        )
        
        if fichier_partage:
            try:
                with open(fichier_partage, 'w', encoding='utf-8') as f:
                    json.dump(self.note_actuelle, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Partage", f"Note partagée avec succès!\nFichier: {fichier_partage}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du partage: {str(e)}")

    def importer_note(self):
        fichier_import = filedialog.askopenfilename(
            filetypes=[("Fichiers StudyHelper", "*.json")],
            title="Importer une note"
        )
        
        if fichier_import:
            try:
                with open(fichier_import, 'r', encoding='utf-8') as f:
                    note_importee = json.load(f)
                
                # Assigner un nouvel ID
                note_importee['id'] = len(self.notes_liste) + 1
                note_importee['titre'] += " (importée)"
                
                self.notes_liste.append(note_importee)
                self.mettre_a_jour_liste_notes()
                messagebox.showinfo("Import", "Note importée avec succès!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import: {str(e)}")

    # SYSTÈME DE RAPPELS
    
    def ajouter_rappel(self):
        titre_rappel = simpledialog.askstring("Rappel", "Titre du rappel:")
        if not titre_rappel:
            return
        
        date_rappel = simpledialog.askstring("Rappel", "Date (YYYY-MM-DD) ou 'demain':")
        if not date_rappel:
            return
        
        if date_rappel.lower() == 'demain':
            date_rappel = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        nouveau_rappel = {
            'titre': titre_rappel,
            'date': date_rappel,
            'actif': True
        }
        
        self.rappels_liste.append(nouveau_rappel)
        self.mettre_a_jour_rappels()
        self.sauvegarder_donnees()
        messagebox.showinfo("Rappel", f"Rappel ajouté pour le {date_rappel}")

    def mettre_a_jour_rappels(self):
        self.liste_rappels.delete(0, tk.END)
        for rappel in self.rappels_liste:
            if rappel['actif']:
                self.liste_rappels.insert(tk.END, f"{rappel['titre']} - {rappel['date']}")

    def verifier_rappels(self):
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        for rappel in self.rappels_liste:
            if rappel['actif'] and rappel['date'] == aujourd_hui:
                messagebox.showinfo("⏰ Rappel", f"Rappel: {rappel['titre']}")
                rappel['actif'] = False
        
        # Programmer la prochaine vérification dans 1 heure
        self.fenetre_principale.after(3600000, self.verifier_rappels)

    # SAUVEGARDE ET CHARGEMENT
    
    def sauvegarder_donnees(self):
        donnees = {
            'notes': self.notes_liste,
            'rappels': self.rappels_liste
        }
        
        try:
            with open(os.path.join(self.dossier_notes, 'donnees.json'), 'w', encoding='utf-8') as f:
                json.dump(donnees, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def charger_donnees(self):
        fichier_donnees = os.path.join(self.dossier_notes, 'donnees.json')
        if os.path.exists(fichier_donnees):
            try:
                with open(fichier_donnees, 'r', encoding='utf-8') as f:
                    donnees = json.load(f)
                self.notes_liste = donnees.get('notes', [])
                self.rappels_liste = donnees.get('rappels', [])
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")

    def demarrer(self):
        self.fenetre_principale.mainloop()
        
   # LANCEMENT DE L'APPLICATION
if __name__ == "__main__":
    app = ApplicationPriseDeNotes()
    app.demarrer()