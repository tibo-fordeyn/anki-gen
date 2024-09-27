#!/usr/bin/env python3

import sys
import subprocess
import requests
import json

def get_all_decks():
    '''
    Getting all decks from Anki
    '''
    url = 'http://localhost:8765'
    headers = {'Content-Type': 'application/json'}

    payload = {
        "action": "deckNames",
        "version": 6
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        decks = response.json().get('result', [])
        return decks
    except requests.exceptions.RequestException as e:
        print(f"Error fetching decks: {e}")
        subprocess.run(['notify-send', 'You do not have an anki instance running!!'])
        sys.exit(1)


def get_note_ids_from_deck(deck_name):
    '''
    Get cards
    '''
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
    '''
    Delete cards
    '''
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

def select_deck_with_dmenu(decks):
    '''
    Dmenu selection
    '''
    dmenu_input = "\n".join(decks).encode('utf-8')
    result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select a deck to empty'], input=dmenu_input, stdout=subprocess.PIPE)
    selected_deck = result.stdout.decode('utf-8').strip()
    return selected_deck

# Hoofdprogramma
def main():
    decks = get_all_decks()
    
    if not decks:
        print("No decks found.")
        subprocess.run(['notify-send', "No decks found!"])
        return
    
    # Selecteer een deck om leeg te maken
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("No deck selected.")
        subprocess.run(['notify-send', "No deck selected!"])
        return
    
    # Verwijder alle kaarten in het geselecteerde deck
    note_ids = get_note_ids_from_deck(selected_deck)
    if note_ids:
        delete_notes(note_ids)
        print(f"Cards deleted: {selected_deck}")
        subprocess.run(['notify-send', f"Cards deleted: {selected_deck}"])
    else:
        print(f"No cards to delete: {selected_deck}")
        subprocess.run(['notify-send', f"No cards to delete: {selected_deck}"])


if __name__ == "__main__":
    main()
