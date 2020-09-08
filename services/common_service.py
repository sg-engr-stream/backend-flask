from models.card_access_model import CardAccess


def access_from_card_access(card_id, auth_user):
    card_from_card_access = [CardAccess.query.filter_by(card_id=card_id, username=username,
                                                        access_status=True, access_deleted=False).first()
                             for username in ['public', auth_user]]
    res = ''
    for item in card_from_card_access:
        if item is not None:
            if item.access_type == 'RW':
                return 'RW'
            else:
                res = 'RO'
    return res
