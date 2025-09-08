from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFloatingActionButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar

from kivy.clock import Clock
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.network.urlrequest import UrlRequest

import os
import json
from datetime import datetime, timedelta
import threading
import random
import re
from collections import Counter


class StudyHelperApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "StudyHelper"
        
        # Configuration
        self.api_key = ""
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',
            'password': ''
        }
        
        # Données
        self.notes_liste = []
        self.note_actuelle = None
        self.rappels_liste = []
        self.matieres = {}
        self.sessions_etude = []
        self.session_actuelle = None
        self.temps_debut_session = None
        self.notes_filtrees = []
        
        # Stockage
        self.store = None
        self.init_storage()
        
        # UI elements
        self.dialog = None
        self.menu = None
        
        # Quiz data
        self.quiz_questions = []
        self.quiz_actuel = None
        self.quiz_score = 0
        self.quiz_question_index = 0
        self.quiz_nombre_questions = 3

    def build(self):
        """Construit l'interface principale"""
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Screen Manager
        self.screen_manager = MDScreenManager()
        
        # Écran principal
        screen = MDScreen(name="main")
        
        # Layout principal
        main_layout = MDBoxLayout(orientation="vertical")
        
        # Toolbar
        toolbar = MDTopAppBar(
            title="StudyHelper",
            elevation=2
        )
        main_layout.add_widget(toolbar)
        
        # Bottom Navigation
        bottom_nav = MDBottomNavigation()
        
        # Onglet Notes
        notes_item = MDBottomNavigationItem(
            name="notes",
            text="Notes",
            icon="note-text"
        )
        notes_item.add_widget(self.create_notes_tab())
        bottom_nav.add_widget(notes_item)
        
        # Onglet Éditeur
        editor_item = MDBottomNavigationItem(
            name="editor", 
            text="Éditeur",
            icon="pencil"
        )
        editor_item.add_widget(self.create_editor_tab())
        bottom_nav.add_widget(editor_item)
        
        # Onglet Rappels
        reminders_item = MDBottomNavigationItem(
            name="reminders",
            text="Rappels", 
            icon="bell"
        )
        reminders_item.add_widget(self.create_reminders_tab())
        bottom_nav.add_widget(reminders_item)
        
        # Onglet Évolution
        evolution_item = MDBottomNavigationItem(
            name="evolution",
            text="Évolution",
            icon="chart-line"
        )
        evolution_item.add_widget(self.create_evolution_tab())
        bottom_nav.add_widget(evolution_item)
        
        main_layout.add_widget(bottom_nav)
        screen.add_widget(main_layout)
        self.screen_manager.add_widget(screen)
        
        return self.screen_manager

    def create_notes_tab(self):
        """Crée l'onglet des notes"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Recherche
        self.search_field = MDTextField(
            hint_text="Rechercher...",
            size_hint_y=None,
            height="48dp"
        )
        self.search_field.bind(text=self.filter_notes)
        layout.add_widget(self.search_field)
        
        # Boutons
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp", 
            size_hint_y=None,
            height="48dp"
        )
        
        new_note_btn = MDRaisedButton(text="Nouvelle Note")
        new_note_btn.bind(on_release=self.nouvelle_note)
        buttons_layout.add_widget(new_note_btn)
        
        clear_search_btn = MDRaisedButton(text="Effacer")
        clear_search_btn.bind(on_release=self.effacer_recherche)
        buttons_layout.add_widget(clear_search_btn)
        
        layout.add_widget(buttons_layout)
        
        # Liste des notes
        scroll = MDScrollView()
        self.notes_list = MDList()
        scroll.add_widget(self.notes_list)
        layout.add_widget(scroll)
        
        self.update_notes_list()
        return layout

    def create_editor_tab(self):
        """Crée l'onglet éditeur"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Titre
        self.title_field = MDTextField(
            hint_text="Titre de la note",
            size_hint_y=None,
            height="48dp"
        )
        layout.add_widget(self.title_field)
        
        # Contenu
        content_card = MDCard(
            elevation=2,
            padding="10dp",
            size_hint_y=None,
            height="400dp"
        )
        
        content_scroll = MDScrollView()
        
        self.content_field = MDTextField(
            hint_text="Contenu de la note...",
            multiline=True,
            size_hint_y=None,
            height="350dp"
        )
        
        content_scroll.add_widget(self.content_field)
        content_card.add_widget(content_scroll)
        layout.add_widget(content_card)
        
        # Boutons d'action
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        save_btn = MDRaisedButton(text="Sauvegarder")
        save_btn.bind(on_release=self.sauvegarder_note)
        buttons_layout.add_widget(save_btn)
        
        delete_btn = MDRaisedButton(text="Supprimer")
        delete_btn.bind(on_release=self.supprimer_note_dialog)
        buttons_layout.add_widget(delete_btn)
        
        share_btn = MDRaisedButton(text="Partager")
        share_btn.bind(on_release=self.partager_note_dialog)
        buttons_layout.add_widget(share_btn)
        
        layout.add_widget(buttons_layout)
        
        # Boutons outils
        tools_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        quiz_btn = MDRaisedButton(text="Quiz")
        quiz_btn.bind(on_release=self.config_quiz_dialog)
        tools_layout.add_widget(quiz_btn)
        
        resume_btn = MDRaisedButton(text="Résumé")
        resume_btn.bind(on_release=self.resumer_texte_intelligent) 
        tools_layout.add_widget(resume_btn)
        
        config_btn = MDRaisedButton(text="Config API")
        config_btn.bind(on_release=self.ouvrir_config_api)
        tools_layout.add_widget(config_btn)
        
        layout.add_widget(tools_layout)
        
        return layout

    def create_reminders_tab(self):
        """Crée l'onglet des rappels"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Titre
        title_label = MDLabel(
            text="Mes Rappels",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="40dp"
        )
        layout.add_widget(title_label)
        
        # Bouton nouveau rappel
        add_btn = MDRaisedButton(
            text="Nouveau Rappel",
            size_hint_y=None,
            height="48dp"
        )
        add_btn.bind(on_release=self.ajouter_rappel_dialog)
        layout.add_widget(add_btn)
        
        # Liste des rappels
        scroll = MDScrollView()
        self.reminders_list = MDList()
        scroll.add_widget(self.reminders_list)
        layout.add_widget(scroll)
        
        self.update_reminders_list()
        return layout

    def create_evolution_tab(self):
        """Crée l'onglet évolution"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Session actuelle
        session_card = MDCard(
            elevation=2,
            padding="15dp",
            size_hint_y=None,
            height="120dp"
        )
        
        session_layout = MDBoxLayout(orientation="vertical", spacing="10dp")
        
        self.session_label = MDLabel(
            text="Aucune session active",
            theme_text_color="Primary",
            font_style="Subtitle1"
        )
        session_layout.add_widget(self.session_label)
        
        session_buttons = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        start_btn = MDRaisedButton(text="Démarrer Session")
        start_btn.bind(on_release=self.demander_nouvelle_session)
        session_buttons.add_widget(start_btn)
        
        stop_btn = MDRaisedButton(text="Terminer")
        stop_btn.bind(on_release=self.terminer_session_etude)
        session_buttons.add_widget(stop_btn)
        
        session_layout.add_widget(session_buttons)
        session_card.add_widget(session_layout)
        layout.add_widget(session_card)
        
        # Statistiques
        stats_card = MDCard(
            elevation=2,
            padding="15dp",
            size_hint_y=None,
            height="200dp"
        )
        
        stats_layout = MDBoxLayout(orientation="vertical", spacing="5dp")
        
        stats_title = MDLabel(text="Statistiques", font_style="H6")
        stats_layout.add_widget(stats_title)
        
        self.temps_label = MDLabel(text="Temps total: 0 min")
        self.sessions_label = MDLabel(text="Sessions: 0") 
        self.matieres_label = MDLabel(text="Matières: 0")
        self.quiz_total_label = MDLabel(text="Quiz réalisés: 0")
        self.quiz_moyenne_label = MDLabel(text="Moyenne quiz: 0%")
        
        stats_layout.add_widget(self.temps_label)
        stats_layout.add_widget(self.sessions_label)
        stats_layout.add_widget(self.matieres_label)
        stats_layout.add_widget(self.quiz_total_label)
        stats_layout.add_widget(self.quiz_moyenne_label)
        
        stats_card.add_widget(stats_layout)
        layout.add_widget(stats_card)
        
        # Liste matières
        subjects_scroll = MDScrollView()
        self.subjects_list = MDList()
        subjects_scroll.add_widget(self.subjects_list)
        layout.add_widget(subjects_scroll)
        
        # Boutons
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        associate_btn = MDRaisedButton(text="Associer Note")
        associate_btn.bind(on_release=self.associer_note_dialogue)
        buttons_layout.add_widget(associate_btn)
        
        stats_btn = MDRaisedButton(text="Statistiques")
        stats_btn.bind(on_release=self.afficher_statistiques)
        buttons_layout.add_widget(stats_btn)
        
        layout.add_widget(buttons_layout)
        
        self.update_evolution_panel()
        return layout

    # === MÉTHODES DE GESTION DES SESSIONS D'ÉTUDE ===
    
    def demander_nouvelle_session(self, *args):
        """Dialogue pour démarrer une nouvelle session d'étude"""
        if self.session_actuelle:
            self.show_snackbar("Une session est déjà en cours!")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Champ matière
        self.session_matiere_field = MDTextField(
            hint_text="Matière à étudier",
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.session_matiere_field)
        
        # Champ objectif
        self.session_objectif_field = MDTextField(
            hint_text="Objectif de la session",
            multiline=True,
            size_hint_y=None,
            height="80dp"
        )
        content.add_widget(self.session_objectif_field)
        
        self.dialog = MDDialog(
            title="Nouvelle Session d'Étude",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Démarrer", on_release=self.demarrer_session_etude),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def demarrer_session_etude(self, *args):
        """Démarre une nouvelle session d'étude"""
        matiere = self.session_matiere_field.text.strip()
        objectif = self.session_objectif_field.text.strip()
        
        if not matiere:
            self.show_snackbar("Veuillez entrer une matière!")
            return
        
        # Créer la nouvelle session
        self.session_actuelle = {
            'id': len(self.sessions_etude) + 1,
            'matiere': matiere,
            'objectif': objectif,
            'date_debut': datetime.now(),
            'temps_ecoule': 0,
            'notes_creees': 0,
            'notes_modifiees': 0,
            'quiz_realises': 0,
            'active': True
        }
        
        # Ajouter ou mettre à jour la matière
        if matiere not in self.matieres:
            self.matieres[matiere] = {
                'nom': matiere,
                'temps_total': 0,
                'sessions': 0,
                'notes': [],
                'quiz_realises': 0,
                'quiz_scores': []
            }
        
        self.temps_debut_session = datetime.now()
        
        # Programmer la mise à jour du timer
        Clock.schedule_interval(self.update_session_timer, 1)
        
        self.close_dialog()
        self.update_evolution_panel()
        self.show_snackbar(f"Session d'étude '{matiere}' démarrée!")

    def update_session_timer(self, dt):
        """Met à jour le timer de la session en cours"""
        if not self.session_actuelle or not self.temps_debut_session:
            return False
        
        # Calculer le temps écoulé
        temps_ecoule = datetime.now() - self.temps_debut_session
        minutes_ecoulees = int(temps_ecoule.total_seconds() / 60)
        
        # Mettre à jour la session
        self.session_actuelle['temps_ecoule'] = minutes_ecoulees
        
        # Mettre à jour l'affichage
        heures = minutes_ecoulees // 60
        minutes = minutes_ecoulees % 60
        
        if heures > 0:
            temps_str = f"{heures}h {minutes}min"
        else:
            temps_str = f"{minutes}min"
        
        self.session_label.text = f"Session: {self.session_actuelle['matiere']} - {temps_str}"
        
        return True  # Continuer la programmation

    def terminer_session_etude(self, *args):
        """Termine la session d'étude en cours"""
        if not self.session_actuelle:
            self.show_snackbar("Aucune session active!")
            return
        
        # Arrêter le timer
        Clock.unschedule(self.update_session_timer)
        
        # Finaliser la session
        temps_final = datetime.now() - self.temps_debut_session
        minutes_finales = int(temps_final.total_seconds() / 60)
        
        self.session_actuelle['temps_ecoule'] = minutes_finales
        self.session_actuelle['date_fin'] = datetime.now()
        self.session_actuelle['active'] = False
        
        # Mettre à jour les statistiques de la matière
        matiere = self.session_actuelle['matiere']
        if matiere in self.matieres:
            self.matieres[matiere]['temps_total'] += minutes_finales
            self.matieres[matiere]['sessions'] += 1
        
        # Ajouter à l'historique des sessions
        self.sessions_etude.append(self.session_actuelle.copy())
        
        # Enregistrer l'activité
        self.enregistrer_activite('session', f"Session {matiere} - {minutes_finales}min")
        
        # Afficher le résumé
        self.afficher_resume_session()
        
        # Nettoyer la session actuelle
        self.session_actuelle = None
        self.temps_debut_session = None
        
        # Sauvegarder et mettre à jour l'affichage
        self.save_data()
        self.update_evolution_panel()

    def afficher_resume_session(self):
        """Affiche un résumé de la session terminée"""
        session = self.session_actuelle
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Statistiques de la session
        stats_text = f"""
Matière: {session['matiere']}
Durée: {session['temps_ecoule']} minutes
Notes créées: {session.get('notes_creees', 0)}
Notes modifiées: {session.get('notes_modifiees', 0)}
Quiz réalisés: {session.get('quiz_realises', 0)}
"""
        
        if session.get('objectif'):
            stats_text += f"\nObjectif: {session['objectif']}"
        
        stats_label = MDLabel(
            text=stats_text.strip(),
            font_style="Body1",
            size_hint_y=None
        )
        stats_label.bind(texture_size=stats_label.setter('size'))
        content.add_widget(stats_label)
        
        self.dialog = MDDialog(
            title="Session Terminée",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="OK", on_release=self.close_dialog)]
        )
        self.dialog.open()

    def update_evolution_panel(self):
        """Met à jour le panneau évolution avec les vraies statistiques"""
        # Calculer les statistiques totales
        temps_total = sum(session['temps_ecoule'] for session in self.sessions_etude)
        nombre_sessions = len(self.sessions_etude)
        nombre_matieres = len(self.matieres)
        
        # Statistiques des quiz
        total_quiz = sum(matiere.get('quiz_realises', 0) for matiere in self.matieres.values())
        scores_quiz = []
        for matiere in self.matieres.values():
            scores_quiz.extend(matiere.get('quiz_scores', []))
        
        moyenne_quiz = int(sum(scores_quiz) / len(scores_quiz)) if scores_quiz else 0
        
        # Mettre à jour les labels
        heures = temps_total // 60
        minutes = temps_total % 60
        
        if heures > 0:
            temps_str = f"{heures}h {minutes}min"
        else:
            temps_str = f"{minutes}min"
        
        self.temps_label.text = f"Temps total: {temps_str}"
        self.sessions_label.text = f"Sessions: {nombre_sessions}"
        self.matieres_label.text = f"Matières: {nombre_matieres}"
        self.quiz_total_label.text = f"Quiz réalisés: {total_quiz}"
        self.quiz_moyenne_label.text = f"Moyenne quiz: {moyenne_quiz}%"
        
        # Mettre à jour la liste des matières
        self.update_subjects_list()

    def update_subjects_list(self):
        """Met à jour la liste des matières"""
        if not hasattr(self, 'subjects_list'):
            return
        
        self.subjects_list.clear_widgets()
        
        for nom, matiere in self.matieres.items():
            temps_matiere = matiere.get('temps_total', 0)
            sessions_matiere = matiere.get('sessions', 0)
            
            heures = temps_matiere // 60
            minutes = temps_matiere % 60
            
            if heures > 0:
                temps_str = f"{heures}h {minutes}min"
            else:
                temps_str = f"{minutes}min"
            
            item = TwoLineListItem(
                text=nom,
                secondary_text=f"{sessions_matiere} sessions - {temps_str}"
            )
            self.subjects_list.add_widget(item)

    # === MÉTHODES PRINCIPALES ===
    
    def nouvelle_note(self, *args):
        """Crée une nouvelle note"""
        self.note_actuelle = None
        self.title_field.text = ""
        self.content_field.text = ""
        self.show_snackbar("Nouvelle note créée. Entrez le titre et le contenu.")

    def sauvegarder_note(self, *args):
        """Sauvegarde la note actuelle"""
        titre = self.title_field.text.strip()
        contenu = self.content_field.text.strip()
        
        if not titre:
            self.show_snackbar("Le titre ne peut pas être vide!")
            return
        
        if self.note_actuelle:
            # Modification d'une note existante
            self.note_actuelle['titre'] = titre
            self.note_actuelle['contenu'] = contenu
            self.note_actuelle['date_modification'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.enregistrer_activite('modification', f"Modification de {titre}")
            
            # Mettre à jour session si active
            if self.session_actuelle:
                self.session_actuelle['notes_modifiees'] = self.session_actuelle.get('notes_modifiees', 0) + 1
            
            message = "Note modifiée avec succès!"
        else:
            # Nouvelle note
            nouveau_id = max([note['id'] for note in self.notes_liste], default=0) + 1
            
            nouvelle_note = {
                'id': nouveau_id,
                'titre': titre,
                'contenu': contenu,
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': []
            }
            
            self.notes_liste.append(nouvelle_note)
            self.note_actuelle = nouvelle_note
            self.enregistrer_activite('creation', f"Création de {titre}")
            
            # Mettre à jour session si active
            if self.session_actuelle:
                self.session_actuelle['notes_creees'] = self.session_actuelle.get('notes_creees', 0) + 1
            
            message = "Nouvelle note sauvegardée!"
        
        self.update_notes_list()
        self.save_data()
        self.show_snackbar(message)

    def update_notes_list(self):
        """Met à jour la liste des notes"""
        if not hasattr(self, 'notes_list'):
            return
            
        self.notes_list.clear_widgets()
        
        notes_a_afficher = self.notes_filtrees if self.notes_filtrees else self.notes_liste
        notes_triees = sorted(notes_a_afficher, 
                            key=lambda x: x.get('date_creation', ''), 
                            reverse=True)
        
        for note in notes_triees:
            contenu_court = note['contenu'][:50] + "..." if len(note['contenu']) > 50 else note['contenu']
            date_affichage = note.get('date_creation', 'Inconnue')
            
            item = ThreeLineListItem(
                text=note['titre'],
                secondary_text=f"Créée: {date_affichage}",
                tertiary_text=contenu_court
            )
            item.bind(on_release=lambda x, note=note: self.select_note(note))
            self.notes_list.add_widget(item)

    def select_note(self, note):
        """Sélectionne une note"""
        self.note_actuelle = note
        self.title_field.text = note['titre']
        self.content_field.text = note['contenu']
        self.enregistrer_activite('lecture', f"Lecture de {note['titre']}")
        self.afficher_note_complete(note)

    def afficher_note_complete(self, note):
        """Affiche la note complète"""
        content = MDBoxLayout(
            orientation="vertical", 
            spacing="15dp", 
            adaptive_height=True,
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))
        
        info_text = f"Créée: {note.get('date_creation', 'Inconnue')}"
        if note.get('date_modification'):
            info_text += f"\nModifiée: {note['date_modification']}"
        
        info_label = MDLabel(
            text=info_text,
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(info_label)
        
        contenu_scroll = MDScrollView(
            size_hint=(1, None),
            height="300dp"
        )
        
        contenu_label = MDLabel(
            text=note['contenu'],
            font_style="Body1",
            text_size=(None, None),
            valign="top",
            markup=True,
            size_hint_y=None
        )
        contenu_label.text_size = (280, None)
        contenu_label.bind(texture_size=contenu_label.setter('size'))
        
        contenu_scroll.add_widget(contenu_label)
        content.add_widget(contenu_scroll)
        
        self.dialog = MDDialog(
            title=note['titre'],
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.8),
            buttons=[
                MDRaisedButton(text="Modifier", on_release=lambda x: self.modifier_note_actuelle()),
                MDRaisedButton(text="Fermer", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def modifier_note_actuelle(self):
        """Charge la note actuelle dans l'éditeur"""
        self.close_dialog()
        self.show_snackbar(f"Note '{self.note_actuelle['titre']}' chargée dans l'éditeur")

    def resumer_texte_intelligent(self, *args):
        """Résumé intelligent"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note à résumer!")
            return
        
        contenu = self.note_actuelle['contenu']
        
        if len(contenu) < 100:
            self.show_snackbar("Note trop courte pour être résumée")
            return
        
        resume = self.generer_resume_basique(contenu)
        
        content = MDBoxLayout(
            orientation="vertical", 
            spacing="15dp", 
            adaptive_height=True,
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))
        
        stats_label = MDLabel(
            text=f"Note originale: {len(contenu.split())} mots\nRésumé: {len(resume.split())} mots",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(stats_label)
        
        resume_scroll = MDScrollView(
            size_hint=(1, None),
            height="300dp"
        )
        
        resume_label = MDLabel(
            text=resume,
            font_style="Body1",
            text_size=(None, None),
            valign="top",
            markup=True,
            size_hint_y=None
        )
        resume_label.text_size = (280, None)
        resume_label.bind(texture_size=resume_label.setter('size'))
        
        resume_scroll.add_widget(resume_label)
        content.add_widget(resume_scroll)
        
        self.dialog = MDDialog(
            title=f"Résumé: {self.note_actuelle['titre']}",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.8),
            buttons=[MDRaisedButton(text="Fermer", on_release=self.close_dialog)]
        )
        self.dialog.open()

    def generer_resume_basique(self, texte):
        """Génère un résumé basique en extrayant les phrases importantes"""
        phrases = re.split(r'[.!?]+', texte)
        phrases = [p.strip() for p in phrases if len(p.strip()) > 20]
        
        if len(phrases) <= 3:
            return texte[:200] + "..." if len(texte) > 200 else texte
        
        # Prendre la première phrase, une du milieu, et une de la fin
        indices = [0, len(phrases)//2, -1]
        phrases_importantes = [phrases[i] for i in indices if i < len(phrases)]
        
        resume = '. '.join(phrases_importantes) + '.'
        
        # Limiter à 150 mots maximum
        mots_resume = resume.split()
        if len(mots_resume) > 150:
            resume = ' '.join(mots_resume[:150]) + '...'
        
        return resume

    # === MÉTHODES QUIZ COMPLÈTES ===
    
    def config_quiz_dialog(self, *args):
        """Dialog de configuration du quiz"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note pour créer un quiz!")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Nombre de questions
        self.quiz_nb_field = MDTextField(
            hint_text="Nombre de questions (3-10)",
            text="5",
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.quiz_nb_field)
        
        info_label = MDLabel(
            text="Le quiz sera généré automatiquement à partir du contenu de votre note.",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(info_label)
        
        self.dialog = MDDialog(
            title="Configuration Quiz",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Créer Quiz", on_release=self.generer_quiz_intelligent),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def generer_quiz_intelligent(self, *args):
        """Génère un quiz intelligent basé sur le contenu"""
        try:
            nb_questions = int(self.quiz_nb_field.text)
            if nb_questions < 3 or nb_questions > 10:
                nb_questions = 5
        except:
            nb_questions = 5
        
        self.quiz_nombre_questions = nb_questions
        contenu = self.note_actuelle['contenu']
        
        # Analyser le contenu
        mots_cles = self.extraire_mots_cles(contenu)
        definitions = self.extraire_definitions(contenu)
        phrases = re.split(r'[.!?]+', contenu)
        themes = self.identifier_themes(contenu, phrases)
        
        # Générer les questions
        questions = []
        types_questions = [
            self.question_definition_concept,
            self.question_mot_cle_contexte,
            self.question_theme_principal,
            self.question_vrai_faux,
            self.question_completion
        ]
        
        tentatives = 0
        while len(questions) < nb_questions and tentatives < 50:
            type_question = random.choice(types_questions)
            
            try:
                if type_question == self.question_definition_concept:
                    question = type_question(definitions, mots_cles)
                elif type_question == self.question_mot_cle_contexte:
                    question = type_question(mots_cles, contenu)
                elif type_question == self.question_theme_principal:
                    question = type_question(themes, contenu)
                elif type_question == self.question_vrai_faux:
                    question = type_question(contenu)
                elif type_question == self.question_completion:
                    question = type_question(phrases)
                
                if question and not self.question_existe_deja(question, questions):
                    questions.append(question)
            except:
                pass
            
            tentatives += 1
        
        if not questions:
            self.show_snackbar("Impossible de générer un quiz pour cette note")
            self.close_dialog()
            return
        
        self.quiz_questions = questions
        self.quiz_question_index = 0
        self.quiz_score = 0
        
        self.close_dialog()
        self.demarrer_quiz()

    def demarrer_quiz(self):
        """Démarre le quiz"""
        if not self.quiz_questions:
            self.show_snackbar("Aucune question disponible!")
            return
        
        self.afficher_question_quiz()

    def afficher_question_quiz(self):
        """Affiche la question actuelle du quiz"""
        if self.quiz_question_index >= len(self.quiz_questions):
            self.terminer_quiz()
            return
        
        question = self.quiz_questions[self.quiz_question_index]
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Progression
        progress_label = MDLabel(
            text=f"Question {self.quiz_question_index + 1}/{len(self.quiz_questions)}",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        content.add_widget(progress_label)
        
        # Question
        question_label = MDLabel(
            text=question['question'],
            font_style="Subtitle1",
            size_hint_y=None,
            height="60dp"
        )
        question_label.bind(texture_size=question_label.setter('size'))
        content.add_widget(question_label)
        
        # Options
        buttons = []
        for i, option in enumerate(question['options']):
            btn = MDRaisedButton(
                text=f"{chr(65+i)}. {option}",
                size_hint_y=None,
                height="48dp"
            )
            btn.bind(on_release=lambda x, index=i: self.repondre_quiz(index))
            buttons.append(btn)
            content.add_widget(btn)
        
        self.dialog = MDDialog(
            title=f"Quiz: {self.note_actuelle['titre']}",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.8)
        )
        self.dialog.open()

    def repondre_quiz(self, reponse_index):
        """Traite la réponse à une question"""
        question = self.quiz_questions[self.quiz_question_index]
        correct = reponse_index == question['correct']
        
        if correct:
            self.quiz_score += 1
        
        # Afficher la réponse
        self.afficher_reponse_quiz(question, reponse_index, correct)

    def afficher_reponse_quiz(self, question, reponse_index, correct):
        """Affiche la correction de la réponse"""
        self.close_dialog()
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Résultat
        resultat_text = "✓ Correct!" if correct else "✗ Incorrect"
        resultat_label = MDLabel(
            text=resultat_text,
            font_style="H6",
            theme_text_color="Primary" if correct else "Error",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(resultat_label)
        
        # Réponse donnée
        votre_reponse = MDLabel(
            text=f"Votre réponse: {question['options'][reponse_index]}",
            font_style="Body1",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(votre_reponse)
        
        # Bonne réponse
        if not correct:
            bonne_reponse = MDLabel(
                text=f"Bonne réponse: {question['options'][question['correct']]}",
                font_style="Body1",
                theme_text_color="Primary",
                size_hint_y=None,
                height="40dp"
            )
            content.add_widget(bonne_reponse)
        
        # Explication
        if question.get('explication'):
            explication = MDLabel(
                text=f"Explication: {question['explication']}",
                font_style="Caption",
                size_hint_y=None,
                height="60dp"
            )
            explication.bind(texture_size=explication.setter('size'))
            content.add_widget(explication)
        
        self.dialog = MDDialog(
            title="Résultat",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Suivant", on_release=self.question_suivante)]
        )
        self.dialog.open()

    def question_suivante(self, *args):
        """Passe à la question suivante"""
        self.close_dialog()
        self.quiz_question_index += 1
        self.afficher_question_quiz()

    def terminer_quiz(self):
        """Termine le quiz et affiche les résultats"""
        pourcentage = int((self.quiz_score / len(self.quiz_questions)) * 100)
        
        # Enregistrer dans les statistiques
        if self.session_actuelle:
            matiere = self.session_actuelle['matiere']
            if matiere in self.matieres:
                self.matieres[matiere]['quiz_realises'] = self.matieres[matiere].get('quiz_realises', 0) + 1
                if 'quiz_scores' not in self.matieres[matiere]:
                    self.matieres[matiere]['quiz_scores'] = []
                self.matieres[matiere]['quiz_scores'].append(pourcentage)
            
            self.session_actuelle['quiz_realises'] = self.session_actuelle.get('quiz_realises', 0) + 1
        
        # Afficher les résultats
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        score_label = MDLabel(
            text=f"Score: {self.quiz_score}/{len(self.quiz_questions)} ({pourcentage}%)",
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp"
        )
        content.add_widget(score_label)
        
        # Évaluation
        if pourcentage >= 80:
            evaluation = "Excellent! Vous maîtrisez bien le sujet."
        elif pourcentage >= 60:
            evaluation = "Bien! Continuez vos efforts."
        elif pourcentage >= 40:
            evaluation = "Passable. Il serait bon de réviser."
        else:
            evaluation = "À revoir. Relisez attentivement la note."
        
        eval_label = MDLabel(
            text=evaluation,
            font_style="Body1",
            size_hint_y=None,
            height="40dp"
        )
        content.add_widget(eval_label)
        
        self.dialog = MDDialog(
            title="Résultats du Quiz",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Terminer", on_release=self.close_quiz)]
        )
        self.dialog.open()
        
        # Sauvegarder
        self.save_data()
        self.update_evolution_panel()

    def close_quiz(self, *args):
        """Ferme le quiz"""
        self.close_dialog()
        self.quiz_questions = []
        self.quiz_actuel = None
        self.show_snackbar("Quiz terminé!")

    # === GÉNÉRATEURS DE QUESTIONS ===
    
    def extraire_mots_cles(self, texte):
        """Extrait les mots-clés du texte"""
        mots = re.findall(r'\b\w{4,}\b', texte.lower())
        mots_communs = {'dans', 'avec', 'pour', 'cette', 'sont', 'peut', 'plus', 'mais', 'tout', 'tous', 'leur', 'bien', 'aussi', 'très', 'encore', 'même', 'grand', 'comme', 'donc', 'depuis'}
        mots_filtres = [mot for mot in mots if mot not in mots_communs]
        
        compteur = Counter(mots_filtres)
        return [mot for mot, freq in compteur.most_common(10)]

    def identifier_themes(self, texte, phrases):
        """Identifie les thèmes principaux"""
        themes = []
        mots_cles = self.extraire_mots_cles(texte)
        
        for mot in mots_cles[:5]:
            theme_phrases = [p for p in phrases if mot in p.lower()]
            if theme_phrases:
                themes.append({
                    'mot_cle': mot,
                    'phrases': theme_phrases[:2]
                })
        
        return themes

    def extraire_definitions(self, texte):
        """Extrait les définitions du texte"""
        definitions = []
        phrases = re.split(r'[.!?]+', texte)
        
        for phrase in phrases:
            if any(pattern in phrase.lower() for pattern in ['est un', 'est une', 'désigne', 'correspond à', 'signifie']):
                parts = phrase.split(':')
                if len(parts) == 2:
                    definitions.append({
                        'terme': parts[0].strip(),
                        'definition': parts[1].strip()
                    })
                elif ' est ' in phrase.lower():
                    parts = phrase.lower().split(' est ')
                    if len(parts) == 2:
                        definitions.append({
                            'terme': parts[0].strip(),
                            'definition': parts[1].strip()
                        })
        
        return definitions[:3]

    def question_existe_deja(self, nouvelle_question, questions_existantes):
        """Vérifie si une question similaire existe déjà"""
        nouveau_texte = nouvelle_question['question'].lower()
        
        for question in questions_existantes:
            if question['question'].lower() == nouveau_texte:
                return True
            
            mots_nouveau = set(nouveau_texte.split())
            mots_existant = set(question['question'].lower().split())
            
            intersection = len(mots_nouveau & mots_existant)
            union = len(mots_nouveau | mots_existant)
            
            if union > 0 and intersection / union > 0.7:
                return True
        
        return False

    def question_definition_concept(self, definitions, mots_cles):
        """Génère une question sur une définition"""
        if not definitions:
            return None
        
        definition = random.choice(definitions)
        fausses_definitions = [
            "Une méthode d'analyse",
            "Un processus complexe", 
            "Un élément fondamental"
        ]
        
        options = [definition['definition']] + fausses_definitions
        random.shuffle(options)
        correct_index = options.index(definition['definition'])
        
        return {
            "question": f"Que signifie '{definition['terme']}'?",
            "options": options,
            "correct": correct_index,
            "explication": f"'{definition['terme']}' {definition['definition']}"
        }

    def question_mot_cle_contexte(self, mots_cles, contenu):
        """Question sur l'utilisation d'un mot-clé"""
        if not mots_cles:
            return None
        
        mot = random.choice(mots_cles)
        phrases = [p.strip() for p in re.split(r'[.!?]+', contenu) if mot.lower() in p.lower()]
        
        if not phrases:
            return None
        
        phrase_vraie = phrases[0][:80] + "..." if len(phrases[0]) > 80 else phrases[0]
        
        fausses_phrases = [
            "Ce terme n'apparaît pas dans la note",
            "Il est mentionné seulement en conclusion",
            "Il est défini au début du texte"
        ]
        
        options = [phrase_vraie] + fausses_phrases
        random.shuffle(options)
        correct_index = options.index(phrase_vraie)
        
        return {
            "question": f"Comment le mot '{mot}' est-il utilisé dans le texte?",
            "options": options,
            "correct": correct_index,
            "explication": f"Le mot '{mot}' apparaît dans ce contexte."
        }

    def question_theme_principal(self, themes, contenu):
        """Question sur le thème principal"""
        if not themes:
            return None
        
        theme = random.choice(themes)
        faux_themes = ["analyse comparative", "étude historique", "recherche empirique"]
        
        options = [f"Le thème de '{theme['mot_cle']}'"] + [f"Le thème de '{t}'" for t in faux_themes]
        random.shuffle(options)
        correct_index = options.index(f"Le thème de '{theme['mot_cle']}'")
        
        return {
            "question": "Quel est l'un des thèmes principaux du texte?",
            "options": options,
            "correct": correct_index,
            "explication": f"Le thème principal concerne '{theme['mot_cle']}' comme mentionné dans le texte."
        }

    def question_vrai_faux(self, contenu):
        """Génère une question vrai/faux"""
        phrases = [p.strip() for p in re.split(r'[.!?]+', contenu) if len(p.strip()) > 20]
        if not phrases:
            return None
        
        phrase_vraie = random.choice(phrases)
        if len(phrase_vraie) > 100:
            phrase_vraie = phrase_vraie[:100] + "..."
        
        # 50% de chance de garder la phrase vraie
        if random.choice([True, False]):
            return {
                "question": f"Vrai ou Faux: {phrase_vraie}",
                "options": ["Vrai", "Faux"],
                "correct": 0,
                "explication": "Cette affirmation est présente dans le texte."
            }
        else:
            # Modifier légèrement la phrase pour la rendre fausse
            phrase_modifiee = phrase_vraie.replace(" est ", " n'est pas ").replace(" a ", " n'a pas ")
            return {
                "question": f"Vrai ou Faux: {phrase_modifiee}",
                "options": ["Vrai", "Faux"],
                "correct": 1,
                "explication": "Cette affirmation est modifiée par rapport au texte original."
            }

    def question_completion(self, phrases):
        """Génère une question à compléter"""
        if not phrases:
            return None
        
        phrase_complete = random.choice([p.strip() for p in phrases if len(p.strip()) > 30])
        if not phrase_complete:
            return None
        
        mots = phrase_complete.split()
        if len(mots) < 5:
            return None
        
        # Enlever un mot important (pas les articles/prépositions)
        mots_importants = [i for i, mot in enumerate(mots) if len(mot) > 3 and mot.lower() not in ['dans', 'avec', 'pour', 'cette']]
        
        if not mots_importants:
            return None
        
        index_mot = random.choice(mots_importants)
        mot_manquant = mots[index_mot]
        
        # Créer la phrase à trous
        phrase_incomplete = ' '.join(mots[:index_mot] + ['_____'] + mots[index_mot+1:])
        
        # Options
        faux_mots = ["analyse", "processus", "élément", "méthode"]
        options = [mot_manquant] + faux_mots[:3]
        random.shuffle(options)
        correct_index = options.index(mot_manquant)
        
        return {
            "question": f"Complétez la phrase: {phrase_incomplete}",
            "options": options,
            "correct": correct_index,
            "explication": f"Le mot correct est '{mot_manquant}'"
        }

    # === MÉTHODES UTILITAIRES ===
    
    def filter_notes(self, instance, text):
        """Filtre les notes selon le texte de recherche"""
        if not text.strip():
            self.notes_filtrees = []
        else:
            self.notes_filtrees = [
                note for note in self.notes_liste
                if text.lower() in note['titre'].lower() or text.lower() in note['contenu'].lower()
            ]
        self.update_notes_list()

    def effacer_recherche(self, *args):
        """Efface la recherche"""
        self.search_field.text = ""
        self.notes_filtrees = []
        self.update_notes_list()

    def supprimer_note_dialog(self, *args):
        """Dialog de suppression de note"""
        if not self.note_actuelle:
            self.show_snackbar("Aucune note sélectionnée!")
            return
        
        self.dialog = MDDialog(
            text=f"Êtes-vous sûr de vouloir supprimer la note '{self.note_actuelle['titre']}'?",
            buttons=[
                MDRaisedButton(text="Supprimer", on_release=self.supprimer_note),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def supprimer_note(self, *args):
        """Supprime la note actuelle"""
        if self.note_actuelle in self.notes_liste:
            self.notes_liste.remove(self.note_actuelle)
            self.update_notes_list()
            self.save_data()
            
            # Vider l'éditeur
            self.title_field.text = ""
            self.content_field.text = ""
            self.note_actuelle = None
            
            self.close_dialog()
            self.show_snackbar("Note supprimée!")

    def partager_note_dialog(self, *args):
        """Dialog de partage de note"""
        if not self.note_actuelle:
            self.show_snackbar("Aucune note sélectionnée!")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        self.email_field = MDTextField(
            hint_text="Email destinataire",
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.email_field)
        
        self.dialog = MDDialog(
            title="Partager la note",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Envoyer", on_release=self.partager_note),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def partager_note(self, *args):
        """Partage la note par email (simulation)"""
        email = self.email_field.text.strip()
        if not email:
            self.show_snackbar("Veuillez entrer un email!")
            return
        
        self.close_dialog()
        self.show_snackbar(f"Note partagée avec {email}!")

    def ajouter_rappel_dialog(self, *args):
        """Dialog pour ajouter un rappel"""
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        self.rappel_titre_field = MDTextField(
            hint_text="Titre du rappel",
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.rappel_titre_field)
        
        self.rappel_date_field = MDTextField(
            hint_text="Date (YYYY-MM-DD HH:MM)",
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.rappel_date_field)
        
        self.dialog = MDDialog(
            title="Nouveau Rappel",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Ajouter", on_release=self.ajouter_rappel),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def ajouter_rappel(self, *args):
        """Ajoute un nouveau rappel"""
        titre = self.rappel_titre_field.text.strip()
        date_str = self.rappel_date_field.text.strip()
        
        if not titre or not date_str:
            self.show_snackbar("Veuillez remplir tous les champs!")
            return
        
        try:
            date_rappel = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except:
            self.show_snackbar("Format de date invalide!")
            return
        
        rappel = {
            'id': len(self.rappels_liste) + 1,
            'titre': titre,
            'date': date_rappel.strftime("%Y-%m-%d %H:%M"),
            'active': True
        }
        
        self.rappels_liste.append(rappel)
        self.update_reminders_list()
        self.save_data()
        
        self.close_dialog()
        self.show_snackbar("Rappel ajouté!")

    def update_reminders_list(self):
        """Met à jour la liste des rappels"""
        if not hasattr(self, 'reminders_list'):
            return
        
        self.reminders_list.clear_widgets()
        
        for rappel in sorted(self.rappels_liste, key=lambda x: x['date']):
            item = TwoLineListItem(
                text=rappel['titre'],
                secondary_text=f"Date: {rappel['date']}"
            )
            self.reminders_list.add_widget(item)

    def associer_note_dialogue(self, *args):
        """Dialog pour associer une note à une matière"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note à associer!")
            return
        
        if not self.matieres:
            self.show_snackbar("Aucune matière disponible! Créez une session d'étude d'abord.")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Liste des matières
        for nom_matiere in self.matieres.keys():
            btn = MDRaisedButton(
                text=nom_matiere,
                size_hint_y=None,
                height="48dp"
            )
            btn.bind(on_release=lambda x, matiere=nom_matiere: self.associer_note_matiere(matiere))
            content.add_widget(btn)
        
        self.dialog = MDDialog(
            title="Associer à une matière",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Annuler", on_release=self.close_dialog)]
        )
        self.dialog.open()

    def associer_note_matiere(self, matiere):
        """Associe la note actuelle à une matière"""
        if matiere in self.matieres:
            if 'notes' not in self.matieres[matiere]:
                self.matieres[matiere]['notes'] = []
            
            # Éviter les doublons
            note_id = self.note_actuelle['id']
            if note_id not in self.matieres[matiere]['notes']:
                self.matieres[matiere]['notes'].append(note_id)
                self.save_data()
                self.close_dialog()
                self.show_snackbar(f"Note associée à {matiere}!")
            else:
                self.close_dialog()
                self.show_snackbar("Note déjà associée à cette matière!")

    def afficher_statistiques(self, *args):
        """Affiche les statistiques détaillées"""
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Statistiques générales
        total_notes = len(self.notes_liste)
        temps_total = sum(session['temps_ecoule'] for session in self.sessions_etude)
        
        stats_text = f"""
📊 STATISTIQUES GÉNÉRALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Notes: {total_notes}
⏱️ Temps total d'étude: {temps_total // 60}h {temps_total % 60}min
📚 Sessions d'étude: {len(self.sessions_etude)}
🎯 Matières étudiées: {len(self.matieres)}

📈 DÉTAIL PAR MATIÈRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for nom, matiere in self.matieres.items():
            temps_matiere = matiere.get('temps_total', 0)
            sessions_matiere = matiere.get('sessions', 0)
            quiz_realises = matiere.get('quiz_realises', 0)
            scores_quiz = matiere.get('quiz_scores', [])
            moyenne_quiz = int(sum(scores_quiz) / len(scores_quiz)) if scores_quiz else 0
            
            stats_text += f"""
📚 {nom}:
   • Temps: {temps_matiere // 60}h {temps_matiere % 60}min
   • Sessions: {sessions_matiere}
   • Quiz: {quiz_realises} (moyenne: {moyenne_quiz}%)
   • Notes associées: {len(matiere.get('notes', []))}
"""
        
        scroll_stats = MDScrollView(
            size_hint=(1, None),
            height="400dp"
        )
        
        stats_label = MDLabel(
            text=stats_text,
            font_style="Body2",
            text_size=(None, None),
            valign="top",
            size_hint_y=None
        )
        stats_label.text_size = (300, None)
        stats_label.bind(texture_size=stats_label.setter('size'))
        
        scroll_stats.add_widget(stats_label)
        content.add_widget(scroll_stats)
        
        self.dialog = MDDialog(
            title="Statistiques Détaillées",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.8),
            buttons=[MDRaisedButton(text="Fermer", on_release=self.close_dialog)]
        )
        self.dialog.open()

    def ouvrir_config_api(self, *args):
        """Ouvre la configuration API"""
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        self.api_key_field = MDTextField(
            hint_text="Clé API (optionnel)",
            text=self.api_key,
            size_hint_y=None,
            height="48dp"
        )
        content.add_widget(self.api_key_field)
        
        info_label = MDLabel(
            text="La clé API permettrait d'améliorer les fonctionnalités de résumé et quiz.",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="60dp"
        )
        content.add_widget(info_label)
        
        self.dialog = MDDialog(
            title="Configuration API",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Sauvegarder", on_release=self.sauvegarder_config_api),
                MDRaisedButton(text="Annuler", on_release=self.close_dialog)
            ]
        )
        self.dialog.open()

    def sauvegarder_config_api(self, *args):
        """Sauvegarde la configuration API"""
        self.api_key = self.api_key_field.text.strip()
        self.save_data()
        self.close_dialog()
        self.show_snackbar("Configuration sauvegardée!")

    # === MÉTHODES DE STOCKAGE ET UTILITAIRES ===
    
    def init_storage(self):
        """Initialise le système de stockage"""
        try:
            if platform == 'android':
                from android.storage import primary_external_storage_path
                storage_path = primary_external_storage_path()
                self.store = JsonStore(os.path.join(storage_path, 'studyhelper_data.json'))
            else:
                self.store = JsonStore('studyhelper_data.json')
            
            self.load_data()
        except Exception as e:
            print(f"Erreur d'initialisation du stockage: {e}")
            self.store = None

    def save_data(self):
        """Sauvegarde toutes les données"""
        if not self.store:
            return
        
        try:
            # Convertir les objets datetime en strings pour la sérialisation
            sessions_serialisables = []
            for session in self.sessions_etude:
                session_copy = session.copy()
                if 'date_debut' in session_copy and isinstance(session_copy['date_debut'], datetime):
                    session_copy['date_debut'] = session_copy['date_debut'].strftime("%Y-%m-%d %H:%M:%S")
                if 'date_fin' in session_copy and isinstance(session_copy['date_fin'], datetime):
                    session_copy['date_fin'] = session_copy['date_fin'].strftime("%Y-%m-%d %H:%M:%S")
                sessions_serialisables.append(session_copy)
            
            data = {
                'notes': self.notes_liste,
                'rappels': self.rappels_liste,
                'matieres': self.matieres,
                'sessions': sessions_serialisables,
                'api_key': self.api_key,
                'email_config': self.email_config
            }
            
            self.store.put('app_data', **data)
            
        except Exception as e:
            print(f"Erreur de sauvegarde: {e}")

    def load_data(self):
        """Charge toutes les données"""
        if not self.store:
            return
        
        try:
            if self.store.exists('app_data'):
                data = self.store.get('app_data')
                
                self.notes_liste = data.get('notes', [])
                self.rappels_liste = data.get('rappels', [])
                self.matieres = data.get('matieres', {})
                self.api_key = data.get('api_key', '')
                self.email_config.update(data.get('email_config', {}))
                
                # Charger et convertir les sessions
                sessions_data = data.get('sessions', [])
                self.sessions_etude = []
                for session in sessions_data:
                    session_copy = session.copy()
                    # Reconvertir les dates
                    if 'date_debut' in session_copy and isinstance(session_copy['date_debut'], str):
                        try:
                            session_copy['date_debut'] = datetime.strptime(session_copy['date_debut'], "%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                    if 'date_fin' in session_copy and isinstance(session_copy['date_fin'], str):
                        try:
                            session_copy['date_fin'] = datetime.strptime(session_copy['date_fin'], "%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                    self.sessions_etude.append(session_copy)
        
        except Exception as e:
            print(f"Erreur de chargement: {e}")

    def enregistrer_activite(self, type_activite, description):
        """Enregistre une activité (pour statistiques futures)"""
        # Cette méthode peut être étendue pour un historique plus détaillé
        pass

    def show_snackbar(self, message):
        """Affiche un message snackbar"""
        snackbar = Snackbar(
            text=message,
            snackbar_x="10dp",
            snackbar_y="10dp",
        )
        snackbar.size_hint_x = (
            Window.width - (snackbar.snackbar_x * 2)
        ) / Window.width if hasattr(self, 'Window') else 0.9
        snackbar.open()

    def close_dialog(self, *args):
        """Ferme le dialogue ouvert"""
        if self.dialog:
            self.dialog.dismiss()

    def on_start(self):
        """Méthode appelée au démarrage de l'app"""
        # Programmer la vérification des rappels
        Clock.schedule_interval(self.verifier_rappels, 60)  # Chaque minute

    def verifier_rappels(self, dt):
        """Vérifie les rappels à échéance"""
        maintenant = datetime.now()
        
        for rappel in self.rappels_liste:
            if rappel.get('active', True):
                try:
                    date_rappel = datetime.strptime(rappel['date'], "%Y-%m-%d %H:%M")
                    
                    # Si le rappel est dans les 5 minutes
                    if abs((date_rappel - maintenant).total_seconds()) < 300:
                        self.show_snackbar(f"Rappel: {rappel['titre']}")
                        rappel['active'] = False  # Marquer comme traité
                        self.save_data()
                        
                except Exception as e:
                    print(f"Erreur rappel: {e}")
        
        return True

    def on_pause(self):
        """Gère la mise en pause de l'app"""
        self.save_data()
        return True

    def on_resume(self):
        """Gère la reprise de l'app"""
        pass

    def on_stop(self):
        """Gère l'arrêt de l'app"""
        # Sauvegarder avant fermeture
        if self.session_actuelle:
            # Terminer automatiquement la session en cours
            Clock.unschedule(self.update_session_timer)
            
            temps_final = datetime.now() - self.temps_debut_session
            minutes_finales = int(temps_final.total_seconds() / 60)
            
            self.session_actuelle['temps_ecoule'] = minutes_finales
            self.session_actuelle['date_fin'] = datetime.now()
            self.session_actuelle['active'] = False
            
            # Mettre à jour les statistiques
            matiere = self.session_actuelle['matiere']
            if matiere in self.matieres:
                self.matieres[matiere]['temps_total'] += minutes_finales
                self.matieres[matiere]['sessions'] += 1
            
            self.sessions_etude.append(self.session_actuelle.copy())
        
        self.save_data()


# Point d'entrée principal
def main():
    """Fonction principale pour lancer l'application"""
    try:
        # Import pour Window si nécessaire
        from kivy.core.window import Window
        
        app = StudyHelperApp()
        app.run()
    except Exception as e:
        print(f"Erreur de lancement: {e}")


if __name__ == '__main__':
    main()