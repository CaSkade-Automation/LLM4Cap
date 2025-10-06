import os
from io import StringIO
import contextlib
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import openai
from openai import OpenAI

import rdflib
from rdflib import Graph, RDF
from rdflib.namespace import SH

from owlready2 import (
    get_ontology, onto_path, sync_reasoner_pellet, sync_reasoner_hermit,
    OwlReadyInconsistentOntologyError
)

from pyshacl import validate

ERROR_FILE = "Fehler.txt"
TEMP_OWL = "temp.owl"

client = OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")

def append_log(msg: str, logfile: str = "ontology_api_core.log") -> None:
    try:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Nur noch: RDF/XML prüfen (KEINE Konvertierung)
# ---------------------------------------------------------------------------
def try_parse_rdfxml(text: str) -> Dict[str, Any]:
    """
    Versucht, den Text als RDF/XML zu parsen. Keine Konvertierung!
    Rückgabe:
      {
        "is_valid_rdfxml": bool,
        "triple_count": int | None,
        "normalized_rdfxml": str | None,  # re-serialisiert, nur wenn gültig
        "error": str | None
      }
    """
    res = {"is_valid_rdfxml": False, "triple_count": None, "normalized_rdfxml": None, "error": None}
    g = Graph()
    try:
        g.parse(data=(text or ""), format="xml")
        res["is_valid_rdfxml"] = True
        res["triple_count"] = len(g)
        # Re-Serialisierung innerhalb RDF/XML (keine Format-Übersetzung)
        xml_bytes_or_str = g.serialize(format="xml")
        res["normalized_rdfxml"] = (
            xml_bytes_or_str.decode("utf-8") if isinstance(xml_bytes_or_str, (bytes, bytearray)) else xml_bytes_or_str
        )
    except Exception as e:
        res["error"] = str(e)
    return res

# ---------------------------------------------------------------------------
# LLM-Aufrufe (hart auf RDF/XML getrimmt)
# ---------------------------------------------------------------------------
def get_gpt_response(user_message: str, system_message: Optional[str] = None) -> str:
    if system_message is None:
        system_message = (
            "Du hast folgende Fehler in der darauf folgenden Ontologie gemacht, "
            "überarbeite diese nur anhand der Fehler und behalte alles außer die Fehler bei. "
            "Antworte AUSSCHLIESSLICH mit einer vollständigen RDF/XML (OWL) Ontologie, "
            "ohne Erklärtext, ohne Code-Fences. "
            "Gib nur das reine RDF/XML aus."
        )
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        error_msg = f"Error: {e}"
        append_log(error_msg)
        return error_msg

# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------
def check_syntax(rdfxml_str: str):
    """Syntax-Prüfung via rdflib als RDF/XML. Liefert Liste der Syntaxfehler und den Graph."""
    g = rdflib.Graph()
    try:
        g.parse(data=rdfxml_str, format="xml")
        return [], g
    except Exception as e:
        return [str(e)], None

def check_reasoner(rdfxml_str: str, reasoner: str = "pellet", mem_mb: int = 8000):
    # HARDCODED Pfade wie im Projekt (bei Bedarf anpassen)
    onto = get_ontology(r"C:\\Users\\xXBl4\\Desktop\\MB\\SHK\\LLM4Cap\\Python\\drilling.owl")
    onto_path.append(r"C:\\Users\\xXBl4\\Desktop\\MB\\SHK\\LLM4Cap\\Python\\ontologien\\importsCask")
    onto.load()
    try:
        if reasoner.lower() == "pellet":
            sync_reasoner_pellet(
                onto, infer_property_values=False,
                infer_data_property_values=False,
                debug=2, keep_tmp_file=False
            )
        else:
            sync_reasoner_hermit(
                onto, infer_property_values=False,
                debug=2, keep_tmp_file=False
            )
        print("✅  Keine Inkonsistenzen gefunden.")
    except OwlReadyInconsistentOntologyError as errors:
        print("\n❌  *** Inkonsistente Ontologie! ***")
        print("Grund laut Reasoner:\n")
        print(errors)
        return [str(errors)]

