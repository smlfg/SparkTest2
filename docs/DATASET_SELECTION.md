# Interaktive Dataset-Auswahl

## Neue Feature: Dataset-Auswahl im Terminal

Ab jetzt kannst du Datensätze interaktiv auswählen, statt den Pfad manuell anzugeben!

## Verwendung

### Option 1: Interaktive Auswahl (NEU!)

```bash
./iterate.sh exp-001
```

Das Script zeigt dir dann alle verfügbaren Datasets:

```
================================
📂 Dataset Selection
================================

Available datasets:

  [1] example-chatbot.json
      📊 Examples: 20  |  💾 Size: 4.2K
      Preview: "Hello! How are you today?"

  [2] example-classifier.json
      📊 Examples: 15  |  💾 Size: 2.8K
      Preview: "Classify this text as positive, negative, or neutral: I ..."

Select dataset [1-2]: _
```

Wähle einfach die Nummer aus!

### Option 2: Direkter Pfad (wie bisher)

```bash
./iterate.sh exp-001 datasets/example-chatbot.json
```

Funktioniert weiterhin wie gewohnt - für Automatisierung und Scripts.

## Neue Datasets hinzufügen

### Schritt 1: Dataset erstellen

Erstelle eine neue JSON-Datei im `datasets/` Ordner:

```bash
nano datasets/mein-dataset.json
```

### Schritt 2: Format

```json
[
  {
    "messages": [
      {"role": "user", "content": "Deine erste Frage"},
      {"role": "assistant", "content": "Die gewünschte Antwort"}
    ]
  },
  {
    "messages": [
      {"role": "user", "content": "Zweite Frage"},
      {"role": "assistant", "content": "Zweite Antwort"}
    ]
  }
]
```

### Schritt 3: Speichern und verwenden

```bash
# Speichere die Datei
# Dann starte iterate.sh

./iterate.sh mein-experiment
# -> Wähle dein neues Dataset aus der Liste!
```

## Beispiel-Session

```bash
$ ./iterate.sh german-bot

================================
📂 Dataset Selection
================================

Available datasets:

  [1] example-chatbot.json
      📊 Examples: 20  |  💾 Size: 4.2K
      Preview: "Hello! How are you today?"

  [2] example-classifier.json
      📊 Examples: 15  |  💾 Size: 2.8K
      Preview: "Classify this text as positive, negative, or neutral: I ..."

  [3] german-responses.json
      📊 Examples: 30  |  💾 Size: 6.1K
      Preview: "Wie geht es dir?"

Select dataset [1-3]: 3

✓ Selected: german-responses.json

================================
Agent 6: Orchestration
================================

Experiment: german-bot
Dataset:    datasets/german-responses.json

[Pipeline starts...]
```

## Vorteile

✅ **Schneller**: Keine Pfade tippen
✅ **Übersichtlich**: Siehst alle verfügbaren Datasets
✅ **Vorschau**: Siehst erste Nachricht jedes Datasets
✅ **Info**: Anzahl Beispiele + Dateigröße
✅ **Kompatibel**: Alte Syntax funktioniert weiterhin

## Dataset-Organisation

Empfohlene Struktur im `datasets/` Ordner:

```
datasets/
├── example-chatbot.json       # Allgemein
├── example-classifier.json    # Sentiment-Analyse
├── german-responses.json      # Deutsche Antworten
├── tech-support.json          # Tech-Support
├── medical-qa.json            # Medizinische Fragen
└── custom-domain.json         # Dein spezielles Thema
```

Benenne deine Datasets beschreibend, damit du sie in der Liste leicht erkennst!

## Beide Versionen unterstützen die neue Feature

```bash
# Original-Version
./iterate.sh exp-001

# Bulletproof-Version
./iterate-robust.sh exp-001
```

Beide zeigen die interaktive Auswahl!

## Automatisierung

Für Scripts und Automatisierung nutze weiterhin den direkten Pfad:

```bash
#!/bin/bash
for i in {1..5}; do
    ./iterate.sh exp-00$i datasets/training-data.json
done
```

So wird nicht nach Eingabe gefragt und das Script läuft durch.

## Troubleshooting

### "No datasets found"

```bash
# Überprüfe datasets/ Ordner
ls -la datasets/

# Falls leer, kopiere Beispiel
cp datasets/example-chatbot.json datasets/my-first-dataset.json
```

### Dataset erscheint nicht

- Datei muss `.json` Endung haben
- Datei muss im `datasets/` Ordner sein
- JSON muss valide sein (teste mit `python3 -m json.tool < datasets/datei.json`)

### Preview zeigt nichts

Das ist ok - Preview ist optional. Dataset funktioniert trotzdem!

---

**Tipp**: Erstelle einen `datasets/README.md` um deine Datasets zu dokumentieren:

```markdown
# Meine Datasets

- `medical-qa.json`: 50 medizinische Fragen (Deutsch)
- `tech-support.json`: 30 Tech-Support Dialoge
- `casual-chat.json`: 40 lockere Gespräche
```
