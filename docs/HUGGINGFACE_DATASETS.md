# Hugging Face Datasets herunterladen

## Überblick

Du kannst große, öffentliche Datasets von Hugging Face automatisch herunterladen und ins richtige Format konvertieren!

## Verfügbare Datasets

### 1. Wikipedia
- **Quelle**: `legacy-datasets/wikipedia`
- **Inhalt**: Wikipedia-Artikel (Englisch)
- **Format**: "Tell me about [Titel]" → Artikel-Auszug

### 2. StackOverflow
- **Quelle**: `c17hawke/stackoverflow-dataset`
- **Inhalt**: StackOverflow Fragen & Antworten
- **Format**: Frage → Antwort

### 3. Tiny Codes
- **Quelle**: `nampdn-ai/tiny-codes`
- **Inhalt**: Kleine Code-Snippets mit Erklärungen
- **Format**: Programmier-Aufgabe → Code-Lösung

### 4. CodeParrot
- **Quelle**: `codeparrot/codeparrot-clean-train`
- **Inhalt**: Saubere Python-Code Beispiele
- **Format**: "Write Python code for [X]" → Code

## Verwendung

### Schritt 1: Dataset herunterladen

```bash
# Wikipedia (1000 Beispiele)
python scripts/download_hf_dataset.py wikipedia --samples 1000

# StackOverflow (500 Beispiele)
python scripts/download_hf_dataset.py stackoverflow --samples 500

# Tiny Codes (300 Beispiele)
python scripts/download_hf_dataset.py tiny-codes --samples 300

# CodeParrot (500 Beispiele)
python scripts/download_hf_dataset.py codeparrot --samples 500
```

**Was passiert:**
1. Script lädt Dataset von Hugging Face
2. Konvertiert in Chat-Format (`messages` mit `user`/`assistant`)
3. Speichert als `datasets/wikipedia.json` oder `datasets/stackoverflow.json`
4. Zeigt Preview und Dateiinfo

### Schritt 2: Dataset verwenden

```bash
# Starte iterate.sh
./iterate.sh my-experiment

# Wähle aus der Liste:
# [1] example-chatbot.json
# [2] example-classifier.json
# [3] wikipedia.json          ← NEU!
# [4] stackoverflow.json      ← NEU!
# [5] tiny-codes.json         ← NEU!
# [6] codeparrot.json         ← NEU!
```

Das wars! 🎉

## Beispiel-Output

```bash
$ python scripts/download_hf_dataset.py wikipedia --samples 100

📥 Downloading wikipedia from Hugging Face
Description: Wikipedia articles (English)
HF Path: legacy-datasets/wikipedia
Samples: 100

Loading dataset...
✓ Dataset loaded

Converting 100 samples...
████████████████████████ 100/100
✓ Converted 100 samples

Saving to datasets/wikipedia.json...
✓ Saved 100 examples
  File: datasets/wikipedia.json
  Size: 0.52 MB

Preview:
User: Tell me about Python (programming language)
Assistant: Python is a high-level, general-purpose programming language...

✅ Done! Dataset ready at: datasets/wikipedia.json

Use it with:
  ./iterate.sh my-experiment
  -> Select 'wikipedia.json' from the list
```

## Optionen

### Anzahl Beispiele ändern

```bash
# Nur 50 Beispiele (schneller Download)
python scripts/download_hf_dataset.py wikipedia --samples 50

# 5000 Beispiele (größeres Dataset)
python scripts/download_hf_dataset.py wikipedia --samples 5000
```

**Empfehlung:**
- **Test/Prototyping**: 50-100 Beispiele
- **Schnelle Iteration**: 500-1000 Beispiele
- **Ernsthafte Training**: 2000-5000 Beispiele

### Eigenes Output-Verzeichnis

```bash
python scripts/download_hf_dataset.py wikipedia \
    --samples 1000 \
    --output custom-datasets/
```

### Verfügbare Datasets anzeigen

```bash
python scripts/download_hf_dataset.py --list
```

## Format-Details

### Wikipedia-Konvertierung

**Original** (Wikipedia):
```json
{
  "title": "Machine Learning",
  "text": "Machine learning is a subset of AI that...[long text]"
}
```

**Konvertiert** (Chat-Format):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Tell me about Machine Learning"
    },
    {
      "role": "assistant",
      "content": "Machine learning is a subset of AI that...[first 500 chars]"
    }
  ]
}
```

### StackOverflow-Konvertierung

**Original** (StackOverflow):
```json
{
  "question": "How do I reverse a string in Python?",
  "answer": "You can use slicing: reversed_string = my_string[::-1]"
}
```

**Konvertiert** (Chat-Format):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I reverse a string in Python?"
    },
    {
      "role": "assistant",
      "content": "You can use slicing: reversed_string = my_string[::-1]"
    }
  ]
}
```

