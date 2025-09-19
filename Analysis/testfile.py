import mailstore

mailstore.init_db()

email_id = mailstore.store_eml("Analysis/Transfer completed!!!.eml")
print(f"Email lagrad med ID: {email_id}")