def check_shacl(data_graph: Graph, shacl_graph: Optional[Graph] = None):
    errors = []
    try:
        conforms, report_graph, _ = validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            inference="owlrl",
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            debug=False,
            return_graph=True
        )
        if not conforms:
            for vr in report_graph.subjects(RDF.type, SH.ValidationResult):
                focus    = report_graph.value(vr, SH.focusNode) or "<?>"
                path     = report_graph.value(vr, SH.resultPath) or "<?>"
                severity = report_graph.value(vr, SH.resultSeverity) or "<?>"
                for msg in report_graph.objects(vr, SH.resultMessage):
                    errors.append(f"[{str(severity).split('#')[-1]}] Node {focus} violates {path}: {msg}")
    except Exception as e:
        errors.append(f"SHACL-Fehler: {e}")
    return errors

def collect_errors_str(rdfxml_str: str):
    """
    Führt Syntax-, Reasoner- und SHACL-Prüfung durch und sammelt alle
    Fehlermeldungen in Fehler.txt. Rückgabe: Dict mit Fehlerlisten.
    """
    errors = {"Syntaxfehler": [], "Inkonsistenzen": [], "SHACL-Fehler": []}

    # 1) Syntax
    syntax_errs, graph = check_syntax(rdfxml_str)
    errors["Syntaxfehler"].extend(syntax_errs)

    # 2) Reasoner
    if not syntax_errs:
        buf_out, buf_err = StringIO(), StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            reasoner_result = check_reasoner(rdfxml_str)
        valid, reasoner_errs = True, []
        if isinstance(reasoner_result, tuple):
            valid, reasoner_errs = reasoner_result
        elif isinstance(reasoner_result, list):
            valid, reasoner_errs = False, reasoner_result
        console_logs = "\n".join(
            line for line in (buf_out.getvalue(), buf_err.getvalue()) if line.strip()
        ).strip()
        if console_logs:
            reasoner_errs.append(console_logs)
        if not valid or reasoner_errs:
            errors["Inkonsistenzen"].extend(reasoner_errs)

    # 3) SHACL
    if not syntax_errs and graph is not None:
        errors["SHACL-Fehler"].extend(check_shacl(graph))

    # 4) persistieren
    with open(ERROR_FILE, "w", encoding="utf-8") as out:
        for cat, elist in errors.items():
            if elist:
                out.write(f"{cat}:\n")
                for e in elist:
                    for line in str(e).splitlines():
                        out.write(f"  – {line}\n")
                out.write("\n")
    return errors

# ---------------------------------------------------------------------------
# Ontologie generieren (prompt: nur RDF/XML zurückgeben)
# ---------------------------------------------------------------------------
def generate_ontology_from_description(
    name: str,
    domain: str,
    description: str,
    capability_sets: List[dict]
) -> str:
    parts = [
        f"Name: {name}",
        f"Domäne: {domain}",
        f"Beschreibung: {description}",
        "Capabilities:",
    ]
    for cap in capability_sets:
        parts.append(
            f"- Capability: {cap.get('capability','')}, "
            f"Skills: {cap.get('skills','')}, Constraint: {cap.get('constraint','')}"
        )
    vorgang_text = "\n".join(parts) + "\n\n"

    system_prompt = (
        "Du bist ein hilfreiches Ontologie-Assistenz-Tool. "
        "Erzeuge eine OWL-Ontologie und ANTWORTE AUSSCHLIESSLICH in RDF/XML. "
        "Kein Begleittext, keine Code-Fences, nur das reine RDF/XML mit XML-Deklaration "
        "und <rdf:RDF> Wurzelelement."
    )
    try:
        llm_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": vorgang_text}
            ]
        )
        return llm_resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# ---------------------------------------------------------------------------
# Reparatur (Prompt zwingt RDF/XML)
# ---------------------------------------------------------------------------
def repair_ontology_from_errors(ontology_content: str, error_text: str) -> str:
    system_msg = (
        "Du hast folgende Fehler in der darauf folgenden Ontologie gemacht, "
        "überarbeite diese nur anhand der Fehler und behalte alles außer die Fehler bei. "
        "Antworte AUSSCHLIESSLICH in RDF/XML (OWL), ohne Erklärtext, nur das reine RDF/XML."
    )
    user_msg = f"FEHLER:\n{error_text}\n\nONTOLOGIE:\n{ontology_content}"
    return get_gpt_response(user_msg, system_msg)