### Tiny Codes-Konvertierung

**Original** (Tiny Codes):
```json
{
  "prompt": "Create a function to check if a number is prime",
  "response": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"
}
```

**Konvertiert** (Chat-Format):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Create a function to check if a number is prime"
    },
    {
      "role": "assistant",
      "content": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"
    }
  ]
}
```

### CodeParrot-Konvertierung

**Original** (CodeParrot):
```json
{
  "content": "def calculate_fibonacci(n):\n    \"\"\"Calculate nth Fibonacci number.\"\"\"\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)"
}
```

**Konvertiert** (Chat-Format):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Write Python code for Calculate nth Fibonacci number."
    },
    {
      "role": "assistant",
      "content": "def calculate_fibonacci(n):\n    \"\"\"Calculate nth Fibonacci number.\"\"\"\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)"
    }
  ]
}
```

**Hinweis:** Der User-Prompt wird automatisch aus Docstrings/Kommentaren extrahiert.

## Empfehlungen

### Wikipedia

**Gut für:**
- ✅ Allgemeinwissen-Modelle
- ✅ Erklärungen und Definitionen
- ✅ Formale, informative Sprache
- ✅ Fakten-basierte Antworten

**Nicht gut für:**
- ❌ Konversation/Chat
- ❌ Code-Beispiele
- ❌ Persönliche Ratschläge

**Empfohlene Samples:** 1000-2000

### StackOverflow

**Gut für:**
- ✅ Technische Fragen & Antworten
- ✅ Code-Hilfe
- ✅ Problemlösungen
- ✅ Programmier-Kontext

**Nicht gut für:**
- ❌ Allgemeinwissen
- ❌ Kreatives Schreiben
- ❌ Nicht-technische Themen

**Empfohlene Samples:** 500-1000

### Tiny Codes

**Gut für:**
- ✅ Kleine, fokussierte Code-Aufgaben
- ✅ Instruction-Following für Code
- ✅ Verschiedene Programmiersprachen
- ✅ Code-Generierung aus Beschreibung
- ✅ Schnelle Iteration (kleine Samples)

**Nicht gut für:**
- ❌ Große, komplexe Projekte
- ❌ System-Design
- ❌ Nicht-Code Aufgaben

**Empfohlene Samples:** 300-800

### CodeParrot

**Gut für:**
- ✅ Python Code-Generierung
- ✅ Clean Code Patterns
- ✅ Realistische Code-Struktur
- ✅ Lernen von Best Practices
- ✅ Vollständige Funktionen/Klassen

**Nicht gut für:**
- ❌ Andere Programmiersprachen
- ❌ Code-Erklärungen (nur Code)
- ❌ Debugging/Fehlersuche
- ❌ Interactive Probleme lösen

**Empfohlene Samples:** 500-1000

**Hinweis:** CodeParrot enthält nur Code ohne Kontext. Das Script erstellt automatisch synthetische Prompts basierend auf Docstrings/Kommentaren.

## Kombinierte Datasets

Du kannst mehrere Datasets mischen:

```bash
# 1. Lade mehrere Datasets
python scripts/download_hf_dataset.py wikipedia --samples 500
python scripts/download_hf_dataset.py stackoverflow --samples 500
python scripts/download_hf_dataset.py tiny-codes --samples 300
python scripts/download_hf_dataset.py codeparrot --samples 500

# 2. Wähle beim Training
./iterate.sh wiki-model
# -> Wähle wikipedia.json

./iterate.sh code-helper
# -> Wähle stackoverflow.json

./iterate.sh code-gen
# -> Wähle tiny-codes.json

./iterate.sh python-expert
# -> Wähle codeparrot.json
```

### Manuelles Mischen

```python
import json

# Lade alle Datasets
with open('datasets/wikipedia.json') as f:
    wiki = json.load(f)

with open('datasets/stackoverflow.json') as f:
    stack = json.load(f)

with open('datasets/tiny-codes.json') as f:
    tiny = json.load(f)

with open('datasets/codeparrot.json') as f:
    parrot = json.load(f)

# Beispiel 1: Gemischtes Code + Knowledge Model
combined_balanced = (
    wiki[:200] +          # Allgemeinwissen
    stack[:200] +         # Q&A Code-Hilfe
    tiny[:200] +          # Code-Generierung
    parrot[:200]          # Python Patterns
)

with open('datasets/combined-balanced.json', 'w') as f:
    json.dump(combined_balanced, f, indent=2)

# Beispiel 2: Nur Code-fokussiert
code_focused = (
    stack[:300] +         # Mehr Q&A
    tiny[:400] +          # Mehr kleine Tasks
    parrot[:300]          # Python Code
)

with open('datasets/code-focused.json', 'w') as f:
    json.dump(code_focused, f, indent=2)
```

