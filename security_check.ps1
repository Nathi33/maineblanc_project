# ==========================================
# Script de veille sécurité pour le projet Django
# Projet : Camping Le Maine Blanc
# Auteur : Nathalie Darnaudat
# ==========================================

Write-Host "=== 🛡️ Vérification de la sécurité du projet Django ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier la version actuelle de Django
Write-Host "1️ Version actuelle de Django :" -ForegroundColor Yellow
python -m django --version
Write-Host ""

# Lister les dépendances obsolètes
Write-Host "2️ Liste des dépendances obsolètes :" -ForegroundColor Yellow
pip list --outdated
Write-Host ""

# Vérifier si pip-audit est installé, sinon l’installer
Write-Host "3️ Audit des dépendances Python avec pip-audit :" -ForegroundColor Yellow
pip show pip-audit > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Installation de pip-audit (non détecté)..."
    pip install pip-audit
}
pip audit
Write-Host ""

# Résumé
Write-Host "=== ✅ Vérification terminée ===" -ForegroundColor Green
Write-Host "Les résultats ci-dessus indiquent les mises à jour ou vulnérabilités à corriger."
Write-Host "Pense à relancer ce script une fois par mois pour garder ton environnement à jour."
pause