# ---------------------------------------------------------------------------
# Pipeline ohne jegliche Konvertierung
# ---------------------------------------------------------------------------
def full_pipeline(
    name: str,
    domain: str,
    description: str,
    capability_sets: List[dict],
    base_iri: Optional[str] = None,  # nur informativ; keine Konvertierung
    max_iterations: int = 2
) -> Dict[str, Any]:
    history: List[Dict[str, Any]] = []

    # 1) Generieren (soll bereits RDF/XML liefern)
    generated_txt = generate_ontology_from_description(name, domain, description, capability_sets)

    # 2) Optional: validieren (ohne zu konvertieren)
    probe = try_parse_rdfxml(generated_txt)
    if probe["is_valid_rdfxml"]:
        current_txt = probe["normalized_rdfxml"] or generated_txt
    else:
        current_txt = generated_txt  # nicht gültig -> so weiter, Fehler werden gemeldet

    # 3) temp.owl schreiben (ohne Formatwechsel)
    with open(TEMP_OWL, "w", encoding="utf-8") as f:
        f.write(current_txt)

    # 4) prüfen
    errs = collect_errors_str(current_txt)
    history.append({
        "stage": "generated",
        "is_valid_rdfxml": probe["is_valid_rdfxml"],
        "triple_count": probe["triple_count"],
        "rdfxml_snapshot": current_txt,
        "errors": errs,
        "parse_error": probe["error"],
    })

    # 5) Reparaturschleife (keine Konvertierung)
    for i in range(max_iterations):
        has_errors = any(len(v) > 0 for v in errs.values())
        if not has_errors:
            break

        try:
            with open(ERROR_FILE, "r", encoding="utf-8") as f:
                error_text = f.read().strip()
        except FileNotFoundError:
            error_text = ""

        repaired_txt = repair_ontology_from_errors(current_txt, error_text)

        # Wieder nur prüfen, NICHT konvertieren
        probe_rep = try_parse_rdfxml(repaired_txt)
        next_txt = probe_rep["normalized_rdfxml"] if probe_rep["is_valid_rdfxml"] else repaired_txt

        with open(TEMP_OWL, "w", encoding="utf-8") as f:
            f.write(next_txt)

        errs = collect_errors_str(next_txt)

        history.append({
            "stage": f"repaired_{i+1}",
            "is_valid_rdfxml": probe_rep["is_valid_rdfxml"],
            "triple_count": probe_rep["triple_count"],
            "rdfxml_snapshot": next_txt,
            "errors": errs,
            "parse_error": probe_rep["error"],
        })

        current_txt = next_txt

    return {
        "iterations": history,
        "final_rdfxml": current_txt,
        "error_file": ERROR_FILE,
        "temp_owl": TEMP_OWL,
    }

# ---------------------------------------------------------------------------
# FastAPI – REST
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Ontology Generator + Validator + Auto-Repair API (no Turtle conversion)",
    description=("Erzeugt eine Ontologie, erwartet strikt RDF/XML, persistiert nach temp.owl, "
                 "validiert (Syntax/Reasoner/SHACL) und repariert iterativ – ohne jegliche Formatkonvertierung."),
    version="1.1.0",
)

class Capability(BaseModel):
    capability: str = Field(default="")
    skills: str = Field(default="")
    constraint: str = Field(default="")

class GenerateRequest(BaseModel):
    name: str
    domain: str
    description: str
    capability_sets: List[Capability] = Field(default_factory=list)
    base_iri: Optional[str] = None
    max_iterations: int = Field(default=2, ge=0, le=10)

class MinimalProcessRequest(BaseModel):
    name: str
    text: str
    base_iri: Optional[str] = None
    max_iterations: int = Field(default=2, ge=0, le=10)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process(req: GenerateRequest):
    try:
        result = full_pipeline(
            name=req.name,
            domain=req.domain,
            description=req.description,
            capability_sets=[c.dict() for c in req.capability_sets],
            base_iri=req.base_iri,
            max_iterations=req.max_iterations,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unerwarteter Fehler: {e}")

@app.post("/process-simple")
async def process_simple(req: MinimalProcessRequest):
    try:
        result = full_pipeline(
            name=req.name,
            domain="",
            description=req.text,
            capability_sets=[],
            base_iri=req.base_iri,
            max_iterations=req.max_iterations,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ontology_api_core:app", host="0.0.0.0", port=8000, reload=True)
