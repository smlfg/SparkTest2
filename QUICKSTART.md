# 🚀 Quick Start für Anfänger

**Komplette Setup-Zeit: 10 Minuten**

---

## Schritt 1: Repository herunterladen

```bash
git clone https://github.com/smlfg/SparkTest2.git
cd SparkTest2
```

---

## Schritt 2: Setup-Skript ausführen

```bash
chmod +x setup.sh
./setup.sh
```

Das Skript macht alles automatisch:
- ✅ Prüft GPU, Docker, Python
- ✅ Erstellt Python Umgebung
- ✅ Installiert Pakete
- ✅ Startet Ollama
- ✅ Lädt Base-Model (500MB)

**Wenn Fehler auftreten**, folge den Anweisungen im Skript!

---

## Schritt 3: Umgebung aktivieren

**Wichtig**: Diesen Befehl bei jedem neuen Terminal ausführen!

```bash
source venv/bin/activate
```

Du siehst dann `(venv)` vor deinem Prompt.

---

## Schritt 4: Testen

```bash
# GPU testen
nvidia-smi

# Ollama testen
curl http://localhost:11434/api/tags

# Benchmark testen (wenn Model vorhanden)
cd benchmark
python run.py --help
```

---

## Was passiert jetzt?

**Aktueller Status**:
- ✅ **Agent 2** (Benchmark System) ist fertig
- 🔜 **Agent 1** (Training) kommt bald
- 🔜 **Agent 5** (Infrastructure) kommt bald
- 🔜 **Agent 3-6** (Analysis, Viz, Orchestration) kommen bald

**Sobald alle Agents fertig sind**, kannst du:

```bash
# Ein komplettes Fine-tuning Iteration in 5 Minuten
./iterate.sh exp-001 datasets/example.json
```

---

## Hilfe

**Problem**: `nvidia-smi` funktioniert nicht
- **Lösung**: GPU-Treiber installieren
  ```bash
  sudo apt-get install nvidia-driver-535
  sudo reboot
  ```

**Problem**: Docker nicht gefunden
- **Lösung**: Docker installieren
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  newgrp docker
  ```

**Problem**: Ollama startet nicht
- **Lösung**: Container-Status prüfen
  ```bash
  docker ps
  docker logs ollama
  docker-compose up -d
  ```

**Weitere Probleme?** Siehe [README.md](README.md) → Troubleshooting Sektion

---

## Nützliche Befehle

```bash
# Umgebung aktivieren (bei jedem Terminal-Start)
source venv/bin/activate

# Umgebung deaktivieren
deactivate

# Ollama-Status prüfen
docker ps
curl http://localhost:11434/api/tags

# Verfügbare Modelle anzeigen
docker exec ollama ollama list

# GPU-Status prüfen
nvidia-smi

# Benchmark laufen lassen (wenn exp-001 Model existiert)
cd benchmark
python run.py --finetuned exp-001
```

---

## Nächste Schritte

1. **Dokumentation lesen**: [README.md](README.md)
2. **Benchmark verstehen**: [benchmark/README.md](benchmark/README.md)
3. **Teaching Guide**: [docs/agents/agent2_teaching.md](docs/agents/agent2_teaching.md)
4. **Auf Agents 1,3,4,5,6 warten** - Coming soon!

---

## Support

- **GitHub Issues**: https://github.com/smlfg/SparkTest2/issues
- **README**: Ausführliche Dokumentation
- **Teaching Docs**: Lernmaterialien in `docs/agents/`

---

**Fertig! Du bist jetzt bereit für die DGX Fast Fine-tuning Iteration Lab! 🎉**
