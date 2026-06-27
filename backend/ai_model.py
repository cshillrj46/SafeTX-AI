# File: backend/ai_model.py
import logging
import os

import joblib

logger = logging.getLogger("safetx.ai_model")

# Caminhos corretos para a pasta backend
model_path = os.path.join(os.path.dirname(__file__), "risk_model.joblib")
encoder_sender_path = os.path.join(os.path.dirname(__file__), "encoder_sender.joblib")
encoder_recipient_path = os.path.join(os.path.dirname(__file__), "encoder_recipient.joblib")
encoder_risk_path = os.path.join(os.path.dirname(__file__), "encoder_risk.joblib")

# Carga dos arquivos
try:
    model = joblib.load(model_path)
    encoder_sender = joblib.load(encoder_sender_path)
    encoder_recipient = joblib.load(encoder_recipient_path)
    encoder_risk = joblib.load(encoder_risk_path)
    logger.info("Modelos carregados com sucesso.")
except (FileNotFoundError, OSError, EOFError) as e:
    logger.error("Erro ao carregar modelo ou encoders: %s", e)
    model = None
    encoder_sender = encoder_recipient = encoder_risk = None


def _encode_or_default(encoder, value: str, label: str) -> int:
    """
    Tenta codificar um valor categórico já visto no treino. Se o
    sender/recipient for desconhecido pelo encoder (LabelEncoder lança
    ValueError), cai para 0 e REGISTRA o evento — antes isso era engolido
    por um `except:` genérico e silencioso, mascarando degradação do modelo.
    """
    try:
        return encoder.transform([value])[0]
    except ValueError:
        logger.warning(
            "%s '%s' desconhecido pelo encoder (fora do vocabulário de treino); "
            "usando valor padrão 0.",
            label,
            value,
        )
        return 0


def predict_risk(sender: str, recipient: str, amount_eth: float) -> str | None:
    if not model:
        logger.error("Modelo indisponível — predict_risk chamado sem modelo carregado.")
        return None

    sender_encoded = _encode_or_default(encoder_sender, sender, "sender")
    recipient_encoded = _encode_or_default(encoder_recipient, recipient, "recipient")

    features = [[sender_encoded, recipient_encoded, amount_eth]]

    try:
        prediction = model.predict(features)[0]
        label = encoder_risk.inverse_transform([prediction])[0]
        return str(label).strip().lower()
    except (ValueError, IndexError) as e:
        logger.error("Erro na previsão do modelo: %s", e)
        return None
