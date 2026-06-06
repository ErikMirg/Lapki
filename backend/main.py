from fastapi import FastAPI, Request
from sqlalchemy.orm import Session

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine
from database import SessionLocal

from models import Base
from models import Order

from schemas import OrderCreate

from yookassa_service import create_payment
from yookassa_service import get_payment

app = FastAPI(
    title="Здоровая лапка",
    version="1.0"
)

@app.middleware("http")
async def security_headers(request: Request, call_next):

    response = await call_next(request)

    response.headers["Strict-Transport-Security"] = \
        "max-age=31536000; includeSubDomains"

    response.headers["X-Content-Type-Options"] = \
        "nosniff"

    response.headers["X-Frame-Options"] = \
        "SAMEORIGIN"

    response.headers["Referrer-Policy"] = \
        "strict-origin-when-cross-origin"

    response.headers["Permissions-Policy"] = \
        "camera=(), microphone=(), geolocation=()"

    response.headers["Content-Security-Policy"] = \
        "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"

    return response

app.mount(
    "/static",
    StaticFiles(directory="/app"),
    name="static"
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return FileResponse("index.html")


@app.get("/price")
def download_price():
    return FileResponse(
        "Список услуг.xlsx",
        filename="Список_услуг.xlsx"
    )

@app.get("/robots.txt", include_in_schema=False)
def robots():
    return FileResponse("robots.txt")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    return FileResponse("sitemap.xml")

@app.post("/orders")
def create_order(order: OrderCreate):

    db: Session = SessionLocal()

    new_order = Order(
        service_name=order.service_name,
        price=order.price,
        status="pending",
        payment_id=""
    )

    db.add(new_order)

    db.commit()

    db.refresh(new_order)

    db.close()

    return {
        "id": new_order.id,
        "service_name": new_order.service_name,
        "price": new_order.price,
        "status": new_order.status
    }


@app.post("/payment/create")
def create_test_payment():

    payment = create_payment(
        100,
        "Тестовая оплата услуг клиники Здоровая лапка"
    )

    return {
        "payment_id": payment.id,
        "status": payment.status,
        "payment_url": payment.confirmation.confirmation_url
    }


@app.get("/payment/status/{payment_id}")
def payment_status(payment_id: str):

    payment = get_payment(payment_id)

    return {
        "payment_id": payment.id,
        "status": payment.status,
        "paid": payment.paid
    }


@app.get("/payment/check-pending")
def check_pending():

    db: Session = SessionLocal()

    orders = db.query(Order).all()

    updated = []

    for order in orders:

        if not order.payment_id:
            continue

        try:

            payment = get_payment(
                order.payment_id
            )

            if payment.status == "succeeded":

                order.status = "paid"

                updated.append({
                    "order_id": order.id,
                    "payment_id": order.payment_id
                })

        except Exception:
            pass

    db.commit()

    db.close()

    return {
        "updated_orders": updated
    }

@app.get("/orders")
def get_orders():

    db: Session = SessionLocal()

    orders = db.query(Order).all()

    result = []

    for order in orders:

        result.append({
            "id": order.id,
            "service_name": order.service_name,
            "price": order.price,
            "status": order.status,
            "payment_id": order.payment_id
        })

    db.close()

    return result

@app.post("/payment/create/{order_id}")
def create_order_payment(order_id: int):

    db: Session = SessionLocal()

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:

        db.close()

        return {
            "error": "Заказ не найден"
        }

    payment = create_payment(
        order.price,
        order.service_name
    )

    order.payment_id = payment.id

    db.commit()

    db.close()

    return {
        "order_id": order.id,
        "payment_id": payment.id,
        "payment_url":
            payment.confirmation.confirmation_url
    }