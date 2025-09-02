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

import os
import json
from datetime import datetime, timedelta


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
        
        content_layout = MDBoxLayout(orientation="vertical")
        
        self.content_field = MDTextField(
            hint_text="Contenu de la note...",
            multiline=True
        )
        content_layout.add_widget(self.content_field)
        content_card.add_widget(content_layout)
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
        quiz_btn.bind(on_release=self.generer_quiz_interactif)
        tools_layout.add_widget(quiz_btn)
        
        resume_btn = MDRaisedButton(text="Résumé")
        resume_btn.bind(on_release=self.resumer_texte_intelligent) 
        tools_layout.add_widget(resume_btn)
        
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
            height="150dp"
        )
        
        stats_layout = MDBoxLayout(orientation="vertical", spacing="5dp")
        
        stats_title = MDLabel(text="Statistiques", font_style="H6")
        stats_layout.add_widget(stats_title)
        
        self.temps_label = MDLabel(text="Temps total: 0 min")
        self.sessions_label = MDLabel(text="Sessions: 0") 
        self.matieres_label = MDLabel(text="Matières: 0")
        
        stats_layout.add_widget(self.temps_label)
        stats_layout.add_widget(self.sessions_label)
        stats_layout.add_widget(self.matieres_label)
        
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

    # Fonctions principales
    def nouvelle_note(self, *args):
        """Crée une nouvelle note"""
        self.note_actuelle = None
        self.title_field.text = ""
        self.content_field.text = ""
        self.show_snackbar("Nouvelle note créée")

    def sauvegarder_note(self, *args):
        """Sauvegarde la note actuelle"""
        titre = self.title_field.text.strip()
        contenu = self.content_field.text.strip()
        
        if not titre:
            self.show_snackbar("Le titre ne peut pas être vide!")
            return
        
        if self.note_actuelle:
            # Modification
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
        
        self.update_notes_list()
        self.save_data()
        self.show_snackbar("Note sauvegardée!")

    def update_notes_list(self):
        """Met à jour la liste des notes"""
        if not hasattr(self, 'notes_list'):
            return
            
        self.notes_list.clear_widgets()
        
        notes_a_afficher = self.notes_filtrees if self.notes_filtrees else self.notes_liste
        
        for note in notes_a_afficher:
            contenu_court = note['contenu'][:50] + "..." if len(note['contenu']) > 50 else note['contenu']
            
            item = ThreeLineListItem(
                text=note['titre'],
                secondary_text=note['date_creation'],
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
        self.show_snackbar(f"Note sélectionnée: {note['titre']}")

    def filter_notes(self, instance, text):
        """Filtre les notes"""
        terme = text.lower()
        
        if not terme:
            self.notes_filtrees = []
        else:
            self.notes_filtrees = [note for note in self.notes_liste 
                                 if terme in note['titre'].lower() or 
                                    terme in note['contenu'].lower()]
        
        self.update_notes_list()

    def effacer_recherche(self, *args):
        """Efface la recherche"""
        self.search_field.text = ""
        self.notes_filtrees = []
        self.update_notes_list()

    def supprimer_note_dialog(self, *args):
        """Dialog de suppression"""
        if not self.note_actuelle:
            self.show_snackbar("Aucune note sélectionnée!")
            return
        
        self.dialog = MDDialog(
            title="Supprimer la note",
            text=f"Supprimer '{self.note_actuelle['titre']}'?",
            buttons=[
                MDRaisedButton(text="ANNULER", on_release=self.close_dialog),
                MDRaisedButton(text="SUPPRIMER", on_release=self.confirm_delete_note)
            ]
        )
        self.dialog.open()

    def confirm_delete_note(self, *args):
        """Confirme la suppression"""
        if self.note_actuelle:
            self.notes_liste = [note for note in self.notes_liste if note['id'] != self.note_actuelle['id']]
            
            # Réassigner les IDs
            for i, note in enumerate(self.notes_liste):
                note['id'] = i + 1
            
            self.title_field.text = ""
            self.content_field.text = ""
            self.note_actuelle = None
            
            self.update_notes_list()
            self.save_data()
            self.show_snackbar("Note supprimée!")
        
        self.close_dialog()

    def partager_note_dialog(self, *args):
        """Dialog de partage"""
        if not self.note_actuelle:
            self.show_snackbar("Aucune note sélectionnée!")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)
        
        self.share_email_field = MDTextField(hint_text="Email destinataire")
        content.add_widget(self.share_email_field)
        
        self.dialog = MDDialog(
            title="Partager la note",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="ANNULER", on_release=self.close_dialog),
                MDRaisedButton(text="PARTAGER", on_release=self.confirm_share_note)
            ]
        )
        self.dialog.open()

    def confirm_share_note(self, *args):
        """Confirme le partage"""
        email = self.share_email_field.text.strip()
        if email:
            self.show_snackbar(f"Note partagée avec {email}!")
            self.close_dialog()
        else:
            self.show_snackbar("Email requis!")

    # Rappels
    def update_reminders_list(self):
        """Met à jour la liste des rappels"""
        if not hasattr(self, 'reminders_list'):
            return
            
        self.reminders_list.clear_widgets()
        
        for rappel in self.rappels_liste:
            if rappel['actif']:
                item = TwoLineListItem(
                    text=rappel['titre'],
                    secondary_text=rappel['date_heure']
                )
                self.reminders_list.add_widget(item)

    def ajouter_rappel_dialog(self, *args):
        """Dialog pour ajouter un rappel"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)
        
        self.reminder_title_field = MDTextField(hint_text="Titre du rappel")
        content.add_widget(self.reminder_title_field)
        
        self.reminder_date_field = MDTextField(
            hint_text="Date (YYYY-MM-DD)",
            text=datetime.now().strftime("%Y-%m-%d")
        )
        content.add_widget(self.reminder_date_field)
        
        self.reminder_time_field = MDTextField(
            hint_text="Heure (HH:MM)",
            text="09:00"
        )
        content.add_widget(self.reminder_time_field)
        
        self.dialog = MDDialog(
            title="Nouveau Rappel",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="ANNULER", on_release=self.close_dialog),
                MDRaisedButton(text="AJOUTER", on_release=self.save_reminder)
            ]
        )
        self.dialog.open()

    def save_reminder(self, *args):
        """Sauvegarde un rappel"""
        titre = self.reminder_title_field.text.strip()
        date_str = self.reminder_date_field.text.strip()
        heure_str = self.reminder_time_field.text.strip()
        
        if not titre:
            self.show_snackbar("Titre requis!")
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
            self.update_reminders_list()
            self.save_data()
            self.show_snackbar("Rappel ajouté!")
            self.close_dialog()
        except ValueError:
            self.show_snackbar("Format date/heure invalide!")

    # Sessions d'étude
    def demander_nouvelle_session(self, *args):
        """Dialog pour nouvelle session"""
        if self.session_actuelle:
            self.dialog = MDDialog(
                title="Session en cours",
                text="Une session est active. La terminer?",
                buttons=[
                    MDRaisedButton(text="NON", on_release=self.close_dialog),
                    MDRaisedButton(text="OUI", on_release=self.terminer_et_nouvelle_session)
                ]
            )
            self.dialog.open()
        else:
            self.show_session_dialog()

    def show_session_dialog(self):
        """Affiche le dialog de session"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)
        
        self.session_subject_field = MDTextField(hint_text="Nom de la matière")
        content.add_widget(self.session_subject_field)
        
        self.dialog = MDDialog(
            title="Nouvelle Session",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="ANNULER", on_release=self.close_dialog),
                MDRaisedButton(text="DÉMARRER", on_release=self.start_session_from_dialog)
            ]
        )
        self.dialog.open()

    def start_session_from_dialog(self, *args):
        """Démarre session depuis dialog"""
        matiere = self.session_subject_field.text.strip()
        
        if not matiere:
            self.show_snackbar("Entrez le nom de la matière!")
            return
        
        note_id = None
        if self.note_actuelle:
            note_id = self.note_actuelle.get('id')
            self.associer_note_matiere(note_id, matiere)
        
        self.demarrer_session_etude(matiere, note_id)
        self.update_evolution_panel()
        self.close_dialog()
        self.show_snackbar(f"Session démarrée pour {matiere}!")

    def terminer_et_nouvelle_session(self, *args):
        """Termine session et en démarre une nouvelle"""
        self.terminer_session_etude()
        self.close_dialog()
        self.show_session_dialog()

    def demarrer_session_etude(self, matiere, note_id=None):
        """Démarre une session d'étude"""
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
        
        self.update_session_interface()

    def terminer_session_etude(self, *args):
        """Termine la session actuelle"""
        if not self.session_actuelle:
            self.show_snackbar("Aucune session active!")
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
        if total_sessions > 0:
            self.matieres[matiere]['progression']['temps_moyen_session'] = self.matieres[matiere]['temps_total'] / total_sessions
        
        self.session_actuelle = None
        self.temps_debut_session = None
        
        self.save_data()
        self.update_session_interface()
        self.show_snackbar(f"Session terminée: {duree:.1f} min")

    def enregistrer_activite(self, type_activite, details=None):
        """Enregistre une activité"""
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

    def associer_note_dialogue(self, *args):
        """Dialog pour associer note à matière"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note!")
            return
        
        content = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)
        
        self.associate_subject_field = MDTextField(hint_text="Nom de la matière")
        content.add_widget(self.associate_subject_field)
        
        self.dialog = MDDialog(
            title="Associer à une matière",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="ANNULER", on_release=self.close_dialog),
                MDRaisedButton(text="ASSOCIER", on_release=self.confirm_associate_note)
            ]
        )
        self.dialog.open()

    def confirm_associate_note(self, *args):
        """Confirme l'association"""
        matiere = self.associate_subject_field.text.strip()
        if matiere and self.note_actuelle:
            self.associer_note_matiere(self.note_actuelle['id'], matiere)
            self.update_evolution_panel()
            self.show_snackbar(f"Note associée à {matiere}!")
        self.close_dialog()

    def update_session_interface(self):
        """Met à jour l'interface de session"""
        try:
            if hasattr(self, 'session_label'):
                if self.session_actuelle:
                    duree = (datetime.now() - self.temps_debut_session).total_seconds() / 60
                    self.session_label.text = f"Session: {self.session_actuelle['matiere']} ({duree:.0f} min)"
                else:
                    self.session_label.text = "Aucune session active"
        except:
            pass

    def update_evolution_panel(self):
        """Met à jour le panel d'évolution"""
        try:
            if not hasattr(self, 'temps_label'):
                return
                
            stats = self.calculer_statistiques_globales()
            self.temps_label.text = f"Temps total: {stats['temps_total_global']:.0f} min"
            self.sessions_label.text = f"Sessions: {stats['sessions_total']}"
            self.matieres_label.text = f"Matières: {stats['matieres_etudiees']}"
            
            # Mettre à jour la liste des matières
            if hasattr(self, 'subjects_list'):
                self.subjects_list.clear_widgets()
                for matiere, data in self.matieres.items():
                    temps = data['temps_total']
                    item = TwoLineListItem(
                        text=matiere,
                        secondary_text=f"Temps: {temps:.0f} min | Sessions: {data['sessions']}"
                    )
                    self.subjects_list.add_widget(item)
        except Exception as e:
            print(f"Erreur update_evolution_panel: {e}")

    def calculer_statistiques_globales(self):
        """Calcule les statistiques globales"""
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
        """Calcule la progression de la semaine"""
        maintenant = datetime.now()
        debut_semaine = maintenant - timedelta(days=maintenant.weekday())
        
        sessions_semaine = [s for s in self.sessions_etude 
                          if datetime.strptime(s['date'], "%Y-%m-%d %H:%M") >= debut_semaine]
        
        return {
            'sessions': len(sessions_semaine),
            'temps': sum(s['duree'] for s in sessions_semaine),
            'matieres': len(set(s['matiere'] for s in sessions_semaine))
        }

    def afficher_statistiques(self, *args):
        """Affiche les statistiques détaillées"""
        if not self.notes_liste and not self.sessions_etude:
            self.show_snackbar("Aucune donnée disponible")
            return
        
        stats = self.calculer_statistiques_globales()
        
        # Note la plus longue
        note_plus_longue = ""
        if self.notes_liste:
            note_longue = max(self.notes_liste, key=lambda n: len(n['contenu']))
            note_plus_longue = f"Note la plus longue: {note_longue['titre']}"
        
        # Note la plus récente
        note_plus_recente = ""
        if self.notes_liste:
            note_recente = max(self.notes_liste, key=lambda n: n['date_creation'])
            note_plus_recente = f"Note récente: {note_recente['titre']}"
        
        stats_text = f"""Statistiques Globales:

Total notes: {stats['notes_total']}
Total sessions: {stats['sessions_total']}
Temps total: {stats['temps_total_global']:.1f} min
Matières étudiées: {stats['matieres_etudiees']}

{note_plus_longue}
{note_plus_recente}

Progression cette semaine:
- Sessions: {stats['progression_semaine']['sessions']}
- Temps: {stats['progression_semaine']['temps']:.1f} min
"""
        
        self.dialog = MDDialog(
            title="Statistiques",
            text=stats_text,
            buttons=[MDRaisedButton(text="OK", on_release=self.close_dialog)]
        )
        self.dialog.open()

    # Fonctions IA et outils
    def generer_quiz_interactif(self, *args):
        """Génère un quiz interactif"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note pour le quiz!")
            return
        
        self.dialog = MDDialog(
            title="Quiz Interactif",
            text=f"Quiz pour: {self.note_actuelle['titre']}\n(Fonction IA - configurez l'API)",
            buttons=[MDRaisedButton(text="OK", on_release=self.close_dialog)]
        )
        self.dialog.open()

    def resumer_texte_intelligent(self, *args):
        """Résumé intelligent"""
        if not self.note_actuelle:
            self.show_snackbar("Sélectionnez une note à résumer!")
            return
        
        self.dialog = MDDialog(
            title="Résumé Intelligent", 
            text=f"Résumé pour: {self.note_actuelle['titre']}\n(Fonction IA - configurez l'API)",
            buttons=[MDRaisedButton(text="OK", on_release=self.close_dialog)]
        )
        self.dialog.open()

    # Stockage
    def init_storage(self):
        """Initialise le stockage"""
        try:
            if platform == 'android':
                try:
                    from android.permissions import request_permissions, Permission
                    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
                except:
                    pass
                
                try:
                    app_dir = "/storage/emulated/0/StudyHelper"
                    if not os.path.exists(app_dir):
                        os.makedirs(app_dir)
                    self.store = JsonStore(os.path.join(app_dir, 'studyhelper.json'))
                except:
                    self.store = JsonStore('studyhelper.json')
            else:
                app_dir = os.path.expanduser("~/StudyHelper")
                if not os.path.exists(app_dir):
                    os.makedirs(app_dir)
                self.store = JsonStore(os.path.join(app_dir, 'studyhelper.json'))
            
            self.load_data()
        except Exception as e:
            print(f"Erreur stockage: {e}")
            try:
                self.store = JsonStore('studyhelper_backup.json')
            except:
                self.store = None

    def save_data(self):
        """Sauvegarde les données"""
        if not self.store:
            return
        
        try:
            donnees = {
                'notes': self.notes_liste,
                'rappels': self.rappels_liste,
                'matieres': self.matieres,
                'sessions_etude': self.sessions_etude,
                'email_config': self.email_config,
                'api_key': self.api_key
            }
            
            self.store.put('app_data', **donnees)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")

    def load_data(self):
        """Charge les données"""
        if not self.store:
            return
        
        try:
            if self.store.exists('app_data'):
                data = self.store.get('app_data')
                self.notes_liste = data.get('notes', [])
                self.rappels_liste = data.get('rappels', [])
                self.matieres = data.get('matieres', {})
                self.sessions_etude = data.get('sessions_etude', [])
                self.email_config.update(data.get('email_config', {}))
                self.api_key = data.get('api_key', '')
        except Exception as e:
            print(f"Erreur chargement: {e}")

    # Utilitaires
    def show_snackbar(self, message):
        """Affiche un snackbar"""
        try:
            Snackbar(text=message, duration=3).open()
        except:
            print(f"Message: {message}")

    def close_dialog(self, *args):
        """Ferme le dialog"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    # Vérification rappels
    def verifier_rappels(self, dt):
        """Vérifie les rappels"""
        maintenant = datetime.now()
        
        for rappel in self.rappels_liste:
            if rappel['actif']:
                try:
                    date_rappel = datetime.strptime(rappel['date_heure'], "%Y-%m-%d %H:%M")
                    if date_rappel <= maintenant:
                        self.show_snackbar(f"Rappel: {rappel['titre']}")
                        rappel['actif'] = False
                except:
                    pass
        
        self.update_reminders_list()

    # Cycle de vie de l'app
    def on_start(self):
        """Au démarrage"""
        Clock.schedule_interval(self.verifier_rappels, 60)
        Clock.schedule_interval(lambda dt: self.update_session_interface(), 60)
        Clock.schedule_interval(lambda dt: self.save_data(), 300)

    def on_pause(self):
        """En pause"""
        self.save_data()
        return True

    def on_resume(self):
        """Reprise"""
        try:
            self.load_data()
            self.update_notes_list()
            self.update_reminders_list()
            self.update_evolution_panel()
        except:
            pass

    def on_stop(self):
        """Arrêt"""
        self.save_data()


# Point d'entrée
if __name__ == "__main__":
    StudyHelperApp().run()