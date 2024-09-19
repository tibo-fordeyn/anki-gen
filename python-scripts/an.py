import subprocess
import requests
import json

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

# Functie om een nieuwe mapnaam in te voeren via dmenu
def get_new_directory_name():
    result = subprocess.run(['dmenu', '-p', 'Enter new deck name:'], input=''.encode('utf-8'), stdout=subprocess.PIPE)
    new_dir_name = result.stdout.decode('utf-8').strip()
    return new_dir_name

# Hoofdprogramma
def main():
    # Vraag de gebruiker om een nieuwe mapnaam in te voeren
    new_dir_name = get_new_directory_name()
    
    if not new_dir_name:
        print("Geen naam ingevoerd, bewerking geannuleerd.")
        return
    
    # Maak het nieuwe deck aan
    create_response = create_new_deck(new_dir_name)
    if create_response.get('error'):
        print(f"Fout bij het aanmaken van nieuw deck: {create_response['error']}")
    else:
        print(f"Nieuw deck '{new_dir_name}' aangemaakt.")

if __name__ == "__main__":
    main()
