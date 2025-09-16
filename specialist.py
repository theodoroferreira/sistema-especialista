import random
import os
import subprocess
import time

import musicpy as mp
import pygame
from musicpy.musicpy import C

FLUIDSYNTH_PATH = r'C:\Program Files\fluidsynth\bin\fluidsynth.exe'
SOUND_FONT = 'FluidR3_GM.sf2'
INPUT_MIDI = 'temp.mid'
OUTPUT_WAV = 'temp.wav'

KNOWLEDGE_BASE = {
    'feliz': {
        'description': 'Progressões alegres e edificantes, com forte senso de resolução e brilho. Comuns em pop, hinos e canções infantis.',
        'progressions': [
            ['I', 'IV', 'V', 'I'],
            ['I', 'V', 'vi', 'IV'],
            ['I', 'vi', 'IV', 'V'],
            ['IV', 'I', 'V', 'vi'],
            ['i', 'V', 'i', 'VI'],
            ['i', 'iv', 'V', 'i'],
            ['VI', 'VII', 'i', 'i'],
            ['i', 'VII', 'VI', 'V']
        ]
    },
    'triste': {
        'description': 'Progressões melancólicas e emotivas, frequentemente usando acordes menores e movimentos descendentes.',
        'progressions': [
            ['I', 'iii', 'IV', 'V'],
            ['IV', 'I', 'V', 'vi'],
            ['I', 'V', 'vi', 'iii'],
            ['vi', 'IV', 'I', 'V'],
            ['i', 'VI', 'III', 'VII'],
            ['i', 'iv', 'v', 'i'],
            ['i', 'iv', 'VI', 'V'],
            ['i', 'VII', 'VI', 'iv']
        ]
    },
    'epico': {
        'description': 'Progressões grandiosas e poderosas, que criam um sentimento de triunfo, aventura e drama.',
        'progressions': [
            ['I', 'bVII', 'IV', 'I'],
            ['IV', 'I', 'V', 'I'],
            ['vi', 'IV', 'I', 'V'],
            ['I', 'V', 'IV', 'V'],
            ['i', 'VI', 'VII', 'i'],
            ['i', 'iv', 'V7', 'i'],
            ['i', 'VI', 'iv', 'V'],
            ['i', 'VII', 'III', 'VI']
        ]
    },
    'calmo': {
        'description': 'Progressões suaves e relaxantes, com movimento harmônico lento e acordes que se misturam suavemente.',
        'progressions': [
            ['I', 'IV', 'I', 'IV'],
            ['Imaj7', 'IVmaj7', 'Imaj7', 'IVmaj7'],
            ['I', 'iii', 'IV', 'I'],
            ['I', 'V', 'IV', 'I'],
            ['i', 'iv', 'i', 'iv'],
            ['im7', 'iv7', 'im7', 'iv7'],
            ['i', 'VI', 'iv', 'i'],
            ['i', 'VII', 'VI', 'VII']
        ]
    },
    'misterioso': {
        'description': 'Progressões que criam suspense e ambiguidade, evitando resoluções claras e usando acordes dissonantes.',
        'progressions': [
            ['I', 'Iaug', 'IV', 'V'],
            ['I', 'bVI', 'bVII', 'I'],
            ['IV', 'iv', 'I', 'I'],
            ['I', 'bIII', 'IV', 'I'],
            ['i', 'ii°', 'V', 'i'],
            ['i', 'i(maj7)', 'VI', 'V'],
            ['i', 'iv', 'bVII', 'III'],
            ['i', 'bII', 'i', 'V']
        ]
    },
    'dancante_groovy': {
        'description': 'Progressões cíclicas e rítmicas com uma sensação de movimento constante. Comuns em funk, disco, EDM e reggae.',
        'progressions': [
            ['I7', 'IV7', 'I7', 'IV7'],
            ['I', 'V', 'vi', 'IV'],
            ['vi', 'IV', 'I', 'V'],
            ['I', 'iii', 'IV', 'I'],
            ['im7', 'ivm7', 'im7', 'ivm7'],
            ['i', 'VII', 'VI', 'VII'],
            ['i', 'III', 'VI', 'VII'],
            ['i', 'v', 'i', 'v']
        ]
    }
}

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
NATURAL_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

