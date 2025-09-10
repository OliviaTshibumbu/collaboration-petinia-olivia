from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.pickers import MDDatePicker, MDTimePicker

from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

import random
import re
import os
from datetime import datetime, timedelta


class StudyHelperApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "StudyHelper Pro"
        
        # Variables principales
        self.notes = []
        self.alarmes = []
        self.quiz_results = []
        self.resumes = []
        self.statistiques = {
            'temps_total': 0,
            'sessions': [],
            'notes_revisees': {},
            'debut_session': datetime.now()
        }
        
        self.note_selectionnee = None
        
        # Stockage des données avec gestion d'erreur
        self.store_file = 'studyhelper_pro.json'
        self.initialiser_store()
        
        # Variables pour les dialogues
        self.dialog = None
        
        # Variables pour les quiz
        self.questions_quiz = []
        self.score_quiz = 0
        self.question_actuelle = 0

    def initialiser_store(self):
        """Initialise le store avec gestion d'erreur pour les fichiers corrompus"""
        try:
            # Essayer de charger le store existant
            self.store = JsonStore(self.store_file)
            # Tester si le fichier est lisible
            if self.store.exists('donnees'):
                test_data = self.store.get('donnees')
            self.charger_donnees()
        except Exception as e:
            print(f"Erreur lors du chargement du store: {e}")
            print("Création d'un nouveau fichier de données...")
            
            # Supprimer le fichier corrompu s'il existe
            if os.path.exists(self.store_file):
                try:
                    os.remove(self.store_file)
                    print(f"Fichier corrompu {self.store_file} supprimé.")
                except:
                    print(f"Impossible de supprimer {self.store_file}")
            
            # Créer un nouveau store
            try:
                self.store = JsonStore(self.store_file)
                # Initialiser avec des données vides
                self.sauvegarder_donnees()
                print("Nouveau fichier de données créé avec succès.")
            except Exception as e2:
                print(f"Erreur lors de la création du nouveau store: {e2}")
                # En dernier recours, ne pas utiliser de stockage persistant
                self.store = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        self.screen_manager = MDScreenManager()
        screen = MDScreen(name="main")
        
        layout_principal = MDBoxLayout(orientation="vertical")
        
        # Toolbar avec hauteur fixe appropriée
        toolbar = MDTopAppBar(
            title="StudyHelper Pro", 
            elevation=2,
            size_hint_y=None,
            height="56dp"
        )
        layout_principal.add_widget(toolbar)
        
        self.navigation = MDBottomNavigation(
            panel_color=self.theme_cls.primary_color
        )
        
        # Onglet Accueil (Historique des notes)
        onglet_accueil = MDBottomNavigationItem(
            name="accueil", text="Accueil", icon="home"
        )
        onglet_accueil.add_widget(self.creer_onglet_accueil())
        self.navigation.add_widget(onglet_accueil)
        
        # Onglet Notes (Créer/Modifier)
        onglet_notes = MDBottomNavigationItem(
            name="notes", text="Notes", icon="note-text"
        )
        onglet_notes.add_widget(self.creer_onglet_notes())
        self.navigation.add_widget(onglet_notes)
        
        # Onglet Alarmes
        onglet_alarmes = MDBottomNavigationItem(
            name="alarmes", text="Alarmes", icon="alarm"
        )
        onglet_alarmes.add_widget(self.creer_onglet_alarmes())
        self.navigation.add_widget(onglet_alarmes)
        
        # Onglet Statistiques
        onglet_stats = MDBottomNavigationItem(
            name="stats", text="Progrès", icon="chart-line"
        )
        onglet_stats.add_widget(self.creer_onglet_statistiques())
        self.navigation.add_widget(onglet_stats)
        
        layout_principal.add_widget(self.navigation)
        screen.add_widget(layout_principal)
        self.screen_manager.add_widget(screen)
        
        # Timer pour les statistiques de temps
        Clock.schedule_interval(self.mettre_a_jour_temps_utilisation, 60)
        
        return self.screen_manager

    def creer_onglet_accueil(self):
        """Onglet Accueil - Liste de toutes les notes créées"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Titre avec marge appropriée
        titre = MDLabel(
            text="Toutes vos notes",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="48dp",
            halign="left"
        )
        titre.bind(texture_size=titre.setter('text_size'))
        layout.add_widget(titre)
        
        # Zone de recherche
        self.champ_recherche = MDTextField(
            hint_text="Rechercher une note...",
            size_hint_y=None,
            height="56dp"
        )
        self.champ_recherche.bind(text=self.rechercher_notes)
        layout.add_widget(self.champ_recherche)
        
        # Liste des notes
        scroll = MDScrollView()
        self.liste_toutes_notes = MDList()
        scroll.add_widget(self.liste_toutes_notes)
        layout.add_widget(scroll)
        
        Clock.schedule_once(lambda dt: self.actualiser_liste_notes(), 0.1)
        return layout

    def creer_onglet_notes(self):
        """Onglet Notes - Créer et éditer des notes"""
        layout = MDBoxLayout(orientation="vertical", padding="15dp", spacing="15dp")
        
        # Info note sélectionnée avec style amélioré
        self.label_note_selectionnee = MDLabel(
            text="Aucune note sélectionnée",
            theme_text_color="Secondary",
            font_style="Body2",
            size_hint_y=None,
            height="32dp",
            halign="left"
        )
        self.label_note_selectionnee.bind(texture_size=self.label_note_selectionnee.setter('text_size'))
        layout.add_widget(self.label_note_selectionnee)
        
        # Champ titre avec taille correcte
        self.champ_titre = MDTextField(
            hint_text="Titre de la note",
            size_hint_y=None,
            height="56dp"
        )
        layout.add_widget(self.champ_titre)
        
        # Champ contenu dans une carte bien dimensionnée
        carte_contenu = MDCard(
            elevation=2,
            padding="15dp",
            size_hint_y=None,
            height="200dp",
            md_bg_color=(1, 1, 1, 1)
        )
        
        self.champ_contenu = MDTextField(
            hint_text="Écrivez le contenu de votre note ici...",
            multiline=True,
            size_hint=(1, 1)
        )
        
        carte_contenu.add_widget(self.champ_contenu)
        layout.add_widget(carte_contenu)
        
        # Boutons d'action pour les notes avec espacement correct
        boutons_notes = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="48dp"
        )
        
        btn_nouvelle = MDRaisedButton(
            text="Nouvelle",
            size_hint_x=0.25
        )
        btn_nouvelle.bind(on_release=self.nouvelle_note)
        boutons_notes.add_widget(btn_nouvelle)
        
        btn_sauver = MDRaisedButton(
            text="Sauvegarder",
            size_hint_x=0.25
        )
        btn_sauver.bind(on_release=self.sauvegarder_note)
        boutons_notes.add_widget(btn_sauver)
        
        btn_modifier = MDRaisedButton(
            text="Modifier",
            size_hint_x=0.25
        )
        btn_modifier.bind(on_release=self.modifier_note)
        boutons_notes.add_widget(btn_modifier)
        
        btn_supprimer = MDRaisedButton(
            text="Supprimer",
            size_hint_x=0.25
        )
        btn_supprimer.bind(on_release=self.supprimer_note)
        boutons_notes.add_widget(btn_supprimer)
        
        layout.add_widget(boutons_notes)
        
        # Section Quiz et Résumé avec séparation visuelle claire
        section_outils = MDCard(
            elevation=3,
            padding="15dp",
            spacing="12dp",
            size_hint_y=None,
            height="160dp",
            md_bg_color=(0.98, 0.98, 0.98, 1)
        )
        
        layout_outils = MDBoxLayout(orientation="vertical", spacing="12dp")
        
        titre_outils = MDLabel(
            text="Outils d'apprentissage",
            font_style="Subtitle1",
            theme_text_color="Primary",
            size_hint_y=None,
            height="32dp",
            halign="left"
        )
        titre_outils.bind(texture_size=titre_outils.setter('text_size'))
        layout_outils.add_widget(titre_outils)
        
        # Boutons Quiz avec meilleure organisation
        boutons_quiz = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="40dp"
        )
        
        btn_quiz_facile = MDFlatButton(
            text="Quiz Facile",
            size_hint_x=0.33
        )
        btn_quiz_facile.bind(on_release=lambda x: self.creer_quiz('facile'))
        boutons_quiz.add_widget(btn_quiz_facile)
        
        btn_quiz_moyen = MDFlatButton(
            text="Quiz Moyen",
            size_hint_x=0.33
        )
        btn_quiz_moyen.bind(on_release=lambda x: self.creer_quiz('moyen'))
        boutons_quiz.add_widget(btn_quiz_moyen)
        
        btn_quiz_difficile = MDFlatButton(
            text="Quiz Difficile",
            size_hint_x=0.33
        )
        btn_quiz_difficile.bind(on_release=lambda x: self.creer_quiz('difficile'))
        boutons_quiz.add_widget(btn_quiz_difficile)
        
        layout_outils.add_widget(boutons_quiz)
        
        # Bouton Résumé séparé
        btn_resume = MDRaisedButton(
            text="Générer un résumé cohérent",
            size_hint_y=None,
            height="44dp"
        )
        btn_resume.bind(on_release=self.generer_resume)
        layout_outils.add_widget(btn_resume)
        
        section_outils.add_widget(layout_outils)
        layout.add_widget(section_outils)
        
        return layout

    def creer_onglet_alarmes(self):
        """Onglet Alarmes"""
        layout = MDBoxLayout(orientation="vertical", padding="15dp", spacing="15dp")
        
        # Titre avec style amélioré
        titre = MDLabel(
            text="Alarmes et Rappels",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="48dp",
            halign="left"
        )
        titre.bind(texture_size=titre.setter('text_size'))
        layout.add_widget(titre)
        
        # Section création d'alarme avec meilleur design
        carte_nouvelle = MDCard(
            elevation=3,
            padding="15dp",
            size_hint_y=None,
            height="240dp",
            md_bg_color=(0.98, 0.98, 0.98, 1)
        )
        layout_nouvelle = MDBoxLayout(orientation="vertical", spacing="12dp")
        
        # Label note alarme avec instruction claire
        self.label_note_alarme = MDLabel(
            text="Aucune note sélectionnée - Allez dans l'Accueil pour choisir une note",
            font_style="Body2",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        self.label_note_alarme.bind(texture_size=self.label_note_alarme.setter('text_size'))
        layout_nouvelle.add_widget(self.label_note_alarme)
        
        # Description de l'alarme
        self.champ_description_alarme = MDTextField(
            hint_text="Description du rappel (ex: Réviser chapitre 1)",
            size_hint_y=None,
            height="56dp"
        )
        layout_nouvelle.add_widget(self.champ_description_alarme)
        
        # Boutons date et heure avec meilleur design
        boutons_datetime = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        self.btn_date = MDRaisedButton(
            text="Choisir Date",
            size_hint_x=0.5
        )
        self.btn_date.bind(on_release=self.afficher_date_picker)
        boutons_datetime.add_widget(self.btn_date)
        
        self.btn_heure = MDRaisedButton(
            text="Choisir Heure",
            size_hint_x=0.5
        )
        self.btn_heure.bind(on_release=self.afficher_time_picker)
        boutons_datetime.add_widget(self.btn_heure)
        
        layout_nouvelle.add_widget(boutons_datetime)
        
        # Bouton créer alarme
        btn_creer_alarme = MDRaisedButton(
            text="Créer l'alarme",
            size_hint_y=None,
            height="48dp"
        )
        btn_creer_alarme.bind(on_release=self.creer_alarme)
        layout_nouvelle.add_widget(btn_creer_alarme)
        
        carte_nouvelle.add_widget(layout_nouvelle)
        layout.add_widget(carte_nouvelle)
        
        # Liste des alarmes avec titre amélioré
        titre_liste = MDLabel(
            text="Alarmes programmées",
            font_style="Subtitle1",
            theme_text_color="Primary",
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        titre_liste.bind(texture_size=titre_liste.setter('text_size'))
        layout.add_widget(titre_liste)
        
        scroll = MDScrollView()
        self.liste_alarmes = MDList()
        scroll.add_widget(self.liste_alarmes)
        layout.add_widget(scroll)
        
        # Variables pour stocker date et heure sélectionnées
        self.date_selectionnee = None
        self.heure_selectionnee = None
        
        Clock.schedule_once(lambda dt: self.actualiser_liste_alarmes(), 0.1)
        return layout

    def creer_onglet_statistiques(self):
        """Onglet Statistiques"""
        # Container principal avec marge supérieure pour éviter le chevauchement
        container = MDBoxLayout(orientation="vertical")
        
        # Espace pour éviter le chevauchement avec la toolbar
        spacer = MDLabel(text="", size_hint_y=None, height="10dp")
        container.add_widget(spacer)
        
        layout = MDBoxLayout(orientation="vertical", padding="15dp", spacing="15dp")
        
        # Titre avec bon positionnement
        titre = MDLabel(
            text="Statistiques et Progrès",
            theme_text_color="Primary",
            font_style="H4",
            size_hint_y=None,
            height="56dp",
            halign="left"
        )
        titre.bind(texture_size=titre.setter('text_size'))
        layout.add_widget(titre)
        
        # Carte temps d'utilisation avec design amélioré
        carte_temps = MDCard(
            elevation=3,
            padding="20dp",
            size_hint_y=None,
            height="140dp",
            md_bg_color=(0.95, 0.98, 1, 1)
        )
        layout_temps = MDBoxLayout(orientation="vertical", spacing="8dp")
        
        titre_temps = MDLabel(
            text="Temps d'utilisation",
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="36dp",
            halign="left"
        )
        titre_temps.bind(texture_size=titre_temps.setter('text_size'))
        layout_temps.add_widget(titre_temps)
        
        self.label_temps_total = MDLabel(
            text="Temps total: 0 minutes",
            font_style="Body1",
            size_hint_y=None,
            height="32dp",
            halign="left"
        )
        self.label_temps_total.bind(texture_size=self.label_temps_total.setter('text_size'))
        
        self.label_temps_aujourd = MDLabel(
            text="Aujourd'hui: 0 minutes",
            font_style="Body1",
            size_hint_y=None,
            height="32dp",
            halign="left"
        )
        self.label_temps_aujourd.bind(texture_size=self.label_temps_aujourd.setter('text_size'))
        
        layout_temps.add_widget(self.label_temps_total)
        layout_temps.add_widget(self.label_temps_aujourd)
        
        carte_temps.add_widget(layout_temps)
        layout.add_widget(carte_temps)
        
        # Carte révisions avec design amélioré
        carte_revisions = MDCard(
            elevation=3,
            padding="20dp",
            size_hint_y=None,
            height="170dp",
            md_bg_color=(0.98, 1, 0.95, 1)
        )
        layout_revisions = MDBoxLayout(orientation="vertical", spacing="8dp")
        
        titre_revisions = MDLabel(
            text="Révisions",
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="36dp",
            halign="left"
        )
        titre_revisions.bind(texture_size=titre_revisions.setter('text_size'))
        layout_revisions.add_widget(titre_revisions)
        
        self.label_nb_notes = MDLabel(
            text="Nombre de notes: 0",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_nb_notes.bind(texture_size=self.label_nb_notes.setter('text_size'))
        
        self.label_notes_revisees = MDLabel(
            text="Notes révisées: 0",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_notes_revisees.bind(texture_size=self.label_notes_revisees.setter('text_size'))
        
        self.label_freq_revision = MDLabel(
            text="Fréquence moyenne: N/A",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_freq_revision.bind(texture_size=self.label_freq_revision.setter('text_size'))
        
        layout_revisions.add_widget(self.label_nb_notes)
        layout_revisions.add_widget(self.label_notes_revisees)
        layout_revisions.add_widget(self.label_freq_revision)
        
        carte_revisions.add_widget(layout_revisions)
        layout.add_widget(carte_revisions)
        
        # Carte quiz avec design amélioré
        carte_quiz = MDCard(
            elevation=3,
            padding="20dp",
            size_hint_y=None,
            height="200dp",
            md_bg_color=(1, 0.98, 0.95, 1)
        )
        layout_quiz = MDBoxLayout(orientation="vertical", spacing="8dp")
        
        titre_quiz = MDLabel(
            text="Performance Quiz",
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="36dp",
            halign="left"
        )
        titre_quiz.bind(texture_size=titre_quiz.setter('text_size'))
        layout_quiz.add_widget(titre_quiz)
        
        self.label_nb_quiz = MDLabel(
            text="Quiz réalisés: 0",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_nb_quiz.bind(texture_size=self.label_nb_quiz.setter('text_size'))
        
        self.label_score_moyen = MDLabel(
            text="Score moyen: N/A",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_score_moyen.bind(texture_size=self.label_score_moyen.setter('text_size'))
        
        self.label_meilleur_score = MDLabel(
            text="Meilleur score: N/A",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_meilleur_score.bind(texture_size=self.label_meilleur_score.setter('text_size'))
        
        self.label_progression = MDLabel(
            text="Progression: N/A",
            font_style="Body1",
            size_hint_y=None,
            height="28dp",
            halign="left"
        )
        self.label_progression.bind(texture_size=self.label_progression.setter('text_size'))
        
        layout_quiz.add_widget(self.label_nb_quiz)
        layout_quiz.add_widget(self.label_score_moyen)
        layout_quiz.add_widget(self.label_meilleur_score)
        layout_quiz.add_widget(self.label_progression)
        
        carte_quiz.add_widget(layout_quiz)
        layout.add_widget(carte_quiz)
        
        container.add_widget(layout)
        
        Clock.schedule_once(lambda dt: self.actualiser_statistiques(), 0.1)
        return container

    # Méthodes pour l'accueil
    def actualiser_liste_notes(self):
        """Met à jour la liste de toutes les notes dans l'accueil"""
        if not hasattr(self, 'liste_toutes_notes'):
            return
            
        self.liste_toutes_notes.clear_widgets()
        
        for note in self.notes:
            date = note.get('date_creation', 'Date inconnue')
            nb_mots = note.get('nb_mots', 0)
            
            item = ThreeLineListItem(
                text=note['titre'],
                secondary_text=f"{note['contenu'][:50]}..." if len(note['contenu']) > 50 else note['contenu'],
                tertiary_text=f"Créé le {date} | {nb_mots} mots"
            )
            item.bind(on_release=lambda x, n=note: self.selectionner_note_accueil(n))
            self.liste_toutes_notes.add_widget(item)

    def selectionner_note_accueil(self, note):
        """Sélectionne une note depuis l'accueil"""
        self.note_selectionnee = note
        
        # Mettre à jour l'affichage dans l'onglet Notes
        if hasattr(self, 'champ_titre'):
            self.champ_titre.text = note['titre']
        if hasattr(self, 'champ_contenu'):
            self.champ_contenu.text = note['contenu']
        if hasattr(self, 'label_note_selectionnee'):
            self.label_note_selectionnee.text = f"Note sélectionnée: {note['titre']}"
        
        # Mettre à jour pour les alarmes
        if hasattr(self, 'label_note_alarme'):
            self.label_note_alarme.text = f"Note sélectionnée: {note['titre']}"
        
        # Incrémenter le compteur de révision
        note_id = note.get('id', note['titre'])
        if note_id not in self.statistiques['notes_revisees']:
            self.statistiques['notes_revisees'][note_id] = 0
        self.statistiques['notes_revisees'][note_id] += 1
        
        self.afficher_message(f"Note '{note['titre']}' sélectionnée")
        self.sauvegarder_donnees()

    def rechercher_notes(self, instance, texte):
        """Recherche dans les notes"""
        self.actualiser_liste_notes()
        
        if not texte.strip():
            return
            
        # Filtrer les notes
        self.liste_toutes_notes.clear_widgets()
        
        for note in self.notes:
            if texte.lower() in note['titre'].lower() or texte.lower() in note['contenu'].lower():
                date = note.get('date_creation', 'Date inconnue')
                nb_mots = note.get('nb_mots', 0)
                
                item = ThreeLineListItem(
                    text=note['titre'],
                    secondary_text=f"{note['contenu'][:50]}..." if len(note['contenu']) > 50 else note['contenu'],
                    tertiary_text=f"Créé le {date} | {nb_mots} mots"
                )
                item.bind(on_release=lambda x, n=note: self.selectionner_note_accueil(n))
                self.liste_toutes_notes.add_widget(item)

    # Méthodes pour les notes
    def nouvelle_note(self, *args):
        """Prépare l'éditeur pour une nouvelle note"""
        self.note_selectionnee = None
        self.champ_titre.text = ""
        self.champ_contenu.text = ""
        self.label_note_selectionnee.text = "Nouvelle note"
        self.afficher_message("Prêt pour créer une nouvelle note")

    def sauvegarder_note(self, *args):
        """Sauvegarde une nouvelle note ou met à jour une existante"""
        titre = self.champ_titre.text.strip()
        contenu = self.champ_contenu.text.strip()
        
        if not titre:
            self.afficher_message("Le titre ne peut pas être vide!")
            return
        
        if not contenu:
            self.afficher_message("Le contenu ne peut pas être vide!")
            return
        
        if self.note_selectionnee:
            # Mettre à jour la note existante
            self.note_selectionnee['titre'] = titre
            self.note_selectionnee['contenu'] = contenu
            self.note_selectionnee['date_modification'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.note_selectionnee['nb_mots'] = len(contenu.split())
            message = "Note mise à jour!"
        else:
            # Créer une nouvelle note
            nouvelle_note = {
                'id': len(self.notes) + 1,
                'titre': titre,
                'contenu': contenu,
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'nb_mots': len(contenu.split())
            }
            self.notes.append(nouvelle_note)
            self.note_selectionnee = nouvelle_note
            message = "Note sauvegardée!"
        
        self.sauvegarder_donnees()
        self.actualiser_liste_notes()
        if hasattr(self, 'actualiser_statistiques'):
            self.actualiser_statistiques()
        self.afficher_message(message)

    def modifier_note(self, *args):
        """Active la modification d'une note sélectionnée"""
        if not self.note_selectionnee:
            self.afficher_message("Sélectionnez d'abord une note à modifier!")
            return
        
        self.afficher_message("Modifiez la note et cliquez sur Sauvegarder")

    def supprimer_note(self, *args):
        """Supprime la note sélectionnée"""
        if not self.note_selectionnee:
            self.afficher_message("Sélectionnez d'abord une note à supprimer!")
            return
        
        self.dialog = MDDialog(
            text=f"Supprimer la note '{self.note_selectionnee['titre']}'?",
            buttons=[
                MDFlatButton(text="ANNULER", on_release=self.fermer_dialog),
                MDFlatButton(text="SUPPRIMER", on_release=self.confirmer_suppression_note)
            ]
        )
        self.dialog.open()

    def confirmer_suppression_note(self, *args):
        """Confirme la suppression de la note"""
        if self.note_selectionnee in self.notes:
            self.notes.remove(self.note_selectionnee)
            self.note_selectionnee = None
            self.champ_titre.text = ""
            self.champ_contenu.text = ""
            self.label_note_selectionnee.text = "Aucune note sélectionnée"
            
            self.sauvegarder_donnees()
            self.actualiser_liste_notes()
            if hasattr(self, 'actualiser_statistiques'):
                self.actualiser_statistiques()
            
        self.fermer_dialog()
        self.afficher_message("Note supprimée!")

    # Méthodes pour les quiz
    def creer_quiz(self, difficulte):
        """Crée un quiz basé sur la note sélectionnée"""
        if not self.note_selectionnee:
            self.afficher_message("Sélectionnez d'abord une note depuis l'Accueil!")
            return
        
        contenu = self.note_selectionnee['contenu']
        
        if len(contenu) < 100:
            self.afficher_message("La note est trop courte pour créer un quiz!")
            return
        
        # Définir le nombre de questions selon la difficulté
        nb_questions = {
            'facile': 3,
            'moyen': 5,
            'difficile': 8
        }
        
        self.questions_quiz = self.generer_questions(contenu, nb_questions[difficulte])
        self.question_actuelle = 0
        self.score_quiz = 0
        
        self.afficher_question_quiz()

    def generer_questions(self, texte, nb_questions):
        """Génère des questions à partir du texte"""
        questions = []
        phrases = re.split(r'[.!?]+', texte)
        phrases = [p.strip() for p in phrases if len(p.strip()) > 20]
        
        for i in range(min(nb_questions, len(phrases))):
            if not phrases:
                break
            phrase = random.choice(phrases)
            phrases.remove(phrase)  # Éviter les doublons
            
            # Créer une question vrai/faux simple
            if random.choice([True, False]):
                questions.append({
                    'question': f"Vrai ou Faux: {phrase}",
                    'options': ["Vrai", "Faux"],
                    'correct': 0,
                    'type': 'vrai_faux'
                })
            else:
                # Modifier la phrase pour la rendre fausse
                phrase_modifiee = phrase.replace(' est ', ' n\'est pas ')
                if phrase_modifiee == phrase:
                    phrase_modifiee = "Ceci est incorrect: " + phrase
                    
                questions.append({
                    'question': f"Vrai ou Faux: {phrase_modifiee}",
                    'options': ["Vrai", "Faux"],
                    'correct': 1,
                    'type': 'vrai_faux'
                })
        
        return questions

    def afficher_question_quiz(self):
        """Affiche la question actuelle du quiz"""
        if self.question_actuelle >= len(self.questions_quiz):
            self.terminer_quiz()
            return
        
        question = self.questions_quiz[self.question_actuelle]
        
        contenu = MDBoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        # Progression
        progress = MDLabel(
            text=f"Question {self.question_actuelle + 1}/{len(self.questions_quiz)}",
            font_style="Caption",
            size_hint_y=None,
            height="30dp"
        )
        contenu.add_widget(progress)
        
        # Question
        q_label = MDLabel(
            text=question['question'],
            font_style="Body1",
            size_hint_y=None,
            height="60dp"
        )
        contenu.add_widget(q_label)
        
        # Options
        for i, option in enumerate(question['options']):
            btn = MDRaisedButton(
                text=option,
                size_hint_y=None,
                height="48dp"
            )
            btn.bind(on_release=lambda x, idx=i: self.repondre_quiz(idx))
            contenu.add_widget(btn)
        
        self.dialog = MDDialog(
            title=f"Quiz: {self.note_selectionnee['titre']}",
            type="custom",
            content_cls=contenu
        )
        self.dialog.open()

    def repondre_quiz(self, reponse):
        """Traite la réponse à une question"""
        question = self.questions_quiz[self.question_actuelle]
        
        if reponse == question['correct']:
            self.score_quiz += 1
            self.afficher_message("Bonne réponse!")
        else:
            self.afficher_message("Mauvaise réponse!")
        
        self.fermer_dialog()
        self.question_actuelle += 1
        Clock.schedule_once(lambda dt: self.afficher_question_quiz(), 0.5)

    def terminer_quiz(self):
        """Termine le quiz et affiche les résultats"""
        pourcentage = int((self.score_quiz / len(self.questions_quiz)) * 100)
        
        # Sauvegarder le résultat
        resultat = {
            'note_titre': self.note_selectionnee['titre'],
            'score': self.score_quiz,
            'total': len(self.questions_quiz),
            'pourcentage': pourcentage,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.quiz_results.append(resultat)
        self.sauvegarder_donnees()
        if hasattr(self, 'actualiser_statistiques'):
            self.actualiser_statistiques()
        
        # Afficher le résultat
        self.dialog = MDDialog(
            text=f"Quiz terminé!\n\nScore: {self.score_quiz}/{len(self.questions_quiz)}\nPourcentage: {pourcentage}%",
            buttons=[MDFlatButton(text="OK", on_release=self.fermer_dialog)]
        )
        self.dialog.open()

    # Méthodes pour les résumés
    def generer_resume(self, *args):
        """Génère un résumé cohérent de la note sélectionnée"""
        if not self.note_selectionnee:
            self.afficher_message("Sélectionnez d'abord une note depuis l'Accueil!")
            return
        
        contenu = self.note_selectionnee['contenu']
        
        if len(contenu) < 100:
            self.afficher_message("La note est trop courte pour créer un résumé!")
            return
        
        # Créer un résumé cohérent
        resume = self.creer_resume_coherent(contenu)
        
        # Sauvegarder le résumé
        resume_obj = {
            'note_titre': self.note_selectionnee['titre'],
            'resume': resume,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'nb_mots_original': len(contenu.split()),
            'nb_mots_resume': len(resume.split())
        }
        self.resumes.append(resume_obj)
        self.sauvegarder_donnees()
        
        # Afficher le résumé
        self.afficher_resume(resume_obj)

    def creer_resume_coherent(self, texte):
        """Crée un résumé cohérent du texte"""
        # Diviser en phrases
        phrases = re.split(r'[.!?]+', texte)
        phrases = [p.strip() for p in phrases if len(p.strip()) > 15]
        
        if len(phrases) <= 3:
            return texte
        
        # Prendre les phrases importantes
        # Première phrase (introduction)
        resume_phrases = [phrases[0]]
        
        # Phrases du milieu (corps)
        if len(phrases) > 4:
            milieu = len(phrases) // 2
            resume_phrases.append(phrases[milieu])
        
        # Dernière phrase (conclusion)
        if len(phrases) > 1:
            resume_phrases.append(phrases[-1])
        
        # Joindre les phrases
        resume = '. '.join(resume_phrases)
        if not resume.endswith('.'):
            resume += '.'
        
        # Limiter la longueur
        mots = resume.split()
        if len(mots) > 100:
            resume = ' '.join(mots[:100]) + '...'
        
        return resume

    def afficher_resume(self, resume_obj):
        """Affiche le résumé généré"""
        contenu = MDBoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        # Stats
        stats = MDLabel(
            text=f"Original: {resume_obj['nb_mots_original']} mots → Résumé: {resume_obj['nb_mots_resume']} mots",
            font_style="Caption",
            size_hint_y=None,
            height="30dp"
        )
        contenu.add_widget(stats)
        
        # Résumé
        scroll = MDScrollView(size_hint=(1, None), height="200dp")
        resume_label = MDLabel(
            text=resume_obj['resume'],
            font_style="Body1",
            size_hint_y=None
        )
        resume_label.bind(texture_size=resume_label.setter('size'))
        scroll.add_widget(resume_label)
        contenu.add_widget(scroll)
        
        self.dialog = MDDialog(
            title=f"Résumé: {resume_obj['note_titre']}",
            type="custom",
            content_cls=contenu,
            buttons=[MDFlatButton(text="OK", on_release=self.fermer_dialog)]
        )
        self.dialog.open()

    # Méthodes pour les alarmes
    def afficher_date_picker(self, *args):
        """Affiche le sélecteur de date"""
        try:
            date_dialog = MDDatePicker()
            date_dialog.bind(on_save=self.sauver_date)
            date_dialog.open()
        except Exception as e:
            self.afficher_message("Erreur lors de l'ouverture du sélecteur de date")

    def sauver_date(self, instance, value, date_range):
        """Sauvegarde la date sélectionnée"""
        self.date_selectionnee = value
        self.btn_date.text = value.strftime("%d/%m/%Y")

    def afficher_time_picker(self, *args):
        """Affiche le sélecteur d'heure"""
        try:
            time_dialog = MDTimePicker()
            time_dialog.bind(on_save=self.sauver_heure)
            time_dialog.open()
        except Exception as e:
            self.afficher_message("Erreur lors de l'ouverture du sélecteur d'heure")

    def sauver_heure(self, instance, time):
        """Sauvegarde l'heure sélectionnée"""
        self.heure_selectionnee = time
        self.btn_heure.text = time.strftime("%H:%M")

    def creer_alarme(self, *args):
        """Crée une nouvelle alarme"""
        if not self.note_selectionnee:
            self.afficher_message("Sélectionnez d'abord une note depuis l'Accueil!")
            return
        
        if not self.date_selectionnee or not self.heure_selectionnee:
            self.afficher_message("Choisissez une date et une heure!")
            return
        
        description = self.champ_description_alarme.text.strip()
        if not description:
            description = f"Réviser: {self.note_selectionnee['titre']}"
        
        # Combiner date et heure
        alarme_datetime = datetime.combine(self.date_selectionnee, self.heure_selectionnee)
        
        # Créer l'alarme
        alarme = {
            'id': len(self.alarmes) + 1,
            'note_titre': self.note_selectionnee['titre'],
            'description': description,
            'date_heure': alarme_datetime.strftime("%Y-%m-%d %H:%M"),
            'active': True
        }
        
        self.alarmes.append(alarme)
        self.sauvegarder_donnees()
        self.actualiser_liste_alarmes()
        
        # Réinitialiser les champs
        self.champ_description_alarme.text = ""
        self.date_selectionnee = None
        self.heure_selectionnee = None
        self.btn_date.text = "Choisir Date"
        self.btn_heure.text = "Choisir Heure"
        
        self.afficher_message("Alarme créée!")

    def actualiser_liste_alarmes(self):
        """Met à jour la liste des alarmes"""
        if not hasattr(self, 'liste_alarmes'):
            return
        
        self.liste_alarmes.clear_widgets()
        
        # Trier les alarmes par date
        alarmes_triees = sorted(self.alarmes, key=lambda x: x['date_heure'])
        
        for alarme in alarmes_triees:
            statut = "Active" if alarme['active'] else "Désactivée"
            
            item = ThreeLineListItem(
                text=alarme['description'],
                secondary_text=f"Note: {alarme['note_titre']}",
                tertiary_text=f"{alarme['date_heure']} | {statut}"
            )
            item.bind(on_release=lambda x, a=alarme: self.gerer_alarme(a))
            self.liste_alarmes.add_widget(item)

    def gerer_alarme(self, alarme):
        """Gère une alarme (activer/désactiver/supprimer)"""
        self.dialog = MDDialog(
            text=f"Que faire avec cette alarme?\n{alarme['description']}",
            buttons=[
                MDFlatButton(
                    text="DÉSACTIVER" if alarme['active'] else "ACTIVER",
                    on_release=lambda x: self.toggle_alarme(alarme)
                ),
                MDFlatButton(text="SUPPRIMER", on_release=lambda x: self.supprimer_alarme(alarme)),
                MDFlatButton(text="ANNULER", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def toggle_alarme(self, alarme):
        """Active ou désactive une alarme"""
        alarme['active'] = not alarme['active']
        self.sauvegarder_donnees()
        self.actualiser_liste_alarmes()
        self.fermer_dialog()
        statut = "activée" if alarme['active'] else "désactivée"
        self.afficher_message(f"Alarme {statut}!")

    def supprimer_alarme(self, alarme):
        """Supprime une alarme"""
        self.alarmes.remove(alarme)
        self.sauvegarder_donnees()
        self.actualiser_liste_alarmes()
        self.fermer_dialog()
        self.afficher_message("Alarme supprimée!")

    # Méthodes pour les statistiques
    def actualiser_statistiques(self):
        """Met à jour toutes les statistiques"""
        if not hasattr(self, 'label_nb_notes'):
            return
        
        # Statistiques de base
        self.label_nb_notes.text = f"Nombre de notes: {len(self.notes)}"
        
        # Notes révisées
        nb_revisees = len(self.statistiques['notes_revisees'])
        self.label_notes_revisees.text = f"Notes révisées: {nb_revisees}"
        
        # Fréquence de révision
        if self.statistiques['notes_revisees']:
            freq_moyenne = sum(self.statistiques['notes_revisees'].values()) / len(self.statistiques['notes_revisees'])
            self.label_freq_revision.text = f"Fréquence moyenne: {freq_moyenne:.1f} fois"
        else:
            self.label_freq_revision.text = "Fréquence moyenne: N/A"
        
        # Statistiques quiz
        self.label_nb_quiz.text = f"Quiz réalisés: {len(self.quiz_results)}"
        
        if self.quiz_results:
            scores = [r['pourcentage'] for r in self.quiz_results]
            score_moyen = sum(scores) / len(scores)
            meilleur = max(scores)
            
            self.label_score_moyen.text = f"Score moyen: {score_moyen:.1f}%"
            self.label_meilleur_score.text = f"Meilleur score: {meilleur}%"
            
            # Progression (comparer les 3 derniers avec les 3 premiers)
            if len(scores) >= 3:
                debut = sum(scores[:3]) / 3
                fin = sum(scores[-3:]) / 3
                progression = fin - debut
                
                if progression > 0:
                    self.label_progression.text = f"Progression: +{progression:.1f}%"
                else:
                    self.label_progression.text = f"Progression: {progression:.1f}%"
            else:
                self.label_progression.text = "Progression: Pas assez de données"
        else:
            self.label_score_moyen.text = "Score moyen: N/A"
            self.label_meilleur_score.text = "Meilleur score: N/A"
            self.label_progression.text = "Progression: N/A"
        
        # Temps d'utilisation
        self.actualiser_temps_utilisation()

    def actualiser_temps_utilisation(self):
        """Met à jour les statistiques de temps"""
        if hasattr(self, 'label_temps_total'):
            temps_total = self.statistiques.get('temps_total', 0)
            self.label_temps_total.text = f"Temps total: {temps_total} minutes"
            
            # Temps aujourd'hui
            aujourd_hui = datetime.now().date()
            temps_aujourd = 0
            
            for session in self.statistiques.get('sessions', []):
                try:
                    if datetime.strptime(session['date'], "%Y-%m-%d").date() == aujourd_hui:
                        temps_aujourd += session['duree']
                except:
                    pass
            
            self.label_temps_aujourd.text = f"Aujourd'hui: {temps_aujourd} minutes"

    def mettre_a_jour_temps_utilisation(self, *args):
        """Appelé périodiquement pour mettre à jour le temps d'utilisation"""
        # Calculer le temps écoulé depuis le début de la session
        if isinstance(self.statistiques.get('debut_session'), datetime):
            temps_ecoule = (datetime.now() - self.statistiques['debut_session']).seconds // 60
        else:
            temps_ecoule = 1
        
        if temps_ecoule > 0:
            self.statistiques['temps_total'] = self.statistiques.get('temps_total', 0) + 1
            
            # Ajouter à la session du jour
            aujourd_hui = datetime.now().strftime("%Y-%m-%d")
            session_trouvee = False
            
            for session in self.statistiques.get('sessions', []):
                if session['date'] == aujourd_hui:
                    session['duree'] += 1
                    session_trouvee = True
                    break
            
            if not session_trouvee:
                if 'sessions' not in self.statistiques:
                    self.statistiques['sessions'] = []
                self.statistiques['sessions'].append({
                    'date': aujourd_hui,
                    'duree': 1
                })
            
            self.statistiques['debut_session'] = datetime.now()
            self.sauvegarder_donnees()
            self.actualiser_temps_utilisation()

    # Méthodes utilitaires
    def afficher_message(self, message):
        """Affiche un message à l'utilisateur"""
        try:
            Snackbar(text=message).open()
        except Exception:
            print(f"Message: {message}")

    def fermer_dialog(self, *args):
        """Ferme le dialogue actuel"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def sauvegarder_donnees(self):
        """Sauvegarde toutes les données avec protection contre les erreurs"""
        if self.store is None:
            print("Store non disponible, sauvegarde ignorée")
            return
            
        try:
            # Convertir datetime en string pour la sérialisation JSON
            stats_copy = self.statistiques.copy()
            if isinstance(stats_copy.get('debut_session'), datetime):
                stats_copy['debut_session'] = stats_copy['debut_session'].isoformat()
            
            self.store.put('donnees', 
                notes=self.notes,
                alarmes=self.alarmes,
                quiz_results=self.quiz_results,
                resumes=self.resumes,
                statistiques=stats_copy
            )
        except Exception as e:
            print(f"Erreur de sauvegarde: {e}")

    def charger_donnees(self):
        """Charge les données sauvegardées avec protection contre les erreurs"""
        if self.store is None:
            return
            
        try:
            if self.store.exists('donnees'):
                data = self.store.get('donnees')
                self.notes = data.get('notes', [])
                self.alarmes = data.get('alarmes', [])
                self.quiz_results = data.get('quiz_results', [])
                self.resumes = data.get('resumes', [])
                self.statistiques = data.get('statistiques', {
                    'temps_total': 0,
                    'sessions': [],
                    'notes_revisees': {},
                    'debut_session': datetime.now()
                })
                # Convertir la chaîne en datetime
                if isinstance(self.statistiques.get('debut_session'), str):
                    try:
                        self.statistiques['debut_session'] = datetime.fromisoformat(self.statistiques['debut_session'])
                    except:
                        self.statistiques['debut_session'] = datetime.now()
                elif not isinstance(self.statistiques.get('debut_session'), datetime):
                    self.statistiques['debut_session'] = datetime.now()
        except Exception as e:
            print(f"Erreur de chargement: {e}")

    def on_pause(self):
        """Appelé quand l'app est mise en pause"""
        self.sauvegarder_donnees()
        return True

    def on_stop(self):
        """Appelé quand l'app se ferme"""
        self.sauvegarder_donnees()


if __name__ == '__main__':
    StudyHelperApp().run()
