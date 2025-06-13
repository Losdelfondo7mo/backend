from fastapi import APIRouter, HTTPException
from prisma import Prisma
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class PaymentCreate(BaseModel):
    """
    Schema de pagos para tarjetas de crédito
    """
    amount: float
    card_number: str  
    card_holder: str
    expiration_date: str
    cvv: str
    description: str | None = None

class PaymentResponse(BaseModel):
    """
    Esquema de respuesta de pagos
    """
    id: int
    amount: float
    status: str
    created_at: datetime
    transaction_id: str

@router.post("/payments/credit-card", response_model=PaymentResponse)
async def create_credit_card_payment(payment: PaymentCreate):
    """
    crea una nueva tarjeta de credito payment
    
    Args:
        payment (PaymentCreate): Payment information including card details
        
    Returns:
        PaymentResponse: Created payment details
        
    Raises:
        HTTPException: If payment processing fails
    """
    try:
        db = Prisma()
        await db.connect()
        
        # Create payment record
        new_payment = await db.payment.create({
            'data': {
                'amount': payment.amount,
                'payment_method': 'credit_card',
                'status': 'pending',
                'card_info': {
                    'create': {
                        'card_number': payment.card_number[-4:],  # Store only last 4 digits
                        'card_holder': payment.card_holder,
                        'expiration_date': payment.expiration_date
                    }
                },
                'description': payment.description
            }
        })
        
        await db.disconnect()
        
        return PaymentResponse(
            id=new_payment.id,
            amount=new_payment.amount,
            status=new_payment.status,
            created_at=new_payment.created_at,
            transaction_id=str(new_payment.id)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to process payment"
        )

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int):
    """
    Get payment details by ID
    
    Args:
        payment_id (int): ID of the payment to retrieve
        
    Returns:
        PaymentResponse: Payment details
        
    Raises:
        HTTPException: If payment is not found
    """
    try:
        db = Prisma()
        await db.connect()
        
        payment = await db.payment.find_unique(
            where={'id': payment_id}
        )
        
        await db.disconnect()
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )
            
        return PaymentResponse(
            id=payment.id,
            amount=payment.amount,
            status=payment.status,
            created_at=payment.created_at,
            transaction_id=str(payment.id)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve payment"
        )
