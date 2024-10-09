#!/usr/bin/env python3
import sys
import re
import os
import shutil
from subprocess import run

def main():
    if len(sys.argv) != 2:
        print("Gebruik: parser.py <input.tex>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = os.path.expanduser("~/.local/share/anki-gen/files/cards.txt")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

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

        # Update index
        idx = next_match.end()

        # Krijg het kader type
        if cmd_type == 'kader':
            kader_cmd = next_match.group(1)
            kader_type = kader_commands[kader_cmd]
            title, idx = extract_brace_content(content, idx)
            title = title.strip()
            # Verwerk inline wiskunde en vetgedrukte tekst in de titel
            title = replace_inline_math(title)
            title = replace_bold_text(title)
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
                # Verwerk inline wiskunde en vetgedrukte tekst in vraag en antwoord
                question_processed = replace_inline_math(current_question)
                question_processed = replace_bold_text(question_processed)
                question_processed = replace_itemize_enumerate(question_processed)
                answer_processed = replace_inline_math(answer)
                answer_processed = replace_bold_text(answer_processed)
                answer_processed = replace_itemize_enumerate(answer_processed)

                # Verwerk afbeeldingen in vraag en antwoord
                question_processed = process_images(question_processed)
                answer_processed = process_images(answer_processed)

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
        idx = next_match.end()

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
    length = len(text)
    while index < length and brace_count > 0:
        if text[index] == '{':
            brace_count += 1
        elif text[index] == '}':
            brace_count -= 1
        index += 1
    content = text[start:index-1]  # Verwijder de laatste '}'
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
    # Vervang \begin{itemize}...\end{itemize} en \begin{enumerate}...\end{enumerate} door HTML-lijsten
    def replace_list(match):
        list_type = match.group(1)
        items_text = match.group(2)
        # Vervang \item door <li>
        items = re.split(r'\\item', items_text)
        items = [item.strip() for item in items if item.strip()]
        items_html = ''.join(f'<li>{item}</li>' for item in items)
        if list_type == 'itemize':
            return f'<ul>{items_html}</ul>'
        else:
            return f'<ol>{items_html}</ol>'
    pattern = re.compile(r'\\begin\{(itemize|enumerate)\}(.*?)\\end\{\1\}', re.DOTALL)
    text = pattern.sub(replace_list, text)
    return text

def process_images(text):
    # Verwerk \begin{figure} ... \end{figure} blokken
    text = process_figure_environments(text)
    # Verwerk \incfig{...} commando's
    text = process_incfig_commands(text)
    return text

def process_figure_environments(text):
    # Zoek naar \begin{figure} ... \end{figure} blokken
    figure_pattern = re.compile(r'(\\begin\{figure\}.*?\\end\{figure\})', re.DOTALL)
    matches = figure_pattern.finditer(text)
    for match in matches:
        figure_block = match.group(1)
        # Verwerk eventuele \incfig{...} commando's binnen de figure omgeving
        figure_block_processed = process_incfig_commands(figure_block)
        # Zoek naar \includegraphics commando in de figure omgeving
        includegraphics_match = re.search(r'\\includegraphics.*?\{(.*?)\}', figure_block_processed)
        if includegraphics_match:
            image_path = includegraphics_match.group(1).strip().strip('"')
            # Kopieer de afbeelding naar de Anki media map
            filename = os.path.basename(image_path)
            filename = sanitize_filename(filename)
            anki_media_folder = os.path.expanduser('~/.local/share/Anki2/Gebruiker 1/collection.media/')
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
            # Als er geen afbeelding gevonden is, verwijder dan de figure omgeving
            text = text.replace(figure_block, '')
    return text

def process_incfig_commands(text):
    # Zoek naar \incfig{...} commando's
    incfig_pattern = re.compile(r'\\incfig\{([^}]+)\}')
    matches = incfig_pattern.finditer(text)
    for match in matches:
        incfig_command = match.group(0)
        image_name = match.group(1).strip()
        # Verwacht dat de afbeelding zich bevindt in './figures/' met extensie '.pdf_tex' of '.pdf'
        images_dir = os.path.join('/home/dyntif/school/current-subject/nota/', 'figures')  # Pas dit pad aan indien nodig
        # Probeer de afbeelding te vinden met extensie '.pdf_tex' of '.pdf'
        possible_extensions = ['.pdf_tex', '.pdf']
        found_image = False
        for ext in possible_extensions:
            image_path = os.path.join(images_dir, image_name + ext)
            if os.path.exists(image_path):
                found_image = True
                break  # We hebben de afbeelding gevonden
        if found_image:
            # Als het een .pdf_tex is, converteer deze naar .pdf en dan naar .png
            if image_path.endswith('.pdf_tex'):
                pdf_path = os.path.join(images_dir, image_name + '.pdf')
                if not os.path.exists(pdf_path):
                    print(f"PDF bestand {pdf_path} niet gevonden voor {image_path}")
                    continue
            else:
                pdf_path = image_path
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
            print(f"Afbeelding {image_name} niet gevonden in {images_dir}")
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
