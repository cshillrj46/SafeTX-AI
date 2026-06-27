# Contributing to SafeTX-AI

We welcome contributions from developers, designers, and security experts to make SafeTX-AI the most trusted and intelligent Web3 anti-fraud platform.

## 🛠️ How to Contribute

1. **Fork the repository**
   - Navigate to [https://github.com/cshillrj46/SafeTX-AI](https://github.com/cshillrj46/SafeTX-AI) and click `Fork`.

2. **Clone your fork**
```bash
   git clone https://github.com/YOUR_USERNAME/SafeTX-AI.git
   cd SafeTX-AI
```

3. **Create a new branch**
```bash
   git checkout -b feature/my-feature
```

4. **Make your changes locally**
   - Follow the coding standards defined in the project
   - Run tests before pushing

5. **Commit your changes**
```bash
   git add .
   git commit -m "✨ Add new feature: my-feature"
```

6. **Push your branch to GitHub**
```bash
   git push origin feature/my-feature
```

7. **Create a Pull Request**
   - Go to your fork and click `Compare & pull request`
   - Provide a clear description of what your PR does

---

## ✅ Contribution Guidelines

- Keep your PRs focused and small
- Include screenshots for UI changes
- Add tests for new functionality
- Follow the folder structure and naming conventions

## 🧪 Local Development Setup

### Backend (FastAPI + SQLite)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend (React + Tailwind)
```bash
cd safetx-dashboard
npm install
npm run dev
```

---

## 🧠 AI Model Training

To improve or retrain the AI model:
```bash
cd backend
python train_model.py
```
The model and encoders will be saved in the backend folder.

---

## 🔐 Security
If you discover a vulnerability, please report it by email at `safetx.alert@proton.me`.

---

## 🙌 Thank You
Your contribution makes SafeTX-AI better and safer for the Web3 community. Let's build the future of secure crypto transactions together!
