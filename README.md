# 📏 LLM Eval Harness

![Status](https://img.shields.io/badge/status-in%20progress-orange?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white) ![OpenRouter](https://img.shields.io/badge/OpenRouter-6566F1?style=for-the-badge&logo=openai&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

> A lightweight harness for measuring how accurately different LLMs extract structured data, and at what cost and speed.

## 🎯 Why this project

Choosing a model for production is hard without numbers. This harness runs the same labelled test set through several models and reports field-level accuracy, cost per document and latency, so model choices are based on evidence rather than guesswork.

## 🧱 Planned stack

- Python 3.12 with pytest-style test cases
- OpenRouter for access to many models through one API
- Pandas for scoring and reports
- Markdown and HTML reports
- GitHub Actions to run evals on every change

## 🗺️ Roadmap

- [ ] Labelled test-set format (input and expected JSON)
- [ ] Field-level accuracy scoring
- [ ] Cost and latency tracking per model
- [ ] Side-by-side model comparison report
- [ ] Regression checks in CI
- [ ] Example evals for order and invoice extraction

## 📌 Status

🚧 This project is in early development. Code is coming soon. It uses synthetic sample data only.

---

Built by [Jahanzaib Ahmad](https://github.com/jehanxaibahmed) · Full Stack Engineer · AI & LLM Systems
