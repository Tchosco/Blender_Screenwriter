"""Pure Python planning. Frames are 1-based, with exclusive beat ends."""
import math
import re
from dataclasses import asdict, dataclass

try:
    from ..fountain import Fountain
except ImportError:  # Standalone tests / CLI, without loading the Blender add-on.
    from fountain import Fountain


@dataclass(frozen=True)
class Beat:
    kind: str
    text: str
    character: str
    start: int
    end: int
    camera: str


@dataclass(frozen=True)
class Plan:
    heading: str
    characters: tuple
    fps: int
    frame_end: int
    beats: tuple

    def to_dict(self):
        return asdict(self)


def build_plan(script, duration=40, fps=24):
    """One scene, exactly two speaking characters, 30–60 seconds.

    SHOT notes select WIDE or a character name for the next beat only.
    Actions get wide shots, dialogue gets the speaker camera by default.
    Natural-language actions remain descriptions, not executable instructions.
    """
    if not math.isfinite(duration) or not 30 <= duration <= 60:
        raise ValueError('M1 duration must be between 30 and 60 seconds')
    if not isinstance(fps, int) or not 1 <= fps <= 60:
        raise ValueError('FPS must be an integer between 1 and 60')
    if not script.strip():
        raise ValueError('The Fountain script is empty')
    elements = Fountain(script).elements
    headings = [e for e in elements if e.element_type == 'Scene Heading']
    if len(headings) != 1:
        raise ValueError('M1 requires exactly one scene heading')
    raw, characters = [], []
    speaker, shot, inside = '', None, False
    for element in elements:
        kind, text = element.element_type, element.element_text.strip()
        if element.is_dual_dialogue:
            raise ValueError('M1 does not support simultaneous dialogue')
        if kind == 'Scene Heading':
            inside = True
        elif not inside:
            continue
        elif kind == 'Character':
            speaker = re.sub(r'\s*\([^)]*\)\s*$', '', text).strip()
        elif kind == 'Comment':
            note = element.original_content.strip().strip('[]').strip()
            if note.upper().startswith('SHOT:'):
                if shot is not None:
                    raise ValueError('Each SHOT note must be followed by an action or dialogue')
                shot = note.split(':', 1)[1].strip()
        elif kind in ('Dialogue', 'Action') and text:
            character = speaker if kind == 'Dialogue' else ''
            if kind == 'Dialogue' and not character:
                raise ValueError('Dialogue has no character')
            if character and character not in characters:
                characters.append(character)
            raw.append((kind, text, character, shot))
            shot = None
    if shot is not None:
        raise ValueError('Trailing SHOT note has no action or dialogue')
    if len(characters) != 2:
        raise ValueError('M1 requires exactly two speaking characters')
    if any(c.upper() == 'WIDE' for c in characters):
        raise ValueError('WIDE is reserved for the wide camera')
    total = round(duration * fps)
    # One second minimum per beat; remaining frames follow word counts.
    if len(raw) * fps > total:
        raise ValueError('Too many beats for the requested duration (minimum 1 second each)')
    weights = [max(1, len(item[1].split())) for item in raw]
    extra = total - len(raw) * fps
    cumulative, cursor, beats = 0, 1, []
    for i, (kind, text, character, requested) in enumerate(raw):
        camera = requested or character or 'WIDE'
        if camera.upper() == 'WIDE':
            camera = 'WIDE'
        if camera not in ['WIDE', *characters]:
            raise ValueError('Unknown SHOT camera: ' + camera)
        cumulative += weights[i]
        end = 1 + (i + 1) * fps + round(extra * cumulative / sum(weights))
        beats.append(Beat(kind, text, character, cursor, end, camera))
        cursor = end
    return Plan(headings[0].original_content, tuple(characters), fps, total, tuple(beats))
