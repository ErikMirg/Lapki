from yookassa import Configuration
from yookassa import Payment

from dotenv import load_dotenv

import os
import uuid

load_dotenv()

Configuration.account_id = os.getenv(
    "YOOKASSA_SHOP_ID"
)

Configuration.secret_key = os.getenv(
    "YOOKASSA_SECRET_KEY"
)


def create_payment(amount, description):

    payment = Payment.create({

        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },

        "confirmation": {
            "type": "redirect",
            "return_url": "http://127.0.0.1:8000"
        },

        "capture": True,

        "description": description

    }, str(uuid.uuid4()))

    return payment


def get_payment(payment_id):

    return Payment.find_one(payment_id)