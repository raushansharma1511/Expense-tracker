from rest_framework.response import Response
from django.core.mail import EmailMessage
from celery import shared_task
from django.conf import settings
from transactions.models import Transaction
import csv
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from account.models import User


@shared_task
def send_transaction_history_email(
    user_id,
    user_email,
    start_date,
    end_date,
    file_format,
):
    """Celery task to generate and send transaction history via email asynchronously."""
    
    user = User.objects.get(id=user_id)
    # Filter transactions for the authenticated user
    transactions = (
        Transaction.objects.filter(
            user=user,
            is_deleted=False,
            date_time__date__range=(start_date, end_date),
        )
        .select_related("category", "wallet")
        .order_by("-date_time")
    )

    # if not transactions.exists():
    #     return {"error": "No transactions found for the given date range"}

    credit_transactions = [
        {
            "category": txn.category.name,  # Fetch category name
            "amount": str(txn.amount),
            "wallet": txn.wallet.name,  # Fetch wallet name
            "date": txn.date_time.date().isoformat(),
        }
        for txn in transactions.filter(type="credit")
    ]

    debit_transactions = [
        {
            "category": txn.category.name,  # Fetch category name
            "amount": str(txn.amount),
            "wallet": txn.wallet.name,  # Fetch wallet name
            "date": txn.date_time.date().isoformat(),
        }
        for txn in transactions.filter(type="debit")
    ]

    # Generate file
    file_data = None
    file_name = f"transactions_history_{start_date}_{end_date}.{file_format}"

    try:
        # Generate file in memory
        if file_format == "csv":
            file_data = generate_csv_transaction_history(
                start_date, end_date, credit_transactions, debit_transactions
            )
        elif file_format == "pdf":
            file_data = generate_pdf_transaction_history(
                start_date, end_date, credit_transactions, debit_transactions
            )

        # Prepare email
        email_subject = "Your Transaction History"
        email_body = f"Attached is your transaction history report from {start_date} to {end_date}."
        email = EmailMessage(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
        )

        # Attach file in memory
        email.attach(file_name, file_data.getvalue(), f"application/{file_format}")
        email.send()

        return {"message": "Transaction history sent via email successfully"}

    except Exception as e:
        return {"error": str(e)}



def generate_csv_transaction_history(
    start_date, end_date, credit_transactions, debit_transactions
):
    """Generates a CSV file for transaction history in memory."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Calculate total amounts
    total_credit = sum(float(txn["amount"]) for txn in credit_transactions)
    total_debit = sum(float(txn["amount"]) for txn in debit_transactions)

    # Metadata
    writer.writerow(["Transaction History Report"])
    writer.writerow([f"Date Range: {start_date} to {end_date}"])
    writer.writerow([])  # Blank line

    # Total Amounts
    writer.writerow(["Total Income", total_credit])
    writer.writerow(["Total Expense", total_debit])
    writer.writerow([])  # Blank line

    # Credit Transactions
    writer.writerow(["Credit Transactions"])
    writer.writerow(["Category", "Amount", "Wallet", "Date"])
    for txn in credit_transactions:
        writer.writerow([txn["category"], txn["amount"], txn["wallet"], txn["date"]])

    writer.writerow([])  # Blank line

    # Debit Transactions
    writer.writerow(["Debit Transactions"])
    writer.writerow(["Category", "Amount", "Wallet", "Date"])
    for txn in debit_transactions:
        writer.writerow([txn["category"], txn["amount"], txn["wallet"], txn["date"]])

    output.seek(0)  # Move cursor to start for reading
    return output



def generate_pdf_transaction_history(
    start_date, end_date, credit_transactions, debit_transactions
):
    """Generates a well-formatted PDF file for transaction history using ReportLab's Platypus."""

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []  # Holds all PDF elements

    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Transaction History Report", styles["Title"]))
    elements.append(Spacer(1, 12))  # Spacer for better readability

    # Date Range
    elements.append(
        Paragraph(f"Date Range: {start_date} to {end_date}", styles["Normal"])
    )
    elements.append(Spacer(1, 12))

    # Calculate total amounts
    total_credit = sum(float(txn["amount"]) for txn in credit_transactions)
    total_debit = sum(float(txn["amount"]) for txn in debit_transactions)

    # Total Income & Expense Table
    total_table_data = [
        ["Total Income", f"{total_credit:.2f}"],
        ["Total Expense", f"{total_debit:.2f}"],
    ]

    total_table = Table(total_table_data, colWidths=[200, 150])
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    elements.append(total_table)
    elements.append(Spacer(1, 12))

    # Function to generate transactions table
    def create_transaction_table(title, transactions):
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 8))

        table_data = [["Category", "Amount", "Wallet", "Date"]]
        for txn in transactions:
            table_data.append(
                [txn["category"], txn["amount"], txn["wallet"], txn["date"]]
            )

        transaction_table = Table(table_data, colWidths=[150, 100, 100, 100])
        transaction_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        elements.append(transaction_table)
        elements.append(Spacer(1, 12))

    # Add Credit Transactions Table
    create_transaction_table("Credit Transactions", credit_transactions)

    # Add Debit Transactions Table
    create_transaction_table("Debit Transactions", debit_transactions)

    # Build PDF
    doc.build(elements)
    output.seek(0)
    return output