MAJOR_KEY_CHORDS = ['', 'm', 'm', '', '', 'm', 'dim']
MINOR_KEY_CHORDS = ['m', 'dim', '', 'm', 'm', '', '']

ROMAN_MAP_ADVANCED = {
    'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6,
    'bII': 1, 'bIII': 2, 'bVI': 5, 'bVII': 6,
    'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4, 'vi': 5, 'vii': 6,
    'ii°': 1, 'i(maj7)': 0, 'im7': 0, 'ivm7': 3,
    'I7': 0, 'IV7': 3, 'V7': 4
}

CHORD_QUALITY_OVERRIDE = {
    'bVII': '',
    'ii°': 'dim',
    'i(maj7)': 'maj7',
    'im7': 'm7',
    'ivm7': 'm7',
    'I7': '7',
    'IV7': '7',
    'V7': '7'
}


def roman_to_chord(numeral, harmonic_field):
    try:
        base_index = ROMAN_MAP_ADVANCED[numeral]
        chord = harmonic_field[base_index]

        if numeral in CHORD_QUALITY_OVERRIDE:
            root_note = chord.replace('m', '').replace('dim', '').replace('maj7', '').replace('7', '')
            chord = root_note + CHORD_QUALITY_OVERRIDE[numeral]
        return chord
    except KeyError:
        return f"({numeral}?)"


def get_harmonic_field(root_note: str) -> list[str]:
    is_minor = 'm' in root_note
    root_note_name = root_note.replace('m', '')

    try:
        root_index = NOTES.index(root_note_name.upper())
    except ValueError:
        return None

    scale_intervals = NATURAL_MINOR_SCALE_INTERVALS if is_minor else MAJOR_SCALE_INTERVALS
    chord_qualities = MINOR_KEY_CHORDS if is_minor else MAJOR_KEY_CHORDS

    harmonic_field = []
    for i in range(7):
        note_index = (root_index + scale_intervals[i]) % 12
        note_name = NOTES[note_index]

        chord_name = f"{note_name}{chord_qualities[i]}"
        harmonic_field.append(chord_name)

    return harmonic_field


def generate_progression(key: str, vibe: str) -> dict:
    if vibe not in KNOWLEDGE_BASE:
        return {'error': f"Vibe '{vibe}' não encontrada na base de conhecimento."}

    rule = KNOWLEDGE_BASE[vibe]
    roman_progression = random.choice(rule['progressions'])
    harmonic_field = get_harmonic_field(key)
    if not harmonic_field:
        return {'erro': f"O tom '{key}' não é válido."}

    chord_progression = [roman_to_chord(numeral, harmonic_field) for numeral in roman_progression]

    return {
        'description': rule['description'],
        'roman_progression': ' - '.join(roman_progression),
        'chords': ' -> '.join(chord_progression),
        'vibe': vibe  # agora incluímos a vibe para playChords
    }


