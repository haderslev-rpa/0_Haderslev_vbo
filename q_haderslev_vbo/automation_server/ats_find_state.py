def find_state(data, search_text: str) -> bool:
    """
    Bruges til at finde ud af om bestemte state findes i item
    Søger i 'state' niveauet efter en linje hvor 'niveau' indeholder search_text.
    
    Parametre:
        data        : dict   - Din JSON data (parsed)
        search_text : str    - Teksten du vil søge efter (f.eks. "3.0 test")
    
    Returnerer: True hvis fundet, ellers False
    """
    if not isinstance(data, dict) or not isinstance(search_text, str):
        return False

    search_text = search_text.lower()   # Gør søgningen case-insensitive

    def search(obj):
        if isinstance(obj, dict):
            # Hvis vi har fundet 'state'
            if 'state' in obj and isinstance(obj['state'], list):
                for linje in obj['state']:
                    if isinstance(linje, dict):
                        niveau = linje.get('niveau') or linje.get('level') or linje.get('Niveau')
                        if isinstance(niveau, str) and search_text in niveau.lower():
                            return True
            
            # Søg videre i alle værdier (rekursivt)
            for value in obj.values():
                if search(value):
                    return True
                    
        elif isinstance(obj, list):
            for item in obj:
                if search(item):
                    return True
        return False

    return search(data)