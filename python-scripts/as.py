import os
import subprocess
import requests
import json

# Bestanden en directories
CARDS_FILE = os.path.expanduser("~/.local/bin/anki/files/cards.txt")

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

# Functie om kaarten toe te voegen vanuit een bestand (cards.txt)
def add_note_to_anki(deck, question, answer):
    url = 'http://localhost:8765'
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck,
                "modelName": "Basic",
                "fields": {
                    "Front": question,
                    "Back": answer
                }
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# Functie om een nieuw deck aan te maken in Anki
def create_new_deck(deck_name):
    payload = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck_name
        }
    }
    response = requests.post('http://localhost:8765', json=payload)
    return response.json()

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

# Functie om het kaartenbestand te lezen (cards.txt)
def read_cards_from_file(file_path):
    cards = []
    with open(file_path, 'r') as file:
        content = file.read()
        card_entries = content.split("----------")  # Splitsen op de scheidingsteken
        for entry in card_entries:
            if entry.strip():  # Als de entry niet leeg is
                question, answer = entry.split("||||||||||")
                cards.append((question.strip(), answer.strip()))
    return cards

# Functie om dmenu te gebruiken om een deck te selecteren
def select_deck_with_dmenu(decks):
    dmenu_input = "\n".join(decks).encode('utf-8')
    result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select or create a deck'], input=dmenu_input, stdout=subprocess.PIPE)
    selected_deck = result.stdout.decode('utf-8').strip()
    return selected_deck

# Hoofdprogramma voor Anki Cards Switch (leader as)
def main():
    # Stap 1: Haal alle bestaande decks op
    decks = get_all_decks()
    
    # Stap 2: Toon decks via dmenu en laat de gebruiker een map kiezen of een nieuwe naam invoeren
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("Geen deck geselecteerd, bewerking geannuleerd.")
        return
    
    # Stap 3: Controleer of de geselecteerde naam een nieuw deck is of een bestaand deck
    if selected_deck not in decks:
        # Maak een nieuw deck aan
        create_response = create_new_deck(selected_deck)
        if create_response.get('error'):
            print(f"Fout bij het aanmaken van nieuw deck: {create_response['error']}")
            return
        print(f"Nieuw deck '{selected_deck}' aangemaakt.")
    
    # Stap 4: Verwijder alle kaarten in het geselecteerde deck
    note_ids = get_note_ids_from_deck(selected_deck)
    if note_ids:
        delete_notes(note_ids)
        print(f"Alle kaarten verwijderd uit deck: {selected_deck}")
    
    # Stap 5: Lees kaarten uit cards.txt en voeg ze toe aan het geselecteerde deck
    cards = read_cards_from_file(CARDS_FILE)
    for question, answer in cards:
        add_note_to_anki(selected_deck, question, answer)
        print(f"Kaartje toegevoegd: {question} -> {answer}")
    
    print(f"Kaartjes in deck '{selected_deck}' vervangen door de inhoud van {CARDS_FILE}")

if __name__ == "__main__":
    main()
