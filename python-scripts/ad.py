import subprocess
import requests
import json

# Functie om alle decks op te halen via AnkiConnect
def get_all_decks():
    url = 'http://localhost:8765'
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "action": "deckNames",
        "version": 6
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    decks = response.json().get('result', [])
    return decks

# Functie om alle kaarten in een deck te vinden
def get_note_ids_from_deck(deck_name):
    url = 'http://localhost:8765'
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:{deck_name}"
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    note_ids = response.json().get('result', [])
    return note_ids

# Functie om een deck te verwijderen, inclusief de kaarten
def delete_deck(deck_name):
    note_ids = get_note_ids_from_deck(deck_name)
    
    if note_ids:
        # Verwijder de kaarten eerst
        delete_notes_payload = {
            "action": "deleteNotes",
            "version": 6,
            "params": {
                "notes": note_ids
            }
        }
        requests.post('http://localhost:8765', json=delete_notes_payload)
    
    # Verwijder vervolgens het deck
    delete_deck_payload = {
        "action": "deleteDecks",
        "version": 6,
        "params": {
            "decks": [deck_name],
            "cardsToo": True  # Zorgt ervoor dat de kaarten worden verwijderd
        }
    }
    
    response = requests.post('http://localhost:8765', json=delete_deck_payload)
    return response.json()

# Functie om dmenu te gebruiken om een deck te selecteren
def select_deck_with_dmenu(decks):
    dmenu_input = "\n".join(decks).encode('utf-8')
    result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select a deck to delete'], input=dmenu_input, stdout=subprocess.PIPE)
    selected_deck = result.stdout.decode('utf-8').strip()
    return selected_deck

# Functie om bevestiging te vragen voor verwijdering
def confirm_deletion():
    result = subprocess.run(['dmenu', '-p', 'Type SURE to confirm:'], input=''.encode('utf-8'), stdout=subprocess.PIPE)
    confirmation = result.stdout.decode('utf-8').strip()
    return confirmation == "SURE"

# Hoofdprogramma
def main():
    # Haal alle bestaande decks op
    decks = get_all_decks()
    
    if not decks:
        print("Geen decks gevonden.")
        return
    
    # Selecteer een deck om te verwijderen
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("Geen deck geselecteerd, bewerking geannuleerd.")
        return
    
    # Bevestiging voordat het deck wordt verwijderd
    if not confirm_deletion():
        print("Verwijdering geannuleerd.")
        return
    
    # Verwijder het geselecteerde deck, inclusief de kaarten
    delete_response = delete_deck(selected_deck)
    if delete_response.get('error'):
        print(f"Fout bij het verwijderen van deck: {delete_response['error']}")
    else:
        print(f"Deck '{selected_deck}' succesvol verwijderd.")

if __name__ == "__main__":
    main()
