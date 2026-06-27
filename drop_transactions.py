# File: drop_transactions.py
"""
Script destrutivo: apaga a tabela 'transactions' inteira.

Antes, este script dropava a tabela só de ser executado, sem nenhuma
confirmação — um `python drop_transactions.py` acidental perdia todos os
dados sem aviso. Agora exige confirmação explícita.

Uso:
    python drop_transactions.py --confirm
"""
import argparse
import sys

from backend.database import TransactionRecord, engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Apaga a tabela 'transactions'.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma a exclusão. Sem esta flag, o script não faz nada.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "[ABORTADO] Nenhuma alteração feita. Esta operação é IRREVERSÍVEL "
            "e apaga TODAS as transações. Execute com --confirm se tiver "
            "certeza, ex.: python drop_transactions.py --confirm"
        )
        sys.exit(1)

    answer = input(
        "Tem certeza que deseja apagar a tabela 'transactions'? Esta ação não "
        "pode ser desfeita. Digite 'sim' para continuar: "
    )
    if answer.strip().lower() != "sim":
        print("[ABORTADO] Confirmação não recebida.")
        sys.exit(1)

    TransactionRecord.__table__.drop(engine)
    print("[OK] Tabela 'transactions' excluída com sucesso.")


if __name__ == "__main__":
    main()
