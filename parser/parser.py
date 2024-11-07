#!/usr/bin/env python3
import sys
import re
import os
import shutil
from subprocess import run

# DEFINEER JE KADER COMMANDO'S HIER
kader_commands = {
    'dfn': 'Definitie',
    'prf': 'Bewijs',
    'lmm': 'Lemma',
    'cor': 'Corollarium',
    'prop': 'Eigenschap',
    'thm': 'Stelling',
    'idea': 'Idee',
    'clar': 'Verduidelijking',
    'rem': 'Herinnering',
    'add': 'Addendum',
    'ex': 'Voorbeeld',
    'qs': 'Vraag',
    'exqs': 'Examenvraag',
    'bsl': 'Besluit',
}

def main():
    if len(sys.argv) != 2:
        print("Gebruik: parser.py <input.tex>")
        sys.exit(1)

    input_file = sys.argv[1]
    # Bepaal de basisdirectory van het inputbestand
    base_dir = os.path.dirname(os.path.abspath(input_file))
    output_file = os.path.expanduser("~/.local/share/anki-gen/files/cards.txt")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Patronen voor commando's
    kader_pattern = re.compile(r'\\(' + '|'.join(kader_commands.keys()) + r')\s*\{')
    akq_pattern = re.compile(r'\\akq\s*\{')
    akns_pattern = re.compile(r'\\akns\s*\{')

    idx = 0
    length = len(content)
    cards = []
    kader_stack = []
    expecting = 'command'  # Kan 'command', 'answer' zijn
    current_question = None

    while idx < length:
        next_kader = kader_pattern.search(content, idx)
        next_akq = akq_pattern.search(content, idx)
        next_akns = akns_pattern.search(content, idx)

        # Bepaal de volgorde
        matches = [(next_kader, 'kader'), (next_akq, 'akq'), (next_akns, 'akns')]
        matches = [(m, t) for m, t in matches if m]
        if not matches:
            break  

        # Dichtstbijzijnde commando
        next_match, cmd_type = min(matches, key=lambda x: x[0].start())

        # Controleer of het commando zich op een regel bevindt die begint met '%'
        match_start = next_match.start()
        # Vind het begin van de regel
        line_start = content.rfind('\n', 0, match_start) + 1  # +1 om voorbij de newline te gaan
        line = content[line_start:match_start]
        if line.lstrip().startswith('%'):
            # Sla deze match over
            idx = next_match.end()
            continue

        # Update index naar het einde van het commando (\cmd{)
        idx = next_match.end() - 1  # Ga naar de positie van de '{'

        # Krijg het kader type
        if cmd_type == 'kader':
            kader_cmd = next_match.group(1)
            kader_type = kader_commands[kader_cmd]
            title, idx = extract_brace_content(content, idx)
            title = title.strip()
            # Verwerk inline wiskunde, vetgedrukte tekst, lijsten en kader commando's in de titel
            title = replace_inline_math(title)
            title = replace_bold_text(title)
            title = replace_kader_commands_in_text(title)
            title = replace_itemize_enumerate(title)
            kader_stack.append((kader_type, title))
        elif cmd_type == 'akq':
            # Verwachten we een vraag?
            if expecting != 'command':
                # Foute vraag
                current_question = None
            # Krijg vraag
            question, idx = extract_brace_content(content, idx)
            question = question.strip()
            if question:
                current_question = question
                expecting = 'answer'
            else:
                # Lege vraag
                if kader_stack:
                    # Als er een kader is, vervang lege vraag door ';'
                    current_question = ';'
                    expecting = 'answer'
                else:
                    current_question = None
                    expecting = 'command'
        elif cmd_type == 'akns':
            # Verwachten we een antwoord?
            if expecting != 'answer':
                # Fout antwoord
                _, idx = extract_brace_content(content, idx)
                continue
            # Krijg antwoord
            answer, idx = extract_brace_content(content, idx)
            answer = answer.strip()
            if answer and current_question:
                # Kader type
                if kader_stack:
                    current_kader_type, current_title = kader_stack[-1]
                else:
                    current_kader_type, current_title = 'qs', '/'
                # Verwerk inline wiskunde, vetgedrukte tekst, lijsten en kader commando's in vraag en antwoord
                question_processed = replace_inline_math(current_question)
                question_processed = replace_bold_text(question_processed)
                question_processed = replace_kader_commands_in_text(question_processed)
                question_processed = replace_itemize_enumerate(question_processed)

                answer_processed = replace_inline_math(answer)
                answer_processed = replace_bold_text(answer_processed)
                answer_processed = replace_kader_commands_in_text(answer_processed)
                answer_processed = replace_itemize_enumerate(answer_processed)

                # Verwerk afbeeldingen in vraag en antwoord
                question_processed = process_images(question_processed, base_dir)
                answer_processed = process_images(answer_processed, base_dir)

                # Voeg de kaart toe
                card = {
                    'type': current_kader_type,
                    'title': current_title,
                    'question': question_processed,
                    'answer': answer_processed,
                }
                cards.append(card)
            current_question = None
            expecting = 'command'
        # idx wordt al bijgewerkt in extract_brace_content, dus we hoeven het hier niet aan te passen

    # Merk op dat we aannemen dat kaders correct zijn afgesloten

    with open(output_file, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(f"{card['type']}; {card['title']}\n")
            f.write(f"{card['question']}\n")
            f.write('||||||||||\n')
            f.write(f"{card['answer']}\n")
            f.write('----------\n')

def extract_brace_content(text, index):
    brace_count = 1
    start = index
    index += 1  # Ga naar het eerste teken binnen de accolades
    length = len(text)
    while index < length and brace_count > 0:
        if text[index] == '{':
            brace_count += 1
        elif text[index] == '}':
            brace_count -= 1
        index += 1
    content = text[start+1:index-1]  # Haal de inhoud tussen de accolades op
    return content, index

def replace_inline_math(text):
    # Vervang $...$ door \( ... \) voor inline wiskunde
    text = re.sub(r'\$(.+?)\$', r'\\(\1\\)', text)
    return text

def replace_bold_text(text):
    # Vervang \textbf{...} door <b>...</b>
    # Zorg ervoor dat geneste \textbf{} correct worden verwerkt
    pattern = re.compile(r'\\textbf\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}')
    while pattern.search(text):
        text = pattern.sub(r'<b>\1</b>', text)
    return text

def replace_itemize_enumerate(text):
    # Recursieve functie om geneste lijsten te vervangen
    def parse_lists(text):
        # Regex om \begin{itemize|enumerate} te vinden
        pattern = re.compile(r'\\begin\{(itemize|enumerate)\}')
        while True:
            match = pattern.search(text)
            if not match:
                break
            list_type = match.group(1)
            start = match.start()
            # Vind het overeenkomende \end{...}
            end_tag = f'\\end{{{list_type}}}'
            end = find_matching_end(text, match.end(), end_tag)
            if end == -1:
                break  # Geen einde gevonden, breek de lus
            # Haal de inhoud tussen \begin en \end
            inner_content = text[match.end():end]
            # Vervang geneste lijsten in de inhoud
            inner_content = parse_lists(inner_content)
            # Vervang \item door <li> tags
            items = re.split(r'\\item', inner_content)
            items = [item.strip() for item in items if item.strip()]
            items_html = ''.join(f'<li>{item}</li>' for item in items)
            # Bouw de lijst op
            if list_type == 'itemize':
                list_html = f'<ul>{items_html}</ul>'
            else:
                list_html = f'<ol>{items_html}</ol>'
            # Vervang de originele tekst met de HTML-lijst
            text = text[:start] + list_html + text[end+len(end_tag):]
        return text

    def find_matching_end(text, start_pos, end_tag):
        # Zoek naar het overeenkomende \end{...} met rekening houden met geneste structuren
        pos = start_pos
        depth = 1
        pattern = re.compile(r'\\begin\{(itemize|enumerate)\}|\\end\{(itemize|enumerate)\}')
        while pos < len(text):
            match = pattern.search(text, pos)
            if not match:
                return -1  # Geen einde gevonden
            if match.group(0).startswith('\\begin'):
                depth += 1
            elif match.group(0) == end_tag:
                depth -= 1
                if depth == 0:
                    return match.start()
            pos = match.end()
        return -1  # Geen einde gevonden

    return parse_lists(text)

def replace_kader_commands_in_text(text):
    # Maak een regex pattern om alle kader commando's te vinden
    kader_cmds = list(kader_commands.keys())
    pattern = re.compile(r'\\(' + '|'.join(kader_cmds) + r')\s*\{')
    idx = 0
    while True:
        match = pattern.search(text, idx)
        if not match:
            break
        cmd = match.group(1)
        replacement = kader_commands[cmd]
        # Vind de inhoud tussen de accolades
        content, end_idx = extract_brace_content(text, match.end() - 1)
        # Bouw de vervangende tekst
        replacement_text = f"{replacement}: {content}"
        # Vervang in de tekst
        text = text[:match.start()] + replacement_text + text[end_idx:]
        # Update de index
        idx = match.start() + len(replacement_text)
    return text

def process_images(text, base_dir):
    text = process_incfig_commands(text, base_dir)
    text = process_figure_environments(text, base_dir)
    return text

def process_figure_environments(text, base_dir):
    anki_media_folder = os.path.expanduser('~/.local/share/Anki2/Gebruiker 1/collection.media/')
    # Zoek naar \begin{figure} ... \end{figure} blokken
    figure_pattern = re.compile(r'(\\begin\{figure\}.*?\\end\{figure\})', re.DOTALL)
    matches = figure_pattern.finditer(text)
    for match in matches:
        figure_block = match.group(1)
        # Verwerk eventuele \incfig{...} commando's binnen de figure omgeving
        figure_block_processed = process_incfig_commands(figure_block, base_dir)
        # Zoek naar \includegraphics commando in de figure omgeving
        includegraphics_match = re.search(r'\\includegraphics.*?\{(.*?)\}', figure_block_processed)
        if includegraphics_match:
            image_path = includegraphics_match.group(1).strip().strip('"')
            # Als het een relatieve pad is, converteer het naar absoluut
            if not os.path.isabs(image_path):
                image_path = os.path.join(base_dir, image_path)
            # Kopieer de afbeelding naar de Anki media map
            if os.path.exists(image_path):
                filename = os.path.basename(image_path)
                filename = sanitize_filename(filename)
                destination_path = os.path.join(anki_media_folder, filename)
                if not os.path.exists(destination_path):
                    try:
                        shutil.copy(image_path, destination_path)
                    except Exception as e:
                        print(f"Fout bij kopiëren van afbeelding {image_path}: {e}")
                # Vervang de figure omgeving door HTML code
                # Voeg stijl toe om de afbeelding kleiner te maken
                img_tag = f'<img src="{filename}" style="width:50%;">'  # Pas de breedte aan indien nodig
                # Vervang de volledige figure omgeving door de img tag
                text = text.replace(figure_block, img_tag)
            else:
                print(f"Afbeelding {image_path} niet gevonden.")
                # Vervang de figure omgeving door een placeholder
                text = text.replace(figure_block, f'[Afbeelding {image_path} niet gevonden]')
        else:
            # Als er geen afbeelding gevonden is, verwijder dan de figure omgeving
            text = text.replace(figure_block, '')
    return text

def process_incfig_commands(text, base_dir):
    # Zorg ervoor dat anki_media_folder beschikbaar is
    anki_media_folder = os.path.expanduser('~/.local/share/Anki2/Gebruiker 1/collection.media/')
    # Zoek naar \incfig\{...\} commando's
    incfig_pattern = re.compile(r'\\incfig\{([^}]+)\}')
    matches = incfig_pattern.finditer(text)
    for match in matches:
        incfig_command = match.group(0)
        image_name = match.group(1).strip()
        # Verwacht dat de afbeelding zich bevindt in './figures/' met extensie '.pdf'
        images_dir = os.path.join(base_dir, 'figures')
        # Pad naar het pdf-bestand
        pdf_path = os.path.join(images_dir, image_name + '.pdf')
        if os.path.exists(pdf_path):
            # Converteer de .pdf naar .png
            png_filename = image_name + '.png'
            png_destination_path = os.path.join(anki_media_folder, png_filename)
            if not os.path.exists(png_destination_path):
                try:
                    # Converteer pdf naar png
                    run(['convert', '-density', '300', pdf_path, '-quality', '90', png_destination_path])
                except Exception as e:
                    print(f"Fout bij converteren van pdf naar png voor {pdf_path}: {e}")
                    continue
            # Vervang het \incfig commando door een <img> tag
            img_tag = f'<img src="{png_filename}" style="width:50%;">'  # Pas de breedte aan indien nodig
            # Vervang de \incfig commando en eventuele omliggende figure omgeving
            text = replace_incfig_with_img(text, incfig_command, img_tag)
        else:
            print(f"Afbeelding {pdf_path} niet gevonden.")
            # Vervang het \incfig commando door een placeholder
            text = text.replace(incfig_command, f'[Afbeelding {image_name} niet gevonden]')
    return text

def replace_incfig_with_img(text, incfig_command, img_tag):
    # Verwijder eventuele omringende figure omgeving
    # Zoek naar \begin{figure} vóór incfig_command
    figure_start = text.rfind('\\begin{figure}', 0, text.find(incfig_command))
    figure_end = text.find('\\end{figure}', text.find(incfig_command))
    if figure_start != -1 and figure_end != -1:
        # Vervang het gehele figure blok door de img tag
        figure_block = text[figure_start:figure_end+len('\\end{figure}')]
        text = text.replace(figure_block, img_tag)
    else:
        # Vervang alleen het incfig commando door de img tag
        text = text.replace(incfig_command, img_tag)
    return text

def sanitize_filename(filename):
    # Verwijder eventuele speciale tekens die Anki niet goed kan verwerken
    filename = re.sub(r'[^\w\.\-]', '_', filename)
    return filename

if __name__ == '__main__':
    # Zorg ervoor dat de Anki media map bestaat
    anki_media_folder = os.path.expanduser('~/.local/share/Anki2/Gebruiker 1/collection.media/')
    if not os.path.exists(anki_media_folder):
        os.makedirs(anki_media_folder)
    main()
