from . models import CommissioneGiudicatrice, CommissioneGiudicatriceUsers

def get_commissioni_attive(user):
    if not user: return []
    commissioni_utente = CommissioneGiudicatriceUsers.objects.filter(user=user,
                                                                     user__is_active=True)
    commissioni_attive = []
    for cu in commissioni_utente:
        if cu.commissione.is_active:
            commissioni_attive.append(cu.commissione)
    return commissioni_attive

def get_commissioni_in_corso(user, commissioni_attive=[]):
    if not user: return []
    if not commissioni_attive:
        commissioni_attive = get_commissioni_attive(user)
    commissioni_in_corso = []
    for c in commissioni_attive:
        if c.is_in_corso():
            commissioni_in_corso.append(c)
    return commissioni_in_corso
