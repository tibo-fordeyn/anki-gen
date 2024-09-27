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
    Get al cards from a deck
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

def delete_deck(deck_name):
    '''
    Deletes deck and it's cards
    '''
    note_ids = get_note_ids_from_deck(deck_name)
    
    if note_ids:
        delete_notes_payload = {
            "action": "deleteNotes",
            "version": 6,
            "params": {
                "notes": note_ids
            }
        }
        requests.post('http://localhost:8765', json=delete_notes_payload)
    
    delete_deck_payload = {
        "action": "deleteDecks",
        "version": 6,
        "params": {
            "decks": [deck_name],
            "cardsToo": True  
        }
    }
    
    response = requests.post('http://localhost:8765', json=delete_deck_payload)
    return response.json()

def select_deck_with_dmenu(decks):
    '''
    Using dmenu to select deck
    '''
    dmenu_input = "\n".join(decks).encode('utf-8')
    result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select a deck to delete'], input=dmenu_input, stdout=subprocess.PIPE)
    selected_deck = result.stdout.decode('utf-8').strip()
    return selected_deck

def confirm_deletion():
    '''
    Conformation
    '''
    options = "YES              \nNO".encode('utf-8')
    prompt = "Are you sure you want to delete this deck? "
    result = subprocess.run(['dmenu', '-p', prompt], input=options, stdout=subprocess.PIPE)
    confirmation = result.stdout.decode('utf-8').strip()
    return confirmation == "YES"


def main():
    decks = get_all_decks()
    
    if not decks:
        print("No decks found.")
        subprocess.run(['notify-send', 'No decks found'])
        return
    
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("No deck selected.")
        subprocess.run(['notify-send', 'No deck selected'])
        return
    
    if not confirm_deletion():
        print("Didn't delete deck.")
        subprocess.run(['notify-send', "Didn't delete deck"])
        return
    
    delete_response = delete_deck(selected_deck)
    if delete_response.get('error'):
        print(f"Error: {delete_response['error']}")
        subprocess.run(['notify-send', f"Error deleting deck: {delete_response['error']}"])
    else:
        print(f"Deck '{selected_deck}' deleted.")
        subprocess.run(['notify-send', 'Deck was deleted'])

if __name__ == "__main__":
    main()