Jetzt hast du `combined-balanced.json` (800 Beispiele) und `code-focused.json` (1000 Beispiele)!

## Troubleshooting

### "ModuleNotFoundError: datasets"

```bash
pip install datasets
# oder
pip install -r requirements.txt
```

### Download dauert sehr lange

```bash
# Reduziere Anzahl Samples
python scripts/download_hf_dataset.py wikipedia --samples 100
```

### "Connection Error"

```bash
# Überprüfe Internet-Verbindung
# Versuche es erneut (Hugging Face Server kann langsam sein)
# Oder nutze VPN falls Hugging Face blockiert ist
```

### Samples werden übersprungen

```
⚠️  Skipped 15 samples (empty or invalid)
```

Das ist normal! Manche Wikipedia-Artikel sind zu kurz oder leer.
Script lädt automatisch mehr, bis gewünschte Anzahl erreicht ist.

## Erweiterte Nutzung

### Eigene Datasets hinzufügen

Bearbeite `scripts/download_hf_dataset.py` und füge hinzu:

```python
DATASETS = {
    # ... existing ...
    "my_dataset": {
        "hf_path": "organization/dataset-name",
        "hf_config": None,  # oder "config_name"
        "split": "train",
        "converter": "my_converter",
        "description": "My custom dataset",
    },
}

def my_converter(example):
    """Convert your dataset format to chat format."""
    return {
        "messages": [
            {"role": "user", "content": example["question"]},
            {"role": "assistant", "content": example["answer"]}
        ]
    }
```

### Streaming vs. Download

Das Script nutzt `streaming=True`:
- ✅ Lädt nur benötigte Samples
- ✅ Kein vollständiger Download nötig
- ✅ Schneller Start

Für sehr große Downloads (>10k Samples) kann vollständiger Download effizienter sein.

## Weitere Datasets

Möchtest du andere Datasets? Schau auf:
- https://huggingface.co/datasets

Beliebte Optionen (noch nicht implementiert):
- **OpenAssistant**: Multi-Turn Conversations
- **Alpaca**: Instruction-Following
- **ShareGPT**: Chat-Daten
- **CodeSearchNet**: Code-Dokumentation
- **The Stack**: Riesiges Multi-Language Code Dataset
- **HumanEval**: Code-Evaluation Tasks

Du kannst eigene Datasets hinzufügen - siehe "Eigene Datasets hinzufügen" oben! 🚀

## Zusammenfassung

### Verfügbare Datasets (Stand jetzt)

| Dataset | Typ | Beispiele | Gut für |
|---------|-----|-----------|---------|
| **wikipedia** | Wissen | 1000-2000 | Allgemeinwissen, Definitionen |
| **stackoverflow** | Code Q&A | 500-1000 | Technische Hilfe, Problemlösung |
| **tiny-codes** | Code Snippets | 300-800 | Code-Generierung, kleine Tasks |
| **codeparrot** | Python Code | 500-1000 | Python Patterns, Clean Code |

### Quick Start

```bash
# 1. Dataset herunterladen (wähle eins)
python scripts/download_hf_dataset.py wikipedia --samples 1000
python scripts/download_hf_dataset.py stackoverflow --samples 500
python scripts/download_hf_dataset.py tiny-codes --samples 300
python scripts/download_hf_dataset.py codeparrot --samples 500

# 2. Training starten
./iterate.sh my-experiment

# 3. Dataset aus interaktiver Liste wählen
# [3] wikipedia.json
# [4] stackoverflow.json
# [5] tiny-codes.json
# [6] codeparrot.json

# 4. Fertig! Model trainiert auf gewähltem Dataset
```

**So einfach ist das!** 🎉

### Empfohlene Kombinationen

**Generalist-Modell** (Wissen + Code):
```bash
python scripts/download_hf_dataset.py wikipedia --samples 500
python scripts/download_hf_dataset.py tiny-codes --samples 500
# Dann manuell mischen (siehe "Kombinierte Datasets")
```

**Code-Experte** (Nur Programmierung):
```bash
python scripts/download_hf_dataset.py stackoverflow --samples 400
python scripts/download_hf_dataset.py tiny-codes --samples 400
python scripts/download_hf_dataset.py codeparrot --samples 400
# = 1200 Code-Beispiele aus 3 Quellen
```

**Schnelles Prototyping** (Klein & schnell):
```bash
python scripts/download_hf_dataset.py tiny-codes --samples 100
# Trainiert in ~2 Minuten
```
