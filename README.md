# 1. Repository klonen (oder kopieren)
git clone <DEIN_REPO_URL> dgx-lab
cd dgx-lab

# 2. Umgebung vorbereiten (Python Dependencies)
# Tipp: Nutze venv, um das System-Python sauber zu halten
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Infrastruktur starten (Docker)
# Prüfe kurz, ob nvidia-smi funktioniert
nvidia-smi
# Starte Ollama
docker-compose up -d

# 4. Basis-Modell laden (WICHTIG: Einmalig manuell machen)
# Das spart Zeit beim ersten Lauf von iterate.sh
docker exec ollama ollama pull qwen2.5:0.5b