def parseMidiFile():
    if not os.path.exists(SOUND_FONT):
        print(f"Erro: arquivo SoundFont não encontrado '{SOUND_FONT}'")
        return False
    if not os.path.exists(INPUT_MIDI):
        print(f"Erro: arquivo MIDI não encontrado '{INPUT_MIDI}'")
        return False

    command = [
        FLUIDSYNTH_PATH,
        '-ni',
        SOUND_FONT,
        INPUT_MIDI,
        '-F',
        OUTPUT_WAV,
        '-r',
        '44100'
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Sucesso! Falha ao converter '{OUTPUT_WAV}'")
        return True
    except subprocess.CalledProcessError as e:
        print("Erro durante a conversão:")
        print(e.stderr.decode())
        return False
    except FileNotFoundError:
        print("Erro: 'fluidsynth' comando não encontrado.")
        return False


def get_vibe_settings(vibe):
    settings = {
        'feliz': {'bpm': 130, 'instrument': 29, 'style': 'batido'},
        'triste': {'bpm': 80, 'instrument': 5, 'style': 'dedilhado'},
        'epico': {'bpm': 100, 'instrument': 30, 'style': 'batido'},
        'calmo': {'bpm': 60, 'instrument': 2, 'style': 'dedilhado'},
        'misterioso': {'bpm': 90, 'instrument': 80, 'style': 'dedilhado'},
        'dancante_groovy': {'bpm': 110, 'instrument': 27, 'style': 'ritmico'}
    }
    return settings.get(vibe, {'bpm': 100, 'instrument': 1, 'style': 'batido'})


def playChords(result):

    chord_string = result['chords']
    chord_list = [c.strip() for c in chord_string.split('->')]

    vibe_settings = get_vibe_settings(result.get('vibe', 'feliz'))
    bpm = vibe_settings['bpm']
    instrument = vibe_settings['instrument']
    style = vibe_settings['style']

    guitar = None

    for chord_name in chord_list:
        if style == 'dedilhado':
            chord_obj = (
                    C(chord_name, 2, 1 / 4, 0 / 8) +
                    C(chord_name, 2, 1 / 4, 0 / 8) +
                    C(chord_name, 2, 1 / 4, 0 / 8) +
                    C(chord_name, 2, 1 / 4, 0 / 8)
            )
        elif style == 'ritmico':
            chord_obj = (C(chord_name, 2, 1 / 8, 0 / 8) ^ 2)
        else:
            chord_obj = (
                    C(chord_name, 2, 1 / 6, 0 / 8) ^
                    C(chord_name, 2, 1 / 6, 0 / 8) ^
                    C(chord_name, 2, 1 / 6, 0 / 8) ^
                    C(chord_name, 2, 1 / 6, 0 / 8)
            )

        if guitar is None:
            guitar = chord_obj
        else:
            guitar |= chord_obj

    mp.play(guitar, bpm=bpm, instrument=instrument)

    parseMidiFile()

    if not os.path.exists(OUTPUT_WAV):
        print(f"Erro: '{OUTPUT_WAV}' não encontrado.")
    else:
        try:
            pygame.init()
            pygame.mixer.init()

            sound = pygame.mixer.Sound(OUTPUT_WAV)
            sound.set_volume(1.0)
            sound.play()

            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(10)

            time.sleep(1)

        except pygame.error as e:
            print(f"\nErro pygame: {e}")

        finally:
            if pygame.get_init():
                pygame.quit()


if __name__ == "__main__":
    valid_keys = [note for note in NOTES]
    valid_keys.extend([f"{note}m" for note in NOTES])
    valid_vibes = list(KNOWLEDGE_BASE.keys())

    while True:
        print("\nNotas disponíveis", ", ".join(valid_keys[:6]) + "..., etc.")
        print("Vibes disponíveis:", ", ".join(valid_vibes))

        user_key = input(f"\nInsira o tom desejado(e.g., C, Gm, F#): ")
        if user_key not in valid_keys:
            print(f"Erro: '{user_key}' não é um tom válido. Tente outro.")
            continue

        user_vibe = input(f"Insira a vibe desejada: ").lower()
        if user_vibe not in valid_vibes:
            print(f"Erro: '{user_vibe}' não é uma vibe válida. Tente outra.")
            continue

        result = generate_progression(user_key, user_vibe)

        playChords(result)

        if 'error' in result:
            print(f"Erro: {result['error']}")
        else:
            print("\nProgressão: ")
            print(f"   - Descrição da vibe: {result['description']}")
            print(f"   - Notação da progressão:   {result['roman_progression']}")
            print(f"   - Acordes da progressão:      {result['chords']}")

        another = input("\nGerar outra progressão? (s/n): ").lower()
        if another != 's':
            break
