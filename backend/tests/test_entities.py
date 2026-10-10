from app.detection.entities import extract_entities


def test_phones_upi_urls_apps_amounts():
    e = extract_entities("Call +91 98765 43210 or 9876543210. Pay to rahul.s@okaxis, mail me at a.b@gmail.com. "
                         "Visit http://bit.ly/kyc-now and install AnyDesk. Send Rs 4,85,000 or 500 rupees.")
    assert "+919876543210" in e.phones and "9876543210" in e.phones
    assert e.upi_ids == ["rahul.s@okaxis"]
    assert "http://bit.ly/kyc-now" in e.urls
    assert "anydesk" in e.apps
    assert any("4,85,000" in a for a in e.amounts)


def test_email_is_not_upi():
    assert extract_entities("write to someone@gmail.com").upi_ids == []


def test_otp_is_not_phone():
    assert extract_entities("your otp is 482913").phones == []
