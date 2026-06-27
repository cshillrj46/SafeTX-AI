<p align="center">
  <img src="./SafeTX.png" alt="SafeTX Banner" />
</p>
A smart and secure Web3 transaction analysis platform using Artificial Intelligence. Built to protect your crypto wallet and alert you of suspicious or high-risk activities in real time.
<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/github/license/cshillrj46/SafeTX-AI)
![Last Commit](https://img.shields.io/github/last-commit/cshillrj46/SafeTX-AI)
![Stars](https://img.shields.io/github/stars/cshillrj46/SafeTX-AI?style=social)

</div>

## 🚀 Features

- 🔍 **AI-Powered Transaction Risk Classification**
- 📊 **Transaction History with Filtering & Pagination**
- 🔔 **Real-Time Alerts via Webhook and Email**
- 🧠 **Machine Learning with Balanced Training**
- 💻 **Modern Web Interface (React + TailwindCSS)**
- 🛡️ **Secure FastAPI Backend with JWT Auth**
- 📁 **Modular and Scalable Project Architecture**

---

## 🛠️ Tech Stack

| Layer        | Technology                    |
|--------------|-------------------------------|
| Frontend     | React, TypeScript, TailwindCSS|
| Backend      | FastAPI, SQLAlchemy, Uvicorn  |
| AI Engine    | scikit-learn, SMOTE, joblib   |
| Database     | SQLite                        |
| Alerts       | SMTP (Gmail), Webhooks        |

---

## 📦 Installation

### 1. Clone the project
```bash
git clone https://github.com/cshillrj46/SafeTX-AI.git
cd SafeTX-AI
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate   # Linux/Mac
cd ..
pip install -r requirements.txt
```

Configure as variáveis de ambiente antes de subir a API:
```bash
cp .env.example .env
# edite o .env com suas próprias credenciais (Gmail App Password, SECRET_KEY, etc.)
```

Suba a API:
```bash
uvicorn backend.main:app --reload
```

### 3. Frontend Setup
```bash
cd safetx-dashboard
npm install
npm run dev
```

---

## 📈 Usage

- Visit `http://localhost:5173` to access the frontend
- Backend runs at `http://localhost:8000`
- All API endpoints (except `/register` and `/token`) require a JWT Bearer token.
  Register a user, then log in to get a token:
  ```bash
  curl -X POST http://localhost:8000/register \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","email":"alice@example.com","password":"senha-forte"}'

  curl -X POST http://localhost:8000/token \
    -d "username=alice&password=senha-forte"
  ```
- You can submit transactions manually or connect a Web3 wallet integration
- Reclassification and alerts are automatically logged

---

## 🧪 Testing AI Model
To retrain the model:
```bash
python backend/train_model.py
```

Model files are saved in `backend/`:
- `risk_model.joblib`
- `encoder_sender.joblib`
- `encoder_recipient.joblib`
- `encoder_risk.joblib`

---

## 🧩 Folder Structure
```
SafeTX-AI/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── train_model.py
│   ├── database.py
│   ├── ai_model.py
│   └── ...
├── safetx-dashboard/      # frontend (React + Vite + TypeScript)
│   ├── src/
│   ├── public/
│   └── ...
├── blockchain/            # contratos Solidity (Hardhat)
├── tests/                 # testes automatizados (pytest)
├── alembic/               # migrações do banco de dados
├── .env.example
├── requirements.txt
├── transactions.csv
├── README.md
└── LICENSE
```

## 🧪 Running automated tests
```bash
pip install -r requirements.txt
pytest
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 💬 Contact

- Twitter: [@SafeTX_AI](https://twitter.com/SafeTX_AI)
- GitHub Issues: [Report a Bug](https://github.com/cshillrj46/SafeTX-AI/issues)

---

> SafeTX-AI: Empowering secure crypto transactions with smart technology.
