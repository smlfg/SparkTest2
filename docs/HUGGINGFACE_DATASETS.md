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

## Verwendung

### Schritt 1: Dataset herunterladen

```bash
# Wikipedia (1000 Beispiele)
python scripts/download_hf_dataset.py wikipedia --samples 1000

# StackOverflow (500 Beispiele)
python scripts/download_hf_dataset.py stackoverflow --samples 500
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

## Kombinierte Datasets

Du kannst mehrere Datasets mischen:

```bash
# 1. Lade mehrere Datasets
python scripts/download_hf_dataset.py wikipedia --samples 500
python scripts/download_hf_dataset.py stackoverflow --samples 500

# 2. Wähle beim Training
./iterate.sh wiki-model
# -> Wähle wikipedia.json

./iterate.sh code-model
# -> Wähle stackoverflow.json

./iterate.sh mixed-model datasets/combined.json
```

### Manuelles Mischen

```python
import json

# Lade beide
with open('datasets/wikipedia.json') as f:
    wiki = json.load(f)

with open('datasets/stackoverflow.json') as f:
    stack = json.load(f)

# Mische
combined = wiki[:250] + stack[:250]  # Je 250 Beispiele

# Speichere
with open('datasets/combined.json', 'w') as f:
    json.dump(combined, f, indent=2)
```

Jetzt hast du `combined.json` mit 500 gemischten Beispielen!

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

Beliebte Optionen:
- **OpenAssistant**: Multi-Turn Conversations
- **Alpaca**: Instruction-Following
- **ShareGPT**: Chat-Daten
- **CodeSearchNet**: Code-Dokumentation

Sag mir welche du brauchst und ich erweitere das Script! 🚀

## Zusammenfassung

```bash
# 1. Dataset herunterladen
python scripts/download_hf_dataset.py wikipedia --samples 1000

# 2. Training starten
./iterate.sh wiki-experiment

# 3. Wikipedia-Dataset aus Liste wählen
# [3] wikipedia.json ← Auswählen

# 4. Fertig! Model trainiert auf Wikipedia-Wissen
```

**So einfach ist das!** 🎉
