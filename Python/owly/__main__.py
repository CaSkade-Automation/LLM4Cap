import openai
import sys
import time
from openai import OpenAI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QWidget, QLabel, QHBoxLayout, QComboBox, QTableWidget,
    QTableWidgetItem, QInputDialog, QDialog, QMessageBox, QToolButton, QMenu, QAction, QDialogButtonBox,
    QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import rdflib
from pyvis.network import Network
from owlready2 import get_ontology, onto_path, sync_reasoner_pellet, sync_reasoner_hermit, OwlReadyInconsistentOntologyError
from pyshacl import validate
from rdflib import Graph, RDF
from rdflib.namespace import SH
from io import StringIO
import contextlib
# ---------------------------------------------------------------------------
# Globale HUD-Styles 
# ---------------------------------------------------------------------------
HUD_STYLE = """
/* Grundlayout */
QWidget {
    background-color: #2b2b2b;
    color: white;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 14px;
}

/* Eingabefelder */
QLineEdit, QTextEdit {
    background-color: #3c3c3c;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px;
}
QLineEdit::placeholder,
QTextEdit::placeholder {
    color: rgba(255,255,255,160);   /* leicht transparentes Weiß */
}

/* Buttons & Tool-Buttons */
QPushButton, QToolButton {
    background-color: #555;
    border: 1px solid #666;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #666;
}
"""

# Constants for ontology checking
ERROR_FILE = "Fehler.txt"

# ---------------- Ontology Checker Functions ----------------

def check_syntax(turtle_str: str):
    """Syntax-Prüfung via rdflib. Liefert Liste der Syntaxfehler und den Graph.(turle/xml)"""
    g = rdflib.Graph()
    try:
        g.parse(data=turtle_str, format="xml")
        return [], g
    except Exception as e:
        return [str(e)], None
def check_reasoner( turtle_str: str , reasoner: str = "pellet", mem_mb: int = 8000):
 #. Reasoner starten
    onto = get_ontology(r"C:\Users\....\LLM4Cap\Python\drilling.owl") #im moment muss noch direkter Pfad zu Datei im Format r"C:\Users\Anwender\...\drilling.owl" angegeben werden
    onto_path.append(r"C:\Users\...\LLM4Cap\Python\ontologien\importsCask") #im moment muss noch direkter Pfad zu Datei im Format r"C:\Users\...\LLM4Cap\Python\ontologien\importsCask" angegeben werden
    onto.load()                                                                                 #wird später durch URIs ersetzt um aktualität zu gewährlesiten
    errors = []
    try:
        if reasoner.lower() == "pellet":
            # debug=2 → volle Konsolenausgabe + automatische pellet explain-Analyse
            sync_reasoner_pellet(
                onto, infer_property_values=False,
                infer_data_property_values=False,
                debug=2, keep_tmp_file=False
            )
        else:  # HermiT
            sync_reasoner_hermit(
                onto, infer_property_values=False,
                debug=2, keep_tmp_file=False
            )
        print("✅  Keine Inkonsistenzen gefunden.")
    except OwlReadyInconsistentOntologyError as errors:
        print("\n❌  *** Inkonsistente Ontologie! ***")
        print("Grund laut Reasoner:\n")
        # Die Exception‐Message enthält bereits die pellet explain-Ausgabe
        print(errors)
        return [str(errors)] 
