#!/usr/bin/env python3
import sys
import re
import os

def main():
    if len(sys.argv) != 2:
        print("Gebruik: parser.py <input.tex>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = os.path.expanduser("~/.local/share/anki-gen/files/cards.txt")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Deleted comments, keeps newlines
    content = re.sub(r'%.*', '', content)

    # DEFINE YOUR BOX COMMANDS HERE
    kader_commands = {
        'dfn': 'Definition',
        'prf': 'Proof',
        'lmm': 'Lemma',
        'cor': 'Corollary',
        'prop': 'Proposition',
        'thm': 'theorem',
        'idea': 'Idea',
        'clar': 'Clarification',
        'rem': 'Reminder',
        'add': 'Addendum',
        'ex': 'Example',
        'qs': 'Question',
        'exqs': 'Exam Question',
        'bsl': 'Conclusion',
    }

    # patterns for commands
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

        # Determine order
        matches = [(next_kader, 'kader'), (next_akq, 'akq'), (next_akns, 'akns')]
        matches = [(m, t) for m, t in matches if m]
        if not matches:
            break  

        # Closest command
        next_match, cmd_type = min(matches, key=lambda x: x[0].start())

        # Update index
        idx = next_match.end()

        # get box type
        if cmd_type == 'kader':
            kader_cmd = next_match.group(1)
            kader_type = kader_commands[kader_cmd]
            title, idx = extract_brace_content(content, idx)
            title = title.strip()
            kader_stack.append((kader_type, title))
        elif cmd_type == 'akq':
            # Are we expecting a question?
            if expecting != 'command':
                # Bad question
                current_question = None
            # Get question
            question, idx = extract_brace_content(content, idx)
            question = question.strip()
            if question:
                current_question = question
                expecting = 'answer'
            else:
                # Empty question
                current_question = None
                expecting = 'command'
        elif cmd_type == 'akns':
            # Expecting an answer?
            if expecting != 'answer':
                # Bad answer
                _, idx = extract_brace_content(content, idx)
                continue
            # gettng answer
            answer, idx = extract_brace_content(content, idx)
            answer = answer.strip()
            if answer and current_question:
                # Box type
                if kader_stack:
                    current_kader_type, current_title = kader_stack[-1]
                else:
                    current_kader_type, current_title = 'qs', '/'
                # Adding the card
                card = {
                    'type': current_kader_type,
                    'title': current_title,
                    'question': current_question,
                    'answer': answer,
                }
                cards.append(card)
            current_question = None
            expecting = 'command'
        idx = next_match.end()

    # Notice we're assuming boxes are closed properly

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
    content = text[start:index-1]  # Getting rid of }
    return content, index

if __name__ == '__main__':
    main()
