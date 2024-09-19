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

# Functie om alle notes in een deck te vinden en te verwijderen
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

def delete_notes(note_ids):
    url = 'http://localhost:8765'
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "action": "deleteNotes",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# Functie om dmenu te gebruiken om een deck te selecteren
def select_deck_with_dmenu(decks):
    dmenu_input = "\n".join(decks).encode('utf-8')
    result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select a deck to empty'], input=dmenu_input, stdout=subprocess.PIPE)
    selected_deck = result.stdout.decode('utf-8').strip()
    return selected_deck

# Hoofdprogramma
def main():
    # Haal alle bestaande decks op
    decks = get_all_decks()
    
    if not decks:
        print("Geen decks gevonden.")
        return
    
    # Selecteer een deck om leeg te maken
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("Geen deck geselecteerd, bewerking geannuleerd.")
        return
    
    # Verwijder alle kaarten in het geselecteerde deck
    note_ids = get_note_ids_from_deck(selected_deck)
    if note_ids:
        delete_notes(note_ids)
        print(f"Alle kaarten verwijderd uit deck: {selected_deck}")
    else:
        print(f"Geen kaarten om te verwijderen in deck: {selected_deck}")

if __name__ == "__main__":
    main()
