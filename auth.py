def phone_number_validator(phone:str):
    phone = phone.strip()
    if isinstance(phone,str) and len(phone) == 10:return phone
    else: return None