def check_shacl(data_graph: Graph, shacl_graph: Graph = None):
    """
    SHACL-Validierung via pyshacl mit vollständiger Fehler-Ausgabe.
    
    :param data_graph: rdflib.Graph mit den zu validierenden Daten.
    :param shacl_graph: rdflib.Graph mit den SHACL-Shapes (optional).
    :return: Liste von Fehler-Strings (leer = valid).
    """
    errors = []
    try:
        conforms, report_graph, _ = validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            inference="owlrl",       # oder "rdfs" je nach Bedarf
            abort_on_first=False,     # alle Fehler sammeln
            meta_shacl=False,         # ggf. auf True setzen, wenn man Shapes auf Shapes prüfen will
            advanced=True,
            debug=False,
            return_graph=True         # wir wollen das Report-Graph für Detail-Auswertung
        )

        if not conforms:
            # Für jeden ValidationResult im Report-Graph
            for vr in report_graph.subjects(RDF.type, SH.ValidationResult):
                focus   = report_graph.value(vr, SH.focusNode) or "<?>"
                path    = report_graph.value(vr, SH.resultPath) or "<?>"
                severity= report_graph.value(vr, SH.resultSeverity) or "<?>"
                # Mehrere Messages möglich
                for msg in report_graph.objects(vr, SH.resultMessage):
                    errors.append(
                        f"[{severity.split('#')[-1]}] Node {focus} violates {path}: {msg}"
                    )

    except Exception as e:
        # Parser- oder Validierungs-Errors
        errors.append(f"SHACL-Fehler: {e}")

    return errors

# -----------------------------------------------------------------------------
#  Fehler sammeln
# -----------------------------------------------------------------------------
def collect_errors_str(turtle_str: str):
    """
    Führt Syntax-, Reasoner- und SHACL-Prüfung durch und sammelt **alle**
    Fehlermeldungen – auch jene, die der Reasoner nur auf der Konsole ausgibt –
    in Fehler.txt.  Rückgabe: Dict mit Fehlerlisten (leer ⇒ keine Fehler).
    """
    errors = {"Syntaxfehler": [], "Inkonsistenzen": [], "SHACL-Fehler": []}

    # --------------------------------------------------------------------- 1)
    # Syntax-Check
    # -------------------------------------------------------------------------
    syntax_errs, graph = check_syntax(turtle_str)
    errors["Syntaxfehler"].extend(syntax_errs)

    # --------------------------------------------------------------------- 2)
    # Reasoner – Konsole abfangen
    # -------------------------------------------------------------------------
    if not syntax_errs:
        buf_out, buf_err = StringIO(), StringIO()
        #  Terminal-Ausgabe während des Reasonings puffern
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            reasoner_result = check_reasoner(turtle_str)

        # Rückgabewerte  auswerten (alt = Liste, neu = Tuple(bool, list))
        valid, reasoner_errs = True, []
        if isinstance(reasoner_result, tuple):
            valid, reasoner_errs = reasoner_result
        elif isinstance(reasoner_result, list):
            valid, reasoner_errs = False, reasoner_result

        #  was auf stdout/stderr stand, anhängen
        console_logs = "\n".join(
            line for line in (buf_out.getvalue(), buf_err.getvalue()) if line.strip()
        ).strip()
        if console_logs:
            reasoner_errs.append(console_logs)

        if not valid or reasoner_errs:
            errors["Inkonsistenzen"].extend(reasoner_errs)

    # --------------------------------------------------------------------- 3)
    # SHACL-Validierung
    # -------------------------------------------------------------------------
    if not syntax_errs and graph is not None:
        shacl_errs = check_shacl(graph)
        errors["SHACL-Fehler"].extend(shacl_errs)

    # --------------------------------------------------------------------- 4)
    # in Fehler.txt schreiben
    # -------------------------------------------------------------------------
    with open(ERROR_FILE, "w", encoding="utf-8") as out:
        for cat, elist in errors.items():
            if elist:
                out.write(f"{cat}:\n")
                for e in elist:
                    # mehrzeilige Reasoner-Ausgaben Zeile für Zeile einrücken
                    for line in str(e).splitlines():
                        out.write(f"  – {line}\n")
                out.write("\n")

    return errors



# ---------------- Chatbot Application ----------------

client = OpenAI()

openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")  # Replace with your API key if not using env variable
ASSISTANT_ID = "asst_8RNbIGuCxRciBsJzs8YBF4g9"  # Replace with your specific assistant ID

class ChatbotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_available_ontologies()
        self.ontology_content = ""
        self.node_relationships = {}

    def initUI(self):
        self.setWindowTitle("Ontology Master")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        # Ontology selection dropdown
        self.ontology_dropdown = QComboBox(self)
        self.ontology_dropdown.setFont(QFont("Arial", 12))
        self.ontology_dropdown.setStyleSheet("background-color: #444444; color: white; padding: 5px;")
        self.ontology_dropdown.currentIndexChanged.connect(self.load_selected_ontology)

        self.layout.addWidget(QLabel("Ontology Selection:", self))
        self.layout.addWidget(self.ontology_dropdown)

        # User messages display
        self.user_label = QLabel("User:")
        self.user_label.setFont(QFont("Arial", 12))
        self.user_label.setStyleSheet("color: white;")
        self.layout.addWidget(self.user_label)
        self.user_messages = QTextEdit(self)
        self.user_messages.setReadOnly(True)
        self.user_messages.setFont(QFont("Arial", 12))
        self.user_messages.setStyleSheet("background-color: #333333; color: white; padding: 10px;")
        self.layout.addWidget(self.user_messages)

        # Bot messages display
        self.bot_label = QLabel("Bot:")
        self.bot_label.setFont(QFont("Arial", 12))
        self.bot_label.setStyleSheet("color: white;")
        self.layout.addWidget(self.bot_label)
        self.bot_messages = QTextEdit(self)
        self.bot_messages.setReadOnly(True)
        self.bot_messages.setFont(QFont("Arial", 12))
        self.bot_messages.setStyleSheet("background-color: #222222; color: white; padding: 10px;")
        self.layout.addWidget(self.bot_messages)

        # Input field and HUD buttons
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.setFont(QFont("Arial", 12))
        self.user_input.setStyleSheet("background-color: #444444; color: white; border-radius: 15px; padding: 10px;")

        self.send_button = QPushButton("Send", self)
        self.send_button.setFont(QFont("Arial", 12))
        self.send_button.setStyleSheet("background-color: #555555; color: white;")
        self.send_button.clicked.connect(self.send_message)

        self.visualize_button = QPushButton("Visualize Ontology", self)
        self.visualize_button.setFont(QFont("Arial", 12))
        self.visualize_button.setStyleSheet("background-color: #555555; color: white;")
        self.visualize_button.clicked.connect(self.open_visualization_window)

        self.check_button = QToolButton(self)
        self.check_button.setText("Check Syntax")
        self.check_button.setFont(QFont("Arial", 12))
        self.check_button.setStyleSheet("background-color:#555; color:white;")
        self.check_button.setPopupMode(QToolButton.InstantPopup)

        check_menu = QMenu(self.check_button)
        action_runcheck  = QAction("Syntax-/Reasoner-/SHACL-Check", self)
        action_repair    = QAction("Ontologie reparieren",          self)
        check_menu.addAction(action_runcheck)
        check_menu.addAction(action_repair)
        self.check_button.setMenu(check_menu)

        action_runcheck.triggered.connect(self.run_ontology_check)
        action_repair.triggered.connect(self.repair_ontology)

        # HUD layout: input and action buttons
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.visualize_button)
        input_layout.addWidget(self.check_button)
        self.layout.addLayout(input_layout)

        # --- Generieren-Button mit Drop-Down -----------------------------
        self.generate_button = QToolButton(self)
        self.generate_button.setText("Generieren")
        self.generate_button.setFont(QFont("Arial", 12))
        self.generate_button.setStyleSheet("background-color: #555555; color: white;")
        self.generate_button.setPopupMode(QToolButton.InstantPopup)

        # Menü-Einträge
        gen_menu = QMenu(self.generate_button)
        action_describe = QAction("Beschreiben", self)
        action_pdf      = QAction("Aus PDF", self)
        gen_menu.addAction(action_describe)
        gen_menu.addAction(action_pdf)
        self.generate_button.setMenu(gen_menu)

        # Signale
        action_describe.triggered.connect(self.open_describe_dialog)
        action_pdf.triggered.connect(self.open_from_pdf)

        # Button in das bestehende HUD-Layout einhängen
        input_layout.addWidget(self.generate_button)

        self.central_widget.setLayout(self.layout)

    def load_available_ontologies(self):
        """Load available ontology names into the dropdown from `available_ontologies.txt`."""
        try:
            with open("available_ontologies.txt", "r") as file:
                ontologies = [line.strip() for line in file if line.strip()]
            self.ontology_dropdown.addItems(ontologies)
        except FileNotFoundError:
            self.ontology_dropdown.addItem("No ontologies found")

    def load_selected_ontology(self):
        selected_ontology = self.ontology_dropdown.currentText()
        self.ontology_content = ""  # Clear previous ontology content
        if selected_ontology and selected_ontology != "No ontologies found":
            try:
                with open(f"{selected_ontology}.owl", "r", encoding="utf-8") as file:
                    self.ontology_content = file.read()
                self.user_messages.append(f"Loaded ontology '{selected_ontology}'")
            except FileNotFoundError:
                self.user_messages.append(f"Ontology file '{selected_ontology}.owl' not found.")
                self.ontology_content = ""
            except UnicodeDecodeError as e:
                self.user_messages.append(f"Unicode error while loading '{selected_ontology}.txt': {e}")
                self.ontology_content = ""

    def run_ontology_check(self):
        """Triggered by Check Ontology button: führt alle Prüfungen aus."""
        if not self.ontology_content:
            QMessageBox.warning(self, "Kein Ontologieinhalt", "Bitte zuerst eine Ontologie laden.")
            return
        self.user_messages.append("Starte Ontologie-Prüfung...")
        errors = collect_errors_str(self.ontology_content)
        for cat, elist in errors.items():
            if elist:
                self.user_messages.append(f"{cat}:")
                for e in elist:
                    self.user_messages.append(f"  - {e}")
            else:
                self.user_messages.append(f"{cat}: ✓ keine Fehler")
        QMessageBox.information(self, "Prüfung abgeschlossen", f"Ergebnisse wurden in {ERROR_FILE} gespeichert.")

    def open_visualization_window(self):
        if not self.ontology_content:
            self.user_messages.append("No ontology selected to visualize.")
            return

        # Create the visualization
        graph = self.create_vowl_graph()

        # Open a new window to show the visualization and search feature
        self.visualization_window = QMainWindow()
        self.visualization_window.setWindowTitle("Ontology Visualization")
        self.visualization_window.setGeometry(100, 100, 800, 600)

        # Web view to display visualization
        web_view = QWebEngineView()
        web_view.setHtml(graph.generate_html())  # Load the visualization
        self.visualization_window.setCentralWidget(web_view)

        # Add a button for opening the connected elements dialog
        search_button = QPushButton("Find Connections", self.visualization_window)
        search_button.setFont(QFont("Arial", 12))
        search_button.setStyleSheet("background-color: #555555; color: white;")
        search_button.setGeometry(10, 10, 150, 40)
        search_button.clicked.connect(self.open_connection_search_window)

        self.visualization_window.show()


    def open_connection_search_window(self):
        """Open a dialog to search for connections of a specific element."""
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Find Connections")
        input_dialog.setLabelText("Enter the name of the element:")
        input_dialog.setFont(QFont("Arial", 12))
        input_dialog.setStyleSheet("background-color: #333333; color: white;")

        if input_dialog.exec_() == QDialog.Accepted:
            element_name = input_dialog.textValue()
            if element_name:
                self.show_connections_for_element(element_name)
        # ------------------------------------------------ Generieren ----------
    def open_describe_dialog(self):
        dlg = CapabilityInputDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()

            # Anzeige in Chat-History
            self.user_messages.append(
                f"🆕 Beschreibung erfasst:\n"
                f"  • Name: {data['name']}\n"
                f"  • Domäne: {data['domain']}\n"
                f"  • Beschreibung: {data['description']}\n"
                f"  • Capabilities: {len(data['capability_sets'])}"
            )

            # 1) Vorgang.txt aktualisieren
            vorgang_block = []
            vorgang_block.append(f"Name: {data['name']}")
            vorgang_block.append(f"Domäne: {data['domain']}")
            vorgang_block.append(f"Beschreibung: {data['description']}")
            vorgang_block.append("Capabilities:")
            for cap in data['capability_sets']:
                vorgang_block.append(
                    f"- Capability: {cap['capability']}, Skills: {cap['skills']}, Constraint: {cap['constraint']}"
                )
            vorgang_text = "\n".join(vorgang_block) + "\n\n"
            try:
                with open("Vorgang_RDF.txt", "a", encoding="utf-8") as vf:
                    vf.write(vorgang_text)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Konnte Vorgang.txt nicht aktualisieren: {e}")

            # 2) Anfrage an OpenAI-LLM senden
            try:
                llm_resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Du bist ein hilfreiches Ontologie-Assistenz-Tool."},
                        {"role": "user",   "content": vorgang_text}
                    ]
                )
                llm_content = llm_resp.choices[0].message.content.strip()
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"OpenAI-Request fehlgeschlagen: {e}")
                return

            # 3) Antwort in Datei mit Ontologie-Name speichern
            filename = f"{data['name']}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as outf:
                    outf.write(llm_content)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Konnte {filename} nicht schreiben: {e}")

            # 4) available_ontologies.txt ergänzen
            try:
                with open("available_ontologies.txt", "a", encoding="utf-8") as af:
                    af.write(data['name'] + "\n")
                # Dropdown aktualisieren
                self.ontology_dropdown.addItem(data['name'])
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Konnte available_ontologies.txt nicht aktualisieren: {e}")

            # Erfolgsmeldung
            QMessageBox.information(
                self, "Fertig",
                f"Vorgang gespeichert, LLM-Antwort in {filename} abgelegt und available_ontologies.txt aktualisiert."
            )
    

    def open_from_pdf(self):
        # Placeholder zum späteren Ausbauen
        QMessageBox.information(
            self, "Aus PDF",
            "Hier kannst du später eine PDF laden und verarbeiten."
        )

    def show_connections_for_element(self, element_name):
        """Display all connected elements and their relationships in a hierarchical structure."""
        if element_name not in self.node_relationships["nodes"]:
            self.user_messages.append(f"No data found for element: {element_name}")
            return

        connections = self.node_relationships["nodes"][element_name]

        # Create a new window to display the connections
        connections_window = QMainWindow()
        connections_window.setWindowTitle(f"Connections of {element_name}")
        connections_window.setGeometry(150, 150, 400, 300)

         # Table widget to display relationships
        table_widget = QTableWidget()
        table_widget.setRowCount(len(connections))
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderLabels(["Relation", "Target"])

        for i, (relation, target) in enumerate(connections):
            table_widget.setItem(i, 0, QTableWidgetItem(relation))
            table_widget.setItem(i, 1, QTableWidgetItem(target))

        layout = QVBoxLayout()
        layout.addWidget(table_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        connections_window.setCentralWidget(central_widget)
        connections_window.show()

        self.connections_window = connections_window

    def create_vowl_graph(self):
        """Parse ontology content and generate a VOWL-like graph with interactivity."""
        g = rdflib.Graph()
        g.parse(data=self.ontology_content, format="turtle")

        net = Network(height="1000px", width="100%", directed=True)

        # Map relationships for hierarchical data
        relationships = {"nodes": {}, "edges": []}
        

        for s, p, o in g:
            source = str(s).split("#")[-1] if "#" in str(s) else str(s)
            predicate = str(p).split("#")[-1] if "#" in str(p) else str(p)
            obj = str(o).split("#")[-1] if "#" in str(o) else str(o)

            if source and obj:
                net.add_node(source, label=source)
                net.add_node(obj, label=obj)
                net.add_edge(source, obj, label=predicate)

                # Add to relationships for table visualization
                relationships["nodes"].setdefault(source, []).append((predicate, obj))

        # Customize visualization settings for better spacing
        net.set_options("""
            var options = {
              "nodes": { "shape": "dot", "size": 10, "font": {"size": 14} },
              "edges": { "arrows": {"to": {"enabled": true}}, "font": {"size": 12, "align": "middle"} },
              "physics": { "enabled": true, "barnesHut": { "gravitationalConstant": -2000, "centralGravity": 0.1, "springLength": 200, "springConstant": 0.01, "avoidOverlap": 0.5 } },
              "interaction": { "hover": true, "dragNodes": true, "zoomView": true }
            }
        """)

        self.node_relationships = relationships
        return net
    def load_basis_content(self):
        """Load the content of Basis.txt for foundational knowledge."""
        file_path = os.path.join(os.path.dirname(__file__), "Basis.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return "Basis.txt not found. Ensure it exists in the application directory."
        except PermissionError:
            return "Permission denied when trying to read Basis.txt."
        except UnicodeDecodeError:
            return "Error reading Basis.txt: Encoding issue detected."
        except Exception as e:
            return f"Unexpected error reading Basis.txt: {str(e)}."
    def send_message(self):
        """
        Handles sending a message to the bot with Basis.txt, user input, and loaded ontology content in that order.
        """
        # Load the user's input message
        user_text = self.user_input.text().strip()
        if not user_text:
            self.user_messages.append("Please enter a message before sending.")
            return
    
        # Load Basis content
        basis_content = self.load_basis_content()
        if not basis_content:
            self.user_messages.append("Basis.txt is missing or empty. Defaulting to user input and ontology content.")
    
            # Combine Basis, user input, and ontology content in the specified order
        combined_message = f"{basis_content}\n\nUser Input:\n{user_text}\n\nLoaded Ontology:\n{self.ontology_content}"
    
            # Display the combined message for debugging (optional, can remove this later)
        self.user_messages.append(f"Sending message:\n{user_text}")
    
            # Clear the user input field
        self.user_input.clear()
    
            # Get the bot response
        response = self.get_gpt_response(combined_message)
        self.bot_messages.append(f"Bot: {response}")
        
    def get_gpt_response(self, user_message):
        try:
            thread = client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
            print(f"👉 Run Created: {run.id}")

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                print(f"🏃 Run Status: {run.status}")
                time.sleep(1)

            message_response = client.beta.threads.messages.list(thread_id=thread.id)
            # Extract the actual answer
            response_content = [
                block.text.value for block in message_response.data[0].content
                if hasattr(block, 'text') and hasattr(block.text, 'value')
            ]
            return response_content[0] if response_content else "No response available"

        except Exception as e:
            return f"Error: {str(e)}"
    # -----  in der Klasse ChatbotWindow ergänzen  -----
    def repair_ontology(self):
        """
        Liest Fehler.txt + aktuelle Ontologie, schickt sie mit festem System-Prompt
        an get_gpt_response, speichert Ergebnis als  <name>_neu.owl  und trägt
        den neuen Namen in  Liste.txt  ein.
        """
        if not self.ontology_content:
            QMessageBox.warning(self, "Keine Ontologie", "Bitte zuerst eine Ontologie laden.")
            return

        # Benutzer bestätigen lassen
        ans = QMessageBox.question(
            self, "Ontologie reparieren",
            "Möchtest du die Ontologie automatisch anhand der gefundenen Fehler "
            "überarbeiten lassen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans != QMessageBox.Yes:
            return

        # Fehler.txt laden
        try:
            with open(ERROR_FILE, "r", encoding="utf-8") as f:
                error_text = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, "Fehler", "Fehler.txt nicht gefunden – erst Syntax-Check ausführen.")
            return

        # Prompt zusammenbauen und an LLM schicken
        system_msg = ("Du hast folgende Fehler in der darauf folgenden Ontologie gemacht, überarbeite diese nur anhand der Fehler und behalte alles außer die Fehler bei. Gebe mir die Vollständige und überarbeitete Ontologie daraufhin wieder aus.")
        user_msg   = f"FEHLER:\n{error_text}\n\nONTOLOGIE:\n{self.ontology_content}"

        self.user_messages.append("⏳ LLM wird zur Reparatur aufgerufen …")
        llm_answer = self.get_gpt_response(user_msg, system_msg)

        if llm_answer.startswith("Error:"):
            QMessageBox.warning(self, "LLM-Fehler", llm_answer)
            return

        # Datei anlegen und Liste.txt aktualisieren
        base_name   = self.ontology_dropdown.currentText()
        new_fname   = f"{base_name}_neu.owl"
        try:
            with open(new_fname, "w", encoding="utf-8") as f:
                f.write(llm_answer)
        except Exception as e:
            QMessageBox.warning(self, "Schreibfehler", f"Konnte {new_fname} nicht speichern: {e}")
            return

        try:
            with open("available_ontologies.txt", "a", encoding="utf-8") as lf:
                lf.write(f"{base_name}_neu\n")
        except Exception as e:
            QMessageBox.warning(self, "Schreibfehler", f"Konnte Liste.txt nicht aktualisieren: {e}")

        self.user_messages.append(f"✅ Reparierte Ontologie gespeichert als {new_fname}")
        QMessageBox.information(self, "Fertig", f"{new_fname} wurde erzeugt und in Liste.txt eingetragen.")
        
    def get_gpt_response(self, user_message, system_message=None):
        if system_message is None:
            system_message = ("Du hast folgende Fehler in der darauf folgenden Ontologie gemacht, überarbeite diese nur anhand der Fehler und behalte alles außer die Fehler bei. Gebe mir die Vollständige und überarbeitete Ontologie daraufhin wieder aus.")
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user",   "content": user_message}
                ]
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            error_msg = f"Error: {e}"
            append_log(error_msg)
            return error_msg

    class CapabilityGroupWidget(QWidget):
        """Ein einzelner Capability-Block (Capability, Skills, Constraint)."""
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QHBoxLayout(self)

            self.cap_line   = QLineEdit()
            self.cap_line.setPlaceholderText("Capability")
            self.skill_line = QLineEdit()
            self.skill_line.setPlaceholderText("Skills")
            self.con_line   = QLineEdit()
            self.con_line.setPlaceholderText("Constraint")

            for w in (self.cap_line, self.skill_line, self.con_line):
                layout.addWidget(w)

        def get_values(self):
            return {
                "capability": self.cap_line.text().strip(),
                "skills":     self.skill_line.text().strip(),
                "constraint": self.con_line.text().strip()
            }
class CapabilityInputDialog(QDialog):
    """Dialog für 'Beschreiben' mit dynamisch anlegbaren Capability-Blöcken."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Objekt beschreiben")
        self.setMinimumWidth(800)

        main_layout = QVBoxLayout(self)

        # --- feste Felder --------------------------------------------------
        self.name_line   = QLineEdit()
        self.domain_line = QLineEdit()
        self.desc_edit   = QTextEdit()

        self.name_line.setPlaceholderText("Name")
        self.domain_line.setPlaceholderText("Domäne / Fachgebiet")
        self.desc_edit.setPlaceholderText("Beschreibung (optional)")

        main_layout.addWidget(QLabel("Name:"))
        main_layout.addWidget(self.name_line)
        main_layout.addWidget(QLabel("Domäne / Fachgebiet:"))
        main_layout.addWidget(self.domain_line)
        main_layout.addWidget(QLabel("Beschreibung:"))
        main_layout.addWidget(self.desc_edit)

        # --- dynamischer Bereich für Capability-Blöcke ---------------------
        self.cap_box = QVBoxLayout()
        cap_container = QWidget()
        cap_container.setLayout(self.cap_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cap_container)
        main_layout.addWidget(scroll, stretch=1)

        # +-Button
        add_btn = QPushButton("+  Capability-Block hinzufügen")
        add_btn.clicked.connect(self.add_cap_block)
        main_layout.addWidget(add_btn)

        # zuerst noch kein Block – erscheint nach dem ersten +
        self.cap_blocks = []

        # Dialog-Buttons OK / Abbrechen
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)
                # ------------------------------------------------------------------
        # Alle Schrift in diesem Dialog weiß färben
        # ------------------------------------------------------------------
        self.setStyleSheet(HUD_STYLE)

    # ---------- helper -----------------------------------------------------
    def add_cap_block(self):
        block = CapabilityGroupWidget(self)
        self.cap_blocks.append(block)
        self.cap_box.addWidget(block)

    def get_data(self):
        return {
            "name":        self.name_line.text().strip(),
            "domain":      self.domain_line.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "capability_sets": [blk.get_values() for blk in self.cap_blocks]
        }
   
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ChatbotWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
