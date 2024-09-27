#!/usr/bin/env python3

import os
import subprocess
import requests
import json
import sys

# To activate the parser and give it the filename
if len(sys.argv) < 2:
    print("No path given.")
    sys.exit(1)
input_file = sys.argv[1]
subprocess.run(['python3', os.path.expanduser('~/.local/share/anki-gen/parser/parser.py'), input_file])

CARDS_FILE = os.path.expanduser("~/.local/share/anki-gen/files/cards.txt")

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

def add_note_to_anki(deck, question, answer):
    '''
    Adding cards from cards.txt
    '''
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
                },
                "options": {
                    "allowDuplicate": True,
                    "duplicateScope": "deck"
                }
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error adding note: {e}")
        return {"error": str(e)}

def create_new_deck(deck_name):
    '''
    Making new deck in Anki
    '''
    payload = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck_name
        }
    }
    try:
        response = requests.post('http://localhost:8765', json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating deck: {e}")
        return {"error": str(e)}

def read_cards_from_file(file_path):
    '''
    Reading cards.txt
    '''
    cards = []
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            card_entries = content.split("----------")  
            for entry in card_entries:
                if entry.strip():  # Makes sure card isn't empty
                    try:
                        question, answer = entry.split("||||||||||")
                        cards.append((question.strip(), answer.strip()))
                    except ValueError:
                        print(f"Invalid card format in entry: {entry}")
        return cards
    except FileNotFoundError:
        print(f"Cards file not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading cards file: {e}")
        sys.exit(1)

def select_deck_with_dmenu(decks):
    '''
    Using dmenu for selection
    '''
    dmenu_input = "\n".join(decks).encode('utf-8')
    try:
        result = subprocess.run(['dmenu', '-l', '10', '-p', 'Select or create a deck'], input=dmenu_input, stdout=subprocess.PIPE)
        selected_deck = result.stdout.decode('utf-8').strip()
        return selected_deck
    except Exception as e:
        print(f"Error with dmenu: {e}")
        subprocess.run(['notify-send', f'Dmenu error: {e}'])
        sys.exit(1)

def main():
    # Step one - get decks
    decks = get_all_decks()
    
    # Step two - select deck
    selected_deck = select_deck_with_dmenu(decks)
    
    if not selected_deck:
        print("No deck selected!")
        subprocess.run(['notify-send', 'No deck selected!'])
        return
    
    # Step three - new deck or selected deck?
    if selected_deck not in decks:
        create_response = create_new_deck(selected_deck)
        if create_response.get('error'):
            print(f"Couldn't add deck: {create_response['error']}")
            subprocess.run(['notify-send', f"There was an error: {create_response['error']}"])
            return
        print(f"New deck created: '{selected_deck}'")
    
    # Step four - read from cards.txt and add them, not deleting the previous cards
    cards = read_cards_from_file(CARDS_FILE)
    for question, answer in cards:
        response = add_note_to_anki(selected_deck, question, answer)
        if response.get('error'):
            print(f"Couldn't add card: {response['error']}")
        else:
            print(f"Added card: {question} -> {answer}")
    
    print(f"All cards processed for deck '{selected_deck}' from {CARDS_FILE}")
    subprocess.run(['notify-send', f"All cards processed for deck '{selected_deck}' from {CARDS_FILE}"])


if __name__ == "__main__":
    main()
