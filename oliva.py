import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import json
from datetime import datetime, timedelta
import random
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

class ApplicationPriseDeNotes:
    def __init__(self):
        # Configuration API
        self.api_key = ""  # Mettez votre clé API Hugging Face ici
        
        # Configuration Email (nouvelles variables)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',
            'password': ''
        }
        
        # NOUVELLES VARIABLES POUR LE SUIVI D'ÉVOLUTION
        self.matieres = {}  # {nom_matiere: {notes_ids: [], temps_total: 0, progression: {}}}
        self.sessions_etude = []  # [{'date', 'matiere', 'duree', 'activite', 'note_id'}]
        self.statistiques = {}  # Stats globales et par matière
        self.session_actuelle = None  # Session en cours
        self.temps_debut_session = None
        
        # Fenêtre principale
        self.fenetre_principale = tk.Tk()
        self.fenetre_principale.title("StudyHelper - Prise de Notes Intelligente")
        self.fenetre_principale.geometry("1400x900")  # Plus large pour les stats
        
        # Variables principales
        self.notes_liste = []
        self.note_actuelle = None
        self.dossier_notes = "mes_notes"
        self.rappels_liste = []
        self.notes_filtrees = []
        
        # Configuration des couleurs et thème
        self.theme_sombre = False
        self.couleurs = {
            "clair": {
                "fond": "#f5f7fa",
                "fond_widget": "#ffffff",
                "texte": "#2c3e50",
                "bouton": "#3498db",
                "bouton_fg": "#ffffff"
            },
            "sombre": {
                "fond": "#2c3e50",
                "fond_widget": "#34495e",
                "texte": "#ecf0f1",
                "bouton": "#3498db",
                "bouton_fg": "#ffffff"
            }
        }
        
        # Créer le dossier de notes
        if not os.path.exists(self.dossier_notes):
            os.makedirs(self.dossier_notes)
        
        # Charger les données
        self.charger_donnees()
        
        # Créer l'interface
        self.creer_interface()
        
        # Démarrer les rappels et sauvegarde auto
        self.verifier_rappels()
        self.auto_save_interval = 300000  # 5 minutes
        self.programmer_sauvegarde_auto()

    # NOUVELLES FONCTIONS POUR SUPPRIMER ET MODIFIER LES NOTES

    def supprimer_note_actuelle(self):
        """Supprime la note actuellement sélectionnée"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée à supprimer!")
            return
        
        # Demander confirmation
        confirmation = messagebox.askyesno(
            "Confirmer la suppression", 
            f"Êtes-vous sûr de vouloir supprimer la note '{self.note_actuelle['titre']}'?\n\nCette action est irréversible."
        )
        
        if confirmation:
            # Supprimer la note de la liste
            self.notes_liste = [note for note in self.notes_liste if note['id'] != self.note_actuelle['id']]
            
            # Réassigner les IDs pour éviter les gaps
            for i, note in enumerate(self.notes_liste):
                note['id'] = i + 1
            
            # Nettoyer l'interface
            self.entree_titre.delete(0, tk.END)
            self.zone_texte.delete(1.0, tk.END)
            self.note_actuelle = None
            
            # Mettre à jour l'affichage
            self.mettre_a_jour_liste_notes()
            self.sauvegarder_donnees()
            
            messagebox.showinfo("Suppression", "Note supprimée avec succès!")

    def ouvrir_editeur_note(self):
        """Ouvre une fenêtre d'édition dédiée pour la note actuelle"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée à modifier!")
            return
        
        # Créer la fenêtre d'édition
        self.fenetre_edition = tk.Toplevel(self.fenetre_principale)
        self.fenetre_edition.title(f"Modifier: {self.note_actuelle['titre']}")
        self.fenetre_edition.geometry("800x600")
        self.fenetre_edition.configure(bg="#f8f9fa")
        
        # Titre
        tk.Label(self.fenetre_edition, text="✏️ Modification de note", 
                font=("Arial", 16, "bold"), bg="#f8f9fa").pack(pady=15)
        
        # Champ titre
        frame_titre = tk.Frame(self.fenetre_edition, bg="#f8f9fa")
        frame_titre.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_titre, text="Titre:", font=("Arial", 12, "bold"), bg="#f8f9fa").pack(anchor="w")
        self.entree_titre_edition = tk.Entry(frame_titre, font=("Arial", 12), width=50)
        self.entree_titre_edition.pack(fill=tk.X, pady=5)
        self.entree_titre_edition.insert(0, self.note_actuelle['titre'])
        
        # Champ contenu
        frame_contenu = tk.Frame(self.fenetre_edition, bg="#f8f9fa")
        frame_contenu.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame_contenu, text="Contenu:", font=("Arial", 12, "bold"), bg="#f8f9fa").pack(anchor="w")
        
        # Zone de texte avec scrollbar
        frame_texte = tk.Frame(frame_contenu)
        frame_texte.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_edition = tk.Scrollbar(frame_texte)
        scrollbar_edition.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.zone_texte_edition = tk.Text(frame_texte, yscrollcommand=scrollbar_edition.set,
                                        font=("Arial", 11), wrap=tk.WORD)
        self.zone_texte_edition.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_edition.config(command=self.zone_texte_edition.yview)
        
        # Insérer le contenu actuel
        self.zone_texte_edition.insert(1.0, self.note_actuelle['contenu'])
        
        # Tags (optionnel)
        frame_tags = tk.Frame(self.fenetre_edition, bg="#f8f9fa")
        frame_tags.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_tags, text="Tags (séparés par des virgules):", font=("Arial", 12, "bold"), bg="#f8f9fa").pack(anchor="w")
        self.entree_tags_edition = tk.Entry(frame_tags, font=("Arial", 10), width=50)
        self.entree_tags_edition.pack(fill=tk.X, pady=5)
        
        # Afficher les tags actuels
        tags_actuels = ", ".join(self.note_actuelle.get('tags', []))
        self.entree_tags_edition.insert(0, tags_actuels)
        
        # Boutons
        frame_boutons = tk.Frame(self.fenetre_edition, bg="#f8f9fa")
        frame_boutons.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(frame_boutons, text="💾 Sauvegarder", command=self.sauvegarder_modifications,
                 bg="#27ae60", fg="white", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_boutons, text="🔄 Annuler", command=self.fenetre_edition.destroy,
                 bg="#e74c3c", fg="white", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_boutons, text="👁️ Aperçu", command=self.apercu_note,
                 bg="#3498db", fg="white", font=("Arial", 11)).pack(side=tk.RIGHT, padx=5)

    def sauvegarder_modifications(self):
        """Sauvegarde les modifications de la note"""
        nouveau_titre = self.entree_titre_edition.get().strip()
        nouveau_contenu = self.zone_texte_edition.get(1.0, tk.END).strip()
        nouveaux_tags = [tag.strip() for tag in self.entree_tags_edition.get().split(',') if tag.strip()]
        
        if not nouveau_titre:
            messagebox.showwarning("Attention", "Le titre ne peut pas être vide!")
            return
        
        # Mettre à jour la note
        ancien_titre = self.note_actuelle['titre']
        self.note_actuelle['titre'] = nouveau_titre
        self.note_actuelle['contenu'] = nouveau_contenu
        self.note_actuelle['tags'] = nouveaux_tags
        self.note_actuelle['date_modification'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Mettre à jour l'interface principale
        self.entree_titre.delete(0, tk.END)
        self.entree_titre.insert(0, nouveau_titre)
        
        self.zone_texte.delete(1.0, tk.END)
        self.zone_texte.insert(1.0, nouveau_contenu)
        
        # Sauvegarder et mettre à jour l'affichage
        self.mettre_a_jour_liste_notes()
        self.sauvegarder_donnees()
        
        # Enregistrer l'activité
        self.enregistrer_activite('modification', f"Modification de {nouveau_titre}")
        
        # Fermer la fenêtre et confirmer
        self.fenetre_edition.destroy()
        messagebox.showinfo("Succès", f"Note '{nouveau_titre}' modifiée avec succès!")

    def apercu_note(self):
        """Affiche un aperçu de la note en cours de modification"""
        titre_apercu = self.entree_titre_edition.get().strip()
        contenu_apercu = self.zone_texte_edition.get(1.0, tk.END).strip()
        tags_apercu = [tag.strip() for tag in self.entree_tags_edition.get().split(',') if tag.strip()]
        
        # Fenêtre d'aperçu
        fenetre_apercu = tk.Toplevel(self.fenetre_edition)
        fenetre_apercu.title("Aperçu de la note")
        fenetre_apercu.geometry("600x500")
        fenetre_apercu.configure(bg="white")
        
        # Contenu de l'aperçu
        frame_apercu = tk.Frame(fenetre_apercu, bg="white")
        frame_apercu.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        tk.Label(frame_apercu, text=titre_apercu, font=("Arial", 16, "bold"), 
                bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        
        # Informations
        tk.Label(frame_apercu, text=f"Date de création: {self.note_actuelle['date_creation']}", 
                font=("Arial", 10), bg="white", fg="#7f8c8d").pack(anchor="w")
        
        if self.note_actuelle.get('date_modification'):
            tk.Label(frame_apercu, text=f"Dernière modification: {self.note_actuelle['date_modification']}", 
                    font=("Arial", 10), bg="white", fg="#7f8c8d").pack(anchor="w")
        
        # Tags
        if tags_apercu:
            tags_text = " ".join([f"#{tag}" for tag in tags_apercu])
            tk.Label(frame_apercu, text=tags_text, font=("Arial", 10), 
                    bg="white", fg="#3498db").pack(anchor="w", pady=5)
        
        # Séparateur
        tk.Frame(frame_apercu, height=2, bg="#bdc3c7").pack(fill=tk.X, pady=10)
        
        # Contenu
        frame_contenu_apercu = tk.Frame(frame_apercu)
        frame_contenu_apercu.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_apercu = tk.Scrollbar(frame_contenu_apercu)
        scrollbar_apercu.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_apercu = tk.Text(frame_contenu_apercu, yscrollcommand=scrollbar_apercu.set,
                            font=("Arial", 11), wrap=tk.WORD, bg="white", state=tk.DISABLED)
        text_apercu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_apercu.config(command=text_apercu.yview)
        
        # Insérer le contenu (en mode éditable temporairement)
        text_apercu.config(state=tk.NORMAL)
        text_apercu.insert(1.0, contenu_apercu)
        text_apercu.config(state=tk.DISABLED)
        
        # Bouton fermer
        tk.Button(fenetre_apercu, text="Fermer", command=fenetre_apercu.destroy,
                 bg="#95a5a6", fg="white").pack(pady=10)

    def dupliquer_note_actuelle(self):
        """Crée une copie de la note actuelle"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Aucune note sélectionnée à dupliquer!")
            return
        
        # Créer une copie
        note_dupliquee = {
            'id': len(self.notes_liste) + 1,
            'titre': f"Copie - {self.note_actuelle['titre']}",
            'contenu': self.note_actuelle['contenu'],
            'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'tags': self.note_actuelle.get('tags', []).copy()
        }
        
        self.notes_liste.append(note_dupliquee)
        self.mettre_a_jour_liste_notes()
        self.sauvegarder_donnees()
        
        messagebox.showinfo("Duplication", f"Note dupliquée: '{note_dupliquee['titre']}'")

    # FONCTIONS D'ÉVOLUTION ET SUIVI

    def demarrer_session_etude(self, matiere, note_id=None):
        """Démarre une nouvelle session d'étude"""
        if self.session_actuelle:
            self.terminer_session_etude()
        
        self.session_actuelle = {
            'matiere': matiere,
            'note_id': note_id,
            'debut': datetime.now(),
            'activites': []
        }
        self.temps_debut_session = datetime.now()
        
        if matiere not in self.matieres:
            self.matieres[matiere] = {
                'notes_ids': [],
                'temps_total': 0,
                'sessions': 0,
                'quiz_scores': [],
                'derniere_session': None,
                'progression': {
                    'notes_creees': 0,
                    'quiz_reussis': 0,
                    'temps_moyen_session': 0
                }
            }
        
        self.mettre_a_jour_interface_session()

    def terminer_session_etude(self):
        """Termine la session d'étude actuelle"""
        if not self.session_actuelle:
            return
        
        fin = datetime.now()
        duree = (fin - self.session_actuelle['debut']).total_seconds() / 60
        
        session_complete = {
            'date': self.session_actuelle['debut'].strftime("%Y-%m-%d %H:%M"),
            'matiere': self.session_actuelle['matiere'],
            'duree': round(duree, 1),
            'note_id': self.session_actuelle.get('note_id'),
            'activites': self.session_actuelle.get('activites', [])
        }
        
        self.sessions_etude.append(session_complete)
        
        matiere = self.session_actuelle['matiere']
        self.matieres[matiere]['temps_total'] += duree
        self.matieres[matiere]['sessions'] += 1
        self.matieres[matiere]['derniere_session'] = datetime.now().strftime("%Y-%m-%d")
        
        total_sessions = self.matieres[matiere]['sessions']
        self.matieres[matiere]['progression']['temps_moyen_session'] = self.matieres[matiere]['temps_total'] / total_sessions
        
        self.session_actuelle = None
        self.temps_debut_session = None
        
        self.sauvegarder_donnees()
        self.mettre_a_jour_interface_session()
        
        messagebox.showinfo("Session terminée", f"Session de {duree:.1f} minutes terminée pour {matiere}")

    def enregistrer_activite(self, type_activite, details=None):
        """Enregistre une activité dans la session actuelle"""
        if self.session_actuelle:
            activite = {
                'type': type_activite,
                'heure': datetime.now().strftime("%H:%M"),
                'details': details
            }
            self.session_actuelle['activites'].append(activite)

    def associer_note_matiere(self, note_id, matiere):
        """Associe une note à une matière"""
        if matiere not in self.matieres:
            self.matieres[matiere] = {
                'notes_ids': [],
                'temps_total': 0,
                'sessions': 0,
                'quiz_scores': [],
                'derniere_session': None,
                'progression': {
                    'notes_creees': 0,
                    'quiz_reussis': 0,
                    'temps_moyen_session': 0
                }
            }
        
        if note_id not in self.matieres[matiere]['notes_ids']:
            self.matieres[matiere]['notes_ids'].append(note_id)
            self.matieres[matiere]['progression']['notes_creees'] += 1

    def calculer_statistiques_globales(self):
        """Calcule les statistiques globales de l'utilisateur"""
        stats = {
            'temps_total_global': 0,
            'sessions_total': len(self.sessions_etude),
            'matieres_etudiees': len(self.matieres),
            'notes_total': len(self.notes_liste),
            'quiz_total': sum(len(m['quiz_scores']) for m in self.matieres.values()),
            'moyenne_quiz_globale': 0,
            'matiere_preferee': None,
            'progression_semaine': self.calculer_progression_semaine()
        }
        
        for session in self.sessions_etude:
            stats['temps_total_global'] += session['duree']
        
        tous_scores = []
        for matiere in self.matieres.values():
            tous_scores.extend([q['pourcentage'] for q in matiere['quiz_scores']])
        
        if tous_scores:
            stats['moyenne_quiz_globale'] = sum(tous_scores) / len(tous_scores)
        
        if self.matieres:
            stats['matiere_preferee'] = max(self.matieres.keys(), 
                                          key=lambda m: self.matieres[m]['temps_total'])
        
        return stats

    def calculer_progression_semaine(self):
        """Calcule la progression de la semaine actuelle"""
        maintenant = datetime.now()
        debut_semaine = maintenant - timedelta(days=maintenant.weekday())
        
        sessions_semaine = [s for s in self.sessions_etude 
                          if datetime.strptime(s['date'], "%Y-%m-%d %H:%M") >= debut_semaine]
        
        return {
            'sessions': len(sessions_semaine),
            'temps': sum(s['duree'] for s in sessions_semaine),
            'matieres': len(set(s['matiere'] for s in sessions_semaine))
        }

    def ouvrir_tableau_bord_evolution(self):
        """Ouvre la fenêtre du tableau de bord d'évolution"""
        fenetre_evolution = tk.Toplevel(self.fenetre_principale)
        fenetre_evolution.title("📊 Tableau de Bord - Évolution")
        fenetre_evolution.geometry("1000x700")
        fenetre_evolution.configure(bg="#f8f9fa")
        
        notebook = ttk.Notebook(fenetre_evolution)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet Vue d'ensemble
        frame_vue = tk.Frame(notebook, bg="#f8f9fa")
        notebook.add(frame_vue, text="🏠 Vue d'ensemble")
        
        stats = self.calculer_statistiques_globales()
        
        tk.Label(frame_vue, text="📊 Vue d'ensemble de votre progression", 
                font=("Arial", 16, "bold"), bg="#f8f9fa").pack(pady=20)
        
        # Cartes de statistiques
        frame_cartes = tk.Frame(frame_vue, bg="#f8f9fa")
        frame_cartes.pack(fill=tk.X, padx=20, pady=10)
        
        # Créer les cartes de stats
        self.creer_carte_stat(frame_cartes, "⏱️", "Temps total", f"{stats['temps_total_global']:.1f} min", "#3498db")
        self.creer_carte_stat(frame_cartes, "📚", "Sessions", f"{stats['sessions_total']}", "#27ae60")
        self.creer_carte_stat(frame_cartes, "🎯", "Matières", f"{stats['matieres_etudiees']}", "#e67e22")
        self.creer_carte_stat(frame_cartes, "🏆", "Notes", f"{stats['notes_total']}", "#9b59b6")

    def creer_carte_stat(self, parent, icone, titre, valeur, couleur):
        """Crée une carte de statistique"""
        carte = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
        carte.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(carte, text=icone, font=("Arial", 24), bg="white").pack(pady=5)
        tk.Label(carte, text=titre, font=("Arial", 12, "bold"), bg="white").pack()
        tk.Label(carte, text=valeur, font=("Arial", 16), bg="white", fg=couleur).pack(pady=5)

    def mettre_a_jour_interface_session(self):
        """Met à jour l'interface pour montrer la session en cours"""
        try:
            if hasattr(self, 'label_session_actuelle'):
                if self.session_actuelle:
                    duree = (datetime.now() - self.temps_debut_session).total_seconds() / 60
                    texte = f"📚 Session: {self.session_actuelle['matiere']} ({duree:.0f} min)"
                    self.label_session_actuelle.config(text=texte, fg="#27ae60")
                else:
                    self.label_session_actuelle.config(text="💤 Aucune session active", fg="#7f8c8d")
        except:
            pass
        
        self.fenetre_principale.after(60000, self.mettre_a_jour_interface_session)

    def demander_nouvelle_session(self):
        """Dialogue pour démarrer une nouvelle session"""
        if self.session_actuelle:
            if messagebox.askyesno("Session en cours", "Une session est déjà active. La terminer?"):
                self.terminer_session_etude()
            else:
                return
        
        fenetre_session = tk.Toplevel(self.fenetre_principale)
        fenetre_session.title("Nouvelle Session d'Étude")
        fenetre_session.geometry("350x200")
        fenetre_session.configure(bg="#f8f9fa")
        
        tk.Label(fenetre_session, text="📚 Nouvelle Session d'Étude", 
                font=("Arial", 14, "bold"), bg="#f8f9fa").pack(pady=20)
        
        tk.Label(fenetre_session, text="Matière:", bg="#f8f9fa").pack()
        
        combo_matiere = ttk.Combobox(fenetre_session, font=("Arial", 10), width=30)
        matieres_existantes = list(self.matieres.keys()) + ["➕ Nouvelle matière..."]
        combo_matiere['values'] = matieres_existantes
        combo_matiere.pack(pady=10)
        
        if matieres_existantes:
            combo_matiere.current(0)
        
        def demarrer():
            matiere = combo_matiere.get().strip()
            if not matiere:
                messagebox.showwarning("Attention", "Choisissez une matière!")
                return
            
            if matiere == "➕ Nouvelle matière...":
                matiere = simpledialog.askstring("Nouvelle matière", "Nom de la matière:")
                if not matiere:
                    return
            
            note_id = None
            if self.note_actuelle:
                note_id = self.note_actuelle.get('id')
                self.associer_note_matiere(note_id, matiere)
            
            self.demarrer_session_etude(matiere, note_id)
            self.mettre_a_jour_panel_evolution()
            fenetre_session.destroy()
            messagebox.showinfo("Session", f"Session démarrée pour {matiere}!")
        
        frame_boutons = tk.Frame(fenetre_session, bg="#f8f9fa")
        frame_boutons.pack(pady=20)
        
        tk.Button(frame_boutons, text="▶️ Démarrer", command=demarrer,
                 bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(frame_boutons, text="Annuler", command=fenetre_session.destroy,
                 bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=5)

    def associer_note_dialogue(self):
        """Dialogue pour associer une note à une matière"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Sélectionnez une note à associer!")
            return
        
        matieres_existantes = list(self.matieres.keys())
        if matieres_existantes:
            matiere = tk.simpledialog.askstring("Associer à une matière", 
                                              f"Matière pour '{self.note_actuelle['titre']}':\n" + 
                                              f"Existantes: {', '.join(matieres_existantes)}")
        else:
            matiere = tk.simpledialog.askstring("Associer à une matière", 
                                              f"Matière pour '{self.note_actuelle['titre']}':")
        
        if matiere:
            self.associer_note_matiere(self.note_actuelle['id'], matiere.strip())
            self.mettre_a_jour_panel_evolution()
            messagebox.showinfo("Succès", f"Note associée à {matiere}!")

    def mettre_a_jour_panel_evolution(self):
        """Met à jour les informations dans le panel d'évolution"""
        try:
            stats = self.calculer_statistiques_globales()
            self.label_temps_total.config(text=f"Temps: {stats['temps_total_global']:.0f} min")
            self.label_sessions_total.config(text=f"Sessions: {stats['sessions_total']}")
            self.label_matieres_total.config(text=f"Matières: {stats['matieres_etudiees']}")
            
            self.liste_matieres.delete(0, tk.END)
            for matiere, data in self.matieres.items():
                temps = data['temps_total']
                self.liste_matieres.insert(tk.END, f"{matiere[:15]} ({temps:.0f}min)")
        except:
            pass

    def appliquer_theme(self):
        theme = "sombre" if self.theme_sombre else "clair"
        couleurs = self.couleurs[theme]
        
        self.fenetre_principale.configure(bg=couleurs["fond"])
        
        try:
            self.cadre_notes.configure(bg=couleurs["fond_widget"])
            self.cadre_editeur.configure(bg=couleurs["fond_widget"])
            self.cadre_outils.configure(bg=couleurs["fond_widget"])
            self.cadre_evolution.configure(bg=couleurs["fond_widget"])
        except:
            pass
        
        widgets_config = [
            (self.zone_texte, {"bg": couleurs["fond_widget"], "fg": couleurs["texte"], "insertbackground": couleurs["texte"]}),
            (self.entree_titre, {"bg": couleurs["fond_widget"], "fg": couleurs["texte"]}),
            (self.entree_recherche, {"bg": couleurs["fond_widget"], "fg": couleurs["texte"]}),
            (self.liste_notes, {"bg": couleurs["fond_widget"], "fg": couleurs["texte"]}),
            (self.liste_rappels, {"bg": couleurs["fond_widget"], "fg": couleurs["texte"]})
        ]
        
        for widget, config in widgets_config:
            try:
                widget.configure(**config)
            except:
                pass

    def basculer_theme(self):
        self.theme_sombre = not self.theme_sombre
        self.appliquer_theme()

    def programmer_sauvegarde_auto(self):
        self.sauvegarder_donnees()
        self.fenetre_principale.after(self.auto_save_interval, self.programmer_sauvegarde_auto)

    def creer_interface(self):
        # Barre de menu
        barre_menu = tk.Menu(self.fenetre_principale)
        self.fenetre_principale.config(menu=barre_menu)
        
        # Menu Configuration
        menu_config = tk.Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Configuration", menu=menu_config)
        menu_config.add_command(label="Configurer API", command=self.configurer_cle_api)
        menu_config.add_command(label="Configurer Email", command=self.configurer_email)
        menu_config.add_command(label="Basculer Thème", command=self.basculer_theme)
        
        # Menu Outils
        menu_outils = tk.Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Outils", menu=menu_outils)
        menu_outils.add_command(label="Quiz Interactif", command=self.generer_quiz_interactif)
        menu_outils.add_command(label="Résumé Intelligent", command=self.resumer_texte_intelligent)
        
        # Menu Partage
        menu_partage = tk.Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Partage", menu=menu_partage)
        menu_partage.add_command(label="Partager Note Actuelle", command=self.partager_note_actuelle)
        menu_partage.add_command(label="Partager Plusieurs Notes", command=self.partager_plusieurs_notes)
        
        # Menu Évolution
        menu_evolution = tk.Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label="Évolution", menu=menu_evolution)
        menu_evolution.add_command(label="Tableau de Bord", command=self.ouvrir_tableau_bord_evolution)
        menu_evolution.add_command(label="Démarrer Session", command=self.demander_nouvelle_session)
        menu_evolution.add_command(label="Terminer Session", command=self.terminer_session_etude)
        menu_evolution.add_separator()
        menu_evolution.add_command(label="Associer Note à Matière", command=self.associer_note_dialogue)
        
        # Cadre principal
        cadre_principal = tk.Frame(self.fenetre_principale)
        cadre_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Créer les panels
        self.creer_panel_notes(cadre_principal)
        self.creer_editeur_texte(cadre_principal)
        self.creer_panel_outils(cadre_principal)
        self.creer_panel_evolution(cadre_principal)
        
        self.appliquer_theme()
        self.mettre_a_jour_interface_session()

    def creer_panel_evolution(self, parent):
        """Crée le nouveau panel d'évolution à droite"""
        self.cadre_evolution = tk.Frame(parent, relief=tk.RAISED, bd=1)
        self.cadre_evolution.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.cadre_evolution.configure(width=250)
        self.cadre_evolution.pack_propagate(False)
        
        # Titre
        tk.Label(self.cadre_evolution, text="Évolution", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Session actuelle
        frame_session = tk.Frame(self.cadre_evolution, bg="white", relief=tk.RIDGE, bd=2)
        frame_session.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frame_session, text="Session actuelle", font=("Arial", 10, "bold"), bg="white").pack(pady=5)
        self.label_session_actuelle = tk.Label(frame_session, text="Aucune session active", 
                                             font=("Arial", 9), bg="white", fg="#7f8c8d")
        self.label_session_actuelle.pack(pady=5)
        
        # Boutons session
        frame_btn_session = tk.Frame(self.cadre_evolution)
        frame_btn_session.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(frame_btn_session, text="Démarrer", command=self.demander_nouvelle_session,
                 bg="#27ae60", fg="white", font=("Arial", 8)).pack(fill=tk.X, pady=1)
        tk.Button(frame_btn_session, text="Terminer", command=self.terminer_session_etude,
                 bg="#e74c3c", fg="white", font=("Arial", 8)).pack(fill=tk.X, pady=1)
        
        # Stats rapides
        frame_stats = tk.Frame(self.cadre_evolution, bg="white", relief=tk.RIDGE, bd=2)
        frame_stats.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(frame_stats, text="Stats rapides", font=("Arial", 10, "bold"), bg="white").pack(pady=5)
        
        self.label_temps_total = tk.Label(frame_stats, text="Temps: 0 min", 
                                        font=("Arial", 9), bg="white")
        self.label_temps_total.pack(pady=2)
        
        self.label_sessions_total = tk.Label(frame_stats, text="Sessions: 0", 
                                           font=("Arial", 9), bg="white")
        self.label_sessions_total.pack(pady=2)
        
        self.label_matieres_total = tk.Label(frame_stats, text="Matières: 0", 
                                           font=("Arial", 9), bg="white")
        self.label_matieres_total.pack(pady=2)
        
        # Matières
        tk.Label(self.cadre_evolution, text="Mes matières", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        
        frame_matieres = tk.Frame(self.cadre_evolution)
        frame_matieres.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar_evo = tk.Scrollbar(frame_matieres)
        scrollbar_evo.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.liste_matieres = tk.Listbox(frame_matieres, yscrollcommand=scrollbar_evo.set, 
                                       font=("Arial", 9), height=6)
        self.liste_matieres.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_evo.config(command=self.liste_matieres.yview)
        
        # Boutons
        frame_btn_evo = tk.Frame(self.cadre_evolution)
        frame_btn_evo.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(frame_btn_evo, text="Tableau de Bord", command=self.ouvrir_tableau_bord_evolution,
                 bg="#3498db", fg="white", font=("Arial", 8)).pack(fill=tk.X, pady=1)
        tk.Button(frame_btn_evo, text="Associer Note", command=self.associer_note_dialogue,
                 bg="#9b59b6", fg="white", font=("Arial", 8)).pack(fill=tk.X, pady=1)
        
        self.mettre_a_jour_panel_evolution()

    def creer_panel_notes(self, parent):
        self.cadre_notes = tk.Frame(parent, relief=tk.RAISED, bd=1)
        self.cadre_notes.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        self.cadre_notes.configure(width=250)
        self.cadre_notes.pack_propagate(False)
        
        # Titre
        tk.Label(self.cadre_notes, text="Mes Notes", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Recherche
        self.entree_recherche = tk.Entry(self.cadre_notes, font=("Arial", 10))
        self.entree_recherche.pack(fill=tk.X, padx=10, pady=5)
        self.entree_recherche.insert(0, "Rechercher...")
        self.entree_recherche.bind("<KeyRelease>", self.filtrer_notes)
        self.entree_recherche.bind("<FocusIn>", self.effacer_placeholder)
        
        # Boutons
        cadre_boutons = tk.Frame(self.cadre_notes)
        cadre_boutons.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(cadre_boutons, text="+ Nouvelle note", command=self.nouvelle_note,
                 bg="#3498db", fg="white").pack(fill=tk.X, pady=1)
        tk.Button(cadre_boutons, text="Effacer recherche", command=self.effacer_recherche,
                 bg="#95a5a6", fg="white").pack(fill=tk.X, pady=1)
        
        # Boutons pour modification/suppression
        tk.Button(cadre_boutons, text="Modifier", command=self.ouvrir_editeur_note,
                 bg="#f39c12", fg="white").pack(fill=tk.X, pady=1)
        tk.Button(cadre_boutons, text="Supprimer", command=self.supprimer_note_actuelle,
                 bg="#e74c3c", fg="white").pack(fill=tk.X, pady=1)
        tk.Button(cadre_boutons, text="Dupliquer", command=self.dupliquer_note_actuelle,
                 bg="#9b59b6", fg="white").pack(fill=tk.X, pady=1)
        
        tk.Button(cadre_boutons, text="Partager", command=self.partager_note_actuelle,
                 bg="#e67e22", fg="white").pack(fill=tk.X, pady=1)
        
        # Liste des notes
        cadre_liste = tk.Frame(self.cadre_notes)
        cadre_liste.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(cadre_liste)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.liste_notes = tk.Listbox(cadre_liste, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.liste_notes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.liste_notes.bind('<<ListboxSelect>>', self.selectionner_note)
        scrollbar.config(command=self.liste_notes.yview)
        
        self.mettre_a_jour_liste_notes()

    def creer_editeur_texte(self, parent):
        self.cadre_editeur = tk.Frame(parent, relief=tk.RAISED, bd=1)
        self.cadre_editeur.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Barre d'outils
        barre_outils = tk.Frame(self.cadre_editeur, height=40)
        barre_outils.pack(fill=tk.X, padx=5, pady=5)
        barre_outils.pack_propagate(False)
        
        tk.Label(barre_outils, text="Titre:").pack(side=tk.LEFT, padx=5)
        self.entree_titre = tk.Entry(barre_outils, font=("Arial", 12), width=40)
        self.entree_titre.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        tk.Button(barre_outils, text="Sauvegarder", command=self.sauvegarder_note,
                 bg="#27ae60", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # Zone de texte
        cadre_texte = tk.Frame(self.cadre_editeur)
        cadre_texte.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar_texte = tk.Scrollbar(cadre_texte)
        scrollbar_texte.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.zone_texte = tk.Text(cadre_texte, yscrollcommand=scrollbar_texte.set,
                                 font=("Arial", 11), wrap=tk.WORD)
        self.zone_texte.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_texte.config(command=self.zone_texte.yview)

    def creer_panel_outils(self, parent):
        self.cadre_outils = tk.Frame(parent, relief=tk.RAISED, bd=1)
        self.cadre_outils.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.cadre_outils.configure(width=200)
        self.cadre_outils.pack_propagate(False)
        
        tk.Label(self.cadre_outils, text="Outils", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Boutons outils
        tk.Button(self.cadre_outils, text="Quiz", command=self.generer_quiz_interactif,
                 bg="#3498db", fg="white").pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.cadre_outils, text="Résumé", command=self.resumer_texte_intelligent,
                 bg="#9b59b6", fg="white").pack(fill=tk.X, padx=10, pady=2)
        
        # Rappels
        tk.Label(self.cadre_outils, text="Rappels", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        
        frame_rappels = tk.Frame(self.cadre_outils)
        frame_rappels.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar_rappels = tk.Scrollbar(frame_rappels)
        scrollbar_rappels.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.liste_rappels = tk.Listbox(frame_rappels, yscrollcommand=scrollbar_rappels.set,
                                      font=("Arial", 9), height=8)
        self.liste_rappels.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_rappels.config(command=self.liste_rappels.yview)
        
        tk.Button(self.cadre_outils, text="Nouveau rappel", command=self.ajouter_rappel,
                 bg="#e67e22", fg="white").pack(fill=tk.X, padx=10, pady=5)
        
        self.mettre_a_jour_rappels()

    # Fonctions principales
    def nouvelle_note(self):
        """Crée une nouvelle note vide"""
        self.note_actuelle = None
        self.entree_titre.delete(0, tk.END)
        self.zone_texte.delete(1.0, tk.END)
        self.entree_titre.focus()

    def sauvegarder_note(self):
        """Sauvegarde la note actuelle"""
        titre = self.entree_titre.get().strip()
        contenu = self.zone_texte.get(1.0, tk.END).strip()
        
        if not titre:
            messagebox.showwarning("Attention", "Le titre ne peut pas être vide!")
            return
        
        if self.note_actuelle:
            # Modification d'une note existante
            self.note_actuelle['titre'] = titre
            self.note_actuelle['contenu'] = contenu
            self.note_actuelle['date_modification'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.enregistrer_activite('modification', f"Modification de {titre}")
        else:
            # Nouvelle note
            nouvelle_note = {
                'id': len(self.notes_liste) + 1,
                'titre': titre,
                'contenu': contenu,
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': []
            }
            self.notes_liste.append(nouvelle_note)
            self.note_actuelle = nouvelle_note
            self.enregistrer_activite('creation', f"Création de {titre}")
        
        self.mettre_a_jour_liste_notes()
        self.sauvegarder_donnees()
        messagebox.showinfo("Succès", "Note sauvegardée!")

    def selectionner_note(self, event):
        """Sélectionne une note dans la liste"""
        try:
            index = self.liste_notes.curselection()[0]
            notes_a_utiliser = self.notes_filtrees if self.notes_filtrees else self.notes_liste
            
            if index < len(notes_a_utiliser):
                self.note_actuelle = notes_a_utiliser[index]
                self.entree_titre.delete(0, tk.END)
                self.entree_titre.insert(0, self.note_actuelle['titre'])
                
                self.zone_texte.delete(1.0, tk.END)
                self.zone_texte.insert(1.0, self.note_actuelle['contenu'])
                
                self.enregistrer_activite('lecture', f"Lecture de {self.note_actuelle['titre']}")
        except:
            pass

    def filtrer_notes(self, event=None):
        """Filtre les notes selon le terme de recherche"""
        terme = self.entree_recherche.get().lower()
        
        if terme == "rechercher..." or not terme:
            self.notes_filtrees = []
        else:
            self.notes_filtrees = [note for note in self.notes_liste 
                                 if terme in note['titre'].lower() or 
                                    terme in note['contenu'].lower()]
        
        self.mettre_a_jour_liste_notes()

    def effacer_placeholder(self, event):
        """Efface le placeholder de recherche"""
        if self.entree_recherche.get() == "Rechercher...":
            self.entree_recherche.delete(0, tk.END)

    def effacer_recherche(self):
        """Efface la recherche et affiche toutes les notes"""
        self.entree_recherche.delete(0, tk.END)
        self.entree_recherche.insert(0, "Rechercher...")
        self.notes_filtrees = []
        self.mettre_a_jour_liste_notes()

    def mettre_a_jour_liste_notes(self):
        """Met à jour l'affichage de la liste des notes"""
        self.liste_notes.delete(0, tk.END)
        
        notes_a_afficher = self.notes_filtrees if self.notes_filtrees else self.notes_liste
        
        for note in notes_a_afficher:
            titre_court = note['titre'][:30] + "..." if len(note['titre']) > 30 else note['titre']
            self.liste_notes.insert(tk.END, titre_court)

    # Fonctions de rappels
    def ajouter_rappel(self):
        """Ajoute un nouveau rappel"""
        fenetre_rappel = tk.Toplevel(self.fenetre_principale)
        fenetre_rappel.title("Nouveau Rappel")
        fenetre_rappel.geometry("400x300")
        
        tk.Label(fenetre_rappel, text="Titre du rappel:").pack(pady=5)
        entree_titre_rappel = tk.Entry(fenetre_rappel, width=50)
        entree_titre_rappel.pack(pady=5)
        
        tk.Label(fenetre_rappel, text="Date (YYYY-MM-DD):").pack(pady=5)
        entree_date = tk.Entry(fenetre_rappel, width=50)
        entree_date.pack(pady=5)
        entree_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Label(fenetre_rappel, text="Heure (HH:MM):").pack(pady=5)
        entree_heure = tk.Entry(fenetre_rappel, width=50)
        entree_heure.pack(pady=5)
        entree_heure.insert(0, "09:00")
        
        def sauvegarder_rappel():
            titre = entree_titre_rappel.get().strip()
            date_str = entree_date.get().strip()
            heure_str = entree_heure.get().strip()
            
            if not titre:
                messagebox.showwarning("Attention", "Le titre est requis!")
                return
            
            try:
                date_heure = datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M")
                rappel = {
                    'id': len(self.rappels_liste) + 1,
                    'titre': titre,
                    'date_heure': date_heure.strftime("%Y-%m-%d %H:%M"),
                    'actif': True
                }
                self.rappels_liste.append(rappel)
                self.mettre_a_jour_rappels()
                self.sauvegarder_donnees()
                fenetre_rappel.destroy()
                messagebox.showinfo("Succès", "Rappel ajouté!")
            except ValueError:
                messagebox.showerror("Erreur", "Format de date/heure invalide!")
        
        tk.Button(fenetre_rappel, text="Sauvegarder", command=sauvegarder_rappel,
                 bg="#27ae60", fg="white").pack(pady=20)

    def mettre_a_jour_rappels(self):
        """Met à jour la liste des rappels"""
        self.liste_rappels.delete(0, tk.END)
        for rappel in self.rappels_liste:
            if rappel['actif']:
                texte = f"{rappel['titre'][:20]}... - {rappel['date_heure']}"
                self.liste_rappels.insert(tk.END, texte)

    def verifier_rappels(self):
        """Vérifie s'il y a des rappels à afficher"""
        maintenant = datetime.now()
        
        for rappel in self.rappels_liste:
            if rappel['actif']:
                date_rappel = datetime.strptime(rappel['date_heure'], "%Y-%m-%d %H:%M")
                if date_rappel <= maintenant:
                    messagebox.showinfo("Rappel", f"Rappel: {rappel['titre']}")
                    rappel['actif'] = False
        
        self.mettre_a_jour_rappels()
        self.fenetre_principale.after(60000, self.verifier_rappels)  # Vérifier chaque minute

    # Fonctions de sauvegarde/chargement
    def sauvegarder_donnees(self):
        """Sauvegarde toutes les données"""
        donnees = {
            'notes': self.notes_liste,
            'rappels': self.rappels_liste,
            'matieres': self.matieres,
            'sessions_etude': self.sessions_etude,
            'email_config': self.email_config
        }
        
        try:
            with open(os.path.join(self.dossier_notes, 'donnees.json'), 'w', encoding='utf-8') as f:
                json.dump(donnees, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def charger_donnees(self):
        """Charge toutes les données"""
        fichier_donnees = os.path.join(self.dossier_notes, 'donnees.json')
        
        if os.path.exists(fichier_donnees):
            try:
                with open(fichier_donnees, 'r', encoding='utf-8') as f:
                    donnees = json.load(f)
                
                self.notes_liste = donnees.get('notes', [])
                self.rappels_liste = donnees.get('rappels', [])
                self.matieres = donnees.get('matieres', {})
                self.sessions_etude = donnees.get('sessions_etude', [])
                self.email_config.update(donnees.get('email_config', {}))
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")

    # Fonctions de configuration
    def configurer_cle_api(self):
        """Configure la clé API"""
        nouvelle_cle = simpledialog.askstring("Configuration API", 
                                             "Entrez votre clé API Hugging Face:",
                                             show='*')
        if nouvelle_cle:
            self.api_key = nouvelle_cle
            messagebox.showinfo("Succès", "Clé API configurée!")

    def configurer_email(self):
        """Configure les paramètres email"""
        fenetre_email = tk.Toplevel(self.fenetre_principale)
        fenetre_email.title("Configuration Email")
        fenetre_email.geometry("400x300")
        
        tk.Label(fenetre_email, text="Serveur SMTP:").pack(pady=5)
        entree_smtp = tk.Entry(fenetre_email, width=50)
        entree_smtp.pack(pady=5)
        entree_smtp.insert(0, self.email_config.get('smtp_server', 'smtp.gmail.com'))
        
        tk.Label(fenetre_email, text="Port:").pack(pady=5)
        entree_port = tk.Entry(fenetre_email, width=50)
        entree_port.pack(pady=5)
        entree_port.insert(0, str(self.email_config.get('smtp_port', 587)))
        
        tk.Label(fenetre_email, text="Email:").pack(pady=5)
        entree_email = tk.Entry(fenetre_email, width=50)
        entree_email.pack(pady=5)
        entree_email.insert(0, self.email_config.get('email', ''))
        
        tk.Label(fenetre_email, text="Mot de passe:").pack(pady=5)
        entree_password = tk.Entry(fenetre_email, width=50, show='*')
        entree_password.pack(pady=5)
        
        def sauvegarder_config():
            self.email_config.update({
                'smtp_server': entree_smtp.get(),
                'smtp_port': int(entree_port.get()),
                'email': entree_email.get(),
                'password': entree_password.get()
            })
            self.sauvegarder_donnees()
            fenetre_email.destroy()
            messagebox.showinfo("Succès", "Configuration email sauvegardée!")
        
        tk.Button(fenetre_email, text="Sauvegarder", command=sauvegarder_config,
                 bg="#27ae60", fg="white").pack(pady=20)

    # Fonctions IA (nécessitent une API)
    def generer_quiz_interactif(self):
        """Génère un quiz basé sur la note actuelle"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Sélectionnez une note pour générer un quiz!")
            return
        
        # Quiz simple basé sur le contenu
        messagebox.showinfo("Quiz", f"Fonction quiz pour: {self.note_actuelle['titre']}\n(Nécessite une implémentation avec l'API)")

    def resumer_texte_intelligent(self):
        """Génère un résumé intelligent de la note"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Sélectionnez une note à résumer!")
            return
        
        messagebox.showinfo("Résumé", f"Fonction résumé pour: {self.note_actuelle['titre']}\n(Nécessite une implémentation avec l'API)")

    # Fonctions de partage
    def partager_note_actuelle(self):
        """Partage la note actuelle par email"""
        if not self.note_actuelle:
            messagebox.showwarning("Attention", "Sélectionnez une note à partager!")
            return
        
        destinataire = simpledialog.askstring("Partage", "Email du destinataire:")
        if destinataire:
            messagebox.showinfo("Partage", f"Note partagée avec {destinataire}\n(Nécessite une configuration email)")

    def partager_plusieurs_notes(self):
        """Partage plusieurs notes sélectionnées"""
        messagebox.showinfo("Partage", "Fonction de partage multiple\n(À implémenter)")

    def exporter_notes(self):
        """Exporte les notes vers un fichier"""
        fichier = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        
        if fichier:
            try:
                with open(fichier, 'w', encoding='utf-8') as f:
                    for note in self.notes_liste:
                        f.write(f"=== {note['titre']} ===\n")
                        f.write(f"Date: {note['date_creation']}\n")
                        f.write(f"Contenu:\n{note['contenu']}\n")
                        f.write("\n" + "="*50 + "\n\n")
                
                messagebox.showinfo("Succès", f"Notes exportées vers {fichier}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {e}")

    def importer_notes(self):
        """Importe des notes depuis un fichier"""
        fichier = filedialog.askopenfilename(
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        
        if fichier:
            try:
                with open(fichier, 'r', encoding='utf-8') as f:
                    contenu = f.read()
                
                # Créer une note avec le contenu importé
                nouvelle_note = {
                    'id': len(self.notes_liste) + 1,
                    'titre': f"Importé - {os.path.basename(fichier)}",
                    'contenu': contenu,
                    'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'tags': ['importé']
                }
                
                self.notes_liste.append(nouvelle_note)
                self.mettre_a_jour_liste_notes()
                self.sauvegarder_donnees()
                
                messagebox.showinfo("Succès", "Fichier importé comme nouvelle note!")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'importation: {e}")

    def rechercher_dans_toutes_notes(self):
        """Recherche avancée dans toutes les notes"""
        terme = simpledialog.askstring("Recherche avancée", "Terme à rechercher:")
        
        if terme:
            resultats = []
            for note in self.notes_liste:
                if terme.lower() in note['titre'].lower() or terme.lower() in note['contenu'].lower():
                    resultats.append(note)
            
            if resultats:
                # Afficher les résultats dans une nouvelle fenêtre
                fenetre_resultats = tk.Toplevel(self.fenetre_principale)
                fenetre_resultats.title(f"Résultats pour '{terme}' ({len(resultats)} trouvé(s))")
                fenetre_resultats.geometry("600x400")
                
                # Liste des résultats
                frame_resultats = tk.Frame(fenetre_resultats)
                frame_resultats.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                scrollbar_res = tk.Scrollbar(frame_resultats)
                scrollbar_res.pack(side=tk.RIGHT, fill=tk.Y)
                
                liste_resultats = tk.Listbox(frame_resultats, yscrollcommand=scrollbar_res.set)
                liste_resultats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar_res.config(command=liste_resultats.yview)
                
                for note in resultats:
                    liste_resultats.insert(tk.END, f"{note['titre']} - {note['date_creation']}")
                
                def ouvrir_note_resultat(event):
                    try:
                        index = liste_resultats.curselection()[0]
                        note_selectionnee = resultats[index]
                        
                        # Ouvrir la note dans l'interface principale
                        self.note_actuelle = note_selectionnee
                        self.entree_titre.delete(0, tk.END)
                        self.entree_titre.insert(0, note_selectionnee['titre'])
                        
                        self.zone_texte.delete(1.0, tk.END)
                        self.zone_texte.insert(1.0, note_selectionnee['contenu'])
                        
                        fenetre_resultats.destroy()
                    except:
                        pass
                
                liste_resultats.bind('<Double-Button-1>', ouvrir_note_resultat)
                
            else:
                messagebox.showinfo("Recherche", f"Aucun résultat trouvé pour '{terme}'")

    def statistiques_notes(self):
        """Affiche des statistiques sur les notes"""
        if not self.notes_liste:
            messagebox.showinfo("Statistiques", "Aucune note disponible pour les statistiques")
            return
        
        # Calculer les statistiques
        total_notes = len(self.notes_liste)
        total_mots = sum(len(note['contenu'].split()) for note in self.notes_liste)
        moyenne_mots = total_mots / total_notes if total_notes > 0 else 0
        
        # Note la plus longue
        note_plus_longue = max(self.notes_liste, key=lambda n: len(n['contenu']))
        
        # Note la plus récente
        note_plus_recente = max(self.notes_liste, key=lambda n: n['date_creation'])
        
        stats_text = f"""📊 STATISTIQUES DES NOTES

📝 Total de notes: {total_notes}
📄 Total de mots: {total_mots:,}
📊 Moyenne de mots par note: {moyenne_mots:.1f}

🏆 Note la plus longue:
   "{note_plus_longue['titre']}" ({len(note_plus_longue['contenu'].split())} mots)

🕐 Note la plus récente:
   "{note_plus_recente['titre']}" ({note_plus_recente['date_creation']})

📚 Matières étudiées: {len(self.matieres)}
⏱️ Temps total d'étude: {sum(m['temps_total'] for m in self.matieres.values()):.1f} minutes
"""
        
        messagebox.showinfo("Statistiques", stats_text)

    def sauvegarder_backup(self):
        """Crée une sauvegarde des données"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fichier_backup = os.path.join(self.dossier_notes, f'backup_{timestamp}.json')
            
            donnees = {
                'notes': self.notes_liste,
                'rappels': self.rappels_liste,
                'matieres': self.matieres,
                'sessions_etude': self.sessions_etude,
                'email_config': self.email_config
            }
            
            with open(fichier_backup, 'w', encoding='utf-8') as f:
                json.dump(donnees, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Backup", f"Sauvegarde créée: {fichier_backup}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def restaurer_backup(self):
        """Restaure les données depuis une sauvegarde"""
        fichier = filedialog.askopenfilename(
            title="Sélectionner une sauvegarde",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        
        if fichier:
            try:
                with open(fichier, 'r', encoding='utf-8') as f:
                    donnees = json.load(f)
                
                self.notes_liste = donnees.get('notes', [])
                self.rappels_liste = donnees.get('rappels', [])
                self.matieres = donnees.get('matieres', {})
                self.sessions_etude = donnees.get('sessions_etude', [])
                self.email_config.update(donnees.get('email_config', {}))
                
                self.mettre_a_jour_liste_notes()
                self.mettre_a_jour_rappels()
                self.mettre_a_jour_panel_evolution()
                
                messagebox.showinfo("Succès", "Données restaurées avec succès!")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la restauration: {e}")

    def lancer_application(self):
        """Lance l'application"""
        self.fenetre_principale.mainloop()


def main():
    """Fonction principale"""
    try:
        app = ApplicationPriseDeNotes()
        app.lancer_application()
    except Exception as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        messagebox.showerror("Erreur critique", f"Impossible de lancer l'application:\n{e}")


if __name__ == "__main__":

  main()      
raise e