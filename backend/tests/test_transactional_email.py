import asyncio

from services import email_brevo


def test_email_templates_escape_customer_and_product_content():
    html = email_brevo.order_confirmation_html(
        customer_name="<script>alert(1)</script>",
        order_ref="ORD<&>",
        total_eur=10.0,
        items=[{"product_name": "<img src=x>", "variant_label": "A&B", "quantity": 1, "unit_price_eur": 10.0}],
    )
    assert "<script>" not in html
    assert "<img src=x>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img src=x&gt;" in html


def test_all_transactional_flow_templates_exist():
    assert "pagamento" in email_brevo.payment_confirmation_html(customer_name="Mario", order_ref="ORD-1", total_eur=10.0).lower()
    assert "problema" in email_brevo.order_problem_html(customer_name="Mario", order_ref="ORD-1", support_code="SUP-1").lower()
    assert "licenza" in email_brevo.license_delivery_html(customer_name="Mario", order_ref="ORD-1", product_name="Office", license_key="AAAA-BBBB").lower()


def test_dry_run_email_never_requires_provider_or_network(monkeypatch):
    monkeypatch.setattr(email_brevo, "EMAIL_DELIVERY_MODE", "dry-run", raising=False)
    monkeypatch.setattr(email_brevo, "BREVO_API_KEY", "")
    message_id = asyncio.run(email_brevo.send_email(
        to_email="customer@example.com",
        to_name="Customer",
        subject="Test",
        html="<p>Safe</p>",
        tags=["test"],
    ))
    assert message_id.startswith("dry-run:")
