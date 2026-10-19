# AI Recommendation Index (Jovian Labs)

Mesure chaque semaine quelles entreprises les assistants IA (Gemini avec Google Search, Perplexity Sonar) recommandent
pour « meilleur [métier] à [ville] » dans de grandes villes américaines, avec intervalles de confiance à 95 % (Wilson).
Les pages sont générées dans `/ai-index/` à la racine du dépôt.

- `config.json` : catégories, villes, formulations des questions, moteurs, nombre d'échantillons, budget d'appels.
- `python -m aiindex run` : mesure (clés `GEMINI_API_KEY` et `PERPLEXITY_API_KEY` en variables d'environnement).
- `python -m aiindex render --out ../..` : génère les pages (4 dernières semaines).
- `python -m aiindex all --mock --data /tmp/d --out /tmp/site` : test complet avec un moteur simulé, sans API (pages marquées TEST et non indexées).
- Automatisation : `.github/workflows/ai-index.yml`, chaque lundi 06:17 UTC, ou à la demande (onglet Actions → Run workflow).
- Les clés d'API se règlent dans GitHub → Settings → Secrets and variables → Actions. Elles ne sont jamais écrites dans le code.
- Coût prévu avec la configuration actuelle (20 pages, 240 réponses par semaine) : quota gratuit Gemini (5 000 requêtes/mois) + environ 3 à 5 $/mois chez Perplexity.
